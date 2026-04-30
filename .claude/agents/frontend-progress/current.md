# Frontend 当前任务进度

> 更新时间: 2026-04-28 16:30 (frontend Agent E, Sonnet 4.6 自更)
> 状态: ✅ TASK-T6-FIXBATCH Wave 2 Agent E — R7-1 Dashboard 列表前端读字段完成，npm build 21 routes 0 errors
> 下一步: PM 审查 → DevOps 部署

---

## 最新完成: TASK-T6-FIXBATCH Wave 2 Agent E — R7-1 Dashboard 列表前端读字段 (2026-04-28 16:30)

**任务**: Wave 2 P1-4 R7-1 Dashboard 列表 frontend 读 Backend Agent D 新增的 4 字段。

**修改文件 (4)**:
- `frontend/src/contexts/AuthContext.tsx` — `ApiProject` 接口新增 `cover_image_url / shot_count / mood`；`mapProject()` 用 `toAbsoluteUrl()` 转 cover + fallback logo + 读 shot_count + mood + ISO Z 时间
- `frontend/src/types/create.ts` — `StoryCard` 加 `mood: string | null`
- `frontend/src/components/dashboard/StoryCard.tsx` — metadata 行加 mood badge（条件渲染）
- `frontend/src/lib/mock-data.ts` — 6 条 mock 补 `mood` 字段

**验收**: ✅ npm build 21 routes 0 errors

---

## 上一个完成: TASK-T6-FIXBATCH Wave 1.2 Agent C (Opus 4.7) — UX-16 (2026-04-28 15:06)

**任务**: P0 — `/create` URL 不变导致刷新丢 state 回到 Stage A，影响用户 30+ min 工作不能保护。

**方案**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage 6 枚举值（outline / characters / scenes / generating / preview / delivery）。

**新建文件 (2)**:
- `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` — 动态路由入口
- `frontend/src/lib/createUrl.ts` — URL ↔ state 映射 + reconcileBackendVsUrl 决策树

**改动文件 (3)**:
- `frontend/src/app/create/CreateContent.tsx` — hydrate hook + state↔URL 双向同步
- `frontend/src/contexts/CreateContext.tsx` — 新增 HYDRATE_FROM_BACKEND reducer
- `frontend/src/types/create.ts` — 新增 HYDRATE_FROM_BACKEND action 类型

**未碰**: backend / StageB-E 核心逻辑 / lib/url.ts / dashboard 路由

**验收**:
- ✅ `npm run build` 21 routes 0 errors
- ✅ HTTP smoke test 全 stage 200, invalid stage 404, dashboard 不破坏
- ✅ 4 核心场景代码 trace 通过：F5 刷新 / 浏览器后退 / 复制链接 / 跨 stage 切换

**反馈环避免**: lastPushedUrlRef echo guard + derivedFromState 短路 + completion guard 三层防护

**已知遗留**: hydrate 后 StageC START_GENERATION reset progress 短闪 ~1.6s（下批优化）

---

## 上一个完成: TASK-T6-FIXBATCH Wave 1.1 Agent B (2026-04-28 14:30)

**改动文件**:
- `frontend/src/lib/url.ts` — 新建，toAbsoluteUrl() 共享工具（含 P3-4 引号 strip）
- `frontend/src/components/create/StageD.tsx` — P0-1 toAbsoluteUrl + P3-5 onError 占位图
- `frontend/src/components/create/BgmPlayer.tsx` — P0-1 toAbsoluteUrl
- `frontend/src/components/create/StageC.tsx` — P0-3 / P2-2 / P2-4 / F-2 / P3-6 + STAGE_LABEL
- `frontend/src/components/create/StageE.tsx` — P1-6 outline.summary
- `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` — 迁移到共享 toAbsoluteUrl

**7 子任务修复**:
| 项 | P | 实现 |
|----|---|------|
| P0-1 StageD image/bgm 404 | P0 | toAbsoluteUrl() 包 img src + audio src |
| P0-3 portrait 数据源 | P0 | character_ready 后 fetch /chapters/1/story，portrait_url 从 chapter.characters_json 读 |
| P1-6 Stage E summary | P1 | outline.summary → idea 三层 fallback |
| P2-2 checkpointPreview 删除 | P2 | 删 IIFE + render 区域 |
| P2-4 副标题统一 + carousel 停止 | P2 | completed 时停 interval + 统一读 message |
| F-2 handleRegenerate 真 API | F2 | POST /projects/{id}/characters/{charId}/regenerate-portrait |
| 旧 P3-4/5/6 | P3 | BgmPlayer 引号 strip + Shot onError 占位 + 进度条 spring 动画 |

**STAGE_LABEL 新增**: `character_design: "正在生成角色画像"` + `image_preparation: "正在准备画面"`
**toAbsoluteUrl 位置**: `frontend/src/lib/url.ts`（StageD / BgmPlayer / StageC / StoryDetailContent 全引用）
**验收**: ✅ npm run build 20 routes 0 errors

---

## 上一个完成: TASK-T5-FIXBATCH-R6 子任务 2 (2026-04-27 17:55)

**改动文件**:
- `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` — 完全重写
- `frontend/src/types/create.ts` — StoryDetail.characters 扩 `portrait_url?: string | null`

**7 bug 修复**:
| Bug | P | 实现 |
|-----|---|------|
| A loading state | P0 | `loading` + `notFound` state 区分 "加载中..." vs "故事不存在" |
| B /storyboard endpoint | P0 | 并行 fetch 3 endpoint: /projects/{id} + /chapters/1/storyboard + /chapters/1/story |
| C image_url 真实值 | P0 | buildShotsFromStoryboard() 从 storyboard_json 解析 shots，toAbsoluteUrl() 拼 SERVER_BASE |
| D summary 用 outline | P1 | `project.confirmed_outline?.summary \|\| original_idea` |
| E mood 用 outline | P1 | `user_selected_mood \|\| mood \|\| "—"` |
| F portrait + silhouette | P1 | 角色显示 portrait_url 图片，无则 SVG 人形 silhouette |
| G BGM player | P2 | fetchBgmInfo() best-effort，bgm_url 存在时渲染 `<audio controls>` 内联播放器 |

**验收**: ✅ npm run build 20 routes 0 errors

---

## 历史: TASK-T5-FIXBATCH 7 条前端修复 (2026-04-27 16:23)

详见 completed.md

---

## [2026-04-29 19:30] Wave 5.1 ✅ (PM 代更，权限 600)

8 子任务全完成 + npm build 22 routes 0 errors:
- D.14 useStageLock hook 新建 + StageB/StageC 三处 banner + 隐藏按钮
- D.13 hydrate guard initialProgressRef
- D.16 mood string|null
- T-1 friendlyMessage replace 张图像→个片段
- StageD onError D.17 配套 safetyAdvice + 改一下文字按钮
- R7-2 favorite/share/公开页 frontend 接 backend API
- /s/[token] Server Component 新建（OG 暂不加）
