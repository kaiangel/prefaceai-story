# Frontend 当前任务进度

> 更新时间: 2026-05-28 [Plan A++ progressive enhancement] 完成 — StageD 主 img thumb→full swap + vitest 5 新 case
> 状态: ✅ 完成 (2 文件改 + 1 新建测试, build 20 routes 0 errors, npm test 20/20 PASS)
> 模型: Sonnet 4.6
> 下一步: 等 PM 审查 + DevOps 部署 + Founder 浏览器手测 (Network tab 确认 thumb 秒出, 后台全图 swap)

## 最新完成: Plan A++ progressive enhancement (2026-05-28)

### 改动文件 (2 改 + 1 新建, 0 越权)

| 文件 | 改动 |
|------|------|
| `frontend/src/components/create/StageD.tsx` | 加 `progressiveImageSrc` + `isHighRes` state; 加 progressive enhancement useEffect (thumb 先显 + cancel flag + 后台全图 swap); 主 `<img>` src 改为 `progressiveImageSrc`; `opacity-90/100` CSS transition |
| `frontend/src/components/create/StageC.tsx` | SceneRefsPreview prefetch useEffect 加注释: `SceneReferenceItem` 无 thumbnail 字段, 不做 progressive (prefetch 已覆盖体感优化) |
| `frontend/src/components/create/StageD.progressive.test.ts` (新) | 5 个 vitest 单测: thumb→full swap / 无 thumb fallback / null src / cancel flag / thumb==full |

### 关键实现细节

**Plan A++ 行为**:
1. `currentShot` 变化 → useEffect 立即 `setProgressiveImageSrc(thumbUrl)` + `setIsHighRes(false)` → thumb ~2s 跨海出图
2. `new window.Image()` 后台加载 fullUrl (~1MB, ~4-7s)
3. `fullImg.onload` → 自动升清 (cancel flag 保证: 快速切 shot 时 stale onload 不更新状态)
4. 旧数据 (无 `imageUrlThumb`) → 直接全图, `isHighRes=true` (兼容)

**SceneRefsPreview 状态**: `SceneReferenceItem` 无 thumbnail 字段, progressive 不适用, prefetch 已是体感优化。

### 验证
- ✅ `npm run test` 20/20 PASS (15 useETA + 5 新 progressive)
- ✅ `npm run build` 20 routes 0 errors

---

## 上一批完成: test30 性能 P0+P2 修复 (2026-05-28)

### 改动文件 (4 改, 0 越权)

| 文件 | 改动 |
|------|------|
| `frontend/src/types/create.ts` | Shot interface 加 `imageUrlThumb?: string \| null` |
| `frontend/src/app/create/CreateContent.tsx` | hydrate rawShots.map() 加 `rawImageUrlThumb` + `imageUrlThumb: toAbsoluteUrl(rawImageUrlThumb)` |
| `frontend/src/components/create/StageC.tsx` | `finalizeAndGoToPreview`: 加 `fixImageUrl()` 修正旧 `/api/projects/` 路径 + `imageUrlThumb` mapping; SceneRefsPreview: 加 prefetch useEffect (全部 interior+exterior URLs) |
| `frontend/src/components/create/StageD.tsx` | import 加 `useEffect`; 加 preload useEffect — currentIndex 变化时 prefetch ±2 相邻 shots |

### P2 #13 根因说明 (通知 PM 需 Backend 根治)
`app/api/projects.py:1025` 硬编码 `f"/api/projects/{project_id}/images/shot_{shot_id:02d}.png"` 而不读 storyboard_json 的 `image_url`。前端 `fixImageUrl()` 是 workaround；backend 根治 = 修 L1025 直接读 `shot.get("image_url")`。

### 验证
- ✅ `npm run test` 15/15 PASS
- ✅ `npm run build` 20 routes 0 errors (0 新增 warning)

---

## 上一批完成: Wave 13 #6 前端 (2026-05-25, 修前后端契约 gap)

## 最新完成: Wave 13 #6 前端 (2026-05-25, 修前后端契约 gap)

### 背景 (前后端契约断裂, PM 地毯式审查抓到)
- Backend Wave 13 #6 把 `regenerate-portrait` 改异步 (返 **202 + job_id**, 复用 adjust_job_manager kind=`regenerate_portrait`)
- 但前端 StageC `handleRegenerate` 还是**同步调用** (期待 200 + `{portrait_url}`), 拿到 202+job_id 不是期待结果 → **reroll (留空调整框) 功能会断**
- 我补前端轮询, 与 Wave 12 adjust 异步 pattern 一致

### 改法 (最大复用 adjust 轮询, 不重复造轮子)
- 抽取共享轮询 helper `pollCharacterJob(jobId, charId, onComplete)` — adjust 和 reroll **共用同一 GET `/characters/adjust-jobs/{job_id}` 轮询端点**
- `CharacterJob` interface 加 `kind?: "adjust" | "regenerate_portrait"` 字段 (严格按 §9.7.4 契约), 提到组件作用域共享
- `handleRegenerate` (reroll): POST 拿 202+job_id → `pollCharacterJob` → completed 读 `result.portrait_url` (cache-buster `bustUrl`) 刷新角色卡 + 清 portraitErrors + toast "已重新生成" / failed → error 提示
- `handleApplyAdjustment` (adjust): 内联轮询循环 (88 行) 替换为调 `pollCharacterJob`, completion 回调额外记录 adjustment text + description (adjust 专属), **行为不变**
- POST kickoff 失败 (404 项目/角色不存在 / 400 未生成大纲) → 立即 toast 不轮询
- loading 显 `adjustJobMsg` = backend `stage_message` + `progress%` (不裸转圈), DEC-030 backend authoritative 不本地猜 60s 完成时间

### 严格按 §9.7.4 契约字段
- `job_id / char_id / kind("regenerate_portrait") / status(pending|processing|completed|failed) / progress / stage_message / result{success,char_id,portrait_url,fullbody_url,message} / error`
- portrait_url 带 ?v={epoch} cache-buster (后端) + 前端再加 `&_={Date.now()}` 双保险; fullbody 失败时 null 非阻塞

### 不破坏 adjust (Wave 12)
- adjust 路径完全保留: 仍 POST `/adjust` 202 → 轮询同端点 → completed 记 adjustment + description + portrait
- 仅把 adjust 内联的 88 行轮询循环抽成共享 helper, 逻辑 1:1 迁移 (POLL_INTERVAL 2s / MAX_POLLS 120 / 800ms 初始延迟 / silentStatuses [404] / progress clamp / friendly stage_message 全保留)

### 验证
- ✅ tsc 0 / build 20 routes 0 errors / eslint StageC 0 / npm test 15/15 PASS
- ⚠️ dev HMR: StageC 非 root layout, HMR 可 reload; 改完已 npm build verify

### 改动文件 (1 改, 0 越权全在 frontend/)
| 文件 | 改动 |
|------|------|
| `src/components/create/StageC.tsx` | 抽 `pollCharacterJob` + `bustUrl` 共享 helper; `handleRegenerate` 同步→异步轮询; `handleApplyAdjustment` 轮询块复用 helper |

[frontend-impact: n/a — 纯前端对接 Backend 已改的异步端点, 0 自己改 API/schema/契约]

---

## 上一批完成: Wave 13 #4 + #5 + #9 (2026-05-25, 内测前 FIXBATCH)

## 最新完成: Wave 13 #4 + #5 + #9 (2026-05-25, 内测前 FIXBATCH)

### #9 前端测试框架 (vitest)
- 装 `vitest@2.1.9` + `jsdom@25` + `@testing-library/react@16` + `@testing-library/jest-dom@6` + `@vitejs/plugin-react@4` (全 devDependencies)
- 新建 `vitest.config.ts` (jsdom env + `@` alias + setupFiles + include `src/**/*.test.ts`)
- 新建 `vitest.setup.ts`: **override `console.assert` 在 falsy 时 throw** (原 useETA.test.ts 用 console.assert, native 永不抛错 → 测试器下失败会"静默 pass"; override 后每条断言变真 pass/fail)
- `package.json` 加 `test: vitest run` + `test:watch: vitest`
- `useETA.test.ts` 改: 底部 IIFE + `process.exit(1)` runner → vitest `describe`/`it` (15 个 it 各调一个 test 函数; **15 个 test 函数体完全不动**, 仅换 runner harness)
- **验证**: `npm test` → 15/15 PASS; 另跑临时 sanity test 证明 console.assert override 真能让失败 case FAIL (非空过)

### #4A 确认流程 hydrate 超时不给"返回工作台" (CreateContent.tsx)
- 根因 (P2-2): hydrate 超时兜底 UI (L1609 timeout branch) 不区分"确认流程中"。确认流程还要确认角色+场景, 此时"返回工作台"打断流程
- 修: 加 `inConfirmationFlow = urlStage ∈ {outline,characters,scenes}`。timeout branch:
  - 确认流程中 → 文案改"正在自动重试…确认环节马上回来", **隐藏"返回工作台"**, 加 `useEffect` 自动重试 (8s 后 reload, sessionStorage 计数上限 3 次防死循环)
  - 纯生成/preview/delivery → 保留"返回工作台" (无确认动作, 离开安全)

### #4B 后台生成按钮守卫 — 修"忽有忽无" (StageC.tsx)
- 根因 (P2-3): 旧守卫 `subPhase==="shot-gen" || (text-gen && currentStage==="storyboard")` → storyboard(显示)→scene_image_preparation(隐藏)→场景确认后(显示) = 闪烁
- 旧 RISK-T17-7 假设"storyboard 时已确认场景"**错** — 场景确认 (scenesConfirmed) 在 R4-3 (scene_references_ready 之后), 晚于 storyboard
- 修 (单一信号 = `state.scenesConfirmed`): `state.scenesConfirmed && subPhase==="shot-gen" && !isError` → 确认前全程隐藏, 仅场景确认后 (image_preparation/image_generation/bgm/music) 一致显示, 与 STAGE_SUBTITLE "可以选择后台生成"文案逻辑对齐
- `scenesConfirmed` 是 backend authoritative (hydrate 自 scenes_confirmed), 页面重进 mid-gen 仍正确

### #5 404 分级 Wave B 未生效 — 🔑 真根因找到 + 实测生效 (layout.tsx)
- **真根因 (e2e 挖出, 非之前推测的"stale tab")**: `CLIENT_LOG_PROXY_SCRIPT` 是 JS **template literal**, Wave B 写的 regex 字面量 `/\/chapters\/\d+\/(...)/` 里的反斜杠在模板字符串构造时被吃掉 (`\d`→`d` / `\/`→`/`), emit 到浏览器的脚本变成 `//chapters/d+/...` — 开头 `//` 把整个 `isRoutine404` 赋值变成**行注释** → isRoutine404 永远 undefined → 全部记 network。**这就是 test28 0 routine-404 + 18 network 的真因 (代码审查看不出, 因为源码 regex 看着对的)**
- 修: regex 字面量 → **无反斜杠纯字符串检查** (`url.indexOf('/chapters/')` + `routineSuffixes` 后缀匹配 + 去 query string), 模板字符串无任何可被吃掉的转义
- 加固: `CLIENT_LOG_PROXY_VERSION = "w13-404-v2"` + 加载时 POST `proxy-init` 记版本号 (将来可在 client.log 确认浏览器加载的是新版, 治"代码审查≠实测生效")
- **e2e 验证 (跑真 shipped 脚本, 非重实现)**: 从 production build 服务的 HTML 抽出真实 proxy IIFE, jsdom + mock fetch 跑 → 6 个 chapter 404 (含 `?poll=1` query) **全 routine-404** ✅ / 真非-chapter 404 仍 network ✅ / proxy-init 版本标记 w13-404-v2 ✅
- ⚠️ 部署注意: layout.tsx 改动 Next.js dev HMR **不刷新** root layout inline script — dev server 必须重启浏览器才拿到新版 (这本身印证 test28 教训: 改 layout 不重启 = 浏览器跑旧脚本)

### 改动文件 (6 改 + 2 新建, 0 越权全在 frontend/)
| 文件 | 任务 | 改动 |
|------|------|------|
| `vitest.config.ts` (新) | #9 | vitest 配置 (jsdom + alias + setup) |
| `vitest.setup.ts` (新) | #9 | console.assert override throw + jest-dom |
| `package.json` | #9 | devDeps + test script |
| `src/hooks/useETA.test.ts` | #9 | runner IIFE → vitest describe/it (15 函数体不动) |
| `src/app/create/CreateContent.tsx` | #4A | inConfirmationFlow 守卫 + 自动重试 effect + 隐藏返回工作台 |
| `src/components/create/StageC.tsx` | #4B | 后台生成按钮守卫改 scenesConfirmed && shot-gen |
| `src/app/layout.tsx` | #5 | regex→纯字符串 routine-404 + 版本标记 proxy-init |

