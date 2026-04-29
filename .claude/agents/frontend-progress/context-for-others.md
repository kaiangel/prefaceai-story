# Frontend 状态速览（供其他Agent参考）

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

