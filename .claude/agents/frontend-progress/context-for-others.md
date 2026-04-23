# Frontend 状态速览（供其他Agent参考）

> 更新时间: 2026-04-23 16:10

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