### 验证
- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npm run build` 20 routes 0 errors
- ✅ `npm test` (vitest) 15/15 PASS
- ✅ `npx next lint` 改动文件 0 warnings/errors
- ✅ #5 e2e: 真 shipped 脚本 jsdom 实测 routine-404 生效 (6/6 chapter 404, 0 误记 network)

---

## 历史完成: TASK-TEST26-FRONTEND-4 (2026-05-24, test26 4 前端问题)

> 状态: ✅ 4 项完成 (5 文件改, npm run build 20 routes 0 errors, tsc 0, useETA 15/15 PASS, lint 0 新增)
> 模型: Opus 4.7 xhigh
> 下一步: 等 PM 审查 + Founder e2e 实测 (重点验"陈明转圈"消失)

## 最新完成: TASK-TEST26-FRONTEND-4 (2026-05-24, test26 4 前端问题)

### 背景
test26 (cyberpunk + ai_entity) 全维度回溯暴露 4 个前端问题 (TEST26_FULL_RETROSPECTIVE):
P2-1 adjust 转圈 (陈明"重新生成"死等 90s + POST 发 3 次) / P2-2 ETA Stage 1-4 冻结 / P3-2 NETWORK_ERROR 96min 异常计时 / P3-3 404 日志分级不一致.

### 改动 5 文件 (0 越权, 全在 frontend/src)

| 文件 | 任务 | 改动 |
|------|------|------|
| `StageC.tsx` | ① P2-1 | `handleApplyAdjustment` 改异步轮询 (POST→202 拿 job_id → 轮询 GET adjust-jobs/{job_id} 每 2s 直到 completed/failed); 加 `adjustJobMsg` state; loading UI 显 stage_message+progress (不再裸 spinner); completed 用 cache-buster 刷 portraitUrl + 清 portraitErrors; failed 读 error 提示 |
| `useETA.ts` | ② P2-2 | P1 backend authoritative 分支加时间插值: anchor (last backend value + 首见时刻), 同值冻结时按 elapsed 平滑递减, 新值来时 re-anchor; floor 在 NEAR_ZERO_SEC 防 Stage 1-4 误显"即将完成"; resetForStage 重置 anchor |
| `useETA.test.ts` | ② P2-2 | 加 `testP22_BackendEtaInterpolation` (15/15 PASS): 首见verbatim / 冻结递减 / 新值re-anchor / NEAR_ZERO floor / 小值floor |
| `api.ts` | ③ P3-2 | NETWORK_ERROR catch: elapsed>120s 或 document.hidden → 判 tab 挂起, 降级 console.error→console.warn + 标注"elapsed unreliable"; 真网络错 (<2min + 可见) 仍 console.error |
| `layout.tsx` | ④ P3-3 | fetch wrapper 对 `/chapters/{n}/(status|story|storyboard|bgm|scene-references)` 的 404 改记 `level: 'routine-404'` (原全记 level:'network'), 与应用层 routine warn 统一 |

### 严格遵循 §9.7 契约
- POST adjust 读 `job_id` (§9.7.1)
- GET adjust-jobs/{job_id} 读 `status`/`progress`/`stage_message`/`result`/`error` (§9.7.2 精确字段名, 无自创)
- completed → `result.portrait_url` + `result.character.description_zh` (§9.7.2 result shape)
- 404 = 过期/未注册 → 重试 (§9.7.2)
- DEC-030: 前端只按 status+progress 派生 loading UI, 不本地猜 90s

### 关键设计决策
- **reroll (留空) 不动**: §9.7.3 明确 regenerate-portrait 本轮未异步化, `handleRegenerate` 仍同步, 保持原样
- **ETA 插值不破坏 backendEstimatedSecondsRef (T20-9)**: 插值只在 P1 branch 内平滑*显示*同一 backend 值, 优先级链 + isBackendAuthoritative bypass smoothing 全保留
- **NETWORK_ERROR 真伪区分**: 1.25min (MySQL 真 transient, tab 可见) 仍 error; 96min/18min (tab 挂起) 降 warn
- **P3-3 真根因**: silentStatuses 只压 api.ts 内部 warn, layout.tsx 全局 fetch wrapper 独立记 level:network — 故 18 个 pre-confirm 404 全混进 network bucket. 改 wrapper 按 endpoint 分流 routine-404

### 验证
- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npm run build` 20 routes 0 errors (warnings 全 pre-existing img)
- ✅ `npx ts-node useETA.test.ts` 15/15 PASS
- ✅ `npx next lint` 我改的 5 文件 0 新增 warning
- ✅ 0 越权 (仅 frontend/src: StageC/useETA/useETA.test/api/layout)

### 等 Founder e2e 实测
| 验证项 | 期望 |
|------|------|
| adjust (填描述重生) | 点"重新生成"后 loading 显 "AI 重绘中 X%", 不再死等转圈; 完成自动刷新头像; POST 只发 1 次 |
| adjust 失败 | 显 "调整失败：{原因}" toast |
| ETA Stage 1-4 | "预计还需约 N 分钟"随时间递减, 不冻结在固定值 |
| NETWORK_ERROR | tab 挂起后 client.log 不再有 error-level "NETWORK_ERROR 96min" (改 warn) |
| 404 分级 | /outline 停留, pre-confirm 404 记 level:'routine-404' (非 network/error) |

---


## 最新审查: T22-NEW-8 StageB confirm-outline wire 审查 (2026-05-22)

### 结论: 已实现, 无需修改

**任务要求**: "确认大纲" 按钮调 `POST /api/projects/{uuid}/chapters/1/confirm-outline`

**实际情况**:
- `chapters/1/confirm-outline` 端点在 backend 中**不存在** (chapters.py grep 确认)
- 正确端点是 `POST /projects/{project_id}/confirm-outline` (projects.py L518-593)
- StageB.tsx `handleConfirm` (L152-255) 已调用此端点, 发送完整编辑大纲 state
- 用户编辑 (title/summary/characters/plotPoints/mood) 均从 `state.outline` 真发出
- success 路径: 调 `start-generation` → `dispatch CONFIRM_OUTLINE` → StageC
- error 路径: toast error (setSubmitError)
- warning 路径: banner + "知悉并继续" 按钮 (RISK-T14-13-frontend)

**结论**: PENDING.md T22-NEW-8 引用了错误 URL (chapters/1 vs project-level). 实际功能已完整实现, 0 代码需要修改.

**npm run build**: 20 routes, 0 errors (验证完成)

---

## 最新完成: T22-NEW-5 R4-2 scene_review 删除 (2026-05-22)

### 背景

删除 R4-2 (`scene_review` / `scene-preview` / `/scenes` 文字情节确认层), 保留 R4-1 (character_review) 和 R4-3 (scene-refs-preview / scene_references_review).

**部署铁律**: 本次 frontend 改动必须与 Backend Wave 8 同时部署:
- Backend Wave 8 需做: pipeline_orchestrator.py 删 R4-2 wait loop + STATUS_API_CONTRACT 升级 v1.5 + chapters.py confirm-scenes endpoint 清理
- 任何一方单独上线都会导致状态机不一致

### 改动: 5 文件

| 文件 | 改动 |
|------|------|
| `frontend/src/types/create.ts` | `GenerationSubPhase` 删 `"scene-preview"` |
| `frontend/src/lib/createUrl.ts` | `UI_PHASE_TO_URL` 删 `scene_review: "scenes"` + `deriveUrlStageFromState` 删 `"scene-preview"` arm + `deriveStateFromUrl` `"scenes"` case 改为返回 `"scene-refs-preview"` |
| `frontend/src/app/create/CreateContent.tsx` | `uiPhaseToSubPhase` 删 `scene_review: "scene-preview"` + 删 `isSceneReview` force-route block (~75 行) + 删 `scenesConfirmedNow` race guard |
| `frontend/src/components/create/StageC.tsx` | 删 `handleConfirmScenes` useCallback + 删 `handleUpdatePreviewScene` useCallback + 删 `scene-preview` render block + 更新 D.23 watcher + `ScenePreview` 函数保留但加 eslint-disable |
| `frontend/src/components/create/StageB.tsx` | D.14 progressStage 三元 `"scene-preview"` arm 改为 `"scene-refs-preview"` |

### 验证

- ✅ `npm run build` 20 routes 0 errors (warnings 全 pre-existing)
- ✅ R4-1 (character_review / char-preview) 保留完整
- ✅ R4-3 (scene_references_review / scene-refs-preview / SceneRefsPreview 组件) 保留完整
- ✅ /outline 页面保留完整
- ✅ 0 越权 (仅改 frontend/src + StageB.tsx)

## 最新完成: T22-NEW-2 SceneRefsPreview 卡片智能展示 (2026-05-22)

### 问题背景 (Founder 5/21-22 真 2 次实测 + 反馈)

Wave II SceneRefsPreview 默认渲染 sm:grid-cols-2 (interior 左 + exterior 右), 有 url 显图, 无 url 显 "内景未生成"/"外景未生成" 占位. 洞穴/海底 by-design 只生 interior, 海面/沙滩 by-design 只生 exterior (DEC-014/DEC-009). 但 "未生成" 占位让用户误以为系统有问题/缺失.

Founder 5/22 13:44: "前端的 UX 可以做的更好"

### 改动: 1 文件

`frontend/src/components/create/StageC.tsx` — `SceneRefsPreview` 卡片渲染逻辑重写 (T22-NEW-2 注释标注)

### 4 种 case 真 cover

| Case | interior_url | exterior_url | 布局 | 标签 | 重生按钮 |
|------|-------------|-------------|------|------|---------|
| 两者都有 (渔村) | 有 | 有 | grid-cols-2 双图 | 无额外标签 | 重生内景 + 重生外景 + 重生全部 |
| 只有 interior (洞穴/海底) | 有 | null | 全宽 interior | "(室内场景，无室外画面)" 灰色小字 | 重生内景 + 重生此场景 (无重生外景) |
| 只有 exterior (海面/沙滩) | null | 有 | 全宽 exterior | "(室外场景，无室内画面)" 灰色小字 | 重生外景 + 重生此场景 (无重生内景) |
| 都无 (异常边缘) | null | null | 统一错误提示 | "场景图生成失败，请重新生成" | 重新生成场景图 |

### 关键设计决策

- **不显示空占位**: 无 interior_url 时真不渲染 interior 图片槽位 (hasInterior/hasExterior flag), 消除视觉空洞
- **无额外标签 (两者都有)**: 正常双图不加额外解释
- **informative 标签 (单图)**: 灰色小字 "(室内场景，无室外画面)" 帮用户理解 by-design 智能, 不是缺失
- **重生按钮适配**: 只显示真实存在的 ref_type 按钮; "重生全部" 在单图场景下改为 "重生此场景"
- **编辑模式适配**: "应用并重生全部" 只在 hasBoth 时显示; 单图时 "仅重生内景/外景" 改为 "应用并重生"
- **内景/外景 badge 适配**: 双图时显示内景/外景 badge 区分; 单图时无需 badge (唯一一图)
- **响应式**: 移动端 (sm 以下) 单列全宽, 桌面端 hasBoth → grid-cols-2, 否则 grid-cols-1

### 验证

- ✅ `npm run build` 20 routes 0 errors (Warnings 全 pre-existing, 0 来自 StageC.tsx)
- ✅ 0 越权 (仅改 StageC.tsx)
- ✅ 0 改 backend / STATUS_API_CONTRACT / .team-brain 维护文档
- ✅ 60s 倒计时 + 编辑描述 + cache-buster URL + Hydrate + 2s poll 全不动 (D 条款)

## 最新完成: T21-NEW-7 Wave II Frontend — 场景视觉确认页面 (2026-05-21)

### Founder DEC-047 决方案 D 真落地

镜像 characters 页面对偶设计 — 场景参考图真预览 + 编辑 + 重生 + 60s 倒计时.

**与 ScenePreview 严格区分**:
- ScenePreview (R4-2 scene-preview): 文字层面情节确认, hydrate `/story.scenes` (Stage 3 数据)
- **SceneRefsPreview (R4-3 scene-refs-preview)**: 视觉层面真场景参考图确认, hydrate `/scene-references` (Stage 4.5 数据)

### 6 文件改 (0 越权)

| 文件 | 改动 | 行数 |
|------|------|------|
| `frontend/src/types/create.ts` | `GenerationSubPhase` 加 `scene-refs-preview` | +6 / -1 |
| `frontend/src/lib/createUrl.ts` | `UI_PHASE_TO_URL` 加 `scene_references_review: "scenes"` + `deriveUrlStageFromState` 加 `scene-refs-preview → scenes` + 注释更新 9 状态机 | +15 / -3 |
| `frontend/src/hooks/useETA.ts` | `STAGE_BUDGET_SECONDS` 加 `scene_image_preparation=180` + `scene_references_ready=0` + `REVIEW_STAGES` 加 `scene_references_ready` | +10 / -1 |
| `frontend/src/app/create/CreateContent.tsx` | `ChapterStatusResp.ui_phase` 类型加 `scene_references_review` + 加 2 新字段 (`scene_references_ready/confirmed`) + Watcher `phaseToSubPhase` 加新映射 + 加 race guard (`scene_references_confirmed=true → override 为 shot-gen`) + 加 `isSceneRefsReview` force-route 分支 (镜像 isCharReview/isSceneReview) | +50 / -3 |
| `frontend/src/components/create/StageC.tsx` | 加 `SceneRefsPreview` 组件 (~370 行) + render switch 加 `subPhase === "scene-refs-preview"` 分支 + D.23 checkpoint watcher 加 scene-refs-preview + STAGE_LABEL/STAGE_SUBTITLE 加 `scene_image_preparation` + `scene_references_ready` 文案 | +405 / -2 |
| `frontend/src/hooks/useETA.test.ts` | 加 5 新 T21-NEW-7 测试 (6a-6e) + 头部 banner 更新 | +170 / -8 |

### SceneRefsPreview 组件核心特性 (370 行)

| 模块 | 实现 |
|------|------|
| **Hydrate** | useEffect 调 `GET /api/projects/{uuid}/chapters/1/scene-references` (silentStatuses 404) + 2s poll 直到 scene_references_ready=true |
| **卡片渲染** | 每 location 一张卡, header 显示 location_zh + atmosphere/time_of_day/lighting_condition meta, 主体 sm:grid-cols-2 同时显示 interior + exterior 2 张图 (aspect-[3/4]) |
| **图像 cache-buster** | `toAbsoluteUrl(ref.interior_url)` — backend 真返带 ?v={epoch} URL, 浏览器自动 bust cache 加载新图 |
| **图像错误** | img.onError → setImgErrors → 显示 ImageOff + "图片加载失败" placeholder (镜像 CharacterPreview B26 模式) |
| **编辑模式** | 点 "编辑描述" → textarea + 4 重生按钮 (应用并重生全部 / 仅重生内景 / 仅重生外景 / 取消) |
| **重生 3 按钮** | "重生内景" (ref_type=interior) / "重生外景" (ref_type=exterior) / "重生全部" (ref_type=both) — 调 POST regenerate-reference body=`{ref_type, user_edit?}` |
| **重生中** | 显示 Loader2 + "重新生成中..." (单 location + ref_type 维度 isRegenerating guard) |
| **重生完成** | setSceneRefs 用 cache-buster URL 替换 + setImgErrors 清旧错误标记 + toast 提示 |
| **60s 倒计时** | useState(60) + setInterval(只做纯 setCountdown) + 独立 useEffect [countdown==0] 触发 confirm (镜像 CharacterPreview T20-15 anti-pattern fix) |
| **paused 状态** | 编辑或重生时 setPaused(true) 停倒计时; 显示 "继续倒计时" 按钮让用户重置 60s 窗口 |
| **D.14 isLocked** | useStageLock() — 用户已过 R4-3 后锁定卡片 (与 CharacterPreview / ScenePreview 一致) |
| **确认 CTA** | 立即 router.replace(/generating) + 后台调 POST confirm-scene-references (镜像 handleConfirmCharacters R6-3 模式) + 防 double-confirm |

### 状态机集成 (Ben 5/13 backend authoritative)

