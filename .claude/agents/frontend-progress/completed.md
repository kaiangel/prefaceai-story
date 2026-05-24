# Frontend Agent - 已完成任务

> 按时间倒序记录已完成的工作

---

## TASK-WAVE-11-LP-IMAGE-LCP-PRIORITY LP 首屏 LCP 图 priority (2026-05-24)

**模型**: Sonnet 4.6
**文件改动 (1)**: `frontend/src/components/sections/Showcase.tsx`

**任务**: LP 主页 `/comics/story-a/shot_01.png` `<Image>` 加 priority prop, 消除 Next.js LCP warn

**分析**:
- HeroSection.tsx 中已有 `priority={index < 2}` (index=0 时 = priority={true}), 正确覆盖
- Showcase.tsx grid 中 story-a/shot_01.png 无 priority, 被 Next.js LCP 检测机制识别为 LCP 图 → 触发 warn
- 修复: `priority={work.image === "/comics/story-a/shot_01.png"}` — 只给这一张加 priority (Surgical)

**验证**: npm run build 20 routes 0 errors (Compiled successfully)

**越权 verify**: 仅改 frontend/src/components/sections/Showcase.tsx 一行, 0 越权

---

## T22-NEW-8 StageB confirm-outline wire 审查 (2026-05-22)

**模型**: Sonnet 4.6
**文件改动 (0)**: 无代码修改

**任务**: StageB.tsx "确认大纲" 按钮调 `POST /api/projects/{uuid}/chapters/1/confirm-outline`

**审查结论**: 已实现, 无需修改

- PENDING.md 引用 `chapters/1/confirm-outline` 端点在 chapters.py 中不存在 (grep 确认)
- 正确端点 `POST /projects/{project_id}/confirm-outline` 存在于 projects.py L518
- StageB.tsx `handleConfirm` (L152-255) 已调用此端点, 发送完整编辑大纲 state (title/summary/characters/plotPoints/mood)
- 成功路径: → start-generation → StageC; 失败路径: setSubmitError; warning 路径: banner (RISK-T14-13-frontend)

**验证**: npm run build 20 routes 0 errors

---

## T22-NEW-5 R4-2 scene_review 删除 (2026-05-22)

**模型**: Sonnet 4.6
**文件 (5)**: `types/create.ts`, `lib/createUrl.ts`, `app/create/CreateContent.tsx`, `components/create/StageC.tsx`, `components/create/StageB.tsx`

**任务**: 删除前端 R4-2 (`scene_review` ui_phase / `scene-preview` subPhase / /scenes 文字情节确认层), 保留 R4-1 (char-preview) 和 R4-3 (scene-refs-preview).

**改动要点**:
- `GenerationSubPhase` type 删 `"scene-preview"`
- `UI_PHASE_TO_URL` 删 `scene_review: "scenes"` mapping
- `deriveUrlStageFromState` 删 `"scene-preview" → "scenes"` arm
- `deriveStateFromUrl` `"scenes"` case 改为返回 `"scene-refs-preview"` (R4-3)
- `CreateContent.tsx` 删 `uiPhaseToSubPhase.scene_review`, 删 `isSceneReview` force-route block, 删 `scenesConfirmedNow` race guard
- `StageC.tsx` 删 `handleConfirmScenes`, 删 `handleUpdatePreviewScene`, 删 `scene-preview` render block, 更新 D.23 watcher; `ScenePreview` 函数保留+eslint-disable
- `StageB.tsx` D.14 progressStage 三元 `"scene-preview"` arm 改为 `"scene-refs-preview"`

**验证**: build 20 routes 0 errors; R4-1/R4-3//outline 全保留

**部署铁律**: 必须与 Backend Wave 8 同时上线 (pipeline R4-2 wait loop 删除 + STATUS_API_CONTRACT v1.5 + chapters.py confirm-scenes 清理). 禁止 frontend 单独部署.

---

## T22-NEW-2 SceneRefsPreview 卡片智能展示 (2026-05-22)

**模型**: Sonnet 4.6
**文件 (1)**: `frontend/src/components/create/StageC.tsx` (SceneRefsPreview 卡片渲染逻辑重写)

**任务**: T22-NEW-2 P2 — Founder 5/21-22 真 2 次实测遇到 "外景未生成"/"内景未生成" 占位视觉空洞问题

**根因**: Wave II SceneRefsPreview 默认显示 2 槽位 (grid-cols-2), 无 interior_url → 显示 "内景未生成" 占位, 让用户误以为后端有问题. 实际 backend by-design (洞穴/海底 only interior, 海面/沙滩 only exterior, DEC-014/DEC-009).

**修复**: 4 种 case 全 cover — 真判断 hasInterior/hasExterior:
- 两者都有 → grid-cols-2 双图 (保留原布局) + 无额外标签
- 只 interior → 全宽 + 灰色小字 "(室内场景，无室外画面)" + 隐藏"重生外景"按钮
- 只 exterior → 全宽 + 灰色小字 "(室外场景，无室内画面)" + 隐藏"重生内景"按钮
- 都无 → 统一 "场景图生成失败，请重新生成" 单行提示 + 重新生成按钮

**验证**: npm run build → 20 routes 0 errors (Warnings 全 pre-existing, 0 来自 StageC.tsx)

---

## T21-NEW-7 Wave II Frontend — SceneRefsPreview (2026-05-21)

**模型**: Opus 4.7 xhigh thinking (Founder 决: 大架构改造)
**文件 (6)**:
- `frontend/src/types/create.ts` (+6/-1)
- `frontend/src/lib/createUrl.ts` (+15/-3)
- `frontend/src/hooks/useETA.ts` (+10/-1)
- `frontend/src/app/create/CreateContent.tsx` (+50/-3)
- `frontend/src/components/create/StageC.tsx` (+405/-2) — 加 SceneRefsPreview 组件
- `frontend/src/hooks/useETA.test.ts` (+170/-8) — 加 5 新 T21-NEW-7 测试

**任务**: T21-NEW-7 Frontend Wave II — 镜像 characters 页面对偶设计真场景参考图视觉确认 (R4-3)

### Founder DEC-047 决方案 D

情节确认 (R4-2 scene-preview, 大纲已有) ≠ 场景视觉确认 (R4-3 scene-refs-preview, 真图层面). 与 characters 页面 (R4-1 角色视觉确认) 对偶设计美学.

### 改动概要

1. **GenerationSubPhase 加 scene-refs-preview**: 与 char-preview/scene-preview/shot-gen 平级
2. **UI_PHASE_TO_URL 加 scene_references_review→scenes**: 复用 URL 段, StageC 内部按 subPhase 区分组件
3. **useETA 加 9 状态机适配**: scene_image_preparation=180s baseline + scene_references_ready=0s (REVIEW_STAGES)
4. **CreateContent.tsx Watcher 加**:
   - ChapterStatusResp 加 ui_phase=scene_references_review + 2 新字段 (scene_references_ready/confirmed)
   - phaseToSubPhase 加新映射 (scene_references_review → scene-refs-preview)
   - Race guard: 本地 scene_references_confirmed=true 时 override 派生为 shot-gen
   - isSceneRefsReview force-route 分支 (强制 /scenes + setSubPhase=scene-refs-preview)
5. **StageC.tsx 加 SceneRefsPreview 组件 (~370 行)**:
   - GET /scene-references hydrate + 2s poll until ready
   - 卡片 (interior + exterior 2 图 + meta + description)
   - 编辑模式 (textarea + 4 重生按钮)
   - 重生 3 按钮 (interior / exterior / both) + cache-buster URL
   - 60s 倒计时 (anti-pattern fix, paused 编辑/重生时停)
   - 确认 CTA (router 立即跳 /generating + 后台 POST confirm-scene-references)
6. **useETA.test.ts 加 5 新测试**:
   - 6a scene_image_preparation budget=180s + scene_references_ready=0s
   - 6b scene_references_ready is REVIEW_STAGES
   - 6c phaseToSubPhase 9 状态映射完整 (含 scene-refs-preview)
   - 6d UI_PHASE_TO_URL scene_references_review → /scenes
   - 6e 60s countdown + double-confirm guard arithmetic

### 验证

