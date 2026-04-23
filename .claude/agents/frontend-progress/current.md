# Frontend 当前任务进度

> 更新时间: 2026-04-23 16:10
> 状态: ✅ TASK-BUG-FIX-BATCH-1 Route C 完成 — FE-1/2/3/4 修复 + FE-5 根因分析，build 20 路由 0 错

---

## 最新完成: TASK-BUG-FIX-BATCH-1 Route C (2026-04-23 16:10)

**改动文件**: `StageC.tsx` + `CreateContext.tsx`（2 个）

| # | 修复 | 文件:行号 | 说明 |
|---|------|----------|------|
| FE-5 | 完成→预览卡"好几分钟" | StageC.tsx:312 / :317-363 / :390 | completedRef 在 shot-gen 入口显式 reset（防 StrictMode/remount 污染）+ 补 progress>=100 触发器 + console.time 观察性 |
| FE-1 | stage 文案细化 | StageC.tsx:55-77 / :106 / :374 / :432 | STAGE_LABEL 映射 6 stage + resolvePhaseTitle + setCurrentStage(status.stage) |
| FE-2 | 时间线去重 | CreateContext.tsx:228-248 | 全列表 dedup（不只比 lastLog） |
| FE-3 | progress quantize | StageC.tsx:224-225 | 去 Math.max，`progress>0 ? real : sim` |
| FE-4 | stage_message 透传 | 现有代码已正确 | filter 只过滤技术错误，业务 stage 全留 |

**FE-5 根因（高置信）**: `completedRef = useRef(false)` 跨 React StrictMode/remount 污染，一旦被误置 `true`，后续 `status==="completed"` 分支全 `return` 早退，UI 卡 100% 不跳转。Fix: shot-gen useEffect 入口显式 reset + 扩 trigger 到 `progress>=100` 兜底。

**Build**: ✅ 20 routes, 0 TS error

**发现额外 bug**:
1. `job_manager.py:302` 任务完成 stage 写成 `story_generation`（应保留 `image_generation` 或 `completed`）— 派给 @backend
2. Stage 6 BGM 无 progress_callback，前端卡 90% 几分钟 — 派给 @backend/@ai-ml
3. StageD shot 兜底"画面生成中..."在 pipeline 已完成后误导用户 — P2 优化

---

## 历史完成: Wave 3 Step 6 — BGM Player (2026-04-21)

**新建**: `frontend/src/components/create/BgmPlayer.tsx`
- 5 状态：idle（暂无配乐）/ loading（初次获取）/ generating（AI 2-5min 生成）/ ready（全功能）/ error（重试）
- HTML5 `<audio>` ref + 播放/暂停 + 进度条 + 时间显示
- 音量滑块（300ms debounce PATCH `/bgm/volume`）
- 版本标签（混合版/英文版）+ credits 显示（mock）
- 按钮：换一首（POST change-meta）+ 重新生成（POST regenerate），2-5min loading UI
- 首次生成按钮（bgm_exists=false 时显示）

**改动**:
- `types/create.ts`: 6 新类型 + `bgmPlayer` 加到 CreateState + 6 个 BGM actions
- `contexts/CreateContext.tsx`: bgmPlayer 初始 state + 6 reducer cases
- `lib/api.ts`: 4 个 BGM API 封装
- `StageD.tsx`: 替换旧 BGM_TRACKS 选择器 → `<BgmPlayer projectId chapter={1} />`

**Build**: ✅ 20 路由 0 TS 错误

---

## 历史完成: TASK-STAGED-WIRE (2026-04-14)

| # | 按钮 | KI | 实现 |
|---|------|-----|------|
| 1 | 重新生成 | KI-001 | async POST API + loading spinner + imageUrl 更新 |
| 2 | 编辑保存 | KI-002 | PATCH API 回写 DB + "保存中..." + toast |
| 3 | 删除 | KI-003 | DELETE API 先成功再 dispatch + "删除中..." + toast |

改动: StageD.tsx + CreateContext.tsx + create.ts (3 文件)

---

## 最新完成: TASK-PIPELINE-OPT-R5 (2026-04-09)

| # | 修复 | P | 状态 |
|---|------|---|------|
| R5-1 | completedRef 防重复触发 completed 分支 + `/generation-result` 只请求一次 | P1 | ✅ |
| R5-2 | progress >= 100 时显示"即将完成"，不再显示预估分钟数 | P2 | ✅ |

**改动文件**: 仅 `frontend/src/components/create/StageC.tsx`（1 个文件），build 20 路由 0 错误

---

## 上一个完成: TASK-PIPELINE-OPT-R3 F-1/F-2/F-3 (2026-04-09)

| # | 修复 | P | 状态 |
|---|------|---|------|
| F-1 | 角色调整 API 返回格式: result.description → result.character.description_zh ∥ result.character.description | P0 | ✅ |
| F-2 | 0%-5% 模拟进度: 12s/1% 最高 5%, max(sim, real) 避免倒退 | P1 | ✅ |
| F-3 | 场景确认展示 description_zh: OutlineScene 类型 + 场景映射优先中文 + 后端 passthrough | P1 | ✅ |

**改动文件**: StageC.tsx + create.ts + projects.py (1 行 data passthrough)

---

## 更早完成: TASK-BUGFIX-STAGEC (2026-04-09) ✅

| # | 修复 | 状态 |
|---|------|------|
| 3-A | StageC.tsx L80 `"generating_images"` → `"image_generation"` + L79 注释更新 | ✅ |
| 3-B | CreateContext.tsx 重复日志去重（比对最后一条 message） | ✅ |

**改动文件**: StageC.tsx + CreateContext.tsx