- frontend 严格不算 ui_phase (从 backend status response 真读)
- createUrl + subPhase + hydrate 全从 ui_phase + hydrate_hints 派生
- Watcher 加 isSceneRefsReview 分支 (与 isCharReview / isSceneReview 对偶) — 强制 push /scenes + setSubPhase=scene-refs-preview
- 加 race guard: 本地确认时 backend 200-500ms 延迟返 scene_references_review, 用 status.scene_references_confirmed 直读判断真状态

### 验证

- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` 0 新增 warning (所有 warning pre-existing)
- ✅ `npm run build` 20 routes 0 errors
- ✅ `npx ts-node useETA.test.ts` 14/14 PASS (含 5 新 T21-NEW-7 测试)
- ✅ 0 越权 (仅改 frontend/src/{types,lib,hooks,app/create,components/create})
- ✅ 0 修改 .team-brain/* (paste 给 PM 代写)

### 等待 PM 审查 + Founder e2e 实测

| 验证项 | 期望 |
|------|------|
| Stage 4.5 跑中 | ui_phase=storyboard_running → URL /generating + 显示 "正在准备场景视觉" + ETA |
| Stage 4.5 完成 R4-3 | ui_phase=scene_references_review → URL /scenes + SceneRefsPreview 卡片 + 60s 倒计时 |
| GET /scene-references | hydrate 真 scene_references list |
| 编辑 + 重生 | textarea 改描述 → 调 POST regenerate-reference 真生新图 + cache-buster URL |
| 60s 自动确认 | 倒计时到 0 → 自动调 POST confirm-scene-references |
| 手动确认 | "确认场景, 继续生成画面" 按钮 → 立即跳 /generating |
| Stage 5 真启动 | confirm 后 backend ui_phase → shot_generating, frontend /generating 显进度 |

### 风险 / 注意

- **subPhase 数学**: scene-preview 与 scene-refs-preview 共享 URL `/scenes` 段. StageC 内部用 subPhase 区分组件. 如果 URL 状态 race 导致 subPhase=scene-preview 但实际应 scene-refs-preview, Watcher 5s tick 会派生纠正 (但用户可能短暂见错组件)
- **Watcher race guard**: 已加 `status.scene_references_confirmed === true → subPhase=shot-gen` 防 backend ~200ms 延迟反复触发 scene-refs-preview
- **重生中 paused 不自动 resume**: 用户重生完后必须手动点 "继续倒计时" 才恢复, 避免重生中倒计时跑完误触发确认
- **DEC-014/DEC-009 backend 保留**: regenerate 时 backend 真用 interior 作 exterior 参考 (frontend 透明)
- **scene-refs-preview hydrate 用 chapter_number=1**: 当前只支持单章故事 (与其他组件一致), 多章节后续扩展

---



## 最新完成: T20-44 Frontend ETA Fix (2026-05-20)

### 3 文件修复

| 文件 | 改动 |
|------|------|
| `frontend/src/hooks/useETA.ts` | T20-44: isBackendAuthoritative flag, P1 active 时 bypass 单调性 guard + smoothing |
| `frontend/src/components/create/StageC.tsx` | text-gen poller >= 0 修复 + type fix; shot-gen poller BGM log guard |
| `frontend/src/hooks/useETA.test.ts` | test 4 → T20-44 新行为验证 (9/9 PASS) |

### 核心逻辑

```
backend ETA 790s → isBackendAuthoritative=true
                 → bypass smoothing/monotonicity
                 → rawSec=790s → "预计还需约 14 分钟" ✅

旧 bug:
backend ETA 790s → prevEta=180s → upward clamp → 178.5s → "约 3 分钟" ❌ (4x 低估)
```

### 验证

- ✅ tsc 0 errors
- ✅ lint 0 新增 warning
- ✅ npm run build 0 errors
- ✅ ts-node useETA.test.ts 9/9 PASS
- ✅ dev server HTTP 200

---

---

## 最新完成: Wave 4 — TASK-T20-FIXBATCH-5 (2026-05-19)

### 3 P2 任务全部完成

| # | RISK | 范围 | 状态 |
|---|------|------|------|
| 1 | T20-24 | progress bar 真接 backend `progress` 字段 (Stage 2 早期 0% 卡住) | ✅ 完成 |
| 2 | T20-25 | confirm-characters 后跳错 (/characters → /scenes 加载 20s → /generating) | ✅ 完成 |
| 3 | T20-11.v2 | /outline 页面 polling 优化 (76 个 404 routine warn) | ✅ 完成 |

### 改动文件 (3 文件, 0 越权)

| 文件 | 改动 | 行数变化 |
|------|------|---------|
| `frontend/src/components/create/StageC.tsx` | T20-24 text-gen + shot-gen poller 立即 fire 第一次 poll (named function); T20-24 加 silentStatuses=[404]; T20-25 handleConfirmCharacters 改 push /generating (不 push /scenes); D.23 watcher 加 silentStatuses=[404] | +30 / -5 |
| `frontend/src/app/create/CreateContent.tsx` | T20-25 Watcher subPhase 派生加 charactersConfirmedNow gate (避免 stale char_review override); T20-25 Watcher isCharReview 加 !charactersConfirmedNow gate; T20-11.v2 Watcher status poll 加 silentStatuses=[404]; T20-11.v2 hydrate status + bgm 加 silentStatuses=[404] | +20 / -5 |
| `frontend/src/lib/api.ts` | T20-11.v2 fetchBgmInfo 加 ApiFetchOptions 参数支持 silentStatuses 透传 | +5 / -2 |

### T20-24 真根因 (深挖追到根)

- **声称**: 实际源是 `state.generationProgress` (CreateContext init=0)
- **公式**: StageC text-gen poller L570 `effectiveProgress = status.progress > 0 ? status.progress : simulatedProgressRef.current`
- **Bug**: `setInterval(async () => {...}, 2000)` 第一次 fire 在 2000ms 后, 这 2s 用户看 0%
- **Founder 实证**: test19 Stage 2 早期 backend progress=5% 但 frontend 显 0% 卡住
- **修复**: 把 poll body 抽成 named function (`runTextGenPoll` / `runShotGenPoll`), call once immediately + setInterval, 第一次 poll ~200ms 内完成
- **同步加 silentStatuses=[404]**: 防止 /generating 早期 chapter 还没 ready 的 404 warn

### T20-25 真根因 (深挖追到根)

- **现象**: confirm-characters 后跳 /characters → /scenes (加载 20s) → /generating
- **真根因 chain**:
  1. `handleConfirmCharacters` (StageC L892-900) 立即 dispatch SET_GENERATION_SUB_PHASE=scene-preview + push `/scenes` URL
  2. 但 confirm-characters API 是 await **after** onConfirm() (handleConfirmWithApi L1376-1389)
  3. backend 还在 `ui_phase=char_review` (或 200-500ms 后 → `scene_review_pending`)
  4. Watcher 5s tick 见 `scene_review_pending` → 派生 subPhase=text-gen → state→URL push `/generating`
  5. Stage 3 done (~90s) → ui_phase=scene_review → Watcher 派生 subPhase=scene-preview → URL push `/scenes`
  6. 净结果: /characters → /scenes (race) → /generating (watcher Stage3 期间) → /scenes (Stage3 done)
- **修复 (Wave 9 contract 对齐)**:
  - `handleConfirmCharacters` 改 push `/generating` (符合 contract: `scene_review_pending` → /generating)
  - subPhase 设 `text-gen` (不 `scene-preview`), 显进度条让用户看到 Stage 3 真进度
  - Watcher subPhase 派生加 `charactersConfirmedNow` gate: 当本地已确认, 不被 stale `ui_phase=char_review` 拉回 char-preview
  - Watcher `isCharReview` URL force 加 `!charactersConfirmedNow` gate: 同上, Wave 9 path 与 legacy path 对齐
  - 同步加 `scenesConfirmedNow` gate 在 scene-preview override (防类似问题)
- **新流程**: /characters → /generating (progress 涨从 ~10% → ~32%) → /scenes (Stage 3 done) → 用户确认 → /generating → 完成
- **不再有**: 跳 3 次, 加载假等待

### T20-11.v2 修复

- **主犯诊断**: CreateContent Watcher (L1277+) 每 5s `/chapters/1/status` 无 silentStatuses
- **从犯**: hydrate `/chapters/1/status` 和 `fetchBgmInfo` 都无 silentStatuses
- **数学**: /outline 4 min 停留 × 12 tick/min ≈ 48 warn (与 audit 76 数量吻合; 加 hydrate ~3 warn + StageC 偶发)
- **修复**:
  - Watcher status poll → silentStatuses=[404]
  - Hydrate status poll → silentStatuses=[404]
  - fetchBgmInfo 加 options 参数 + hydrate 调用传 silentStatuses=[404]
  - D.23 watcher (StageC L431) status poll → silentStatuses=[404] (防御性)
- **效果**: /outline 4 min 停留预期 0 warn (合规 4xx 完全静默)

### 验证

- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` 0 新增 error/warning (所有 warning 均为 pre-existing img / BgmPlayer useCallback)
- ✅ dev server /create + / + /dashboard HTTP 200
- ✅ 0 越权 (仅改 StageC.tsx + CreateContent.tsx + api.ts)
- ✅ 不动 useETA.ts (Wave 1+2 修复保护)
- ✅ Wave 2 滑动窗口 + Wave 1 anti-pattern 修复 + T20-12 60s 倒计时 不退化

### 待 Founder 实测验证