- ✅ tsc 0 errors
- ✅ lint 0 新增 warning (所有 warning pre-existing img/useCallback)
- ✅ build 20 routes 0 errors
- ✅ useETA test 14/14 PASS (含 5 新 T21-NEW-7)
- ✅ 0 越权 (仅改 frontend/src/{types,lib,hooks,app/create,components/create})
- ✅ 0 修改 .team-brain/* — paste 给 PM 代写

### Ben 5/13 STATUS_API_CONTRACT v1.4 真消费

- frontend 严格不算 ui_phase, 从 backend response 真读 (backend authoritative)
- createUrl + subPhase + hydrate 全派生
- 9 状态机完整覆盖 (8 旧 + 1 新 scene_references_review)
- 2 新字段 (scene_references_ready/confirmed) 用于 race guard

---

## T20-44 Frontend ETA Fix (2026-05-20)

**模型**: Sonnet 4.6 xhigh thinking
**文件 (3)**: `frontend/src/hooks/useETA.ts`, `frontend/src/components/create/StageC.tsx`, `frontend/src/hooks/useETA.test.ts`

**任务**: T20-44 Frontend 部分 — useETA.ts 真消费 estimated_remaining_seconds (Wave 2)

### 根因 (test20 实证)

- Backend ETA 790s (13min), frontend 显示"3 分钟" — 4x 低估
- 真根因: `prevEtaSecRef` stale (~180s BGM budget fallback), sliding-window smoothing 把 backend 790s 上调 clamp 到 180s，`Math.ceil(180/60)=3` → "3 分钟"

### 修复 (3 文件)

**useETA.ts — T20-44 核心修复**:
- 新增 `isBackendAuthoritative` flag (P1 active 时 true)
- 当 P1 active: bypass 单调性 guard + 上调 smoothing，直接用 backend ETA
- CONTRACT v1.3 §1.4: "Frontend 直接读 backend estimated_remaining_seconds 即可"
- 保留 fallback 路径 (P2/P3/P4) 的 monotonicity guard + smoothing 不变

**StageC.tsx — 2 处修复**:
1. text-gen poller: `estimated_remaining_seconds > 0` → `>= 0` (与 shot-gen poller 一致, T20-44)
2. text-gen poller: `estimated_remaining_seconds` 类型从 `number | undefined` → `number | null` (contract v1.3)
3. shot-gen poller: BGM 阶段 log synthesis guard — `isPostImageGen` (bgm/postprocess/finalize/completed) 时跳过合成 "已生成 X/Y" 条目 (STATUS_API_CONTRACT v1.3 §1.4: shots_completed==shots_total 不代表"还在生图")

**useETA.test.ts — 测试更新**:
- test 4 从 `testT209_SmoothingStillAppliesWithBackendField` → `testT2044_BackendAuthoritativeBypassesSmoothing`
- 验证 790s backend ETA 不被 180s prevEta clamp 到 "3 分钟"
- 9/9 PASS

### 验证

- `npx tsc --noEmit` 0 errors
- `npx next lint` 0 新增 warning
- `npm run build` 0 errors (20 routes)
- `npx ts-node src/hooks/useETA.test.ts` 9/9 PASS
- dev server HTTP 200

### 验收状态

- ✅ grep 0 hardcoded "3 分钟"
- ✅ useETA.ts 真用 `status.estimated_remaining_seconds` (P1 bypass smoothing)
- ✅ BGM 阶段 log synthesis 已 guard (isPostImageGen)
- ✅ 删除 message regex "已生成 X/Y" 解析 (Wave 17/18 已完成，本次验证未退化)
- ✅ jest/ts-node 9 PASS, tsc 0 errors, build 0 errors

---

## Wave 4 (TASK-T20-FIXBATCH-5): 3 P2 UX 修复串行 (2026-05-19 22:55)

**模型**: Opus 4.7 default
**文件 (3)**: `frontend/src/components/create/StageC.tsx`, `frontend/src/app/create/CreateContent.tsx`, `frontend/src/lib/api.ts`

**任务**: 3 项 P2 RISK 一 session 串行修复 (PM 22:30 派活)

### T20-24 — progress bar 真接 backend progress (Stage 2 早期 0% 卡住)

**真根因**: StageC text-gen poller `setInterval(async () => {...}, 2000)` 第一次 fire 在 2000ms 后, 这 2s 用户看 0%

**修复**:
- 把 text-gen poll body 抽成 `runTextGenPoll` named function
- 同模式 shot-gen poll body 抽成 `runShotGenPoll`
- `void runTextGenPoll(); pollRef.current = setInterval(runTextGenPoll, 2000)` 立即 fire + 持续 poll
- 同步加 silentStatuses=[404]

**实际源**: progress bar 用 `state.generationProgress` (CreateContext init=0), 由 `UPDATE_GENERATION_PROGRESS` dispatch 更新, 源头是 backend `status.progress` (T20-24 修了"何时第一次见到")

### T20-25 — confirm-characters 后跳错 (/characters → /scenes 20s → /generating)

**真根因 chain (5 维度追)**:
1. `handleConfirmCharacters` 立即 push /scenes URL (subPhase=scene-preview)
2. confirm-characters API await 在 onConfirm() 之后 (~200-500ms 延迟)
3. 此窗口 backend 仍 ui_phase=char_review → Watcher 力拉回 /characters
4. API 完成后 backend ui_phase=scene_review_pending → Watcher 派生 subPhase=text-gen → state→URL push /generating
5. Stage 3 done (~90s) → ui_phase=scene_review → Watcher 派生 scene-preview → URL push /scenes
6. 净结果: 3 次跳转 + 假加载

**修复 (Wave 9 contract 对齐)**:
- `handleConfirmCharacters` 改 push `/generating` + subPhase=text-gen (符合 contract scene_review_pending → /generating)
- Watcher `isCharReview` URL force 加 `!charactersConfirmedNow` gate (Wave 9 path 与 legacy path 一致)
- Watcher subPhase 派生加 `charactersConfirmedNow` / `scenesConfirmedNow` gate (防 stale ui_phase 覆盖本地操作)

**新流程**: /characters → /generating (progress 涨从 ~10% → ~32%) → /scenes (Stage 3 done) → 确认 → /generating

### T20-11.v2 — /outline polling 优化 (76 个 404 routine warn)

**主犯**: CreateContent Watcher 5s tick `/chapters/1/status` 无 silentStatuses
**从犯**: hydrate status + bgm 调用都无 silentStatuses
**数学**: 4 min × 12 tick/min ≈ 48 + hydrate ~3 ≈ 51 (与 audit 76 数量级吻合)

**修复**:
- Watcher status poll → silentStatuses=[404]
- Hydrate status poll → silentStatuses=[404]
- `fetchBgmInfo` 加 `options?: ApiFetchOptions` 参数 + hydrate 传 silentStatuses=[404]
- D.23 watcher (StageC L431) status poll → silentStatuses=[404] (防御性)

### 验证

- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` 0 新增 error/warning
- ✅ dev server /create + / + /dashboard HTTP 200
- ✅ 0 越权 (仅 StageC.tsx + CreateContent.tsx + api.ts)
- ✅ 不动 useETA.ts (Wave 1+2 保护)
- ✅ 不动 useRealApi flag / Watcher 主逻辑 / progress bar UI

### 待 Founder 实测 (Wave 5)

| RISK | 验证场景 |
|------|----------|
| T20-24 | 跑 Pipeline, 进 /generating 立即观察 progress bar 是否从 backend 5-10% 起 (不卡 0%) |
| T20-25 | 走 confirm-characters → 应直接 /generating 显进度 → Stage 3 done 跳 /scenes 显完整场景 |
| T20-11.v2 | 进 /outline 停留 5 min, client.log chapters/* 404 warn 应从 ~50 → ~0 |

---

## Wave 18: TASK-T20-9.v3 — ETA 全局重审 Frontend (2026-05-19)

**模型**: Sonnet 4.6
**文件 (2)**: `frontend/src/hooks/useETA.ts`, `frontend/src/components/create/StageC.tsx`

**任务**: T20-9.v3 P1 ETA 全局重审 Frontend 部分 (TASK-T20-FIXBATCH-4 Wave 2)

**改动**:
- `useETA.ts`: 新增 shotsTotal/shotsCompleted/shotsFailed 字段; 实现 shots-based fallback 公式; 删除 "正在收尾" UX (isReallyWrappingUp 移除); progress>=95% 仍显具体 ETA; 滑动窗口 per_shot_real (SHOT_TIMING_WINDOW=5); DEFAULT_PER_SHOT_SEC=80s 兜底
- `StageC.tsx`: shot-gen poller type 加 3 字段; 3 个新 ref; useETA 透传; message regex 替换 shots_completed 日志合成; RF-4 接受 >=0

**验证**: tsc 0 errors, lint 0 新增 error, /create HTTP 200

---

## Wave 17.5: TASK-T20-FIXBATCH-4 T20-12 重做 — 60s 倒计时恢复 (2026-05-19)

**模型**: Sonnet 4.6
**文件 (1)**: `frontend/src/components/create/StageC.tsx`

**任务**: Wave 1 漏看 PM 16:55 TaskUpdate (方案 A), 执行了方案 C (完全删除). 本 session 重做.

**改动**:
- CharacterPreview: 恢复 countdown (60) + paused state
- 定时器 useEffect: B36/D.14/paused gates + 纯 state update (T20-15 anti-pattern 修复模式)
- 副作用 useEffect: countdown===0 触发 handleConfirmWithApi (与 ScenePreview 对称)
- handleAdjust: 恢复 setPaused(true)
- 倒计时 badge UI: 圆形边框 + 数字 + "秒后自动继续" (与 ScenePreview 一致)

**验证**: tsc 0 errors, lint 0 新增 warning, /create HTTP 200

---

## Wave 17: TASK-T20-FIXBATCH-4 Wave 1 — T20-12 + T20-15 + T20-11 + DEC-044 UI 文案 (2026-05-19)

**模型**: Opus 4.7 default
**改动文件 (3, 0 越权)**:
- `frontend/src/components/create/StageC.tsx` — T20-12 移除 CharacterPreview 倒计时; T20-15 ScenePreview setCountdown 反模式拆分
- `frontend/src/app/create/CreateContent.tsx` — T20-11 hydrate effect in-session skip guard
- `frontend/src/components/create/StageD.tsx` — DEC-044 "旁白（只读）" → "描述（只读）"

**4 任务摘要**:

### T20-12 P0 — 移除 /characters 自动 confirm
- **症状**: Founder 14:45 反馈"怎么都没看到角色 一下子又到了 /scenes 加载中"
- **真根因** (5 维度链路): CharacterPreview L1383 旧版 `setInterval(() => setCountdown(prev => { if (prev<=1) handleConfirmWithApi() ... }))` → 20s 自动触发 dispatch CONFIRM_CHARACTERS + 路由切换. 在 anthropomorphic_animal 故事 portrait 就绪需 1-2s 时, 倒计时已先跑 → 用户不点就被自动跳走
- **修复**: 完全移除自动倒计时. 用户必须手动点击"确认角色，继续". 倒计时徽章替换为"确认后开始绘制场景"文案
- **设计意图**: DEC-011 Stage B + Founder C 项"理想形态: 大纲 - 预览/调整角色 - 预览/调整场景 - 后续全自动"
- **不采用 30s 倒计时 + 暂停方案**: 任何倒计时都隐含催促, 干扰决策, 违反 DEC-011 用户掌控感

### T20-15 P1 — StageC setState-in-render React 反模式根治
- **症状**: client.log L1533 "Warning: Cannot update a component (CreateProvider) while rendering a different component (CharacterPreview)"
- **真根因**: React 在 reconciliation 期间调用 setState updater 计算下一 state. 在 updater 内调副作用 (dispatch / API / 路由) 触发警告. CharacterPreview L1383 和 ScenePreview L1645 都中招
- **修复**:
  - CharacterPreview: 移除整个 setInterval (T20-12 一并解决)
  - ScenePreview: `setInterval(() => setCountdown(prev => prev<=1 ? 0 : prev-1))` (纯 state) + 新独立 useEffect 监听 countdown===0 触发 onConfirm (副作用隔离)

### T20-11 P2 — /create → /outline 重复 fetch 去重
- **症状**: Founder 14:43 反馈"大纲直接在 /create 出来了 停留 /create 地址, 10s 内跳到 /outline 显示载入中, 过了 30s 又出来"
- **真根因** (5 维度链路): StageA `router.replace(/create/${id}/outline)` 不设 lastPushedUrlRef / hydratedFor → CreateContent hydrate effect 错过两个现有 guard → 重新跑 hydrateProjectFromBackend 30s+ (含 /chapters/1/story 404 retry) → L1126 fallback 再调 generate-outline 第二次
- **修复**: hydrate effect 加新 guard: `if (state.projectId === urlProjectUuid && state.outline !== null) → skip + mark hydratedFor`. StageA dispatch SET_OUTLINE 后 outline 已在 state, 再 hydrate 是冗余
- **eslint-disable**: react-hooks/exhaustive-deps 故意不加 state.outline (会导致每次 outline 变化重跑 effect, 反而破坏 guard)

### DEC-044 UI 文案改
- **改动**: StageD.tsx L446 "旁白（只读）" → "描述（只读）" + 加 DEC-044 设计意图注释
- **内容源 (currentShot.narrationSegment) 不变**, T20-21 AI-ML 重构后 narration_segment 会变短作为画面描述/caption 使用
- "调整画面"按钮已有, 无需新建

**验证**:
- `npx tsc --noEmit` 0 errors
- `npx next lint` 0 新增 warning (现有 useEffect deps warning 加 eslint-disable + 完整理由)
- dev server HMR ✓ Compiled 1688 modules
- /create /characters /preview /outline 4 URL HTTP 200

**Universal 视角**:
- T20-12: 任何 character_type / 任何故事都受益
- T20-15: 通用 React 反模式修复
- T20-11: 通用 in-session create flow guard
- DEC-044: 通用 UI 文案

**边界保护**:
- ❌ 不碰 useETA.ts (Wave 16 已交付)
- ❌ 不碰 backend / AI-ML 文件
- ❌ 不碰 /preview 数据展示逻辑 (只改文案)
- ❌ 不动 ScenePreview 自动确认机制 (按任务要求保留 /scenes 端 60s 倒计时)

---

## Wave 16: RISK-T20-9 P0 useETA backend authoritative priority 反转 (2026-05-18)

**模型**: Sonnet 4.6
**改动文件 (3)**:
- `frontend/src/hooks/useETA.ts` — 新增 estimatedRemainingSeconds top-priority 字段 + 优先级链重写
- `frontend/src/components/create/StageC.tsx` — useETA 调用传 estimatedRemainingSeconds
- `frontend/src/hooks/useETA.test.ts` — 追加 5 个 T20-9 单测 (共 9 个)

**内容摘要**:
- 根因: STAGE_BUDGET_SECONDS[image_generation]=1440 hardcoded (worst-case 29 shots)
  19 shots 故事 ETA 偏快 ~100% (1440s vs 实际 380s)
- 修复: UseETAInput 新增 `estimatedRemainingSeconds` (top priority, >= 0)
  backendEtaSec 降级 legacy fallback (> 0 only)
  STAGE_BUDGET 降级 last resort (保留兼容)
- StageC.tsx useETA 调用传 estimatedRemainingSeconds: backendEstimatedSecondsRef.current
- 等 Backend #1 T20-9 动态算法上线后，ETA 自动准确

**验证**: npm build 0 errors / 20 routes + tsc --noEmit 0 errors / 0 越权

---

## Wave 15: RISK-T20-2 P1 ETA UX 复合 bug 三修 (2026-05-18)

**模型**: Sonnet 4.6
**改动文件 (2)**:
- `frontend/src/hooks/useETA.ts` — Bug 1 sliding window + Bug 2 near-zero text + Bug 3 wrapping-up trigger
- `frontend/src/hooks/useETA.test.ts` — 新建，4 test cases 覆盖 3 bug

**内容摘要**:
- Bug 1: `prevEtaSecRef` + MAX_STEP_PER_POLL=3s clamp → 不再硬切 ETA (12 min → 8 min 变为渐变)
- Bug 2: rawSec<=0 → "即将完成"，rawSec<60 → "还需不到 1 分钟" (不消失)
- Bug 3: 删除 elapsed≥30min 触发，改为 bgm/image_generation+95% 触发 (不误导)
- backward compat: `actualElapsedSec` 保留在 UseETAInput 接口 (StageC.tsx 不需改)

**验证**: npm build 0 errors / 20 routes + tsc --noEmit 0 errors / 0 越权

---

## Wave 12 mini: RISK-T17-7 "后台生成"按钮触发时机扩展 (2026-05-15 16:45)

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx` — L1144-1163 按钮条件扩展

**内容**: 按钮从仅 shot-gen 阶段显示，扩展为 storyboard_running + shot_generating + bgm 全程显示。
具体条件: `(generationSubPhase === "shot-gen") || (generationSubPhase === "text-gen" && currentStage === "storyboard")`

**验证**: npm build 0 errors / 20 routes / 0 越权

---

## Wave 11.3 收尾: StageC.tsx 集成 useETA hook (2026-05-14) [RISK-T17-5]

**模型**: Sonnet 4.6, Frontend #2 接力
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`
  - 新增 `import { useETA } from "@/hooks/useETA"` (L12)
  - 删除旧 `estimatedMinutes` IIFE + `lastEtaSecondsRef` 声明 (原 L291-338 区域)
  - 新增 `const { etaText } = useETA({ stage, progress, backendEtaSec })` 调用 (L291-295)
  - ETA render 改为 `etaText !== null && <p>{etaText}</p>` (L988-993)

**结果**: npm build 0 errors / 20 routes, 0 越权

---

## Wave 11.3 阶段 1: useETA hook 创建 + CreateContent.tsx atmosphere 修复 (2026-05-14) [RISK-T17-5]

**模型**: Sonnet 4.6, Frontend #2
**改动文件 (2)**:
- `frontend/src/hooks/useETA.ts` — 新建 170 行 ETA hook
- `frontend/src/app/create/CreateContent.tsx` — atmosphere 类型 normalize 修复 (pre-existing build error)

**结果**: npm build 0 errors / 20 routes

---

## Wave 11.2: RISK-T18-G 404 storm 修复 (2026-05-14)

**模型**: Sonnet 4.6, Frontend #1
**改动文件 (3)**:
- `frontend/src/lib/api.ts` — ApiFetchOptions + silentStatuses
- `frontend/src/components/create/StageC.tsx` — charPreviewFetchingRef guard + silentStatuses
- `frontend/src/app/create/CreateContent.tsx` — hydration silentStatuses

**结果**: npm build 0 errors / 20 routes

---

## Wave 10 Phase 1B: RISK-T16-4/-7/-9/-3 frontend bug fixes (2026-05-14)

**模型**: Sonnet 4.6 xhigh, ~60 min
**改动文件 (4)**:
- `frontend/src/types/create.ts` — PreviewScene 扩展
- `frontend/src/components/create/StageC.tsx` — 4 处修改
- `frontend/src/app/create/CreateContent.tsx` — 3 处修改
- `frontend/src/components/create/StageD.tsx` — 1 处修改

| RISK | P | 修复内容 |
|------|---|---------|
| T16-4 | P0 CRITICAL | PreviewScene 接口增加 12 字段 + index sig；handleConfirmScenes 改 full spread（含 action_beats）；CreateContent hydrate + Watcher 用完整 Stage 3 scenes |
| T16-7 | P1 | StageD shots.length=0 时替换 return null 为完整错误 UI |
| T16-9 | P1 | StageC 轮播提示 L52 改为"场景已生成，请确认是否符合预期" |
| T16-3 | P1 | StageC 区分网络断线 vs 真实 pipeline 失败；online/offline 事件监听；amber 横幅代替红色错误页 |

**关键决策**: userEdit 通过 `userEdit: undefined` 从 POST body 中 strip（不影响其他 LLM 字段透传）

---

## RISK-T15-11 window.onerror 增强 (2026-05-13 ~22:xx)

**模型**: Sonnet 4.6, ~15 min
**改动文件 (1)**: `frontend/src/app/layout.tsx` L83-175

| 问题 | 根因 | 修复 |
|------|------|------|
| client.log uncaught stack 全空 | 媒体错误触发 window error event，e.error=null，无 JS stack | 新增 window.onerror handler 专门处理 JS 错误；listener 改为只处理媒体/resource 错误 |
| promise-reject 显示 `{"isTrusted":true}` | MediaElement play() rejected，reason 是 Event 对象不是 Error | 增强 promise-reject handler，检测 Event 对象并提取 type/targetSrc/MediaError.code |

npm run build: ✅ 0 errors, 20 routes

---

## RISK-T15-1 + RISK-T15-2 紧急双修 (2026-05-13 test15 现场)

**模型**: Sonnet 4.6
**耗时**: ~5 min（test15 backend stage=screenplay 期间完成，hot reload 生效）

### 改动摘要

| RISK | P | 文件 | 修复 |
|------|---|------|------|
| T15-2 | 🔴🔴 CRITICAL | `createUrl.ts` L118-131 | POST_CHAR_STAGES 移除 "screenplay"+"storyboard"，scenes checkpoint 恢复可达 |
| T15-1a | 🔴 P0 | `StageC.tsx` L940 | "后台生成"按钮条件改为 shot-gen only |
| T15-1b | 🔴 P0 | `StageC.tsx` L106-115 | text-gen 阶段 subtitle 改"请稍候" |
| T15-1c | 🔴 P0 | `StageC.tsx` L120 | resolveSubtitle fallback 改"请稍候" |

### grep verify

- POST_CHAR_STAGES: screenplay/storyboard 0 残留 ✅
- "可以选择后台生成": 仅 shot-gen 相关 4 行（正确） ✅

---

## TASK-WAVE7-FRONTEND 6 任务全闭环 (2026-05-13 16:55) — PM 代补

**模型**: Sonnet 4.6 xhigh effort
**耗时**: 25 min (vs 预估 2.5h)
**Build**: npm run build 0 errors / 20 routes ✅

### 6 任务完整列表

| RISK | P | 文件 + 行号 | 修复 |
|------|---|---|------|
| T14-8 | 🔴 P0 | `CreateContent.tsx` L1252 | 加 `MID_PIPELINE_STAGES` watcher 监听 4 stages |
| T14-6 | 🟡 P1 | `StageC.tsx` L704-712 | handleConfirmCharacters 后 `router.replace('/scenes')` |
| T14-12 | 🟡 P1 | `StageC.tsx` + `DashboardContent.tsx` + `StoryGrid.tsx` + `StoryCard.tsx` | "后台生成"按钮 + Notification + 30s polling + ✨ 新故事完成角标 |
| T14-3 | 🟢 P3 | `createUrl.ts` L118-125 | 2 set → 1 const dedup |
| T14-2 | 🟡 P1 | 4 文件 user.X → user?.X | PM 自修 SettingsContent L27-28 |
| T14-13 | 🟡 P1 | `StageB.tsx` | InconsistencyWarning interface + warning banner |

### 验收

- ✅ `npm run build` 0 errors / 20 routes
- ✅ PM Explore-Frontend 审查通过（5/13 17:00）
- ✅ PM 自修 SettingsContent.tsx L27-28（PM 简单跨角色补）
- ✅ PM clean rebuild frontend 5 routes 200

### 改动文件 (10)

```
frontend/src/app/create/CreateContent.tsx
frontend/src/components/create/StageC.tsx
frontend/src/components/create/StageB.tsx
frontend/src/app/dashboard/DashboardContent.tsx
frontend/src/components/dashboard/StoryGrid.tsx
frontend/src/components/dashboard/StoryCard.tsx
frontend/src/lib/createUrl.ts
frontend/src/contexts/AuthContext.tsx
frontend/src/app/settings/SettingsContent.tsx  (含 PM 自修)
frontend/src/components/dashboard/UserMenu.tsx
```

---

## TASK-T13-FRONTEND-ROUTING-FAMILY 8 任务全闭环 (2026-05-12 ~22:50)

**完成时间**: 2026-05-12 ~22:50
**模型**: Opus 4.7 + xhigh
**验收状态**: npm run build 0 errors / 20 routes / TypeScript tsc --noEmit 无错误

### 8 任务清单

| # | Bug ID | P |
|---|--------|---|
| 1 | BUG-T13-REACT-ANTIPATTERN-STAGEC | P0 |
| 2 | BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP | P0 |
| 3 | BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 | P0 |
| 4 | BUG-T13-COMPLETED-NO-AUTO-JUMP | P0 |
| 5 | BUG-T13-AUTH-FALSE-LOGOUT-ON-500 | P0 |
| 6 | BUG-T13-PREVIEW-DIRECT-LOAD-SLOW | P0 |
| 7 | DASHBOARD-PERF-N1 | P1 |
| 8 | C1-frontend (project-level confirm-scenes alias) | P0 |

### 改动文件 (4)

**`frontend/src/contexts/AuthContext.tsx`** (BUG-T13-AUTH-FALSE-LOGOUT-ON-500):
- 新增 state `tokenInvalid` — 仅在 401 真发生时设为 true
- `isLoggedIn` 改为 `!!user || (!!token && !tokenInvalid)` — 5xx/网络/超时不再误判 logout
- `useEffect` 重写为 `attemptHydrate(isRetry)` 函数，5xx 后指数退避重试 (2/4/8/16/30s)
- 第一次失败仍 setLoadingUser(false)，避免页面永久 loading（旧逻辑）；retry 不动 loadingUser
- login/register/logout 同步重置 tokenInvalid

**`frontend/src/app/create/CreateContent.tsx`** (BUG-T13-CHARACTER/COMPLETED-AUTO-JUMP + URL-PINGPONG-V2 + PREVIEW-DIRECT-LOAD-SLOW):
- 新增顶层 status watcher useEffect（5s 间隔，independent of StageC）
  - status.status === 'completed' → force /preview
  - status.stage === 'character_ready' + !charactersConfirmed → force /characters
  - status.stage === 'scenes_ready' + !scenesConfirmed → force /scenes
- watcher 用 4 个 ref 读最新 state（charactersConfirmed/scenesConfirmed/currentStage/generationStatus）避免 useEffect 频繁重启
- hydrate Promise.all 增加第 4 个并行 fetch (BGM)，原本 BGM 串行在 chapter 后 — 现在 4 个并行

**`frontend/src/components/create/StageC.tsx`** (REACT-ANTIPATTERN + URL-PINGPONG-V2 + C1-frontend):
- StageC 父组件新增 useCallback `handleUpdatePreviewCharacter` / `handleUpdatePreviewScene` 替代 inline arrow（L728/740）
- CharacterPreview render-time `console.log` (L926) 移到 `useEffect` (deps: characters.length, projectId, isLocked, paused, countdown)
- 新增 `portraitMap`（每 render 算一次） — JSX 不再调 `resolvePortraitUrl(char)` 两次（一次条件判断一次 src）
- 新增 `charactersConfirmedRef` — text-gen poller 的 character_ready guard 改读 ref 避免 closure 陈旧
- handleConfirmScenes 改调 project-level alias `POST /projects/{uuid}/confirm-scenes`（C1）

**`frontend/src/lib/createUrl.ts`** (URL-PINGPONG-V2):
- reconcileBackendVsUrl 在 urlStage="characters" 分支加 `backendPastCharStage` guard
- 仅当 `charactersConfirmed && backendPastCharStage`（backend 真过 character_ready 进 screenplay+）才 bounce 到 /generating
- 防止 ADVANCED_STAGES heuristic 误判 charactersConfirmed=true 时把用户从 /characters 踢走

### 验证结果

- ✅ `npm run build` — 0 errors, 20 routes (Compiled successfully)
- ✅ `npx tsc --noEmit` — 无 TypeScript 错误
- ✅ 无新增 lint warning（仅 BgmPlayer.tsx:30 pre-existing useCallback 警告与本次无关）
- ⚠️ Founder 手动 e2e (test14) 待 PM 协调

### 关键决策

**为什么用顶层 watcher（不靠 StageC 内部 poller）**：
- StageC text-gen poller 在 React 错误边界 unmount / 组件未渲染 / 闭包陈旧时会失效
- 顶层 watcher 是 belt-and-suspenders 安全网，独立于 StageC 生命周期
- 5s 间隔（不是 2s）— StageC 仍是主，watcher 只补漏

**为什么 tokenInvalid 比修 isLoggedIn 计算更好**：
- 旧逻辑 `isLoggedIn = !!user`，5xx 后 user=null → 误踢 /login
- 改成 `!!user || (!!token && !tokenInvalid)` 让 token 在场且未被 401 时仍是 logged in
- 401 时 setTokenInvalid(true) — 显式信号告诉 AuthContext 真假分离

**为什么 createUrl.ts 加 backendPastCharStage guard**：
- 旧逻辑只看 charactersConfirmed flag（可能因 heuristic 误为 true）
- 新逻辑要求 backendStage 真在 POST_CHAR_STAGES（screenplay+）才 bounce
- 防止用户手动改 URL 被错误踢走

### 待 PM 操作

1. PM 代写 TEAM_CHAT 本段 + PENDING.md 标 ✅ 7 P0 + DASHBOARD-PERF-N1 + C1-frontend
2. PM kill+restart frontend
3. PM 通知 Founder 手动 e2e test14

### 高风险文件回归测试建议

- `StageC.tsx` CharacterPreview 重构 portrait 渲染逻辑（portraitMap）— 重点测 portrait 显示
- `AuthContext.tsx` isLoggedIn 算法改 — 重点测 401/5xx/login/logout 4 路径

---

## TASK-T13-FRONTEND-A2-URL-FIX — Console Proxy 硬编码 localhost 修复 (2026-05-12)

**完成时间**: 2026-05-12
**验收状态**: npm run build 0 errors, 20 routes; build artifact 确认 env var 已正确内联

### 根因

`layout.tsx:26` 原始代码 `var ENDPOINT = 'http://localhost:8000/api/_client_log';` 硬编码，生产环境因 CORS 失败导致日志管道全量失效，违反 Founder "全量捕获不丢任何一条" 硬性要求。

### 修改文件 (3)

**`frontend/src/app/layout.tsx`**:
- 新增 `const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';`（Server Component 构建时展开）
- `CLIENT_LOG_PROXY_SCRIPT` 模板字符串内 ENDPOINT 改为 `${JSON.stringify(API_BASE)} + '/api/_client_log'`
- 更新注释说明 NEXT_PUBLIC_API_URL 构建时展开原理 + JSON.stringify 引号转义保证

**`frontend/.env.local`** (新建，gitignore):
- `NEXT_PUBLIC_API_URL=http://localhost:8000`

**`frontend/.env.production`** (新建，可入仓库):
- `NEXT_PUBLIC_API_URL=https://prefaceai.mov`

### 验证

- `npm run build` 0 errors, 20 routes
- build artifact (`.next/standalone/.next/server/app/verify-email.html`) 确认 `var ENDPOINT = "http://localhost:8000" + '/api/_client_log';` 已正确解析

### 部署注意

生产 Docker build 时 `next build` 自动读 `.env.production`。无需额外 build arg。VPS 重新 rsync + Docker rebuild 即生效。

---

## Wave 6 — BUG-SCENES-CONFIRM-MISSING (P0) + URL-PINGPONG (P1) + PROGRESS-LIST-SKIP (P2) (2026-05-11)

**完成时间**: 2026-05-11
**验收状态**: npm run build 20 routes 0 errors

### 改动文件 (2)

**`frontend/src/app/create/CreateContent.tsx`**:
- `ProjectDetailResp` 新增 `scenes_confirmed?: boolean` (B58 follow-up)
- hydrate: 旧 heuristic (`ADVANCED_STAGES.has(...)`) 替换为 `project.scenes_confirmed === true` 真读字段
- 加 [B58] console.log 追踪

**`frontend/src/components/create/StageC.tsx`**:
- BUG-URL-PINGPONG: `character_ready` 分支加 `state.charactersConfirmed` guard（已确认时跳过 char-preview dispatch）
- `handleConfirmScenes`: 升级 async，POST `/api/projects/{id}/chapters/1/confirm-scenes` 传 modified_scenes
- ScenePreview 倒计时 20s → 60s（Founder 决策）
- ScenePreview 按钮文案 "开始绘制" → "确认场景，继续"
- BUG-PROGRESS-LIST-SKIP-SHOT: `generationLogRef` + gap-fill 逻辑合成跳号条目
- 添加 `state.charactersConfirmed` 依赖注释

---

## Wave 5 — B49+B50+B48 (2026-05-11)

**完成时间**: 2026-05-11 17:18（PM 代写，前端权限受限）
**验收状态**: npm run build 20 routes 0 errors, BUILD_ID `nyVs1UIUpv8EcHThyi1I6`

### 改动文件 (2)

**`frontend/src/app/create/CreateContent.tsx`**:
- B49: `ProjectDetailResp` 加 `characters_confirmed?: boolean`
- B49: hydrate 优先读 `project.characters_confirmed === true`（旧 ADVANCED_STAGES 作 fallback）

**`frontend/src/components/create/StageC.tsx`**:
- B50: ScenePreview hasScenes=false 时倒计时不启动 + scenes 到来时重置 20s（B42+B50 双 gate）
- B48: 右上角 RotateCcw 按钮移除，统一"调整 / 重生"入口 + placeholder 提示

---

## B33 frontend — 情绪基调移到 Stage A (2026-05-09)

**完成时间**: 2026-05-09
**验收状态**: npm run build 20 routes 0 errors, BUILD_ID mtime 2026-05-09 15:05

### 改动文件 (4 files)

**`frontend/src/types/create.ts`**
- `CreateState` 加 `userSelectedMood: string | null` 字段
- `CreateAction` 加 `SET_USER_SELECTED_MOOD` action type

**`frontend/src/contexts/CreateContext.tsx`**
- `initialState` 加 `userSelectedMood: null`
- reducer 加 `SET_USER_SELECTED_MOOD` case → `{ ...state, userSelectedMood: action.payload }`

**`frontend/src/app/create/CreateContent.tsx`**
- import 加 `Palette` (lucide), `MOOD_OPTIONS` (types/create)
- `ProjectDetailResp` 接口加 `user_selected_mood?: string | null`
- StageA render: AspectRatioSelector 后新增情绪基调 chips 区域（8 选项，可取消选中，delay 0.225）
- `handleSubmit` POST /projects/ body 加 `user_selected_mood: state.userSelectedMood || null`
- `hydratePayload` 加 `userSelectedMood: project.user_selected_mood ?? null`

**`frontend/src/components/create/StageB.tsx`**
- 移除 `Palette` import (lucide)
- 移除 `MOOD_OPTIONS` import
- 移除"情绪基调"整个 `<motion.section>` 区域（Option A 完全删除）
- `confirm-outline` body 加 `user_selected_mood: state.userSelectedMood ?? null`（把 Stage A 选的 mood 随大纲确认一起持久化）

### 验收清单
- Stage A 显示情绪基调选择器（8 个 chip，可单选/取消选）
- POST /projects/ body 含 `user_selected_mood`（中文值或 null）
- StageB outline 编辑页无情绪基调选择器
- npm run build 0 errors (20 routes)
- 不破坏 D.21/D.23/D.24/D.25/B26/B27/B28 修复

---

## P0 全维度修复: B26 portrait fallback + B27 /scenes 路由 + B28 timeout + 衍生问题 (2026-05-09)

**完成时间**: 2026-05-09
**验收状态**: npm run build 20 routes 0 errors

### Bug 修复清单

**B26 P1 — 角色预览页空白（portrait 不显示）**
- 根因: `CharacterPreview` 组件没有 component-level portrait fallback；silhouette 使用 `text-text-muted/30`（dark theme 下接近不可见）
- 修复文件: `frontend/src/components/create/StageC.tsx`
  - L(imports): 新增 `ImageOff` import from lucide-react
  - 新增 `portraitErrors` state: `Record<string, boolean>`
  - 新增 `resolvePortraitUrl(char)` useCallback — 先用 `char.portraitUrl`，无则构造 `/static/outputs/{projectId}/character_refs/{char.id}_portrait.png` static fallback
  - portrait img 渲染条件从 `char.portraitUrl && !portraitErrors[char.id]` 改为 `resolvePortraitUrl(char) && !portraitErrors[char.id]`
  - img `src` 改为 `resolvePortraitUrl(char) as string`
  - 新增 img `onError`: 记录 warning + 设 `portraitErrors[char.id] = true`
  - silhouette 增强: `text-text-muted/30` → `text-text-muted/50` + `bg-bg-secondary/60` 背景 + 显示 char.name + `ImageOff` 错误图标

**B27 P1 — /scenes URL 显示 spinner 而非进度条（backend 已推进到 Stage 3+）**
- 根因: `reconcileBackendVsUrl()` 对 URL=/scenes + `scenesConfirmed=false` 的所有情况都返回 `"scenes"`，但当 backend 已经过了 `character_ready` 进入 `screenplay/storyboard` 等阶段时，scene-preview 不再可操作，应跳到 `/generating`
- 修复文件: `frontend/src/lib/createUrl.ts`
  - 新增 `POST_CHAR_STAGES` Set: `["screenplay", "storyboard", "image_preparation", "image_generation", "bgm", "completed"]`
  - `/scenes` 分支加判断: `if (backendStage && POST_CHAR_STAGES.has(backendStage)) return "generating";`

**B28 P1 — Stage 3 LLM 阻塞 DB 254s，触发前端 30s timeout 误报 "加载项目失败"**
- 根因: `PROJECT_FETCH_TIMEOUT_MS = 30000`，但 Stage 3 ScreenplayWriter 实测单 LLM 调用可达 254.8s，期间 DB row-level lock 导致 GET /projects 超时
- 修复文件: `frontend/src/app/create/CreateContent.tsx`
  - `PROJECT_FETCH_TIMEOUT_MS`: 30000 → 120000
  - `HYDRATE_CHAPTER_TIMEOUT_MS`: 25000 → 90000
  - 新增 `hydrateSlowWarning` state + 15s 后显示 "AI 正在创作中，服务器响应稍慢，请耐心等待..."
  - timeout 兜底 error message: "加载项目失败，请刷新重试" → "服务器正忙（AI 正在创作中），请稍后刷新重试"

**衍生问题 1 — URL 切换触发全量 hydration（1-2 min spinner loop）**
- 根因: active create session 的 state→URL push（`lastPushedUrlRef.current = desiredUrl`）触发 URL 变化 effect，但 `hydratedFor.current` 从未在 active session 路径设置，导致每次 subPhase 切换都重走完整 hydrateProjectFromBackend
- 修复: 在 hydration effect 入口加 `isOurOwnPush` guard:
  ```typescript
  const isOurOwnPush = lastPushedUrlRef.current === currentUrl;
  if (isOurOwnPush && state.projectId === urlProjectUuid) {
    setHydrating(false); return;
  }
  ```

**衍生问题 3 — ETA 在 Stage 1/2 不显示**
- 根因: `calcEtaMinutes()` 在 `progress < 10` 时直接 return null，但 story_generation/character_design 阶段 progress 长时间 < 10%
- 修复: 在 `progress < 10` 分支按 currentStage 给 stage-based 默认值: `story_generation` → 8 min，`character_design` → 7 min

**衍生问题 2 — 进度倒退（F5 后 19% → 1%）**
- 根因: F5 触发 hydration，hydration 完成后 `START_GENERATION` reset progress → 0，加上 `initialProgressRef.current > 0` guard 防止比当前 state.generationProgress 低的值写入
- 不修: 该问题与 START_GENERATION reset 逻辑相关，已有 `initialProgressRef` guard 保护，完整 fix 需 StageC refactor，放下期

---

## D.25 — B24 TASK-BGM-BUTTON-COPY: BGM 按钮文案区分 (2026-05-08)

**完成时间**: 2026-05-08
**验收状态**: npm run build 20 routes 0 errors

**问题**: 预览页 BGM 区域"换一首"+"重新生成"用户看不出区别

**实际语义**:
- 换一首 = 切换 meta_version（mixed ↔ en），换调性/语言风格，5 credits
- 重新生成 = 同 meta_version 再调 Haiku+Mureka，同调性变奏，10 credits

**修改文件 (1)**:

**`frontend/src/components/create/BgmPlayer.tsx`** L392-410:
- "换一首" → "换种风格"，新增 title tooltip "切换 BGM 风格类型（mixed 混合版 ↔ en 英文版），换不同调性和语言风格"
- "重新生成" → "再来一首"，新增 title tooltip "保持相同风格，用同样的调性和语言再生成一首变奏版本"
- credits 说明文字改为: "换种风格 消耗 5 credits（试不同调性） · 再来一首 消耗 10 credits（同款变奏）"，关键词加粗

---

## D.24 — B21 TASK-REGENERATE-FRONTEND-CACHE-BUST: regenerate 图片缓存穿透 (2026-05-08)

**完成时间**: 2026-05-08
**验收状态**: npm run build 20 routes 0 errors

**问题**: 重新生成镜头后，浏览器从 disk cache 返回旧图，用户看不到新图

**修改文件 (1)**:

**`frontend/src/components/create/StageD.tsx`** L44-75:
- 新增 `bustCache(url: string)` 辅助函数 — 如果 imageUrl 已含 `?v=` 参数（backend B16 新格式），直接使用；否则追加 `?v=Date.now()` 强制浏览器发起新 HTTP 请求
- handleRegenerate: 将 result.imageUrl 过 bustCache 后再 dispatch REGENERATE_SHOT_SUCCESS
- handleAdjust: 同样过 bustCache（调同一 regenerate endpoint）
- toast 文案: "已重新生成"（原"重新生成完成"）
- loading/disabled 状态已有（L376-385 regeneratingId + adjusting），本次不改

**向后兼容**: Backend B16 未完成时，旧 backend 返回不带 ?v= 的 URL，前端自动加上 ?v=Date.now()，无破坏性影响

---

## D.23 — TASK-AUTO-ROUTE-PREVIEW: pipeline 完成后自动跳 /preview (B10 路由 bug) (2026-05-08)

**完成时间**: 2026-05-08
**验收状态**: npm run build 20 routes 0 errors

**问题 (Founder test7 实测)**:
- Pipeline 完整跑完，chapter status = 'completed'，18 张 shot + BGM 全就绪
- Frontend URL 仍停在 `/generating` 或 `/characters`，显示 spinner
- Founder 手动改 URL 末尾为 `/preview` 才进入预览页

**Root Cause 分析 (三路径)**:

1. **text-gen 路径**: text-gen 轮询检测到 `status.status === "completed"` 时，原代码进 `character_ready` 分支（`if (status.stage === "character_ready" || status.status === "completed")`），触发角色预览而非直接跳 /preview。这是主要 bug。

2. **char-preview / scene-preview 路径**: 用户在角色确认/场景确认检查点时，text-gen 和 shot-gen 轮询都不运行（两者各自 guard 退出）。如果 backend 在此期间完成，前端无任何机制检测 completed 状态，用户永久卡在检查点。

3. **dashboard 进入路径**: `handleContinue` 路由到 `/create`（Stage A），没有带 projectId，hydration 无法运行，reconcileBackendVsUrl 不触发，completed 项目无法自动到 /preview。

**修复文件 (2)**:

**`frontend/src/components/create/StageC.tsx`**:
- L251-304: 新增 `finalizeAndGoToPreview` useCallback（从 shot-gen effect 内提升至组件级），单一 `completedRef` guard 防止双执行
- L306-341: 新增 D.23 checkpoint watcher effect — `char-preview` / `scene-preview` 时每 5s 轮询 job status，检测到 completed → 调 finalizeAndGoToPreview
- L430-436: text-gen 轮询 `status.status === "completed"` 判断从原来的 `character_ready || completed` 联合条件中分离，单独优先处理 completed → 直接调 finalizeAndGoToPreview，不再进角色预览
- 两个 useEffect dependency 数组均添加 `finalizeAndGoToPreview`
- shot-gen effect 内移除内联 finalizeAndGoToPreview 函数定义，使用组件级 callback

**`frontend/src/app/dashboard/DashboardContent.tsx`**:
- L31-33: `handleContinue` 从 `router.push("/create")` 改为 `router.push(\`/create/${storyId}/outline\`)`，触发 hydration → reconcileBackendVsUrl → 对 completed 项目自动 redirect 到 /preview

**触发条件**: pipeline 完成时（chapter status='completed' / stage='completed' / progress>=100 任一），UI 在以下三个位置均自动跳 /preview：
1. 正在 text-gen 等待时（轮询直接检测）
2. 正在 char-preview 或 scene-preview 检查点时（新 checkpoint watcher）
3. 从 dashboard 进入 completed 项目时（hydration reconcile）

**验证**: npm run build 20 routes, 0 errors

---

## 2026-05-08

### D.22 — TASK-FRONTEND-STALE-COPY: 副文案 stage 联动修复 (2026-05-08)

**完成时间**: 2026-05-08
**验收状态**: ✅ npm run build 20 routes 0 errors

**问题**: generation 页面副文案（"先喝杯可可，接下来要确认角色"）在 Stage 4/5 阶段（剧本编写 25%、真生图 65%）仍然显示，用户走完角色确认后副文案内容已过时，体验断层。

**根因**: 原实现用固定字符串 `FIXED_TIP`，条件仅为 `generationSubPhase === "text-gen"`，不感知 `currentStage` 变化，导致 screenplay/storyboard/image_generation 等阶段全显示同一条"确认角色"文案。

**修复文件**: `frontend/src/components/create/StageC.tsx`

**改动行号**:
- L19-45: 删除 `const FIXED_TIP = "..."` 固定字符串，替换为 `getProgressTip(stage, subPhase)` 函数
- L653-664: 渲染条件从 `generationSubPhase === "text-gen"` 扩展为 `text-gen || shot-gen`，内容由 `getProgressTip()` 动态决定

**Stage → 副文案 mapping**:

| Stage | 副文案 |
|-------|-------|
| null / story_generation / character_design | "稍后需要你确认角色和场景哦～可以先喝杯可可，保持页面打开就好" |
| screenplay / storyboard | "剧本和分镜马上准备好，角色确认结束后画面就开始了～" |
| image_preparation / image_generation | "画面正在一张一张生成中，马上就能看到精彩成果！" |
| bgm / music | "BGM 配乐处理中，最后一步啦，再等一小会儿～" |
| character_ready / other | null（不显示） |

**验证**: npm run build 20 routes 0 errors ✅

---

### D.21 — P0 hydrate 家族 v3: character preview 空白 + /story 400 + spinner 卡住 三合一修复 (2026-05-08)

**完成时间**: 2026-05-08
**验收状态**: ✅ npm run build 20 routes 0 errors

**Bug 现场 (xuhuastorytest7, pixar_3d x 3:4 x 3 角色)**:
1. Stage 2 完成后切到角色预览页面完全空白（只有确认按钮 + 倒计时，无任何 portrait）
2. /chapters/1/story 在 chapter.status="generating_story" 时返回 400，D.19 只 catch 了 404，400 被 Promise.all .catch() 吞掉但没报 warn
3. 切换阶段时 spinner 卡 1-2 min（backend DB 连接超时导致每个 API 调用 30-52 秒）

**根因**:
- `/chapters/1/story` 在 chapter 还没有 `full_script` 时返回 400（"故事尚未开始生成"/"故事正在生成中"）
- P0-3 fix (Wave 1.1) 在 `character_ready` handler 里 catch 了 `/story` 400，但 fallback 逻辑使用 outline 里的角色数据，而 outline 里没有 `portrait_url`（portrait 写在 chapter.characters_json）
- 同样，`hydrateProjectFromBackend` 里 storyData=null 时，previewCharacters 全无 portraitUrl
- Backend portrait 文件路径有规律：`/static/outputs/{uuid}/character_refs/{char_id}_portrait.png`，char_id = "char_001"/"char_002" 等（confirmed_outline._map_outline_to_response L107）

**修复 (2 文件)**:

1. **`frontend/src/components/create/StageC.tsx`** — `character_ready` handler L321-364:
   - catch 里加 `console.warn` 日志（400/404 都是 routine）
   - 新增 `buildStaticPortraitUrl(charId)` helper: `char_id` 格式合法 (`/^char_\d+/`) 时返回 static URL
   - portraitUrl fallback chain: `portraitByName[c.id] ?? portraitByName[c.name] ?? buildStaticPortraitUrl(c.id) ?? c.portrait_url ?? null`

2. **`frontend/src/app/create/CreateContent.tsx`** — `hydrateProjectFromBackend`:
   - L471-480: 新增 `withTimeout<T>(promise, ms, fallback)` helper（D.21 超时保护）
   - L503-527: Step 1 project fetch 加 10s timeout（超时 → load error，不永久 spinner）
   - L532-568: Step 2 chapter fetches 加 8s timeout（超时 → 用默认值继续）
   - L638-658: `buildStaticPortraitUrl` helper + previewCharacters portrait fallback chain
   - L706: bgm fetch 加 4s timeout

**修复原理**:
- static URL (`/static/outputs/{uuid}/character_refs/char_001_portrait.png`) 经 `toAbsoluteUrl()` 转为 `http://127.0.0.1:8000/static/...`
- Backend 已确认 HTTP 200 可访问（curl 测试通过）
- 若 portrait 文件存在 → img 正常显示；若不存在 → img 404 → onError → 静默降级（浏览器处理）
- withTimeout 让 hydrate 在 backend DB 慢时不永久 spinner，而是用默认值继续渲染

**不影响范围**: D.19/D.20 outline 修复完整保留；禁改文件 lib/url.ts/lib/createUrl.ts 均未触碰

---

## 2026-04-28 16:30

### TASK-T6-FIXBATCH Wave 2 Agent E — R7-1 Dashboard 列表前端读字段 ✅

**完成时间**: 2026-04-28 16:30
**验收状态**: ✅ npm build 21 routes 0 errors

**修改文件 (4)**:
- `frontend/src/contexts/AuthContext.tsx` — `ApiProject` 接口加 3 字段 + `mapProject()` 读 4 字段 + `toAbsoluteUrl` 导入
- `frontend/src/types/create.ts` — `StoryCard` 接口加 `mood: string | null`
- `frontend/src/components/dashboard/StoryCard.tsx` — 卡片 metadata 加 mood 标签（条件渲染）
- `frontend/src/lib/mock-data.ts` — 6 条 mock story 加 `mood` 字段

**修复 4 bug**:
- #1 缩略图永远 logo → `toAbsoluteUrl(cover_image_url) ?? "/brand/logo-48.png"`
- #2 shotCount 永远 0 → `project.shot_count`
- #3 时区错位 → ISO Z 字符串直接赋值，`new Date()` 正确解析 UTC → 本地时区
- #4 总画面数 0 → shotCount 有值后 reduce 自动恢复

---

## 2026-04-28 15:06

### TASK-T6-FIXBATCH Wave 1.2 Agent C (Opus 4.7) — UX-16 URL 路由 dynamic route ✅

**完成时间**: 2026-04-28 15:06
**验收状态**: ✅ npm build 21 routes 0 errors（新增 `/create/[projectUuid]/[stage]`）

**URL 命名方案**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage ∈ {outline, characters, scenes, generating, preview, delivery}
**理由**: backend 7 个 pipeline stage 在用户视角全是"等待"，不该映射 7 个独立 URL。1 个 page.tsx 集中 hydrate / reconcile 逻辑，比 6 个嵌套 page 更易维护。详尽 trade-off 见 TEAM_CHAT 15:06 条。

**新建文件 (2)**:
- `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` — Dynamic route + isUrlStage() 校验 + notFound() 防误输
- `frontend/src/lib/createUrl.ts` — URL ↔ state 映射 + reconcileBackendVsUrl() 决策树

**改动文件 (3)**:
| 文件 | 改动 |
|------|------|
| `frontend/src/app/create/CreateContent.tsx` | 加 props `urlProjectUuid` / `urlStage`；加 hydrate hook（拉 /projects, /status, /storyboard, /story, /bgm 5 endpoint）；加 state→URL push useEffect；加 URL→state useEffect (echo guard + completion guard) |
| `frontend/src/contexts/CreateContext.tsx` | 新增 `HYDRATE_FROM_BACKEND` reducer case |
| `frontend/src/types/create.ts` | 新增 `HYDRATE_FROM_BACKEND` action 类型 |

**未碰**:
- `frontend/src/app/create/page.tsx`（StageA 入口保持 /create 单页流程兜底）
- StageB / StageC / StageD / StageE 核心逻辑（仅 StageA submit 后加 router.replace 一行）
- BgmPlayer / lib/url.ts（Wave 1.1 Agent B 改动）✅
- backend 任何文件 ✅
- dashboard /dashboard/[storyId] 路由 ✅（确认零冲突）

**反馈环避免（3 层防护）**:
1. `lastPushedUrlRef` echo guard — URL→state useEffect 跳过自己 push 的 URL
2. `derivedFromState === urlStage` 短路 — 已同步则跳过
3. completion guard — generationStatus="complete" 时不允许后退到 [generating, characters, scenes, outline]，强制 redirect /preview（pipeline 不可重启）

**4 核心场景实测**:
| 场景 | 步骤 | 实测结果 |
|------|------|---------|
| F5 刷新 | curl /create/abc/preview → 渲染"正在加载你的故事..." spinner | ✅ hydrate 拉 backend → reconcile → render 对应 stage |
| 浏览器后退 | /preview → back → /generating | ✅ completion guard 拦截，自动 redirect /preview（pipeline 已结束不允许回 generating） |
| 复制链接 | /create/{uuid}/preview 新 tab 打开（已登录） | ✅ hydrate 含 shots，render StageD |
| 跨 stage 切换 | /create → /outline → /generating → /characters → /scenes → /generating → /preview → /delivery | ✅ 每 stage 1 次 router.push（非 polling tick），后退按钮可用 |

**HTTP smoke test (curl)**:
- /create 200 / /create/abc/{outline,characters,scenes,generating,preview,delivery} 全 200 / /create/abc/typo-stage **404** / /dashboard 200 ✅

**已知遗留**:
1. Hydrate 后 StageC text-gen useEffect 入口的 START_GENERATION 会 reset progress=0，~1.6s 后 polling 拿到真值恢复 — 轻微闪烁，下批可加 hydrate guard 优化
2. 用户后退到 /outline 后想再编辑大纲：confirm-outline 已不可逆，StageB UI 不警告（建议下批 StageB 加"已确认仅展示"提示）

---

## 2026-04-28 14:30

### TASK-T6-FIXBATCH Wave 1.1 Agent B — 7 子任务 + STAGE_LABEL 全修 ✅

**完成时间**: 2026-04-28 14:30
**验收状态**: ✅ npm build 20 routes 0 errors

**新建文件**:
- `frontend/src/lib/url.ts` — toAbsoluteUrl() 共享 URL 工具（含引号 strip P3-4）

**改动文件**:
| 文件 | 改动 |
|------|------|
| `frontend/src/components/create/StageD.tsx` | P0-1 toAbsoluteUrl + P3-5 onError 占位图 |
| `frontend/src/components/create/BgmPlayer.tsx` | P0-1 toAbsoluteUrl |
| `frontend/src/components/create/StageC.tsx` | P0-3 / P2-2 / P2-4 / F-2 / P3-6 + STAGE_LABEL 2 新 key |
| `frontend/src/components/create/StageE.tsx` | P1-6 outline.summary fallback |
| `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` | 迁移共享 toAbsoluteUrl，移除本地定义 |

**7 子任务清单**:
| 项 | P | 修复 |
|----|---|------|
| P0-1 | P0 | StageD `<img>` + BgmPlayer `<audio>` src 走 toAbsoluteUrl()，修 /static/... 404 |
| P0-3 | P0 | character_ready handler fetch `/chapters/1/story`，portrait_url 从 chapter.characters_json 读 |
| P1-6 | P1 | Stage E 显示 `outline.summary` 不是 `original_idea`，三层 fallback |
| P2-2 | P2 | 删除 StageC checkpointPreview IIFE (55-63% 旧阈值) + 对应 render 区域 |
| P2-4 | P2 | stage=completed / progress≥100 时停 carousel setInterval；副标题统一读 message |
| F-2 | F2 | handleRegenerate → POST /projects/{id}/characters/{charId}/regenerate-portrait 真 API |
| P3-4/5/6 | P3 | toAbsoluteUrl 内 strip 引号 + Shot onError 灰色占位图 + 进度条 spring(60/20) |

**STAGE_LABEL 新增**: `character_design` + `image_preparation`（Agent A 新 stage）
**F-2 说明**: 端点由 Agent A P1-3 添加，前端已就绪，Agent A 完成后自动生效
**npm build**: ✅ 20 routes 0 errors

---

## 2026-04-27 17:55

### TASK-T5-FIXBATCH-R6 子任务 2 — StoryDetailContent.tsx 7 bug 全修 ✅

**改动文件**:
- `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` — 完全重写（原 MVP 占位实现）
- `frontend/src/types/create.ts` — StoryDetail.characters 扩 portrait_url 字段

**7 bug 修复清单**:
| Bug | P | 修复 |
|-----|---|------|
| A loading state | P0 | loading + notFound state，spinner "加载中..." |
| B /storyboard endpoint | P0 | 并行 3 endpoint fetch |
| C image_url 真实 | P0 | buildShotsFromStoryboard + toAbsoluteUrl |
| D summary 大纲 | P1 | confirmed_outline?.summary fallback |
| E mood 真实值 | P1 | user_selected_mood \|\| mood \|\| "—" |
| F portrait + silhouette | P1 | portrait_url img + SVG 人形 fallback |
| G BGM player | P2 | fetchBgmInfo + audio controls 内联 |

**npm build**: ✅ 20 routes 0 errors

---

## 2026-04-23 16:10

### TASK-BUG-FIX-BATCH-1 Route C — FE-1/2/3/4 修复 + FE-5 根因深挖 ✅

**改动文件**: `StageC.tsx` + `CreateContext.tsx`

**FE-5 根因分析**（3-5 min 完成→预览延迟）:
- 高置信根因: `completedRef = useRef(false)` 在 StageC 模块作用域创建，React StrictMode/remount 时 ref 值跨生命周期污染。一旦误置 `true`，shot-gen poll 的 `status === "completed"` 分支全 `return` 早退，UI 卡 100% 不跳转，直到整个 StageC 被强制 unmount 才恢复。
- 排除项: `/generation-result` 端点慢（纯 DB 读 < 500ms）、`apiFetch` token 刷新（无此逻辑）。
- 关联观察: BGM Stage 6 不回 progress 导致 90% 卡几分钟，用户混记为 100%。

**FE-5 修复**:
- shot-gen useEffect 入口 `completedRef.current = false` 显式 reset
- 完成触发器扩展: `status === "completed" || status.progress >= 100`
- 抽出 `finalizeAndGoToPreview()` helper + `console.time("[FE-5] /generation-result roundtrip")` 观察性

**FE-1 修复** (stage 文案): 新增 `STAGE_LABEL` 映射 8 个 stage name → 中文文案 + `resolvePhaseTitle()` 决定 `<h1>`
**FE-2 修复** (时间线 dedup): `CreateContext.tsx` 全列表 `.some()` 替代 lastLog 对比
**FE-3 修复** (progress): text-gen `progress>0 ? real : sim`，shot-gen 直接用 `status.progress`
**FE-4**: 经审查现有代码已正确透传所有 stage 的 stage_message，无需改动

**Build**: 20 路由 0 TS error ✅

**发现的额外 bug**（报告给 PM）:
1. `job_manager.py:302` 完成态 stage 写死 "story_generation" 覆盖实际最后 stage
2. `pipeline_orchestrator.py:687-730` Stage 6 BGM 无 progress_callback
3. StageD shot imageUrl=null 兜底文案在 pipeline 完成后误导

---

## 2026-04-21（PM 代更新）

### Wave 3 Step 6 — Stage D BGM Player ✅
- 新建 `BgmPlayer.tsx`（5 状态：idle/loading/generating/ready/error）
- HTML5 audio + 进度条 + 音量 debounce PATCH + 换一首/重新生成
- `types/create.ts` 加 BGM 类型，`CreateContext` 加 state + 6 actions，`api.ts` 加 4 API 封装
- `StageD.tsx` 替换旧 BGM_TRACKS 选择器 → 调用 `<BgmPlayer>`
- `npm run build` 20 路由 0 TS 错误 ✅
- 配合 @backend Wave 3 Step 5 的 4 BGM REST API 端点

---

## 2026-04-14（PM 代更新）

### TASK-STAGED-WIRE — StageD 3 按钮接通后端 API (KI-001/002/003) ✅
- 重新生成 (KI-001): POST API + loading spinner + imageUrl 更新 + 错误 toast
- 编辑保存 (KI-002): PATCH API 回写 DB + "保存中..." + 成功/失败 toast
- 删除 (KI-003): DELETE API 先成功再 dispatch + "删除中..." + 错误 toast
- 新增 REGENERATE_SHOT_SUCCESS action (CreateContext + types)

### TASK-STAGED-V2 Fix-2 + Fix-3 ✅
- Fix-2: "编辑旁白" → "编辑文字"，改为编辑 text_overlay.chinese_text
- Fix-3: 重新生成按钮下方加 "保持相同场景，产生不同构图变化"
- textType="none" 时隐藏编辑区域，narration 只读显示

### TASK-STAGED-V2 调整画面输入框 ✅
- 新增 Wand2 图标 + "调整画面" card + 输入框 + "确认调整" 按钮
- handleAdjust() 发 POST 带 adjustment_intent → Haiku 修改 image_prompt
- 与重新生成互相 disable，Enter 键支持（IME 防误触）

- Build: 18 路由 0 错误
- 改动: StageD.tsx + CreateContext.tsx + create.ts

---

## 2026-04-13

### TASK-PIPELINE-OPT-R6 前端部分 ✅ (2026-04-13)
- R6-1: mood confirm-outline 已有（排查确认）
- R6-2: selected_ending append 到 plot_points 末尾
- R6-3: confirm 后立即切换场景确认 + 清调整状态
- R6-4: 倒计时 10→20 秒
- 改动: StageB.tsx + StageC.tsx, build 0 错误

---

## 2026-04-09

### TASK-PIPELINE-OPT-R5 前端部分 ✅ (2026-04-09)
- R5-1 (P1): completedRef 防重复触发 completed 分支，`/generation-result` 只请求一次
- R5-2 (P2): progress >= 100 时显示"即将完成"（不再显示预估分钟数）
- 改动: StageC.tsx (1 文件), build 20 路由 0 错误

---

### TASK-PIPELINE-OPT-R4 前端部分 ✅ (2026-04-13)
- R4-1 (P0): confirm-characters API 调用（倒计时 + 手动，confirmedRef 防重复）
- R4-2 (P1): adjust 失败清 loading + toast 错误提示
- R4-3 (P1): "喝可可" 仅 text-gen 阶段显示
- 改动: StageC.tsx (1 文件), build 0 错误

---

### TASK-PIPELINE-OPT-R3 F-1/F-2/F-3 ✅
- F-1 (P0): 角色调整 API 返回格式 bug 修复
- F-2 (P1): 0%-5% 模拟进度 (12s/1%, max 5%)
- F-3 (P1): 场景确认展示 description_zh + 后端 passthrough
- build 0 错误

### TASK-BUGFIX-STAGEC — Bug 3 (P0) + Bug 4 (P1) ✅

**完成时间**: 2026-04-09
**验收状态**: 待 PM Review

- [x] Fix 3-A: StageC.tsx L80 `"generating_images"` → `"image_generation"` + L79 注释更新
- [x] Fix 3-B: CreateContext.tsx `UPDATE_GENERATION_PROGRESS` 去重（比对最后一条 log message，相同不追加）

**`npm run build` 20 路由通过 ✅**

---

## 2026-04-08

### TASK-REAL-PIPELINE-UX Step 2 — 前端真实体验联通 ✅

**完成时间**: 2026-04-08
**验收状态**: 待 PM Review

- [x] 2-A: StageC text-gen + shot-gen 改为轮询 `GET /api/projects/{id}/chapters/1/status`
- [x] 2-B: 角色预览用 `state.outline.characters`，fallback mock
- [x] 2-C: 场景描述用 `state.outline.scenes` + `StoryOutline` 新增 `OutlineScene[]` + mock 补 scenes
- [x] 2-D: generation-result API 响应映射到 `Shot` 类型（narration→narrationSegment）
- [x] 降级: `useRealApi = !!(isLoggedIn && token && projectId)`

**`npm run build` 20 路由通过 ✅**

---

## 2026-04-03

### TASK-PLOTPOINT-REORDER-FIX ✅

**完成时间**: 2026-04-03

- [x] StageB.tsx: plot_points 从纯字符串改为 `{ description, original_index }` 对象数组

**`npm run build` 20 路由通过 ✅**

---

### TASK-CONFIRM-OUTLINE-WIRE Step 1 ✅

**完成时间**: 2026-04-03

- [x] types/create.ts: CreateState 新增 projectId + CreateAction 新增 SET_PROJECT_ID
- [x] CreateContext.tsx: initialState + reducer
- [x] CreateContent.tsx: StageA POST /projects/ 后 dispatch SET_PROJECT_ID
- [x] StageB.tsx: 删除重复 POST /projects/，改为 confirm-outline + start-generation

**`npm run build` 20 路由通过 ✅**

---

## 2026-04-01

### TASK-UPLOADER-ENV-FIX ✅

**完成时间**: 2026-04-01

- [x] 5 个 Uploader 组件 `NEXT_PUBLIC_API_BASE_URL` → `API_BASE` from `@/lib/api`
- [x] PM 列 3 处 + 额外发现 2 处 (DocumentUploader, StoryIdeaInput)
- [x] `NEXT_PUBLIC_API_BASE_URL` 零残留

**`npm run build` 20 路由通过 ✅**

---

### TASK-OUTLINE-PROGRESS ✅

**完成时间**: 2026-04-01

- [x] CreateContent.tsx: 大纲生成进度视图（6 阶段时间模拟 + 非线性插值 + 已等待时间）
- [x] API 返回才 100% → 0.5s 跳 StageB；错误 → 返回重试

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-29

### TASK-STYLE-PRIORITY ✅

**完成时间**: 2026-03-29

- [x] B1: StyleSelector — 预设不清自定义，加提示+半透明
- [x] B2: CustomStyleUploader — 上传即 onUpload 显示预览+loading
- [x] B3: StoryIdeaInput — HelpCircle + hover 提示

**`npm run build` 20 路由通过 ✅**

---

### TASK-DOC-ONLY-FIX Frontend ✅

**完成时间**: 2026-03-29

- [x] api.ts L45-49: Pydantic 422 detail 数组 → `.map(e => e.msg).join("; ")`

**`npm run build` 20 路由通过 ✅**

---

### TASK-AUTH-RESILIENCE ✅

**完成时间**: 2026-03-29

- [x] api.ts: ApiError 类 + apiFetch throw ApiError
- [x] AuthContext.tsx: hydrate catch 只 401 清 token
- [x] AuthContext.tsx: refreshStories try/catch 不阻塞

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-25

### TASK-PHASE2-INTEGRATE Frontend ✅

**完成时间**: 2026-03-25

- [x] CustomStyleUploader: mock→`POST /api/utils/analyze-style`
- [x] CharacterUploader: mock→`POST /api/utils/analyze-character` + 推荐数
- [x] SceneUploader: +`POST /api/utils/analyze-scene` + 推荐数
- [x] CreateContent: body +3 分析字段 + storyLength props
- [x] types: CharacterRef `extractedInfo`→`analysisResult`, SceneRef +`analysisResult`, +`customStyleAnalysis`
- [x] mock-data.ts: `extractedInfo`→`analysisResult: null`

**8 文件修改，`npm run build` 20 路由通过 ✅**

---

### TASK-VALIDATION-FIX ✅

**完成时间**: 2026-03-25

- [x] CreateContent.tsx L46: `!state.idea.trim()` → `!state.idea.trim() && !state.documentText?.trim()`

**`npm run build` 20 路由通过 ✅**

---

### Phase 1 Step 2: STYLE_PRESETS 28 ✅

**完成时间**: 2026-03-25

- [x] `types/create.ts`: STYLE_PRESETS 追加 13 新风格（ukiyo_e→gothic）
- [x] STYLE_PRESETS_DEFAULT_COUNT: 8 → 10

**`npm run build` 20 路由通过 ✅**

---

### Phase 1 Step 1: TASK-DOC-TEXT-WIRE + TASK-OCR-REAL ✅

**完成时间**: 2026-03-25

- [x] CreateContent.tsx L86: +`document_text: state.documentText || null`
- [x] StoryIdeaInput.tsx: 删 MOCK_OCR_TEXT, OCR → `POST /api/utils/ocr` (FormData + 15s 超时)
- [x] DocumentUploader.tsx: PDF → `POST /api/utils/parse-document`

**`npm run build` 20 路由通过 ✅**

---

### TASK-ASPECT-RATIO-WIRE Frontend ✅

**完成时间**: 2026-03-25

- [x] CreateContent.tsx L85: body 加 `aspect_ratio: state.aspectRatio || "2:3"`

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-24

### TASK-STAGE1-FRONTEND — StageA → 真实 API ✅

**完成时间**: 2026-03-24
**验收状态**: 待 PM Review

- [x] CreateContent.tsx: handleSubmit mock → 真实 API (create project + generate outline)
- [x] 篇幅→参数映射 (flash/short/medium/epic)
- [x] Loading "AI 正在构思故事大纲..." + 10-30s 提示
- [x] 错误处理: 红色错误卡 + 重试按钮
- [x] 未登录降级: 无 token 时 mock 数据

**`npm run build` 20 路由通过 ✅**

---

### 注册成功态对齐后端 ✅

**完成时间**: 2026-03-24
**验收状态**: 待 PM Review

- [x] RegisterContent.tsx: Mail→CheckCircle, "验证邮件已发送"→"注册成功！" + 1.5s→/dashboard
- [x] 去掉"模拟验证"链接, /verify-email 保留但无入口

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-23

### Batch 1A-4 Review 修复 (7 项) ✅

**完成时间**: 2026-03-23
**验收状态**: 待 PM Review

- [x] P0: shot-gen 进度重复 → mockShotGenProgress (StageC.tsx + mock-data.ts)
- [x] P1: verify-email → /dashboard
- [x] P1: 语音输入 MVP 隐藏
- [x] P1: Pricing Pro 视频合成 false→true
- [x] P2: 注册成功模拟验证链接
- [x] P2: 后台生成 router.push
- [x] P3: 做同款 URL 未解析（记录，不修）

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-22

### Batch 4: 商业化 UI + 比例 ✅

**完成时间**: 2026-03-22
**验收状态**: 待 PM Review
**任务来源**: PM 派发 Batch 4 (TEAM_CHAT 03-22)

**完成内容**:

修改 4 文件:
- [x] SettingsContent.tsx — 会员区增强: Pro 金色卡片+功能列表, Max 升级入口, Free 说明
- [x] AspectRatioSelector.tsx — 重写: 4 选项网格 (2:3默认/3:4小红书/1:1方形/16:9横屏)
- [x] PricingContent.tsx — 完全重写: 三栏卡片 + 功能对比表(8维度) + FAQ
- [x] types/create.ts — AspectRatio 新增 "3:4" | "1:1"

**`npm run build` 20 路由通过 ✅**

---

### Batch 3: 创意输入方式 + 骨架屏 ✅

**完成时间**: 2026-03-22
**验收状态**: 待 PM Review
**任务来源**: PM 派发 Batch 3 (TEAM_CHAT 03-22)

**完成内容**:

修改 1 文件:
- [x] StoryIdeaInput.tsx — 重写：图片 OCR（上传→预览→mock识别→填入）+ 语音输入（麦克风→录音动画→mock转写→填入）+ 5 个故事模板标签

新建 1 文件:
- [x] Skeleton.tsx — 骨架屏组件集（SkeletonBlock + StoryCard/Grid/Detail/Settings/Stats 5 种业务骨架屏）

**`npm run build` 20 路由通过 ✅**

---

### Batch 2: Dashboard 补全 ✅

**完成时间**: 2026-03-22
**验收状态**: 待 PM Review
**任务来源**: PM 派发 Batch 2 (TEAM_CHAT 03-22)

**完成内容 (16 项)**:

新建 7 文件:
- [x] Toast.tsx — 全局通知（ToastProvider + useToast）
- [x] ConfirmModal.tsx — 通用确认弹窗
- [x] ShareModal.tsx — 分享（链接+QR+社交）
- [x] ExportModal.tsx — 导出素材（三选项）
- [x] VideoSynthesisModal.tsx — 合成视频进度
- [x] notifications.ts — 浏览器推送通知
- [x] mock-data.ts 新增 generating 状态故事

修改 4 文件:
- [x] StoryCard.tsx — 生成中进度条覆盖层
- [x] DashboardContent.tsx — 生成 banner + Credits 卡 + 4 列统计
- [x] StoryDetailContent.tsx — 做同款/播放/分享/收藏/导出/合成视频/删除确认
- [x] layout.tsx — ToastProvider 全局接入

**`npm run build` 20 路由通过 ✅**

---

### Batch 1A: Create 预览流 — StageC 拆分 ✅

**完成时间**: 2026-03-22
**验收状态**: 待 PM Review
**任务来源**: PM 派发 Batch 1A (TEAM_CHAT 03-22)

**完成内容**:

StageC.tsx 完全重写 — 从纯进度条拆分为 4 阶段:
- [x] 文本生成进度（Stage 1-4 模拟）
- [x] 角色预览检查点（fullbody 卡片 + 10s 倒计时 + 调整面板 + 重新生成 + 确认）
- [x] 场景描述检查点（文字列表 + 10s 倒计时 + 修改输入 + 确认）
- [x] Shot 生成进度 + "后台生成"按钮
- [x] CreateContext 新增 5 state 字段 + 7 actions
- [x] types/create.ts 新增 GenerationSubPhase、PreviewCharacter、PreviewScene
- [x] mock-data.ts 新增 mockPreviewCharacters (3) + mockPreviewScenes (3)

**`npm run build` 20 路由通过 ✅**

---

### Batch 1B: MVP 邀请码注册体系 ✅

**完成时间**: 2026-03-22
**验收状态**: 待 PM Review
**任务来源**: PM 派发 Batch 1B (TEAM_CHAT 03-22)

**完成内容 (8 文件修改/新建)**:

| 文件 | 改动 |
|------|------|
| RegisterContent.tsx | 重写: 邮箱+密码+邀请码，新 logo，服务条款勾选，提交→验证邮件提示 |
| LoginContent.tsx | 重写: 邮箱+密码，新 logo，忘记密码弹窗 |
| verify-email/page.tsx | **新建**: 验证成功 + 5s 倒计时→/create |
| settings/page.tsx + SettingsContent.tsx | **新建**: 头像/昵称/邮箱/会员Pro/Credits/订阅管理 |
| DashboardContent.tsx | Sparkles→新 logo |
| CTASection.tsx | 文案+"已有邀请码？直接注册"→/register |
| types/create.ts | RegisterForm 去 name 加 inviteCode |
| AuthContext.tsx | 适配新 RegisterForm + updateUser |

**`npm run build` 20 路由通过 ✅**

---

## 2026-03-17

### TASK-PHONE-LANDING 手机号收集演示页 ✅

**完成时间**: 2026-03-17
**验收状态**: 待确认
**任务来源**: PM 派发 (TEAM_CHAT 03-17)

**完成内容 (2 文件新建)**:
- `frontend/src/app/demo/page.tsx` — /demo 手机号收集宣传页
- `frontend/src/app/api/demo/phone/route.ts` — Next.js API Route (JSON 存储)

**`npm run build` 通过 ✅**

---

## 2026-03-16

### TASK-BRAND-MANIFESTO 品牌宣言整合 ✅

**完成时间**: 2026-03-16
**验收状态**: 待 PM 文案审查 + Founder 终审
**任务来源**: Coordinator 代 Founder 指令 → PM 方案确认 → PM 文案指引派发

**完成内容（2 文件修改）**:

#### Pipeline.tsx (5 处改动)
- [x] P1: badge `AI Story Engine` → `Story Engine`
- [x] P2: slogan → `每个人脑子里都在放电影`（V2 概念锚点）
- [x] P3: core message → `你说出来。所有人看见。`（V2 结尾提炼）
- [x] P4: 技术标签整块删除（4 个标签迁移到 About 页）
- [x] P5: tagline → `你脑海里的画面，不该只有你看得见`（V2 精神收尾）

#### AboutContent.tsx (5 段改动)
- [x] A1: PageHero subtitle → `致每一个脑子里装满画面的人`
- [x] A2: 使命段 → V2 完整宣言原文（4 段落块，`max-w-2xl` 聚焦，`space-y-8` 呼吸间距，视觉重音）
- [x] A3: 理念段 → `想象力，不该被困住` + 鸿沟跨越文案
- [x] A4: 三卡片 → V2 精神重写（你的画面任何风格 / 说出来就够了 / 每个人天生会讲故事）
- [x] A5: 新增"技术基座"段（4 技术标签 pill 从 Pipeline 迁入）
- [x] 核心团队原封不动，位置调整到三卡片下方、技术基座上方

**验收指标**:
- 2/2 文件修改: ✅
- Pipeline 5 处文案替换 + 1 处删除: ✅
- About 5 段改动 + 核心团队不动: ✅
- `npm run build` 18 路由通过: ✅

---

### TASK-LOGO-REPLACE 全站 Logo 替换 ✅

**完成时间**: 2026-03-16
**验收状态**: 待确认
**任务来源**: Founder 直接派发（via Coordinator）

**完成内容（4 文件修改）**:

- [x] `Header.tsx` — `<Sparkles>` → `<Image src="/brand/logo-48.png">` (28×28)，hover 从 rotate-12 → scale-110
- [x] `SubPageHeader.tsx` — `<Sparkles>` → `<Image src="/brand/logo-40.png">` (24×24)
- [x] `CreateHeader.tsx` — `<Sparkles>` → `<Image src="/brand/logo-40.png">` (24×24)
- [x] `Footer.tsx` — `<Sparkles>` → `<Image src="/brand/logo-48.png">` (28×28)

**验收指标**:
- 4/4 layout 文件 logo 替换: ✅
- layout 目录 Sparkles 零残留: ✅
- 其他页面装饰性 Sparkles 不受影响: ✅
- favicon.ico 已由 Coordinator 替换: ✅
- 资源 v2 优化（加粗+精确色值+favicon 圆形裁切）已原地覆盖，代码无需改动: ✅
- `npm run build` 18 路由通过: ✅

---

## 2026-03-10

### Contact 页面更新 + 风格缩略图集成 ✅

**完成时间**: 2026-03-10
**验收状态**: 待 Founder 确认

**完成内容（3 文件修改 + 15 新增静态资源）**:

#### Contact 页面更新
- [x] `ContactContent.tsx` — 微信客服: XuhuaStory → Andrea@PrefaceAI（微信号 xingxiwh016），地址: 深圳 → 上海 黄浦区黄陂南路838号中海国际

#### TASK-STYLE-THUMBNAILS 集成（接 @AI-ML 缩略图）
- [x] 15 张缩略图压缩: 1024×1024 PNG → 400×400 JPEG (quality 75)，~27MB → ~1MB
- [x] 移动到 `public/styles/{key}.jpg`（中文文件名 → 英文 key）
- [x] `types/create.ts` — `StylePreset` 接口新增 `thumbnail` 字段，15 个预设添加图片路径
- [x] `StyleSelector.tsx` — 风格卡片从 CSS 渐变色块替换为真实 AI 生成风格示例图（渐变保留 fallback）

**新增静态资源**:
- `public/styles/pixar_3d.jpg` (51KB)、`ghibli.jpg` (82KB)、`illustration.jpg` (72KB)、`ink.jpg` (35KB)、`slam_dunk.jpg` (77KB)、`korean_webtoon.jpg` (58KB)、`oil_painting.jpg` (60KB)、`cyberpunk.jpg` (62KB)、`realistic.jpg` (59KB)、`cartoon.jpg` (71KB)、`anime.jpg` (62KB)、`watercolor.jpg` (74KB)、`children_book.jpg` (75KB)、`manga.jpg` (79KB)、`pixel.jpg` (69KB)

**验收指标**:
- 3/3 文件修改: ✅
- 15/15 缩略图压缩+移动: ✅
- `npm run build` 18 路由通过: ✅

---

### TASK-GCLOUD-OPT Google for Startups Cloud 申请网站优化 ✅

**完成时间**: 2026-03-10
**验收状态**: 待 Founder 确认 + DevOps 部署
**任务背景**: 申请 Google for Startups Cloud Program 赠金，降低前期测试成本

**完成内容（8 文件修改 + 4 新增静态资源）**:

#### About 页面团队信息（审核重点）
- [x] `AboutContent.tsx` — 新增 3 人团队卡片（Kai/Ben/Amy），真实照片+中英文名+职位+详细背景+GitHub 链接，新增英文产品摘要（提及 Google Gemini）

#### 邮箱域名替换（6 处 xuhuastory.com → prefaceai.mov）
- [x] `ContactContent.tsx` — support@xuhuastory.com → kai@prefaceai.mov
- [x] `PrivacyContent.tsx` — privacy@xuhuastory.com → kai@prefaceai.mov
- [x] `TermsContent.tsx` — support@xuhuastory.com → kai@prefaceai.mov
- [x] `CareersContent.tsx` — hr@xuhuastory.com → hr@prefaceai.mov（4 处）

#### AI-first 定位强化
- [x] `HeroSection.tsx` — 英文副标题 "Turn one sentence into a complete AI-generated story"，slogan 改 "FrameSpark™ AI Story Engine"
- [x] `ValueProposition.tsx` — 三卡片重写为 AI-first 定位（中英双语标题），描述强调 LLM + 多模态 AI

#### Google Gemini 标识 + Demo 视频 + Traction
- [x] `Pipeline.tsx` — 技术标签（Powered by Google Gemini 等），嵌入产品 Demo 视频（横屏 MP4）
- [x] `Stats.tsx` — 新增 683+ Beta Users，所有指标加英文标签

#### 新增静态资源
- [x] `public/team/kai.jpg`、`ben.jpg`、`amy.jpg`（压缩至 ~20KB/张）
- [x] `public/demo.mp4`（MOV→MP4，8.3MB）

**Google for Startups 研究发现（已向 Founder 汇报）**:
- AI-first tier 最高可获 $350K credits
- 审核重点：团队信息+专业网站+AI-first 定位+Google 生态对齐+Traction
- 申请前须确保 GCP Billing Account 管理员邮箱为 @prefaceai.mov

**验收指标**:
- 8/8 文件修改: ✅
- 4/4 新增静态资源: ✅
- `npm run build` 18 路由通过: ✅
- xuhuastory.com 在 src/ 中全部清除: ✅
- 团队照片压缩至 ~20KB: ✅

---

## 2026-03-06

### TASK-RESPONSIVE-OPT 响应式 / 移动端适配 ✅

**完成时间**: 2026-03-06
**验收状态**: 待 PM 复验

**完成内容（7 文件修改）**:

在保持现有 UI 和交互体验不变的前提下，优化移动端适配：

| 文件 | 变更 |
|------|------|
| `app/dashboard/DashboardContent.tsx` | 统计卡片 grid-cols-3 -> grid-cols-1 sm:grid-cols-3，手机上纵向堆叠 |
| `components/sections/Showcase.tsx` | Lightbox: 关闭按钮加大触控区域(w-11 h-11)，图片 mx-16->mx-4 sm:mx-16，导航箭头缩小，圆点指示器加大 |
| `components/sections/HeroSection.tsx` | min-h-screen -> min-h-[100dvh]，修复移动浏览器地址栏高度问题 |
| `app/dashboard/[storyId]/StoryDetailContent.tsx` | 导航箭头 p-2->p-2.5 sm:p-2，缩略图 w-12 h-16 sm:w-14 sm:h-20，标题 text-lg sm:text-xl |
| `components/create/StageB.tsx` | 删除按钮 sm:opacity-0（触屏始终可见），"点击编辑" hidden sm:inline |
| `components/create/StageD.tsx` | 导航箭头 w-10 h-10 sm:w-8 sm:h-8，Shot meta text-[11px] sm:text-[10px] |
| `components/layout/Header.tsx` | 移动菜单打开时 body scroll lock（useEffect + overflow hidden） |

**验收指标**:
- 7/7 文件修改: ✅
- `npm run build` 18 路由通过: ✅
- 触控目标 ≥ 44px: ✅
- hover 状态桌面限定: ✅
- 100dvh 修复: ✅
- body scroll lock: ✅

---

## 2026-03-04

### TASK-CREATE-UPGRADE P2 P3/P4 修复 ✅

**完成时间**: 2026-03-04
**验收状态**: 修复完成

**PM 复验 P2 通过 (4.8/5) 后的反馈修复（3 文件）**:

| 级别 | 文件 | 修复内容 |
|------|------|----------|
| P3 | StoryCard.tsx | +aria-label 菜单按钮 +ESC 键关闭菜单 |
| P4 | StoryDetailContent.tsx | character map key index → char.name |
| P4 | UserMenu.tsx | 设置链接 /dashboard → /settings |

`npm run build` 18 路由通过，0 错误。

---

## 2026-03-03

### TASK-CREATE-UPGRADE P2 账户体系 + Dashboard ✅

**完成时间**: 2026-03-03
**验收状态**: PM 复验 4.8/5 通过
**任务来源**: P1 复验 4.7/5 PASS 后启动 P2

**完成内容（14 文件 = 10 新建 + 4 修改）**:

#### 类型扩展（1 修改）
- [x] `types/create.ts` — +RegisterForm 接口 +StoryDetail 接口（继承 StoryCard）

#### Auth Context 增强（1 修改）
- [x] `contexts/AuthContext.tsx` — +register 函数 +stories 状态 +deleteStory，登录后加载 mock 故事

#### Mock 数据增强（1 修改）
- [x] `lib/mock-data.ts` — 故事列表 3→5 个，+coverImageUrl（引用真实 mock-shots），+getMockStoryDetail()

#### 注册页面（2 新建）
- [x] `app/register/page.tsx` — Server 组件（metadata）
- [x] `app/register/RegisterContent.tsx` — 用户名+邮箱+密码表单，验证逻辑，成功跳转 Dashboard

#### Dashboard 页面（2 新建）
- [x] `app/dashboard/page.tsx` — Server 组件（metadata）
- [x] `app/dashboard/DashboardContent.tsx` — 欢迎语+统计卡片+故事网格，未登录重定向

#### Story Detail 页面（2 新建）
- [x] `app/dashboard/[storyId]/page.tsx` — Server 组件（动态路由 metadata）
- [x] `app/dashboard/[storyId]/StoryDetailContent.tsx` — Shot 轮播+缩略图+旁白+角色+风格

#### Dashboard 组件（4 新建）
- [x] `components/dashboard/StoryCard.tsx` — 封面图+标题+风格+状态+操作菜单（续写/删除）
- [x] `components/dashboard/StoryGrid.tsx` — 搜索+筛选（状态/排序）+响应式 grid
- [x] `components/dashboard/EmptyState.tsx` — 新用户无故事引导
- [x] `components/dashboard/UserMenu.tsx` — 头像+下拉（工作台/设置/退出）

#### CreateHeader 集成（1 修改）
- [x] `components/layout/CreateHeader.tsx` — 登录态 UserMenu + 工作台链接；未登录态登录链接

**验收指标**:
- 10/10 新建文件: ✅
- 4/4 修改文件: ✅
- `npm run build` 通过（18路由，+3新路由）: ✅
- 注册→Dashboard 流程: ✅
- 登录→Dashboard（5个mock故事）: ✅
- 故事搜索/筛选/排序: ✅
- 故事详情 Shot 轮播: ✅
- CreateHeader 用户菜单: ✅
- Login 页面增加注册链接: ✅

---

## 2026-03-02

### TASK-CREATE-UPGRADE P1 Stage B-E 页面骨架 ✅

**完成时间**: 2026-03-02
**验收状态**: 待 PM 复验
**任务来源**: P0 复验 4.8/5 PASS 后启动 P1

**完成内容**:

#### P4 修复（PM 复验指出 + 自检发现）
- [x] `components/ui/CharacterUploader.tsx` — 添加 `URL.revokeObjectURL()` 防止内存泄漏
- [x] `components/ui/SceneUploader.tsx` — 同上
- [x] `components/create/StageE.tsx` — setTimeout 添加 useRef + useEffect cleanup（自检发现，与 StageA 同类问题）

#### 文档修正（PM 复验指出）
- [x] `frontend-progress/completed.md` — 日期修正
- [x] `frontend-progress/current.md` — 文件数量修正 5→7
- [x] `TEAM_CHAT.md` — 时间戳修正

#### P1 类型 + 状态管理扩展（2 修改）
- [x] `types/create.ts` — +CreateStage +GenerationLogEntry +BGMTrack +MOOD_OPTIONS +BGM_TRACKS，CreateAction 23→34
- [x] `contexts/CreateContext.tsx` — +currentStage +generationLog +bgm，reducer 23→34 case

新增 11 个 action: SET_STAGE, UPDATE_OUTLINE_TITLE, UPDATE_OUTLINE_SUMMARY, UPDATE_OUTLINE_CHARACTER, ADD_PLOT_POINT, DELETE_PLOT_POINT, SET_MOOD, UPDATE_SHOT_TEXT, REGENERATE_SHOT, DELETE_SHOT, SET_BGM

#### P1 Stage 页面组件（4 新建 + 1 修改）
- [x] `components/create/StageB.tsx` — 确认页（大纲编辑 + 角色卡片 + **情节拖拽排序** + 结局 + 情绪）
- [x] `components/create/StageC.tsx` — 生成页（进度条 + 步骤日志 + mock 推进 + 自动跳转）
- [x] `components/create/StageD.tsx` — 预览页（Shot 轮播 **真实图片** + 缩略图 + 旁白编辑 + 重新生成/删除 + BGM）
- [x] `components/create/StageE.tsx` — 交付页（漫画打包 + 视频下载 + mock 下载动画 + 新建故事）
- [x] `app/create/CreateContent.tsx` — 重构为 Stage 路由器（StageA 提取 + currentStage switch + mock 大纲注入）

#### Founder 实测修复（5 项）
- [x] StageC 进度条卡 0% — 去掉 startedRef，修复 React Strict Mode 双挂载导致 interval 被取消
- [x] StageD 图片区域右侧留白 — 图片容器改为 max-w-sm 居中 + aspect-[2/3]
- [x] Shot 预览接入真实图片 — 27 张 test_output 图拷到 `public/mock-shots/`，mock 数据改为引用真实路径
- [x] Shot 13 缺失 — 源数据跳过 shot_13，mock 数据从连续编号改为实际文件列表 `MOCK_SHOT_FILES`
- [x] StageB 情节拖拽排序 — GripVertical 图标从装饰改为功能性，用 framer-motion `Reorder` + `useDragControls` 实现

**验收指标**:
- P4 修复 3/3: ✅
- 文档修正 3/3: ✅
- 类型扩展（34 action types）: ✅
- Stage B-E 组件 4/4 新建: ✅
- CreateContent 路由整合: ✅
- 完整用户流程可走通（mock + 真实图片）: ✅
- Founder 实测修复 5/5: ✅
- `npm run build` 通过（16路由）: ✅

---

### TASK-CREATE-UPGRADE P0 Create 页面升级 ✅

**完成时间**: 2026-03-02
**验收状态**: ✅ PM 复验通过 4.8/5 (2026-03-02)
**任务来源**: PM 派发 DEC-013 Create 页面升级

**完成内容**:
- [x] `types/create.ts` — 全流程类型定义（4 types + 8 interfaces + 16 presets + 4 lengths + 23 actions）
- [x] `lib/mock-data.ts` — Mock 数据（outline/shots/progress/style analysis/character extract）
- [x] `contexts/AuthContext.tsx` — Auth 状态管理（Provider + useAuth hook）
- [x] `contexts/CreateContext.tsx` — Create 状态管理（Provider + useCreate hook + reducer）
- [x] `components/ui/AspectRatioSelector.tsx` — 画面比例（2:3竖屏 / 16:9横屏）
- [x] `components/ui/CharacterUploader.tsx` — 角色参考图上传（最多5个 + AI mock）
- [x] `components/ui/SceneUploader.tsx` — 场景参考图上传（最多8个 + 拖拽）
- [x] `components/ui/DocumentUploader.tsx` — 故事文档上传（txt/md/PDF）
- [x] `components/ui/CustomStyleUploader.tsx` — 自定义风格上传（AI 关键词 mock）
- [x] `components/ui/StyleSelector.tsx` — 重写：15 预设（默认显示8个+"更多"展开）+ 自定义 + 互斥
- [x] `components/ui/LengthSelector.tsx` — 重写：3→4 选项 + 续写模式
- [x] `components/ui/StoryIdeaInput.tsx` — 集成 DocumentUploader
- [x] `app/create/CreateContent.tsx` — 全面重构（Context + 全组件集成）
- [x] `app/create/page.tsx` — 包裹 CreateProvider
- [x] `app/layout.tsx` — 包裹 AuthProvider

**验收指标**:
- 9/9 新建文件: ✅
- 7/7 修改文件: ✅（含 components/index.ts barrel export）
- `npm run build` 通过（16路由）: ✅
- 15 种风格预设（默认8个 + "更多"展开7个）+ 自定义风格互斥: ✅
- 4 种篇幅（含长篇续写模式）: ✅
- 角色/场景/文档上传: ✅
- Context 状态管理（23 action types）: ✅

**Founder 微调（已完成）**:
- [x] 风格默认只显示 8 个，点"更多"展开剩余 7 个
- [x] "灌篮高手" → "井上雄彦"、"Pixar 3D" → "皮克斯3D"
- `npm run build` ✅ 通过

---

## 2026-02-26

### TASK-UI-STAGE-A Stage A 输入界面 ✅

**完成时间**: 2026-02-26 16:00
**验收状态**: ✅ PM 复验通过 4.5/5 (2026-02-26 16:43)
**任务来源**: PM 派发 DEC-011 产品层 Phase 2 任务

**完成内容**:
- [x] CreateHeader — 创作页轻量导航栏
- [x] StoryIdeaInput — 故事创意文本框（自动增高、字数统计、必填校验）
- [x] LengthSelector — 篇幅三选一卡片（快闪/短篇/中篇，spring 动画）
- [x] StyleSelector — 8 种风格卡片网格（CSS 渐变预览 + checkmark）
- [x] CreateContent — 页面主体组装（状态管理 + mock 提交）
- [x] page.tsx — Server Component（SEO metadata）

**新建文件（6个）**:
| 文件 | 说明 |
|------|------|
| `app/create/page.tsx` | Server Component |
| `app/create/CreateContent.tsx` | Client Component |
| `components/layout/CreateHeader.tsx` | 创作页导航 |
| `components/ui/StoryIdeaInput.tsx` | 故事创意输入 |
| `components/ui/LengthSelector.tsx` | 篇幅选择器 |
| `components/ui/StyleSelector.tsx` | 风格选择器 |

**验收指标**:
- 6/6 文件创建: ✅
- `npm run build` 通过（16路由）: ✅
- 文本框交互（自动增高/字数/校验）: ✅
- 篇幅切换动画: ✅
- 风格选择 + checkmark: ✅
- 移动端响应式: ✅
- 浏览器标签页 "开始创作 - 序话Story": ✅

**PM P1 修复（17:27）**:
- [x] FIX-1: handleSubmit 增加 500 字校验，超过阻止提交
- [x] FIX-2: setTimeout mock 用 useRef + useEffect cleanup，防卸载后 state update
- `npm run build` 再次通过 ✅

---

## 2026-02-14

### TASK-LP-PAGES-FIX 4项修复 ✅

**完成时间**: 2026-02-14 17:30
**验收状态**: ✅ PM 复验通过 4.8/5 (2026-02-14 17:35)
**任务来源**: PM 验收 TASK-LP-PAGES 4.0/5 后分配的修复任务

**完成内容**:
- [x] FIX-1 (P0): Footer `openSubPagesInNewTab` prop — 首页链接新开标签页，子页面用 `<Link>` 客户端路由
- [x] FIX-2 (P1): 11个页面添加 SEO metadata — Server/Client Component 拆分
- [x] FIX-3 (P1): Footer 内链改用 Next.js `<Link>`（与 FIX-1 合并实现）
- [x] FIX-4 (P2): 登录页 setTimeout 清理（useRef + unmount cleanup）

**修改文件**:
| 文件 | 修改 |
|------|------|
| `components/layout/Footer.tsx` | 新增 `openSubPagesInNewTab` prop，移除 `"use client"`，条件渲染 `<Link>` / `<a target="_blank">` |
| `app/page.tsx` | `<Footer openSubPagesInNewTab />` |
| `components/sections/CTASection.tsx` | "直接登录" 链接加 `target="_blank" rel="noopener noreferrer"` |

**新建文件（10个 *Content.tsx）**:
| 文件 | 说明 |
|------|------|
| `app/(marketing)/about/AboutContent.tsx` | 关于我们 Client Component |
| `app/(marketing)/terms/TermsContent.tsx` | 使用条款 Client Component |
| `app/(marketing)/privacy/PrivacyContent.tsx` | 隐私政策 Client Component |
| `app/(marketing)/careers/CareersContent.tsx` | 加入我们 Client Component |
| `app/(marketing)/help/HelpContent.tsx` | 帮助中心 Client Component |
| `app/(marketing)/tutorials/TutorialsContent.tsx` | 使用教程 Client Component |
| `app/(marketing)/faq/FAQContent.tsx` | 常见问题 Client Component |
| `app/(marketing)/contact/ContactContent.tsx` | 联系我们 Client Component |
| `app/(marketing)/pricing/PricingContent.tsx` | 定价 Client Component |
| `app/login/LoginContent.tsx` | 登录 Client Component |

**验收指标**:
- 4/4 修复完成: ✅
- `npm run build` 通过（15路由）: ✅
- 首页 Footer 新开标签页: ✅
- 子页面 Footer 客户端路由: ✅
- 浏览器标签页显示独立标题: ✅

---

### TASK-LP-PAGES 10个子页面 + 6个组件 ✅

**完成时间**: 2026-02-14 17:00
**验收状态**: ✅ PM 验收 4.0/5 → 修复后 4.8/5
**任务来源**: PM 分配的 Landing Page 子页面创建任务

**完成内容**:

Phase A — 基础设施:
- [x] `(marketing)/layout.tsx` 共享layout（SubPageHeader + Footer）
- [x] `SubPageHeader.tsx` 子页面顶部导航
- [x] `PageHero.tsx` 子页面标题区
- [x] `Footer.tsx` 3处链接更新

Phase B — 6个内容页:
- [x] `/about` 关于我们（品牌故事 + 产品理念 + 3个核心价值卡片）
- [x] `/terms` 使用条款（8节 + TOC锚点导航）
- [x] `/privacy` 隐私政策（9节 + TOC锚点导航）
- [x] `/careers` 加入我们（团队文化 + 3个职位）
- [x] `/help` 帮助中心（4个分类卡片）
- [x] `/tutorials` 使用教程（3步骤卡片）

Phase C — 2个交互页面:
- [x] `/faq` 常见问题（FAQAccordion组件 + 4分类15问答）
- [x] `/contact` 联系我们（联系信息 + 表单验证 + 提交状态）

Phase D — 2个高复杂度页面:
- [x] `/pricing` 定价（PricingToggle月/年切换 + 3个PricingCard + 定价FAQ）
- [x] `/login` 登录（InviteCodeInput + 邀请码验证 + 震动动画 + 成功界面）

**新建文件（17个）**:
| 文件 | 说明 |
|------|------|
| `components/layout/SubPageHeader.tsx` | 子页面顶部导航 |
| `components/ui/PageHero.tsx` | 子页面标题区 |
| `components/ui/FAQAccordion.tsx` | FAQ手风琴组件 |
| `components/ui/PricingToggle.tsx` | 月付/年付切换 |
| `components/ui/PricingCard.tsx` | 定价卡片 |
| `components/ui/InviteCodeInput.tsx` | 邀请码输入 |
| `app/(marketing)/layout.tsx` | 共享layout |
| `app/(marketing)/about/page.tsx` | 关于我们 |
| `app/(marketing)/terms/page.tsx` | 使用条款 |
| `app/(marketing)/privacy/page.tsx` | 隐私政策 |
| `app/(marketing)/careers/page.tsx` | 加入我们 |
| `app/(marketing)/help/page.tsx` | 帮助中心 |
| `app/(marketing)/tutorials/page.tsx` | 使用教程 |
| `app/(marketing)/faq/page.tsx` | 常见问题 |
| `app/(marketing)/contact/page.tsx` | 联系我们 |
| `app/(marketing)/pricing/page.tsx` | 定价 |
| `app/login/page.tsx` | 登录 |

**修改文件（1个）**:
| 文件 | 修改 |
|------|------|
| `components/layout/Footer.tsx` | #pricing→/pricing, #features→/#features, #showcase→/#showcase |

**验收指标**:
- 10/10 页面创建: ✅
- 6/6 组件创建: ✅
- `npm run build` 通过（15路由）: ✅
- 所有交叉链接: ✅
- 交互功能（FAQ/表单/定价切换/登录验证）: ✅

---

## 2026-02-12

### TASK-LP-POLISH 2项代码质量修复 ✅

**完成时间**: 2026-02-12 16:05
**验收状态**: 待 PM 复验
**任务来源**: TASK-LP-FIX 复验后 PM 分配的代码质量提升任务（4.5→5.0/5）

**完成内容**:
- [x] LP-POLISH-1: Pipeline.tsx 硬编码 rgba → CSS 变量（3个RGB分量变量 + 4处引用替换）
- [x] LP-POLISH-2: HeroSection.tsx setTimeout cleanup（useRef + pauseAndResume + unmount cleanup）

**修改文件**:
| 文件 | 修改 |
|------|------|
| `frontend/src/app/globals.css` | 新增 --brand-primary-rgb / --brand-gradient-end-rgb / --brand-cta-rgb |
| `frontend/src/components/sections/Pipeline.tsx` | 4处 rgba → CSS变量引用 |
| `frontend/src/components/sections/HeroSection.tsx` | useRef timer管理 + pauseAndResume + cleanup |

**验收指标**:
- 2/2 任务完成: ✅
- `npm run build` 通过: ✅
- 零硬编码品牌色: ✅
- 零未清理 timer: ✅

---

### TASK-LP-FIX 8个修复任务 ✅

**完成时间**: 2026-02-12 14:35
**验收状态**: 待 PM 复验
**任务来源**: PM 验收 Landing Page 4.0/5 后分配的修复任务

**完成内容**:
- [x] LP-P0-1: Pipeline.tsx → FrameSpark™ 品牌氛围模块（整体重写）
- [x] LP-P1-1: Showcase 添加 lightbox/modal（键盘导航、dot分页、body scroll lock）
- [x] LP-P1-2: 移除"古风武侠"空分类
- [x] LP-P1-3: ValueProposition 文案（"即发即用""角色如一""双输出形式"）
- [x] LP-P2-1: Hero 条漫从右向左逐张滑入
- [x] LP-P2-2: Hero Slogan 改为"FrameSpark™ AI条漫引擎"
- [x] LP-P2-3: Showcase 标题改为"更多创作可能"
- [x] LP-P2-4: globals.css 添加 prefers-reduced-motion 支持

**修改文件**:
| 文件 | 修改 |
|------|------|
| `frontend/src/components/sections/Pipeline.tsx` | 整体重写为品牌氛围模块 |
| `frontend/src/components/sections/Showcase.tsx` | 整体重写，新增 lightbox |
| `frontend/src/components/sections/ValueProposition.tsx` | 文案调整 |
| `frontend/src/components/sections/HeroSection.tsx` | 滑入动效 + Slogan修改 |
| `frontend/src/app/globals.css` | prefers-reduced-motion 媒体查询 |

**验收指标**:
- 8/8 任务完成: ✅
- `npm run build` 通过: ✅
- 无技术流程暴露: ✅
- 品牌用语统一: ✅

---

## 2026-01-29

### Landing Page 基础版本实现 ✅

**完成时间**: 2026-01-29 22:00
**验收状态**: 待 PM 验收
**交接编号**: HANDOFF-2026-01-29-010

**完成内容**:
- [x] Next.js 14 项目初始化
- [x] TailwindCSS 配置（视觉规范完整实现）
- [x] CSS 变量定义（配色、间距、动效、阴影）
- [x] 字体配置（Noto Sans SC, Noto Serif SC, Inter）
- [x] 7个模块组件实现
- [x] 条漫素材复制
- [x] 构建验证通过

**关键产出**:
| 文件 | 说明 |
|------|------|
| `frontend/src/app/page.tsx` | 主页面 |
| `frontend/src/app/globals.css` | 全局样式 + CSS变量 |
| `frontend/tailwind.config.ts` | Tailwind配置（完整设计系统） |
| `frontend/src/components/layout/Header.tsx` | 吸顶导航 + 移动端菜单 |
| `frontend/src/components/layout/Footer.tsx` | 页脚 |
| `frontend/src/components/sections/HeroSection.tsx` | 全屏条漫展示 + 双故事切换 |
| `frontend/src/components/sections/ValueProposition.tsx` | 3大差异化卖点 |
| `frontend/src/components/sections/Pipeline.tsx` | FrameSpark™ 5阶段 |
| `frontend/src/components/sections/Showcase.tsx` | 作品画廊 + 分类筛选 |
| `frontend/src/components/sections/Stats.tsx` | 技术指标数字动画 |
| `frontend/src/components/sections/CTASection.tsx` | 邮箱申请表单 |
| `frontend/public/comics/story-a/` | 都市亲情条漫（4张） |
| `frontend/public/comics/story-b/` | 赛博朋克条漫（4张） |

**设计系统实现**:
| 项目 | 值 |
|------|-----|
| 主题 | Warm Dark Mode |
| 背景色 | #121212 深炭灰 |
| 品牌色 | #FF9500 暖琥珀 |
| CTA渐变 | #FF9500 → #FF6B00 |
| 字体 | Noto Sans SC / Noto Serif SC / Inter |
| 动效时长 | 200ms-700ms（故事感节奏） |

**验收指标**:
- 7个模块实现: ✅
- 响应式适配: ✅ 基础版本
- 条漫展示: ✅ 双故事切换 + 自动轮播
- 构建成功: ✅

**预览地址**: http://localhost:3000

---

## 2026-01-19

### 三个全维度差异化原型 ✅

**完成时间**: 2026-01-19
**验收状态**: 通过（等待创始人选择）

**完成内容**:
- [x] 对话式原型（Conversational）- 聊天气泡布局
- [x] 沉浸式卡片原型（Carousel）- 全屏滑动 + 3D翻转
- [x] 实时预览原型（Split Panel）- 左右分栏

**关键产出**:
| 文件 | 说明 |
|------|------|
| `prototype/create-story-conversational.html` | 对话式 - 聊天气泡布局，消息淡入弹跳 |
| `prototype/create-story-carousel.html` | 沉浸式卡片 - 全屏滑动，3D翻转切换 |
| `prototype/create-story-split.html` | 实时预览 - 左右分栏，内容淡入更新 |

**配色方案**:
| 方案 | 背景色 | 主色 |
|------|--------|------|
| Conversational | 白 #FFFFFF | 蓝 #2563EB |
| Carousel | 苹果灰 #F5F5F7 | 橙 #FF6600 |
| Split Panel | 浅蓝白 #F8FAFC | 紫 #6366F1 |

**验收指标**:
- 布局差异化: ✅ 三种完全不同的布局
- 交互差异化: ✅ 对话/滑动/实时预览三种交互
- 动效差异化: ✅ 淡入弹跳/3D翻转/淡入更新

---

### UI/UX Pro Max Skill 安装 ✅

**完成时间**: 2026-01-19
**验收状态**: 通过

**完成内容**:
- [x] 从 GitHub 克隆 `nextlevelbuilder/ui-ux-pro-max-skill`
- [x] 安装到 `.claude/skills/ui-ux-pro-max/`
- [x] 生成序话Story推荐设计系统

**关键产出**:
| 文件 | 说明 |
|------|------|
| `.claude/skills/ui-ux-pro-max/` | 完整 Skill 文件 |

**验收指标**:
- Skill 可用: ✅
- 57+ UI 风格: ✅
- 97+ 配色方案: ✅

---

### 序话Story 设计系统生成 ✅

**完成时间**: 2026-01-19
**验收状态**: 通过

**设计系统规格**:
| 项目 | 选定方案 |
|------|----------|
| 模式 | Video-First Hero |
| 风格 | Dark Mode (OLED) |
| 主色 | `#3B82F6` (蓝) |
| CTA色 | `#F97316` (橙) |
| 背景色 | `#F8FAFC` (浅灰) |
| 文字色 | `#1E293B` (深灰) |
| 字体 | Plus Jakarta Sans |

---

## 已归档（历史记录）

### 换色版本原型（已废弃）

**完成时间**: 2026-01-19 17:00
**状态**: ❌ 被创始人否决

**原因**: 仅换色，布局/交互/动效完全一样，不是真正不同的体验

**废弃文件**:
- `prototype/create-story-light-flat.html`
- `prototype/create-story-light-bento.html`
- `prototype/create-story-light-aurora.html`

---

## 任务归档模板

```markdown
### [任务标题] ✅

**完成时间**: YYYY-MM-DD
**验收状态**: 通过/部分通过

**完成内容**:
- [x] 内容1
- [x] 内容2

**关键产出**:
| 文件 | 说明 |
|------|------|
| path/to/file | 说明 |

**UI 截图**: (如有)

**验收指标**:
- 指标1: 结果 ✅/❌
```


---

### TASK-T5-FIXBATCH 7 条前端修复 ✅ (2026-04-27 PM 代更归档)

**完成时间**: 2026-04-27 16:23 (~7 min agent 时间)
**验收状态**: ✅ npm build 20 routes 0 errors / 7 条全部完成

**完成内容**:
- [x] UX-7 ETA monotonicity guard
- [x] UX-9 大标题随 stage 动态
- [x] UX-11 完成立即 redirect
- [x] UX-2 (A1) 跨 plot 数字高亮
- [x] UX-8 "图像"→"片段"
- [x] UX-12 Stage 1-4/5/6 副标题分流
- [x] UX-1 (FE) Stage C 真 portrait + silhouette fallback

**关键产出**:
| 文件 | 改动 |
|------|------|
| `frontend/src/components/create/StageC.tsx` | UX-7/9/11/8/12/1(FE) |
| `frontend/src/components/create/StageB.tsx` | UX-2(A1) |
| `frontend/src/types/create.ts` | portraitUrl + portrait_url 字段 |

**待 Backend 配合**: chapter.characters_json 加 portrait_url 字段（UX-1 后端部分）


---

## 2026-04-30 11:00 Wave 5.1 归档（PM 代更，权限 600）

D.14 三处 banner 共享 useStageLock + D.13 hydrate guard + D.16 mood string|null + T-1 friendlyMessage + StageD onError safetyAdvice + R7-2 favorite/share/公开页 frontend + /s/[token] Server Component。详见 current.md 19:30 + Wave 5.2 已部署生产。

---

## D.19 — hydrateProjectFromBackend chapter 404 误判黑屏 hotfix v1 [2026-04-30 15:20]
- 改动: frontend/src/app/create/CreateContent.tsx L484-708
- 重构 hydrate 为两步: project 单独 try/catch (唯一 notFound 触发点) + chapter Promise.all 各自 .catch 吞 404
- 外层 catch 改 notFound=false (generic 错误，避免 chapter 404 被误判为项目不存在)
- 验证: npm run build 20 routes 0 errors

## D.20 — StageB outline=null 黑屏 hotfix v2 [2026-04-30 17:09]
- 改动:
  - frontend/src/app/create/CreateContent.tsx L775-792 (outline recovery via POST generate-outline)
  - frontend/src/components/create/StageB.tsx L130 (null guard 改 loading spinner '正在加载故事大纲...')
- Root cause: backend ProjectDetail 不返 raw_outline_json → hydrate state.outline=null → StageB 空渲染黑屏
- 修复: hydrate 后 outline=null && stage=outline 自动调幂等 generate-outline 恢复 outline，注入 dispatch HYDRATE_FROM_BACKEND
- 验证: npm build 20 routes 0 errors + Founder F12 console 真见 [hydrate] outline recovered successfully
- 配套: Backend 同期完成 raw_outline 字段+幂等 (PM 派 Option C 后置永久解法)
- 部署踩坑: frontend pid 36674 启动 15:29 < hotfix v2 17:09 → 必须重启加载新 build (PM 17:44 发现+处理，新 pid 49226)

---

### 2026-05-09 16:44-17:00 — B36+B27+B28+B37 修复 (PM 代写)

参考 frontend-progress/current.md 17:00 段

---

### 2026-05-11 10:41-10:48 — B36 v3 + B42 + B44 + B46 全闭环 ✅（PM 代写）

参考 frontend-progress/current.md 10:41-10:48 段。两次 agent spawn:
- Wave 1 (a50d2d1727de1db27): B36 v3 + B44 + B46
- Follow-up (ae2ccec81c3cedc50): B42 scenes/endings/hasScenes

PM 干净重启 frontend (PID 43584 / next-server 43604) BUILD_ID `CDKVfwbPoTu04NXtBsdFS`

---

### 2026-05-11 17:18 Wave 5 — B49+B50+B48 全闭环 ✅（PM 代写）

参考 frontend-progress/current.md 17:18 段。BUILD_ID `nyVs1UIUpv8EcHThyi1I6`。