| RISK | 验证场景 |
|------|----------|
| T20-24 | 跑 Pipeline, 进 /generating 立即观察 progress bar 是否真接 backend 的 5-10% (不卡 0%) |
| T20-25 | 走 confirm-characters → 不再有 /scenes 假加载, 应直接 /generating 显进度 → 最后跳 /scenes 显完整场景 |
| T20-11.v2 | 进 /outline 停留 5 min, client.log 应几乎无 chapters/* 404 warn (旧 ~48-76 → 新 ~0-3) |

### 风险/注意事项

- **T20-25 行为变更**: 用户从看到"假 ScenePreview loading"变成看到"progress bar + ETA + 文案'正在编写分场剧本'". 更诚实的 UX, 也符合 Wave 9 contract
- **Watcher gate 调整**: char_review 强制 /characters 现在要求 `!charactersConfirmedNow`. 与 legacy 行为对齐, 防止 stale backend ui_phase 覆盖本地操作
- **silentStatuses 透传**: fetchBgmInfo 加 optional options 参数, 默认行为 (无 silentStatuses) 不变, 向后兼容
- **dev server PID 14043** 仍在运行 (Founder 早上启动的), 改动通过 Next.js fast refresh 自动加载, 无需重启

---

## 最新完成: Wave 18 — TASK-T20-9.v3 ETA Frontend (2026-05-19)

### 模型 + 范围
- 模型: Sonnet 4.6
- 范围: 2 文件 — `useETA.ts` (主战场) + `StageC.tsx` (poller + useETA call)

### 改动文件 (2, 0 越权)

| 文件 | 改动概要 |
|------|---------|
| `frontend/src/hooks/useETA.ts` | 新增 shots_total/completed/failed 输入字段; 实现 frontend fallback 公式; 删除 isReallyWrappingUp + "正在收尾" UX; progress>=95% 仍显具体 ETA; 滑动窗口 per_shot_real; 保留 estimatedRemainingSeconds 优先权 |
| `frontend/src/components/create/StageC.tsx` | shot-gen poller type 加 3 字段; 新增 3 个 ref (shotsTotalRef/ShotsCompletedRef/ShotsFailedRef); useETA call 透传新字段; 替换 message regex 为 shots_completed 合成日志; RF-4 接受 >=0 (旧仅 >0) |

### T20-9.v3 具体改动

#### useETA.ts
1. **删除 message regex**: 不再在 useETA 内解析 "已生成 X/Y" (从未存在于 useETA; 改动在 StageC)
2. **新增接口字段**: `shotsTotal`, `shotsCompleted`, `shotsFailed` (STATUS_API_CONTRACT v1.1)
3. **Priority chain (Wave 18)**:
   - P1: `estimatedRemainingSeconds` (backend authoritative, >=0)
   - P2: `(shots_total - shots_completed) * per_shot_real / MAX_CONCURRENT` (T20-9.v3 fallback)
   - P3: `backendEtaSec` (legacy, >0)
   - P4: `STAGE_BUDGET_SECONDS` (hardcoded last resort)
4. **滑动窗口**: SHOT_TIMING_WINDOW=5, per_shot_real = 窗口内单 shot 实测均值 (floor 20s, cap 600s, fallback 80s)
5. **删除 isReallyWrappingUp + WRAPPING_UP_PROGRESS_THRESHOLD**: "正在收尾" 已移除
6. **Terminal UX**: progress>=95% 显示具体 ETA; rawSec<=0 才显 "即将完成"; stage=completed/progress>=100 返 null

#### StageC.tsx
1. **shot-gen poller type**: 加 `shots_total`, `shots_completed`, `shots_failed` (均为 `number | null`)
2. **3 个新 ref**: `backendShotsTotalRef`, `backendShotsCompletedRef`, `backendShotsFailedRef`
3. **useETA call**: 透传 `shotsTotal`, `shotsCompleted`, `shotsFailed`
4. **日志合成**: message regex 替换为 shots_completed 直接比较 (无字符串解析)
5. **RF-4**: `estimated_remaining_seconds >= 0` (旧 `> 0`, 允许 0 = "almost done")

### 验证
- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` 0 新增 error/warning (所有 warning 均为 pre-existing <img> 等)
- ✅ dev server 响应 HTTP 200
- ✅ 0 越权 (仅改 useETA.ts + StageC.tsx shot-gen 区域)
- ✅ Wave 1 修复不退化: T20-15 ScenePreview anti-pattern / T20-12 60s 倒计时 / T20-11 hydrate guard 均未触及

### 等待验证 (需 Founder 跑 Pipeline)
- ETA 误差 < ±20% vs 实际剩余时间
- 不再 "即将完成" → "没有 ETA" 错乱
- stage 切换 ETA 自然过渡

---

## 前一完成: Wave 17.5 — TASK-T20-FIXBATCH-4 T20-12 重做 (2026-05-19)

### 模型 + 范围
- 模型: Sonnet 4.6
- 范围: 1 文件 1 任务 — T20-12 重做 (20s 删除 → 60s 恢复, anti-pattern 修复模式)

### 改动文件 (1, 0 越权)
| 文件 | 改动概要 |
|------|---------|
| `frontend/src/components/create/StageC.tsx` | T20-12: CharacterPreview 恢复 60s 倒计时 (Founder 5/19 16:55 方案 A 决策); 使用 T20-15 anti-pattern 修复模式 (setInterval 内只做纯 state update, 副作用在独立 useEffect); 恢复 paused state + handleAdjust setPaused(true); 恢复倒计时徽章 UI (与 ScenePreview 一致) |

### 背景
Wave 1 (前一 session) 执行了方案 C (完全删除倒计时). 但 Founder 16:55 决策是方案 A (升级 20s → 60s, 与 /scenes B58 一致). PM 17:30 发现 agent 漏看 TaskUpdate, 指派重做.

### 具体改动 (StageC.tsx CharacterPreview, L1279-1515)

| 段 | 改动内容 |
|---|---------|
| L1279-1284 | 新增 `countdown` (60) + `paused` state (替换旧的"REMOVED"注释) |
| L1334-1339 | timerRef + clearTimer 清理 (移除"no-op"注释) |
| L1368-1408 | 恢复 hasCharacters reset effect + 定时器 useEffect (B36/D.14/paused gates) + 独立 countdown===0 副作用 useEffect |
| L1410-1414 | handleAdjust 恢复 setPaused(true) |
| L1506-1515 | 倒计时徽章 UI (圆形边框 + countdown 数字 + "秒后自动继续") |

### 验证
- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` 0 新增 warning (所有 warning 均为 pre-existing)
- ✅ dev server /create HTTP 200
- ✅ 0 越权 (仅改 StageC.tsx CharacterPreview 区域)

### Anti-pattern 修复模式 (RISK-T20-15)
同 ScenePreview 模式:
- `setInterval(() => setCountdown(prev => prev<=1 ? 0 : prev-1))` — 纯 state
- 独立 `useEffect(() => { if (countdown===0 && !confirmedRef.current) handleConfirmWithApi(); }, [countdown, handleConfirmWithApi])` — 副作用

### 验收对照
1. ✅ CharacterPreview 有 60s 倒计时
2. ✅ 倒计时 UI badge 显示
3. ✅ countdown===0 时触发 handleConfirmWithApi (confirm-characters API)
4. ✅ B36 gate 保护 (无 characters 不启 timer)
5. ✅ D.14 locked 清除 timer + 不显示 badge
6. ✅ 用户点"调整"时暂停 (paused=true, badge 隐藏)
7. ✅ anti-pattern 修复模式正确
8. ✅ tsc 0 errors
9. ✅ lint 0 新增 warning
10. ⏳ DevTools console anti-pattern warning 0 — 待 Founder e2e 实测
11. ⏳ /characters 实测 60s badge 倒计时显示 — 待 Founder e2e

---

## 历史归档: Wave 17 — TASK-T20-FIXBATCH-4 Wave 1 (2026-05-19)

### 模型 + 范围
- 模型: Opus 4.7 default
- 范围: 4 任务 1 session 串行 — T20-12 P0 → T20-15 P1 → T20-11 P2 → DEC-044 UI 文案

### 改动文件 (3, 0 越权)
| 文件 | 改动概要 |
|------|---------|
| `frontend/src/components/create/StageC.tsx` | T20-12: CharacterPreview 移除 20s 倒计时 useEffect + countdown state + paused state + JSX 倒计时徽章; T20-15: ScenePreview 的 setCountdown 更新器内不再调 onConfirm, 改用单独 useEffect 监听 countdown===0 触发 |
| `frontend/src/app/create/CreateContent.tsx` | T20-11: hydrate effect 加 in-session 跳过 guard (`state.projectId === urlProjectUuid && state.outline !== null` → skip + 设 hydratedFor/lastPushedUrlRef) |
| `frontend/src/components/create/StageD.tsx` | DEC-044: "旁白（只读）" → "描述（只读）" (含设计意图注释) |

### RISK-T20-12 P0 真根因

**症状**: Founder 14:45 反馈"怎么都没看到角色 一下子又到了 /scenes 加载中"

**排查路径** (5 维度):
1. **WatcherRouting** (CreateContent.tsx L1348-1366): 触发条件 `status.ui_phase === "char_review"` 或 `status.stage === "character_ready" && !charactersConfirmed` → router.replace(/characters) — **正确, 没问题**
2. **CharacterPreview useEffect 倒计时** (StageC.tsx L1373-1390 旧版): `setInterval(() => setCountdown(prev => { if (prev <= 1) handleConfirmWithApi() ... }))` — **真根因**:
   - 20s 倒计时自动触发 `handleConfirmWithApi()` → 调 `onConfirm()` → 调 `handleConfirmCharacters` → dispatch `CONFIRM_CHARACTERS` + push /scenes
   - 在 anthropomorphic_animal 故事中, characters 数据从 status poll 到 portrait 全就绪要 1-2s, 倒计时已经在跑 → 用户从 /generating 跳到 /characters 后, **20s 内不点就被自动 confirm 跳走**
3. **handleConfirmWithApi** (StageC L1342-1366): API 调用 + onConfirm + 路由切换 — 正确
4. **dispatch 链路** (handleConfirmCharacters L869-877): 正确接通
5. **DEC-011 用户旅程**: 明确 Stage B 应"预览/调整角色", Founder C 项理想形态也强调 — 自动确认违反设计意图

**修复决策**: 完全移除自动倒计时, 用户**必须**手动点击"确认角色，继续"按钮才能进 /scenes
- 不采用"30s 倒计时 + 暂停"方案 — DEC-011 强调用户掌控感, 任何倒计时都隐含催促, 干扰决策
- 保留 ScenePreview 60s 倒计时 (按任务描述"保留 /scenes 端的'修改/完成'交互不变")
- 副作用: 同步根治 RISK-T20-15 (见下)

### RISK-T20-15 P1 真根因

**症状**: client.log L1533 "Warning: Cannot update a component (CreateProvider) while rendering a different component (CharacterPreview)"

**真根因** (不是 setState 在 render 期间直接调用, 而是 React 反模式):
- CharacterPreview L1383-1388 (旧版): `setInterval(() => setCountdown((prev) => { if (prev <= 1) { handleConfirmWithApi(); return 0; } return prev - 1; }))`
- **React 在 reconciliation 期间会调用 setState 的 updater function 来计算下一个 state**
- 在 updater 内调用 `handleConfirmWithApi()` — 该函数会 dispatch (CreateProvider 的 setState) — 触发警告
- ScenePreview L1645-1648 同样有此反模式 (setCountdown 内调 onConfirm(scenes))

**修复**:
1. CharacterPreview: 直接删除整个 setInterval (T20-12 一并解决)
2. ScenePreview: 拆分关注点
   - `setInterval(() => setCountdown(prev => prev <= 1 ? 0 : prev - 1))` — 纯 state 更新
   - 新增独立 useEffect: `if (countdown === 0 && hasScenes && !paused && !confirmedRefScene.current) { confirmedRefScene.current = true; onConfirm(scenes); }` — 副作用隔离

**为什么真根本**: React 的官方反模式. setState updater 必须是 pure 函数 (无副作用). 任何 dispatch / fetch / 路由切换都应在 useEffect 或 event handler 中

### RISK-T20-11 P2 真根因

**症状**: Founder 14:43 反馈"大纲直接在 /create 出来了 停留 /create 地址, 10s 内跳到 /outline 显示载入中, 过了 30s 又出来"

**真根因** (5 维度):
1. **StageA generate-outline 流程** (CreateContent L143-191):
   - POST /projects/ + POST /projects/{id}/generate-outline → dispatch SET_OUTLINE + SET_STAGE confirm → `router.replace(/create/${id}/outline)`
2. **CreateContent re-render** with new urlProjectUuid:
   - hydrate effect (L1064) 跑
   - 现有 guard: `hydratedFor.current === urlProjectUuid && state.projectId === urlProjectUuid` — **失败 because hydratedFor 未被 StageA 设置**
   - 现有 guard: `isOurOwnPush = lastPushedUrlRef.current === currentUrl` — **失败 because lastPushedUrlRef 未被 StageA 设置**
3. **hydrateProjectFromBackend** 跑 — 30s+ 的 /chapters/1/story 404 retry loop
4. **L1126 fallback**: `if (outline === null) → 再调 generate-outline` — 第二次 API 调用
5. **结果**: 用户体验"载入中"30s+, 实则数据早就在 state 里了

**修复**: 加新 guard `if (state.projectId === urlProjectUuid && state.outline !== null) → skip + mark hydratedFor`
- StageA dispatch SET_OUTLINE 后 outline 已在 state, projectId 已设, 再 hydrate 是冗余
- 任何场景下用户在 in-session 流转后 outline 已在 memory, 后端 echo 不会更新鲜

### DEC-044 UI 文案改

**改动**: StageD.tsx L446 "旁白（只读）" → "描述（只读）" + 加 DEC-044 设计意图注释
- 内容源 (currentShot.narrationSegment) 不变
- T20-21 重构后 AI-ML 会让 narration_segment 变短作为画面描述/caption 使用
- 用户可通过"调整画面"按钮触发画面级编辑 (已有功能, 不需新建)

### 验证
- ✅ `npx tsc --noEmit` 0 errors
- ✅ `npx next lint` — 我加的代码 0 warning (现有 useEffect deps warning 已加 eslint-disable + 完整理由注释)
- ✅ dev server HMR ✓ Compiled 1688 modules
- ✅ /create /characters /preview /outline 4 URL HTTP 200
- ✅ 0 越权 (仅改 frontend/src/ 范围内 3 文件)

### Universal 视角
- T20-12: 任何 character_type / 任何故事都受益 (CharacterPreview 是通用组件)
- T20-15: 通用 React 反模式修复, 任何用户路径都受益
- T20-11: in-session create flow 通用 guard, 不限故事类型
- DEC-044: 通用 UI 文案

### 边界保护
- ❌ 不碰 useETA.ts (Wave 16 已交付)
- ❌ 不碰 backend (T20-13/T20-14/T20-19 由 Backend 处理)
- ❌ 不碰 AI-ML 文件 (T20-21 由 AI-ML 处理)
- ❌ 不碰 /preview 的核心数据展示逻辑 (只改文案)
- ❌ 不动 ScenePreview 自动确认逻辑 (按任务要求"保留 /scenes 端的'修改/完成'交互不变")

### 给 PM
- 4 项 1 session 串行完成
- 真根因均地毯式追完整调用链路 (无"拿字符串反推数据源"的偷懒)
- T20-12 + T20-15 一石二鸟 (移除 setInterval 同时根治 setState-in-render anti-pattern)
- T20-11 加最小 guard, 不破坏 hydrate effect 的现有 9 路触发条件
- DEC-044 仅文案改, 不动 narration_segment 数据源

### 给 @backend
- 0 影响 — frontend 改动不涉及 API 契约

### 给 @ai-ml (T20-21 owner)
- StageD 仍读 `currentShot.narrationSegment` 字段, 你重构 narration_segment 变短不影响显示
- 如果你新增其他字段 (e.g. `caption` / `description`) 想替代 narration_segment, 告知 frontend 改读字段名

### 给 @tester
建议 e2e 验证点:
1. 进 /characters: 倒计时徽章不再显示, 替换为"确认后开始绘制场景"文案. 等 30s+ 不自动跳 /scenes. 必须点击"确认角色，继续"按钮才进 /scenes.
2. DevTools console: 进 /characters 应**无** "Cannot update a component (CreateProvider) while rendering a different component (CharacterPreview)" 警告
3. /create 提交 idea 等大纲生成完 → router.replace 进 /outline → **不再有** 30s 二次载入 (应秒到 outline 内容)
4. /preview 右侧画面文字区域显示"描述（只读）" (不再是"旁白（只读）")
5. ScenePreview 60s 倒计时仍正常工作 (B58 + Founder 决策保留)

---

## 上一个最新完成: Wave 16 — RISK-T20-9 P0 useETA backend authoritative (2026-05-18)

**模型**: Sonnet 4.6
**改动文件 (3)**:
- `frontend/src/hooks/useETA.ts` — 新增 estimatedRemainingSeconds 字段 + 优先级反转
- `frontend/src/components/create/StageC.tsx` — useETA 调用传 estimatedRemainingSeconds
- `frontend/src/hooks/useETA.test.ts` — 追加 5 个 T20-9 单测

### 改动内容

**RISK-T20-9 (P0) — useETA backend authoritative priority**

**根因**: `STAGE_BUDGET_SECONDS[image_generation] = 1440` (hardcoded worst-case 29 shots).
19 shots 的故事实际只需 ~380s，但 fallback 用 1440s → ETA 偏快 ~100%。

**修复**:

1. **`UseETAInput` 接口新增字段** (`useETA.ts`):
   ```typescript
   estimatedRemainingSeconds?: number | null;  // RISK-T20-9: top priority, accepts >= 0
   backendEtaSec?: number | null | undefined;   // legacy, deprecated, > 0 only
   ```

2. **优先级反转** (useETA.ts priority chain):
   ```
   旧: backendEtaSec (> 0) → STAGE_BUDGET fallback
   新: estimatedRemainingSeconds (>= 0) → backendEtaSec (> 0, legacy) → STAGE_BUDGET fallback
   ```
   关键差异: `estimatedRemainingSeconds` 接受 `>= 0`（包含 0 = "即将完成"），
   而旧 `backendEtaSec` 用 `> 0`（零被忽略 → 误 fallback 到 1440s）

3. **StageC.tsx 调用方改动**:
   ```typescript
   // 旧:
   backendEtaSec: backendEstimatedSecondsRef.current
   // 新:
   estimatedRemainingSeconds: backendEstimatedSecondsRef.current,  // top priority
   backendEtaSec: backendEstimatedSecondsRef.current,              // legacy fallback
   ```
   两者当前读同一 ref，等 Backend #1 确认字段名后视情况调整。

4. **STAGE_BUDGET_SECONDS 保留**:
   - image_generation: 1440 仍在，但现在是第 3 优先级 (last resort)
   - 注释明确: T20-9 backend 上线后 99% 走 estimatedRemainingSeconds，不会到这

5. **单元测试 (+5)**:
   - test 1: estimatedRemainingSeconds 优先于 backendEtaSec
   - test 2: estimatedRemainingSeconds=null 时 fallback 到 backendEtaSec
   - test 3: estimatedRemainingSeconds=0 被接受 (>= 0)，backendEtaSec=0 被忽略 (> 0)
   - test 4: 滑动窗口平滑仍适用于新字段
   - test 5: 后端平滑倒计时无抖动

### 等待 Backend #1 协调

Backend #1 正在加 `estimated_remaining_seconds` 动态计算字段到 status response。
字段名暂定 `estimated_remaining_seconds` (与现有 status response 字段名一致)。

当前 `backendEstimatedSecondsRef` 已经读 `status.estimated_remaining_seconds`，
前端传给 `estimatedRemainingSeconds` 后，一旦 Backend #1 的动态算法上线，
ETA 将使用 `actual_shot_count × 60 / max_concurrent` 替代 hardcoded 1440s。

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `UseETAInput` 新增 `estimatedRemainingSeconds?: number \| null` | ✅ |
| 2 | 优先级: estimatedRemainingSeconds >= 0 → backendEtaSec > 0 → fallback | ✅ |
| 3 | T20-2 3 sub-bug 修复保留 (平滑/不消失/真收尾) | ✅ |
| 4 | StageC.tsx useETA 调用传 estimatedRemainingSeconds | ✅ |
| 5 | STAGE_BUDGET_SECONDS 保留 (last resort fallback) | ✅ |
| 6 | useETA.test.ts 追加 5 个 T20-9 单测 | ✅ |
| 7 | npm build 0 errors / 20 routes | ✅ |
| 8 | npx tsc --noEmit 0 errors | ✅ |
| 9 | 0 越权 (只改 useETA.ts + StageC.tsx useETA 调用行 + useETA.test.ts) | ✅ |

### Universal 验证

- 5 shots 故事: backend estimatedRemainingSeconds = 100s → 正确显示 ~2 min
- 19 shots 故事 (test18): backend estimatedRemainingSeconds = 380s → 正确 ~6 min (不再 1440s 误算)
- 29 shots 故事: backend estimatedRemainingSeconds = 580s → 正确 ~10 min
- backend null (pre-T20-9 部署): 走 backendEtaSec → 若 backendEtaSec 也 null → 走 STAGE_BUDGET (向后兼容)

---

## 上一个最新完成: Wave 15 — RISK-T20-2 P1 ETA UX 复合 bug 三修 [2026-05-18]

**模型**: Sonnet 4.6
**改动文件 (2)**:
- `frontend/src/hooks/useETA.ts` — 3 个 bug 修复
- `frontend/src/hooks/useETA.test.ts` — 新建单元测试 (4 test cases)

### Bug 1 — 阶段跳变 (Stage 切换硬切)

**根因**: stage 切换时 ETA 瞬间跳到新 stage budget (e.g. 12 min → 8 min 一次跳变)

**修复**:
- 新增 `prevEtaSecRef` (line 131)
- 每次 render 前检查: `delta = prevEta - rawSec`
- 若 `delta > MAX_STEP_PER_POLL (3s)` → clamp 到 `prevEta - 3s`
- 每 2s poll 最多移动 3s → 5 min 跳变需要 ~3 min 平滑收敛，用户感知平滑
- 关键: `resetForStage` 不重置 `prevEtaSecRef`，跨 stage 保留连续性

### Bug 2 — ETA 突然消失 (Monotonicity guard 副作用)

**根因**: monotonicity guard 将 ETA 驱动到 0 → `Math.ceil(0/60)=0` → `etaText=null` → ETA 消失

**修复**:
- `rawSec <= 0` → return `{ etaText: "即将完成", etaSeconds: 0 }`
- `rawSec < 60 (NEAR_ZERO_SEC)` → return `{ etaText: "还需不到 1 分钟", etaSeconds }`
- 正常路径 `rawSec >= 60` → `预计还需约 ${minutes} 分钟` (原逻辑)
- 移除了 `const etaText = minutes > 0 ? ... : null` (旧的 null 返回路径)

### Bug 3 — "正在收尾" 文案误导 (RISK-NEW-1 副作用)

**根因**: `actualElapsedSec >= 1800 (30 min)` 触发 "收尾" 文案，但 test18 11:07 时 4 shots 还没生成

**修复**:
- 删除 elapsed-time 触发逻辑 (`VERY_LONG_ELAPSED_SEC` 常量保留在接口注释中)
- 改为 pipeline 真实状态判断:
  ```
  isReallyWrappingUp = stage==="bgm" || stage==="music" ||
                       (stage==="image_generation" && progress >= 95)
  ```
- `actualElapsedSec` 字段在 `UseETAInput` 接口中保留 (backward compatible with StageC.tsx caller)，但 hook 函数签名不再解构它 (ignored)

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | Bug 1: `prevEtaSecRef` 新增 + `resetForStage` 不重置它 | ✅ |
| 2 | Bug 1: `delta > MAX_STEP_PER_POLL` → clamp (line ~232-236) | ✅ |
| 3 | Bug 2: `rawSec <= 0` → "即将完成" | ✅ |
| 4 | Bug 2: `rawSec < 60` → "还需不到 1 分钟" | ✅ |
| 5 | Bug 3: `isReallyWrappingUp` 用 stage+progress 判断 (not elapsed) | ✅ |
| 6 | Bug 3: `actualElapsedSec` 在接口保留 (backward compat，IGNORED) | ✅ |
| 7 | StageC.tsx 无需修改 (useETA 签名 + return 类型完全兼容) | ✅ |
| 8 | npm build 0 errors / 20 routes | ✅ |
| 9 | npx tsc --noEmit 0 errors | ✅ |
| 10 | useETA.test.ts 新建，4 test case 覆盖 3 bug | ✅ |
| 11 | 0 越权 (只改 useETA.ts + 新建 useETA.test.ts) | ✅ |

### Universal 验证

- 短篇 5 min 故事: stage 切换频繁但 budget 小，sliding window 步长足够快收敛
- 长篇 60 min 故事 (含 B51 fallback): elapsed 超过 30 min 不再误触 "收尾"
- BGM 阶段: 正常触发 "正在收尾" (stage=bgm 判断准确)
- image_generation 95%+: 正常触发 "正在收尾" (最后几张图)

---

## 上一个最新完成: Wave 13 — RISK-T19-3 storyboard 阶段 progress 真值显示 [2026-05-15 17:30]

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`

### 改动内容

**RISK-T19-3 (P1) — Frontend storyboard 阶段 progress 不显示 backend 真值**

**根因分析 (完整调用链路)**:

问题根因是 3 层嵌套 bug：

1. **Watcher 设计**: CreateContent.tsx watcher (5s) 看到 `ui_phase="storyboard_running"` → 映射为 `"text-gen"` (L1308) → 从 "shot-gen" 切换到 "text-gen"

2. **text-gen effect 的 START_GENERATION 守卫失效**: text-gen useEffect 用 `initialProgressRef.current`（StageC 挂载时快照，永远=0）判断是否要 dispatch START_GENERATION。但 StageC 在首次创建时挂载（进度=0），`initialProgressRef.current = 0`。当用户确认场景后进入 shot-gen，shot-gen poller 更新进度到 37%+，随后 Watcher 把 subPhase 改回 text-gen。text-gen effect 重新运行，但 `initialProgressRef.current = 0 > 0 = false` → dispatch START_GENERATION → **进度被重置为 0%**！

3. **结果**: 即使 backend 已经在 37-62%，frontend 重置为 0% 且在下一个 2s poll 才能恢复。如果 backend 进度涨得很慢（storyboard 每个 scene 需时），用户看到 0% 长达数分钟。

**修复三处**:

1. **新增 `generationProgressRef`** (L164-171):
   ```tsx
   // Live ref tracking current generationProgress — used by text-gen effect as
   // START_GENERATION guard (replacing mount-time initialProgressRef).
   const generationProgressRef = useRef(state.generationProgress);
   generationProgressRef.current = state.generationProgress;
   ```

2. **text-gen effect START_GENERATION 守卫** (L449-468):
   ```tsx
   // 改前 (mount-time snapshot, 永远=0 导致 START_GENERATION 每次误发):
   if (initialProgressRef.current > 0) { ... }

   // 改后 (live ref, 准确反映当前进度):
   if (generationProgressRef.current > 0) { ... }
   ```

3. **删除失效的 `initialProgressRef` 声明** (L324-327):
   - 替换为注释说明 "initialProgressRef 已被 generationProgressRef 取代"
   - 0 编译错误（之前 `no-unused-vars` error）

4. **副改 — subtitle 显示更精确** (L1050-1063):
   - 改前: text-gen subPhase 一律显示 "AI 正在全力创作，请耐心等待"
   - 改后: 用 `resolveSubtitle(currentStage)` 全阶段统一显示 stage-specific 文案
   - storyboard 阶段: "AI 正在创作故事，请稍候" (STAGE_SUBTITLE 有定义)
   - 0 regression: image_generation 阶段仍显示 "AI 正在逐张绘制画面，可以选择后台生成"

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `generationProgressRef` 声明 (L170-171) | ✅ |
| 2 | text-gen effect 用 `generationProgressRef.current > 0` 判断 (L463) | ✅ |
| 3 | `initialProgressRef` 声明已删除 (no `const initialProgressRef = useRef`) | ✅ |
| 4 | subtitle 用 `resolveSubtitle(currentStage)` (L1062) | ✅ |
| 5 | npm run build 0 errors / 20 routes | ✅ |
| 6 | 0 越权 (只改 StageC.tsx，0 backend / team_ben 文件) | ✅ |

### 预期效果

- storyboard 阶段 frontend progress 跟随 backend 真值 (0% → 37% → 60% → 62%)
- msg "Scene X/Y" 真显示 (text-gen poller dispatch message)
- 不再出现"0% 等 6 分钟"
- Wave 12 mini 改的 L1144 后台按钮显示条件 不影响 (该区域未动)
- Wave 12 Frontend 改的 isError UI 区域 不影响

### npm build 结果

✅ 0 errors / 20 routes / Generating static pages (20/20)
仅 pre-existing `<img>` warnings + BgmPlayer useCallback warning

### 其他阶段是否有类似问题

- **character_design / screenplay**: 这些阶段 Watcher 的 `char_review_pending` / `scene_review_pending` 映射到 "text-gen"，且从未被 shot-gen poller 写过进度，subPhase 始终是 text-gen。无此 bug。
- **image_preparation / image_generation / bgm**: 通过 `shot_generating → "shot-gen"` 映射，text-gen effect 不会重新运行。无此 bug。
- **结论**: 只有 `storyboard_running → "text-gen"` 这一路径在 shot-gen→text-gen 切换时有进度 reset 问题。已修复。

---

## 上一个最新完成: Wave 12 mini — RISK-T17-7 "后台生成"按钮触发时机扩展 [2026-05-15 16:45]

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`

### 改动内容

**RISK-T17-7 (P2 升级, Founder 5/15 16:35 澄清)**

按钮显示条件从 `state.generationSubPhase === "shot-gen"` 扩展为：

```typescript
// 改前 (RISK-T15-1 原始 fix，仅 shot-gen):
{state.generationSubPhase === "shot-gen" && !isError && (

// 改后 (RISK-T17-7 P2 升级，storyboard + shot-gen):
{((state.generationSubPhase === "shot-gen") ||
  (state.generationSubPhase === "text-gen" && currentStage === "storyboard")) &&
  !isError && (
```

**按钮显示矩阵**：

| ui_phase / stage | generationSubPhase | currentStage | 按钮显示 |
|---|---|---|---|
| storyboard_running | text-gen | storyboard | 显示 (新增) |
| image_preparation | shot-gen | image_preparation | 显示 (保留) |
| image_generation | shot-gen | image_generation | 显示 (保留) |
| bgm/music | shot-gen | bgm/music | 显示 (保留) |
| story_generation/character_design/screenplay | text-gen | 非 storyboard | 不显示 (正确) |
| completed | 任意 | completed | !isError=false → 不显示 (正确) |

**设计理由**: storyboard 阶段用户已完成角色+场景确认，不再需要守着做任何审查动作，安全允许后台生成。story_generation/character_design/screenplay 阶段用户可能仍需确认角色/场景，不宜此时离开。

**行号**: L1144-1163 (注释更新 + 条件修改)

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | L1153-1154 按钮条件真改 (shot-gen OR storyboard) | ✅ |
| 2 | RISK-T17-7 注释在 L1144-1152 | ✅ |
| 3 | npm run build 0 errors / 20 routes | ✅ |
| 4 | 只有 pre-existing warnings (img + useCallback) | ✅ |
| 5 | 0 越权 (只改 StageC.tsx L1144-1163 区域，不碰 isError UI / backend / team_ben) | ✅ |

### npm build 结果

✅ 0 errors / 20 routes / 仅 pre-existing warnings

---

## 上一个最新完成: Wave 12 — RISK-T19-2 + RISK-T17-8 配套 [2026-05-15]

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`

### 改动内容

**RISK-T19-2: Failed UI 友好化**

1. **新增 lucide 图标 import** (L5): `RefreshCw`, `ChevronDown`, `ChevronUp`, `RotateCcw`

2. **新增状态变量** (L209-220):
   - `showTechDetails: boolean` — 控制技术详情折叠
   - `restartLoading: boolean` — 原地重启调用中
   - `restartError: string | null` — 重启失败错误文案

3. **错误 console.error useEffect** (L952-960):
   - 当 `isError && generationMessage` 时记录完整技术 message 到 `console.error`
   - 保证 client.log 和 backend metric 能看到完整 Pydantic stack trace

4. **副标题简化** (L1021): 错误时不再显示 `friendlyError(state.generationMessage)` 原始文本，改为"生成遇到问题"短语，避免重复

5. **新 isError UI 块** (L1157-1220):
   - 友好描述: "故事生成过程中遇到了一些技术问题，我们已记录并会尽快修复。你可以选择："
   - 重启错误反馈: `restartError` 非 null 时显示红色小条
   - **主按钮 "原地重启（从失败步骤继续）"** + 副文案"不浪费已有进度"
   - **次按钮 "返回重试（重新创建故事）"** (保留旧行为)
   - **"查看技术详情"折叠按钮** — 展开后显示完整原始 `state.generationMessage` (font-mono, select-all)

**RISK-T17-8 配套: handleRestartFromFailedStage**

6. **新增 async handler** (L915-950):
   - `POST /api/projects/{projectId}/chapters/1/restart-from-failed-stage`
   - 成功 → `dispatch({ type: "START_GENERATION" })` + `router.replace(/generating URL)`
   - 失败 → `setRestartError(msg)`，UI 提示用户改用"返回重试"

### API Contract (待 Backend #2 确认)

```
POST /api/projects/{project_id}/chapters/1/restart-from-failed-stage
Body: {} (empty)
Response: { success: true, restarted_from_stage: 4 }
```

Backend #2 endpoint 尚未完成时，调用会得到 404/500 → `restartError` 设置 → UI 提示用户改用"返回重试"。Backend #2 完成后无需前端改任何代码，自动 work。

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | StageD failed UI 不再显示原始 Pydantic stack trace | ✅ |
| 2 | 显示友好描述 + 三个选项区域 | ✅ |
| 3 | "原地重启"主按钮显示，点击调 POST endpoint | ✅ |
| 4 | "返回重试"次按钮保留 (dispatch SET_STAGE confirm) | ✅ |
| 5 | "查看技术详情"折叠 (默认收起，展开显示完整 message) | ✅ |
| 6 | console.error 记录完整 technical message | ✅ |
| 7 | npm run build 0 errors / 20 routes | ✅ |
| 8 | 0 越权 (只改 StageC.tsx，0 backend / team_ben 文件) | ✅ |

### npm build 结果

✅ 0 errors / 20 routes / Generating static pages (20/20)

---

## 上一个最新完成: RISK-NEW-1 — useETA 消费 actual_elapsed_sec (死字段闭环) [2026-05-14 23:xx]

**模型**: Sonnet 4.6
**改动文件 (3)**:
- `frontend/src/hooks/useETA.ts`
- `frontend/src/components/create/StageC.tsx`
- `frontend/src/app/create/CreateContent.tsx`

### 改动内容

**设计选择: 用法 A (sanity check 文案增强)**

当 `actualElapsedSec >= 1800`（30 分钟）时，将 ETA 文案替换为"正在收尾，请稍候..."，
避免在长尾任务中显示"预计还需约 25 分钟"等可能已过期的数字 ETA。

1. **`useETA.ts` 接口扩展** (L74-82):
   - `UseETAInput` 新增可选字段 `actualElapsedSec?: number | null`
   - 新增模块级常量 `VERY_LONG_ELAPSED_SEC = 30 * 60`
   - hook 函数签名扩展: `useETA({ stage, progress, backendEtaSec, actualElapsedSec })`
   - 逻辑: 在"4. Convert to display string"前插入 sanity check — 若 `actualElapsedSec >= 1800` → 返回 `{ etaText: "正在收尾，请稍候...", etaSeconds }` (不是 null，不是数字 ETA)

2. **`StageC.tsx` 三处改动**:
   - `backendActualElapsedSecRef` 声明 (L183): `useRef<number | null>(null)`
   - text-gen poller 类型扩展 (L499): `actual_elapsed_sec?: number | null`
   - text-gen poller 写入 (L521-522): `backendActualElapsedSecRef.current = typeof status.actual_elapsed_sec === "number" ? status.actual_elapsed_sec : null`
   - shot-gen poller 类型扩展 (L743): `actual_elapsed_sec?: number | null`
   - shot-gen poller 写入 (L764-765): 同上
   - `useETA` 调用 (L299): 新增 `actualElapsedSec: backendActualElapsedSecRef.current`

3. **`CreateContent.tsx` 类型扩展** (L486):
   - `ChapterStatusResp` 接口新增 `actual_elapsed_sec?: number | null`

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `UseETAInput` 含 `actualElapsedSec?: number \| null` | ✅ |
| 2 | `useETA` hook 真用 `actualElapsedSec` 做 sanity check (不是 ignore) | ✅ |
| 3 | `StageC.tsx` 两个 poller 解析 `actual_elapsed_sec` + 写入 ref | ✅ |
| 4 | `StageC.tsx` useETA 调用传 `actualElapsedSec` | ✅ |
| 5 | `CreateContent.tsx ChapterStatusResp` 含 `actual_elapsed_sec` | ✅ |
| 6 | npm run build 0 errors / 20 routes | ✅ |
| 7 | 0 越权 (0 backend / team_ben / 其他 agent 文件) | ✅ |

### actual_elapsed_sec 不再是死字段的证据

```
grep -n "actual_elapsed_sec\|actualElapsedSec\|backendActualElapsed" useETA.ts StageC.tsx CreateContent.tsx
useETA.ts:74        — UseETAInput 接口字段
useETA.ts:91        — hook 函数参数解构
useETA.ts:173-180   — sanity check 消费逻辑 (条件判断 + if 分支返回)
CreateContent.tsx:486 — ChapterStatusResp 类型字段
StageC.tsx:183      — backendActualElapsedSecRef 声明
StageC.tsx:299      — useETA 调用传参
StageC.tsx:499      — text-gen poller 类型
StageC.tsx:521-522  — text-gen poller 写入 ref
StageC.tsx:743      — shot-gen poller 类型
StageC.tsx:764-765  — shot-gen poller 写入 ref
共 11 个真消费点，0 死字段
```

### npm build 结果

✅ 0 errors / 20 routes / Generating static pages (20/20)
仅 pre-existing `<img>` warnings + BgmPlayer useCallback warning

---

## 上一个最新完成: Wave 11.3 收尾 — StageC.tsx 集成 useETA hook [2026-05-14 20:xx] — Frontend #2 接力

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/components/create/StageC.tsx`

### 改动内容

1. **新增 import** (L12): `import { useETA } from "@/hooks/useETA";`

2. **删除旧 estimatedMinutes IIFE + lastEtaSecondsRef** (原 L291-338 区域):
   - 完整删除旧的 `estimatedMinutes = (() => { ... })()` IIFE (包含线性外推 + 旧 monotonicity guard + lastEtaSecondsRef 引用)
   - `lastEtaSecondsRef` 声明整体移除（不再需要，功能由 useETA hook 内置）
   - `backendEstimatedSecondsRef` 保留（poller 仍需写入此 ref，useETA hook 读取它）

3. **Wave 9 stage tracking useEffect 保留但简化** (L269-283):
   - 保留 lastStageRef 追踪 (用于 debug log)
   - 移除 `lastEtaSecondsRef.current = null` 重置（已由 useETA hook 内部 useEffect([stage]) 处理）

4. **新增 useETA hook 调用** (L285-295):
   ```tsx
   const { etaText } = useETA({
     stage: currentStage,
     progress: state.generationProgress,
     backendEtaSec: backendEstimatedSecondsRef.current,
   });
   ```

5. **ETA 显示替换** (render 区, 原 L1035-1038):
   - 旧: `estimatedMinutes !== null && <p>预计还需约 {estimatedMinutes} 分钟</p>`
   - 新: `etaText !== null && <p>{etaText}</p>` (etaText 已包含"预计还需约 X 分钟"格式)

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `import { useETA } from "@/hooks/useETA"` 真存在 (L12) | ✅ |
| 2 | `estimatedMinutes` IIFE 已完全删除 (grep 不到) | ✅ |
| 3 | `lastEtaSecondsRef` 变量已删除 (grep 不到声明) | ✅ |
| 4 | `const { etaText } = useETA({...})` 真调用 (L291) | ✅ |
| 5 | ETA 显示用 `etaText !== null` 判断 (L990) | ✅ |
| 6 | `npm run build` 0 errors / 20 routes | ✅ |
| 7 | 0 越权 (不碰 backend / team_ben / Frontend #1 改的 charPreviewFetchingRef + silentStatuses 区域) | ✅ |

### 与 Backend #3 的协调

- Backend #3 正在加 `actual_elapsed_sec` 字段到 chapters.py status response
- 当前 useETA hook 不消费 `actual_elapsed_sec`（设计上是可选增强）
- `estimated_remaining_seconds` 字段已被 `backendEstimatedSecondsRef.current` 传入 hook — Wave 11.3 backend ETA 算法修复后自动生效
- 如 Backend #3 加了 `actual_elapsed_sec`，前端**目前无需修改**，预留位置: useETA hook 的 backendEtaSec 参数即可

### npm build 结果

✅ 0 errors / 20 routes / Generating static pages (20/20)
只有 pre-existing `<img>` warnings，非本次引入

---

## 上个任务: Wave 11.2 RISK-T18-G 404 storm 修复 (2026-05-14) — Frontend #1

**模型**: Sonnet 4.6
**改动文件 (3)**:
- `frontend/src/components/create/StageC.tsx` — charPreviewFetchingRef guard (4 处)
- `frontend/src/lib/api.ts` — ApiFetchOptions interface + silentStatuses support
- `frontend/src/app/create/CreateContent.tsx` — 2 个 hydration call 加 silentStatuses

### 修复说明

**Storm 1 (StageC text-gen poller)**:
- 根因: 2s poller 在 `character_ready` 时多个 tick 都进入 shouldShowCharPreview 分支 → 并发多次 `/chapters/1/story` fetch → 多次 404 → 多次 console.warn → client-log 风暴
- 修复: 新增 `charPreviewFetchingRef = useRef(false)` guard
  - 第一次进入 shouldShowCharPreview 分支时设 `charPreviewFetchingRef.current = true`
  - 后续 tick 检测到 true → 直接 return，不发 fetch
  - dispatch 完成后 reset false（允许 re-mount 后重新触发）
  - useEffect cleanup 里也 reset false（React StrictMode double-invoke 安全）

**Storm 2 (CreateContent.tsx hydration)**:
- 根因: 每次 URL 变化 / 水合触发时，parallel fetch `/storyboard` + `/story`，在早期 pipeline 阶段必然 404 → `apiFetch` 的 L65 console.warn 在 throw 前执行 → client-log 记录
- 修复: 为 `apiFetch` 添加第 4 参数 `options?: ApiFetchOptions`（含 `silentStatuses?: number[]`）
  - 404/400 列为 silentStatuses 时，跳过 console.warn，仅 throw ApiError（caller .catch() 照常处理）
  - CreateContent.tsx 两处 hydration call 加 `{ silentStatuses: [400, 404] }`
  - StageC.tsx `/chapters/1/story` 在 char-preview fetch 处也加 `{ silentStatuses: [400, 404] }`

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `charPreviewFetchingRef` 声明 (StageC L143-147) | ✅ |
| 2 | guard check (shouldShowCharPreview 分支入口) | ✅ |
| 3 | reset after dispatch (dispatch SET_GENERATION_SUB_PHASE 之后) | ✅ |
| 4 | reset in cleanup (return () => 里) | ✅ |
| 5 | `ApiFetchOptions` interface + silentStatuses 在 api.ts | ✅ |
| 6 | CreateContent hydration `/storyboard` call 有 silentStatuses | ✅ |
| 7 | CreateContent hydration `/story` call 有 silentStatuses | ✅ |
| 8 | StageC char-preview `/story` call 有 silentStatuses | ✅ |
| 9 | `npm run build` 0 errors / 20 routes | ✅ |
| 10 | 0 越权 (不碰 backend / team_ben / 其他 agent 文件) | ✅ |

### 预期效果

- client.log 不再出现 `[ClientLog] [WARN] [API] GET ... HTTP_ERROR status=404` (story|storyboard) 风暴
- 正常 404 错误（非 silentStatuses 路径）仍会 warn — 不影响其他端点的可观测性

---

## 上个任务: Wave 11.3 RISK-T17-5 Frontend ETA hook (2026-05-14) — 独立阶段完成

**模型**: Sonnet 4.6
**改动文件 (2)**:
- `frontend/src/hooks/useETA.ts` — 新建 ETA hook (RISK-T17-5)
- `frontend/src/app/create/CreateContent.tsx` — atmosphere 类型修复 (pre-existing build error)

### useETA hook — RISK-T17-5 核心修复

**问题根因**:
- backend `estimated_remaining_seconds` 大部分时间为 null
- 现有 fallback = 线性外推（elapsed/progress），在 progress 低时跳变严重（8→9→8 min 跳变）
- `startTimeRef` 在 sub-phase 切换时 reset，导致 elapsed 变小，ETA 重新变大

**useETA hook 设计**:
```typescript
// frontend/src/hooks/useETA.ts
useETA({ stage, progress, backendEtaSec }) → { etaText, etaSeconds }
```

**三层优先级**:
1. backend `backendEtaSec > 0` → 直接用（Wave 11.3 backend 修复后大部分时间生效）
2. fallback = stage-based budget - elapsed（稳定，不跳变）
   - 基于 test18 实测校准的 per-stage 时间预算
   - image_generation 阶段: 1440s 预算（24 min 上界）
   - image_preparation: 180s, storyboard: 210s, screenplay: 240s, bgm: 60s 等
3. 如无任何数据 → null（不显示 ETA，而不是乱猜）

**Stage 切换 reset**:
- `useEffect([stage])` 监听 stage 变化 → 重置 `stageStartTimeRef`, `lastEtaSecRef`, `stageBudgetRef`
- 新 stage 第一次 status response 时用新的 budget 从头倒计时

**Monotonicity guard**:
- EPSILON = 1.5s，每 poll 周期（2s）保证至少下降 1.5s
- 只在 stage 内单调递减；stage 切换时 reset（不跨 stage 压缩）

**Review stages 不显示 ETA**:
- `character_ready`, `scenes_ready`, `completed` 不显示（用户在 review，不是等计算）

**atmosphere 类型修复**:
- `CreateContent.tsx` L1409: storyResp.scenes.atmosphere 可能是 `{ mood, sound_design_hint }` 对象
- 修复: 在 .map() 中显式 normalize atmosphere → string（object.values().join(", ")）
- 消除了 Wave 10 遗留的 pre-existing build error

### 验收清单

| # | 验证项 | 状态 |
|---|--------|------|
| 1 | `useETA.ts` 文件存在 + TS 类型完整 | ✅ |
| 2 | `npm run build` 0 errors | ✅ |
| 3 | stage 切换时 console log "RISK-T17-5: stage transition → X" | ✅ (hook 内 console.log) |
| 4 | backend `backendEtaSec > 0` 时优先用 backend 值 | ✅ |
| 5 | `backendEtaSec = null` 时用 stage budget fallback（不用线性外推） | ✅ |
| 6 | 越权 check: 0 越权 | ✅ |

### 待做（等 Frontend #1 完成后）

- [ ] 将 `useETA` 集成到 `StageC.tsx`，替换现有 `estimatedMinutes` 计算逻辑 + `backendEstimatedSecondsRef` + `lastEtaSecondsRef` 等 4 个 ref
- [ ] StageC ETA 显示从 `estimatedMinutes !== null` 改为用 `useETA().etaText !== null`

---

## 上一个完成: Wave 10 Phase 1B frontend bug fixes (2026-05-14) — test16 RISK 闭环

**模型**: Sonnet 4.6 xhigh
**改动文件 (4)**:
- `frontend/src/types/create.ts` — `PreviewScene` 接口扩展 (RISK-T16-4)
- `frontend/src/components/create/StageC.tsx` — 4 处修改 (RISK-T16-4/-9/-3)
- `frontend/src/app/create/CreateContent.tsx` — 3 处修改 (RISK-T16-4)
- `frontend/src/components/create/StageD.tsx` — 1 处修改 (RISK-T16-7)

### RISK-T16-4 (P0 CRITICAL): PreviewScene full payload + handleConfirmScenes 修复

**根因**: `handleConfirmScenes` 只 POST 4 字段（id/name/description/description_zh），strip 了 `action_beats` 等 Stage 3 LLM 字段 → Stage 4 失败 → pipeline 标记 complete 但 storyboard 空 → 前端显示空白

**修复三处**:

1. **types/create.ts** — `PreviewScene` 接口扩展 12 个可选字段 + index signature:
   ```typescript
   scene_id?, scene_heading?, plot_point?, location_id?, time_of_day?, weather?,
   lighting_condition?, atmosphere?, action_beats?: unknown[], narration?, characters_in_scene?,
   [key: string]: unknown  // 允许任意额外 LLM 字段透传
   ```

2. **StageC.tsx `handleConfirmScenes`** (~L875) — 改为 full spread:
   ```typescript
   modified_scenes: modifiedScenes
     ? modifiedScenes.map((s) => ({
         ...s,  // spread 所有 LLM 原始字段 (action_beats, narration, location_id ...)
         description: s.userEdit || s.description,
         description_zh: s.userEdit || s.description_zh || s.description,
         userEdit: undefined,  // strip 前端专用字段
       }))
     : null,
   ```

3. **CreateContent.tsx** — 两处修复:
   - `ChapterStoryResp.scenes` 类型扩展（含 action_beats 等全字段 + index signature）
   - `previewScenes` 构建优先使用 `storyData.scenes`（全 Stage 3 payload），而非 `outline.scenes`（仅 4 字段）
   - Watcher `isSceneReview` 分支新增：fetch `/chapters/1/story` → dispatch `SET_PREVIEW_SCENES` 含完整字段

### RISK-T16-7 (P1 UX): StageD failed-state UI

**根因**: `shots.length === 0` 时 `return null` 导致空白屏

**修复**: `frontend/src/components/create/StageD.tsx`
- 新增 `useRouter`, `XCircle`, `RotateCcw` imports
- 替换 `return null` 为完整错误 UI（标题/说明/重新创建故事按钮/返回工作台按钮）

### RISK-T16-9 (P1 UX): StageC 轮播提示文案纠正

**StageC.tsx L52**:
```
旧: "场景确认环节，你可以修改每个场景的氛围描述"
新: "场景已生成，请确认是否符合预期"
```

**背景**: 旧文案诱导用户点击 Edit 触发 T16-4 bug

### RISK-T16-3 (P1 UX): 网络断线区分真实 pipeline 失败

**修复**: `StageC.tsx` — 4 处改动

1. 新增状态: `const [networkOffline, setNetworkOffline] = useState(false);`

2. 新增 useEffect: 监听 `window` `online`/`offline` 事件
   - online → 重置 textGenErrorCount + shotGenErrorCount + networkOffline + showRetryHint
   - offline → 设 networkOffline=true + showRetryHint=true

3. text-gen + shot-gen catch block: 改为网络感知
   - `navigator.onLine === false` 或 `TypeError: Failed to fetch` → setNetworkOffline(true)（amber 横幅，不派发 GENERATION_ERROR）
   - 仅连续 15+ 次非网络错误才 dispatch GENERATION_ERROR（真实 server 失败）
   - 成功 poll 时 → 重置 networkOffline=false + showRetryHint=false

4. UI: 在进度条下方新增条件渲染
   - networkOffline: amber "网络连接中断，正在等待恢复...（后台生成继续进行）"
   - showRetryHint + !networkOffline: muted "网络波动中，正在重试..."

### 设计原则

**forward-only**: 所有修复均 backward compatible；老数据（无 action_beats 的 outline.scenes）仍可正常 fallback

**no npm run build**: 4 文件均为 .tsx，Next.js dev hot reload 自动生效，无需 rebuild（见 KEY_LEARNINGS #7）

### 验证清单（给 PM）

| # | 验证项 | 期望 |
|---|--------|------|
| 1 | grep `action_beats` in StageC.tsx | `...s,` spread 包含（不再 4 字段 map）✅ |
| 2 | grep `PreviewScene` in create.ts | 含 `action_beats?: unknown[]` + index sig ✅ |
| 3 | grep `T16-9` in StageC.tsx L52 area | 文案改为"场景已生成，请确认是否符合预期" ✅ |
| 4 | grep `networkOffline` in StageC.tsx | 状态 + useEffect + UI 三处存在 ✅ |
| 5 | grep `XCircle` in StageD.tsx | return null 替换为错误 UI ✅ |
| 6 | T16-4 e2e | 场景确认后 Stage 4 正常生成 shots（需 backend Phase 1A 合并修复也到位）|
| 7 | T16-7 e2e | pipeline 失败后显示错误 UI + 重新创建按钮 |
| 8 | T16-3 e2e | 断网时显示 amber 横幅，不弹红色错误页 |

### 给 @pm（paste 用）

见下方"sendmessage paste 区"

---

## 上一个完成: TASK-WAVE9-P2-FRONTEND-STATE-DERIVATION (2026-05-13 23:xx) — DEC-030 frontend 闭环

**模型**: Opus 4.7 xhigh
**改动文件 (3)**:
- `frontend/src/lib/createUrl.ts` — `reconcileBackendVsUrl` 新增 `uiPhase` 参数 + 8-state 映射表优先路径
- `frontend/src/app/create/CreateContent.tsx` — `ChapterStatusResp` 扩 6 字段 + 水合 prefer status.\*\_confirmed + watcher 5s 派生 subPhase + URL routing 改 ui_phase 优先
- `frontend/src/components/create/StageC.tsx` — `lastStageRef` + stage 切换重置 ETA guard + 两个 poller 类型升级 + char_review 派生 + completed 多源检测

### 改动详情

#### 1. createUrl.ts（顺解 ui_phase → URL 派生）

**新增**:
- 模块级 `UI_PHASE_TO_URL: Record<string, UrlStage>` 8-state 映射表（input/outline_review/char_review_pending/char_review/scene_review_pending/scene_review/storyboard_running/shot_generating/completed）
- `reconcileBackendVsUrl` 输入新增可选字段 `uiPhase?: string | null`
- 优先路径：`uiPhase` 存在 → 直接映射；特例 `uiPhase=completed && URL=delivery` 保留 delivery
- 未知 ui_phase 值 → console.warn + 落到 legacy heuristic

**保留**:
- 全部旧 heuristic（POST_CHAR_STAGES Set + character_ready / scenes / generating / outline 分支）作为 fallback
- RISK-T15-2 修复（POST_CHAR_STAGES 不含 screenplay/storyboard）依然生效

#### 2. CreateContent.tsx（水合 + Watcher Wave 9 派生）

**新增 type**:
- `HydrateHints` interface
- `ChapterStatusResp` 6 个 Wave 9 可选字段（ui_phase/hydrate_hints/characters_confirmed/scenes_confirmed/storyboard_ready/outline_ready + failed_shot_count/partial_failure）

**水合路径改造（L723-755）**:
- `charactersConfirmed` / `scenesConfirmed` 三层优先级：`status.*_confirmed`（Wave 9 status authoritative）→ `project.*_confirmed`（B49/B58 DB cache）→ `ADVANCED_STAGES` heuristic
- `reconcileBackendVsUrl` 调用新增 `uiPhase: status.ui_phase ?? null`

**Watcher 改造（L1167-1370）**:
- 顶部新增 `watcherSubPhaseRef` 追踪当前 subPhase 防止重复 dispatch
- 5s tick 内：`uiPhaseToSubPhase` 9-state 映射表 → 只在 `derivedSubPhase !== current` 时 dispatch（顺解 RISK-T15-8）
- 4 个路由分支全部支持 ui_phase 优先 + legacy stage fallback：
  - completed: `ui_phase === "completed" || status === "completed" || stage === "completed" || progress >= 100`
  - char_review: `ui_phase === "char_review" || (stage === "character_ready" && !charactersConfirmedNow)`
  - scene_review: `ui_phase === "scene_review" || (stage === "scenes_ready" && charactersConfirmedNow && !scenesConfirmedNow)`
  - shot phase: `ui_phase === "storyboard_running" || "shot_generating" || (scenesConfirmedNow + MID_PIPELINE_STAGES)`

#### 3. StageC.tsx（ETA reset + 多源完成检测 + char_review）

**新增 (顺解 RISK-T15-7)**:
- `lastStageRef` (L187) 追踪上次 backend stage
- useEffect (L233-249) 监听 `currentStage` 变化 → `lastEtaSecondsRef.current = null` 重置，让新 stage 的 ETA 自然显示
- 解决 Founder test15 观察："1 分钟" UI 显示 vs backend 真实 ETA=350s 的体感误差

**类型升级**:
- D.23 watcher poller (L394-403): 加 `ui_phase?` 字段，`isCompleted` 多源检测
- text-gen poller (L488-503): 加 `ui_phase?` + `hydrate_hints?` + `characters_confirmed?` + `scenes_confirmed?` 全字段
- shot-gen poller (L695-708): 加 `ui_phase?` + `failed_shot_count?` + `partial_failure?`

**char_review 派生 (顺解 RISK-T15-8 frontend 端)**:
- text-gen poller (L543-548): `shouldShowCharPreview = ui_phase === "char_review" || stage === "character_ready"`
- 用户在 R4-1 还没确认时，ui_phase=char_review，frontend 跳 /characters；用户点确认后 ui_phase 推进，poller 不再触发 char-preview

**完成检测多源化**:
- text-gen / shot-gen / checkpoint watcher 三处均检测 `ui_phase === "completed" || status === "completed" || stage === "completed" || progress >= 100`

### Wave 9 顺解 RISK 列表 (frontend 端)

| RISK | 顺解前 | 顺解后 |
|---|---|---|
| **T15-3** | hydrate `/storyboard` 永远 404 | Backend GET /story 在 scenes_ready 阶段返 scenes，frontend 现有 hydrate parallel fetch 自动受益（/storyboard 仍 404 fallback 但无害） |
| **T15-7** | UX-7 monotonicity guard 跨 stage 压缩 ETA | `lastStageRef` + useEffect 监听 currentStage 变化时重置 lastEtaSecondsRef |
| **T15-8** | generationSubPhase 只通过 user click 切换 | Watcher 5s 监听 ui_phase 派生 subPhase；StageC text-gen poller 也加 ui_phase=char_review 触发 |
| **T15-9** | failed_shot_count 延迟更新 | Backend 已修，frontend status response 已含 failed_shot_count 字段（保留供 /preview 显示用） |

### 设计原则

**backward compat 第一**: 所有 Wave 9 字段为 `?` 可选；老 backend（无 ui_phase）走 legacy heuristic 路径，行为完全不变；新 backend（有 ui_phase）走优先路径，更精确。

**不删除旧逻辑**: B49/B58 + ADVANCED_STAGES + POST_CHAR_STAGES + MID_PIPELINE_STAGES 全保留作为 fallback。Wave 9 之后只是在前面加了一层"认 ui_phase"优先逻辑。

**防 dispatch 抖动**: watcherSubPhaseRef 比对，只在真切换时 dispatch。

**单向 backend authoritative**: subPhase / URL 都从 status response 派生，不从 user action 推导。

### npm build 结果

✅ 0 errors / 20 routes / pre-existing warnings only

### 验证清单（给 PM）

| # | 验证项 | 期望 |
|---|---|---|
| 1 | npm run build | 0 errors / 20 routes ✅ |
| 2 | createUrl.ts uiPhase 优先 | 8 phase 全映射 + completed/delivery 特例 + unknown 落 fallback |
| 3 | StageC lastStageRef useEffect | stage 变化时 lastEtaSecondsRef = null |
| 4 | CreateContent watcher subPhase 派生 | 5s tick 内只在 derivedSubPhase !== ref 时 dispatch |
| 5 | RISK-T15-2 不退化 | POST_CHAR_STAGES 仍不含 screenplay/storyboard |
| 6 | RISK-T14-8 不退化 | MID_PIPELINE_STAGES 仍存在 watcher fallback |
| 7 | B49/B58 不退化 | project.*\_confirmed 仍是 status fallback |

### 给 @pm（paste 用）

完整 paste 在 TEAM_CHAT message + 见下方"sendmessage paste"段

---

## 历史完成: RISK-T15-11 window.onerror 增强 (2026-05-13)

**模型**: Sonnet 4.6
**改动文件 (1)**:
- `frontend/src/app/layout.tsx` — L83-175 window.onerror + resource error listener + promise-reject 增强

### 修复清单

| # | 问题 | 修复 |
|---|------|------|
| 1 | 原 `addEventListener('error')` 拿不到 JS stack（e.error/filename/lineno 全空） | 新增 `window.onerror` handler — 拿完整 message/source/line/col/error.stack |
| 2 | 原 `addEventListener('error')` JS 错误和媒体错误混在一起，都显示"Unknown error" | 改为: JS 错误 → `window.onerror` 处理; 媒体/resource 错误 → 保留 listener 但加 `e.error` 守卫区分 + 提取 `target.tagName/src/MediaError.code` |
| 3 | promise-reject 的 reason 是 Event 对象时只显示 `{"isTrusted":true}` | 改为：检测是否为 Event 对象 → 提取 `type/isTrusted/targetSrc/MediaError.code/message` |

### 根因分析

test15 `client.log` 里 source/line/col/stack 全空的 "Unknown error" + `promise-reject: {"isTrusted":true}` 是媒体错误（HTMLMediaElement 播放失败）的典型特征：
- `<audio>` 或 `<video>` 加载失败 → 触发 `error` 事件 → 冒泡到 window
- `e.error` 是 null（因为不是 JS Error），`e.filename` 为空，`e.lineno` = 0
- 播放 Promise 被 reject，reason 是 MediaError Event 对象（isTrusted=true）

修复后，媒体错误在 client.log 里会显示：
- `args`: `"Resource load error: audio src=http://... MediaError.code=4 msg=..."`
- `target_info`: `"audio src=http://... MediaError.code=4 msg=..."` (新字段)
- promise-reject `args`: `"Event{type=error,isTrusted=true,targetSrc=...,MediaError.code=4,...}"`

### npm build 结果

✅ 0 errors, 20 routes, pre-existing warnings only

### PM e2e verify 步骤

```javascript
// DevTools Console 执行 — 验证 JS 错误 stack
throw new Error("test-js-stack-12345");
// 期望 client.log: level="uncaught", args=["Uncaught Error: test-js-stack-12345"], source 非空, line>0, stack 含完整 trace

// Promise reject 验证
Promise.reject(new Error("test-promise-stack-12345"));
// 期望 client.log: level="promise-reject", args 含 "test-promise-stack-12345", stack 非空
```

---

---

## 最新完成: RISK-T15-1 + RISK-T15-2 紧急双修 (2026-05-13 test15 期间)

**模型**: Sonnet 4.6
**改动文件 (2)**:
- `frontend/src/lib/createUrl.ts` — RISK-T15-2: POST_CHAR_STAGES 移除 screenplay + storyboard
- `frontend/src/components/create/StageC.tsx` — RISK-T15-1: 删 text-gen 分支 (L943) + subtitle 文案纠正 (L106-115) + fallback 文案纠正 (L120)

### 修复清单

| # | RISK | P | 文件 | 行号 | 修复 |
|---|------|---|------|------|------|
| 1 | T15-2 | 🔴🔴 CRITICAL | `createUrl.ts` | L118-131 | POST_CHAR_STAGES Set 中移除 "screenplay" + "storyboard"；scenes checkpoint 不再被永久 bypass |
| 2 | T15-1a | 🔴 P0 UX | `StageC.tsx` | L940-950 | "后台生成"按钮条件改为 shot-gen 独有，删除 text-gen 分支 |
| 3 | T15-1b | 🔴 P0 UX | `StageC.tsx` | L106-115 | STAGE_SUBTITLE story_generation/character_design/character_ready/screenplay/storyboard 五行改为"请稍候" |
| 4 | T15-1c | 🔴 P0 UX | `StageC.tsx` | L120 | resolveSubtitle fallback 改为"AI 正在创作故事，请稍候" |

### grep verify 结果

- `POST_CHAR_STAGES`: 1 处定义，无 screenplay/storyboard 残留 ✅
- `可以选择后台生成` 残留: 仅 image_preparation/image_generation/bgm/music 四行（shot-gen 阶段，正确） ✅
- 0 个误导文案残留 ✅

### dev hot reload

改完后 Next.js dev server 会自动热重载两个文件，无需手动重启。

---

## 最新完成: TASK-WAVE7-FRONTEND 6 任务全闭环 (2026-05-13)

**模型**: Sonnet 4.6 + 继承
**改动文件 (7)**:
- `frontend/src/app/create/CreateContent.tsx` — RISK-T14-8: 加 MID_PIPELINE_STAGES branch
- `frontend/src/components/create/StageC.tsx` — RISK-T14-6: handleConfirmCharacters 加 router.replace('/scenes'); RISK-T14-12: handleBackgroundGenerate 改 async+Notification 权限请求; "后台生成"按钮扩展到 text-gen; finalizeAndGoToPreview 加 Browser Notification
- `frontend/src/app/dashboard/DashboardContent.tsx` — RISK-T14-12: 30s polling + newlyCompletedIds + prevShotCountRef + Browser Notification
- `frontend/src/components/dashboard/StoryGrid.tsx` — RISK-T14-12: 透传 newlyCompletedIds
- `frontend/src/components/dashboard/StoryCard.tsx` — RISK-T14-12: "✨ 新故事完成" badge
- `frontend/src/lib/createUrl.ts` — RISK-T14-3: 两个相同 Set 提取为模块级 POST_CHAR_STAGES
- `frontend/src/contexts/AuthContext.tsx` — RISK-T14-2: user?.name/email/avatarUrl/plan/credits 全面可选链
- `frontend/src/components/create/StageB.tsx` — RISK-T14-13-frontend: confirm-outline 捕获 inconsistency_warnings, 非阻塞黄色 banner + 知悉并继续
- `frontend/src/app/settings/SettingsContent.tsx` — RISK-T14-2: user?.X 可选链
- `frontend/src/components/dashboard/UserMenu.tsx` — RISK-T14-2: user?.X 可选链

### 6 任务完成清单

| # | ID | P | 状态 | 修复方式 |
|---|---|---|------|----------|
| 1 | RISK-T14-8 | P0 | ✅ | CreateContent.tsx watcher 加 MID_PIPELINE_STAGES 分支：scenesConfirmed + stage in ['storyboard'/'image_preparation'/'image_generation'/'bgm'] + URL=/scenes → force /generating |
| 2 | RISK-T14-6 | P1 | ✅ | StageC handleConfirmCharacters 末尾加 router.replace(buildCreateUrl(projectId,'scenes'))，直接跳 /scenes 无需等 watcher |
| 3 | RISK-T14-12 | P1 | ✅ | "后台生成"按钮扩展到 text-gen；handleBackgroundGenerate async+Notification.requestPermission；finalizeAndGoToPreview 后台完成时 new Notification；Dashboard 30s polling + 新完成检测 + badge + Notification |
| 4 | RISK-T14-3 | P3 | ✅ | createUrl.ts POST_CHAR_STAGES_FOR_CHARS + POST_CHAR_STAGES 合并为模块级一个 const POST_CHAR_STAGES |
| 5 | RISK-T14-2 | P1 | ✅ | AuthContext/DashboardContent/UserMenu/SettingsContent 所有 user.X 改为 user?.X（含兜底 ?? ""） |
| 6 | RISK-T14-13-frontend | P1 | ✅ | StageB: apiFetch 泛型捕获 inconsistency_warnings，有警告时 setWarningBanner 并 return；知悉并继续调 handleAcknowledgeWarnings 再触发 start-generation |

### 验证结果

- ✅ `npm run build` 0 errors / 20 routes（仅 pre-existing warnings）
- ✅ TypeScript 无新错误
- ⚠️ Founder 手动 e2e 验证待 PM 协调

### 关键技术决策

**RISK-T14-8 只在 URL=/scenes 时触发**: MID_PIPELINE_STAGES 分支用 `currentPath?.endsWith("/scenes")` 判断，防止从 /generating 等其他页面意外触发。

**RISK-T14-12 dashboard 新完成检测逻辑**: 用 prevShotCountRef（Record<id,count>）跨 render 存储上次 shotCount；当 prev===0 且 current>0 才认为"新完成"（排除初次加载时所有 stories 的误触发）；Badge/Notification 均只在确定新完成时触发。

**RISK-T14-13 两步流程**: confirm-outline 有 warnings → 显示 banner + return（不调 start-generation）；用户点"知悉并继续" → handleAcknowledgeWarnings 调 start-generation + dispatch。confirm-outline 无 warnings → 原流程不变（直接 start-generation）。

### 待 PM 操作

1. PM 代写 TEAM_CHAT 本段 + PENDING.md 标 ✅ 6 任务
2. PM kill+restart frontend（npm run build 新 chunk）
3. PM 通知 Founder 手动 e2e 验证要点：
   - backend stage='storyboard' + scenes confirmed + URL=/scenes → 5s 内自动跳 /generating (RISK-T14-8)
   - 角色确认按钮 → 立即跳 /scenes（无延迟）(RISK-T14-6)
   - /generating text-gen 阶段出现"后台生成"按钮；点击浏览器弹权限询问 (RISK-T14-12)
   - 从 /generating 后台生成后，dashboard 30s 内刷新；新完成故事显示 ✨ badge (RISK-T14-12)
   - 5xx 时 user?.name 不崩溃（需后端配合模拟）(RISK-T14-2)
   - confirm-outline 返回 warnings 时显示黄色 banner，"知悉并继续"后正常生成 (RISK-T14-13)

---

## 历史归档: TASK-T13-FRONTEND-ROUTING-FAMILY 8 任务全闭环 (2026-05-12 ~22:50)

**模型**: Opus 4.7 + xhigh
**改动文件 (4)**:
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/app/create/CreateContent.tsx`
- `frontend/src/components/create/StageC.tsx`
- `frontend/src/lib/createUrl.ts`

### 8 任务完成清单

| # | Bug ID | P | 状态 | 修复方式 |
|---|--------|---|------|----------|
| 1 | BUG-T13-REACT-ANTIPATTERN-STAGEC | P0 | ✅ | StageC: useCallback 稳定 inline props (L728/740) + console.log L926 移到 useEffect + portraitMap 预算消除重复 resolvePortraitUrl 调用 |
| 2 | BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP | P0 | ✅ | CreateContent.tsx 加顶层 status watcher useEffect（5s 间隔），character_ready + !confirmed → force /characters |
| 3 | BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 | P0 | ✅ | 1. createUrl.ts reconcile 加 backendPastCharStage guard，仅当 backend 真过 character_ready + confirmed 才 bounce 2. StageC text-gen poller 用 ref 替代 closure state.charactersConfirmed 防 stale |
| 4 | BUG-T13-COMPLETED-NO-AUTO-JUMP | P0 | ✅ | 同 #2 watcher，status==='completed' → force /preview |
| 5 | BUG-T13-AUTH-FALSE-LOGOUT-ON-500 | P0 | ✅ | AuthContext 新增 tokenInvalid state + isLoggedIn 改为 `!!user \|\| (!!token && !tokenInvalid)`，5xx/网络/超时不再 logout，背景重试（指数退避 2-30s） |
| 6 | BUG-T13-PREVIEW-DIRECT-LOAD-SLOW | P0 | ✅ | CreateContent hydrate 把 BGM fetch 并入 chapter Promise.all 4 个并行（原本 BGM 串行在 chapter 之后）+ #1+#5 修复消除 React 卡死 + auth 误踢级联 |
| 7 | DASHBOARD-PERF-N1 | P1 | ✅ | 验证 dashboard 列表 GET /projects/ 单调用无 N+1。CreateContent hydrate 已有 hydratedFor + isOurOwnPush dedup 完整。BGM 并行化算入 perf 优化 |
| 8 | C1-frontend (confirm-scenes alias) | P0 | ✅ | StageC handleConfirmScenes 改调 project-level alias `POST /projects/{uuid}/confirm-scenes`（与 confirm-outline/confirm-characters 对称） |

### 验证结果

- ✅ `npm run build` 0 errors / 20 routes
- ✅ TypeScript `tsc --noEmit` 无错误
- ✅ 无新增 lint warnings（仅有 BgmPlayer.tsx:30 的 pre-existing useCallback 警告）
- ⚠️ Founder 手动 e2e 测试待 PM 协调

### 关键技术决策

**为什么用顶层 watcher（CreateContent.tsx）+ useEffect refs**：
- StageC text-gen poller 在某些场景会失效（React 错误边界 unmount / 闭包陈旧 / 阶段子组件未渲染）
- 顶层 watcher 是 belt-and-suspenders 安全网，独立于 StageC 生命周期
- 5s 间隔（不是 2s）— StageC 2s poller 仍是主，watcher 只补漏
- 用 refs 读最新 state 值，避免 useEffect 因 state 变化频繁重建 interval

**为什么用 tokenInvalid state（AuthContext）**：
- 旧逻辑 `isLoggedIn = !!user`，5xx 后 user=null → 误踢回 /login
- 新逻辑允许 user=null 但 token 仍有效（5xx 期间）= isLoggedIn=true
- 只有真 401 才设 tokenInvalid=true
- 背景指数退避重试（2/4/8/16/30s）让 user 数据在 backend 恢复后自动填充

**为什么 createUrl.ts 加 backendPastCharStage guard**：
- 旧逻辑 `urlStage="characters"` + `charactersConfirmed=true` → 一律 bounce 到 /generating
- 但 charactersConfirmed 可能因 ADVANCED_STAGES heuristic 误为 true
- 新逻辑要求 backendStage 真在 POST_CHAR_STAGES（screenplay 之后）才 bounce
- 防止用户手动改 URL 到 /characters 时被错误踢回

### 待 PM 操作

1. PM 代写 TEAM_CHAT 本段 + PENDING.md 标 ✅ 7 P0 + DASHBOARD-PERF-N1 + C1-frontend
2. PM kill+restart frontend（npm run build 已完成，新 chunk 含改动）
3. PM 通知 Founder 手动 e2e test14 验证：
   - 角色 ready → 自动跳 /characters（不需手动改 URL）
   - 完成 → 自动跳 /preview
   - 5xx 时不被踢回 /login
   - /preview 直链能 < 5s 加载
   - DevTools Console 无 setState in render 警告

### 高风险文件回归测试建议

- `frontend/src/components/create/StageC.tsx` — 改动较大（callback 稳定化 + console 移位 + portraitMap）。重点回归：
  - CharacterPreview 渲染时 portrait 是否仍正常显示（依赖 portraitMap.get）
  - 确认按钮点击后倒计时清除/onConfirm 触发
  - 倒计时 20s 自动确认仍正常
- `frontend/src/contexts/AuthContext.tsx` — 改 isLoggedIn 计算，重点回归：
  - 第一次登录不应卡 loadingUser=true
  - 401 仍立即 logout（设 tokenInvalid=true）
  - 5xx 不再误踢
  - logout/login 后 tokenInvalid 状态正确重置

---

## 历史归档 (TASK-T13-FRONTEND-A2-URL-FIX 2026-05-12 17:01)

✅ layout.tsx 硬编码 localhost URL P0 bug 已修。改用 NEXT_PUBLIC_API_URL env var 在构建时展开，生产环境日志管道不再 CORS 失败。npm run build 0 errors, 20 routes。

PM 17:15 收尾修复命名约定漂移 — `NEXT_PUBLIC_API_URL` 含 `/api` 后缀。

---

## 历史归档 (TASK-T13-FRONTEND-CLIENTLOG A2-frontend 2026-05-12 16:37)

✅ `frontend/src/app/layout.tsx` 注入 console proxy `<script>`，覆盖 7 类（error/warn/onerror/unhandledrejection/React strict/Next hydration/network 失败）。npm run build 0 errors, 20 routes。

---

## 上一个完成: 2026-05-11 Wave 6 — BUG-SCENES-CONFIRM-MISSING (P0) + URL-PINGPONG (P1) + PROGRESS-LIST-SKIP-SHOT (P2)

详见 completed.md

---

## 上一个完成: 2026-05-11 17:18 Wave 5 完成（PM 代写补完）- B49+B50+B48

详见 completed.md
