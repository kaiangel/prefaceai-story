# PM Agent - 当前任务

> **最后更新**: 2026-04-29 17:35
> **状态**: 🔄 **Wave 5.1 进行中** — Backend + Frontend + AI-ML 三真彩色 agent 并行（D.17 二次修订移除 NB2/Seedream 混合 fallback + 11 项暂缓项除导出/视频外全做）

## 2026-04-29 17:25 Founder 二次修订 D.17 — 关键铁律确立

**Pipeline 必须用单一生图模型，不可 NB2/Seedream 混合**（永久 memory: `feedback_pipeline_single_model_only.md`）

理由: 18 张 shot 里 1 张异类风格用户细看大概率发现，破坏视觉统一性。

修复:
- ❌ 删除 `image_generator.py` L796-801 + L1389-1398 + `seedream_generator.py` L720-740 _run_fallback 全部 NB2↔Seedream 自动切换
- ✅ 保留 PromptRewriter 改写重试（首选模型内）
- ✅ 新建 `app/services/prompt_safety_advisor.py` Haiku 智能提示用户改 prompt（仍拒时）

## 2026-04-29 17:30 Wave 5.1 spawn 3 agent 并行

| Agent | subagent_type | 任务 | 工时 |
|-------|--------------|------|------|
| 🟦 Backend | "backend" 真彩色 | D.17 移除 fallback + 智能提示 + D.18 SIZE_BY_MODEL + O-2 cap + T-2 callback + R7-2 schema/endpoint × 6 | ~3 hr |
| 🟩 Frontend | "frontend" 真彩色 | D.14 三 banner + D.13/D.16/T-1 + StageD onError 升级 + R7-2 frontend × 8 | ~2 hr |
| 🟨 AI-ML | "ai-ml" 真彩色 | O-1 outline 一致性 prompt | ~15 min |

## 关键产品决策（本轮 17:00-17:30）

1. **R7-2 DB schema 选 B**：PM 直接派 Backend 设计 schema + Alembic 迁移（**纯增量加列/加表，不破坏 Ben 现有架构**），事后通知 Ben
2. **R7-2 分享页内容方案 A**：部分 shot（前 3 张）+ 引流注册 CTA
3. **R7-2 OG meta tags**：暂不加，记 PENDING
4. **R7-2 分享过期机制**：永久（不加 expires_at）
5. **R7-2 PV 统计**：记录到 share_pv_logs 表
6. **D.17 二次修订**：移除 NB2/Seedream 混合 fallback（全 pipeline 单一模型铁律）
7. **R7-2 导出 zip + 合成视频**：暂缓 MVP 后做（已记 PENDING）
8. **ARCH-2 死表清理**：本轮做完后 Founder 人工通知 Ben 操作（DBA 边界）
9. **测试 + 部署节奏**：A — 全部做完一次性 push + VPS 部署（避免多次 docker rebuild）

## Wave 5 流程

- 5.1 Backend + Frontend + AI-ML 并行 (~2-3 hr)
- 5.2 Frontend 第二轮接 Backend R7-2 真 API
- 5.3 DevOps push + rsync VPS + Alembic 迁移 + 通知 Ben
- 5.4 Tester 端到端验收（本地 + 浏览器域名 2 套）

---

## ✅ TASK-T6-FIXBATCH 历史结案（17:00 之前）

Wave 0+1.1+1.2+2+2.5+3+3.5+3.6+4 全部 PASS

## 2026-04-29 16:50 Wave 4 DevOps 部署 ✅
- DevOps 真彩色 (subagent_type: "devops") 部署
- commit 84a2d35 (代码) + ec471a6 (文档) push GitHub main
- rsync VPS + Docker rebuild + 容器 healthy
- Ben 通知发了（team_ben/TEAM_CHAT.md 15:57）
- 生产 T8 (uuid a3966a40-6d27-42c0-a7cf-109729e453e7) 4 验收 PASS：D.15 1:1 ✅ / R7-1 cover+shot ✅ / R7-3 mtime+45s ✅ / UX-16 dynamic route HTTP 200 ✅
- T8 NB2 实际成本 ~¥12-15（NB2 单价比 Seedream 高，下次用 SKIP_IMAGE_GENERATION 节省）

## 2026-04-29 17:00 D.18 P3 新发现
- DevOps 报告 NB2 1:1=1024x1024 vs Seedream 1:1=2048x2048
- _ASPECT_RATIO_TO_SIZE 字典是 Seedream 标准，SceneImage 元数据写 2048x2048 跟 NB2 实际不一致
- 用户视觉感受不到（仍是 1:1），只影响 DB 元数据 + 后续单 shot 重生成参数 — P3 暂缓

## 暂缓项追踪 (PENDING D.13-D.18 共 6 条 + R7-2 5 按钮 + ARCH-2 + OPS-3 + 文案小批)

详见 PENDING + 用户视角故事见 TEAM_CHAT 17:00 PM 总结。

## 2026-04-29 15:50 Wave 3.5/3.6 + D.17 简化
- Wave 3.5 R7-3 修复 (character_prompt_builder isinstance) ✅
- Wave 3.6 Tester 真彩色复测 6 证据点 ✅ + PM 5 角度地毯式深挖 ✅
- D.17 CONTENT_SAFETY 脱敏策略族 — Founder 简化为只 Layer 3 末端 fallback（不前置脱敏，保护故事生动性）
- D.17 含 Seedream 未来首发生产可能性备注

## 2026-04-28 21:30 Wave 3 Tester ✅ + R7-3 P1 立即修
- T7 真生图 1:1 朋友圈 16 shots，11 PASS / 1 FAIL
- D.15 P0 PIL 实测全部 2048x2048（用户选 1:1 真生效）
- R7-3 portrait 重生 `'str' object has no attribute 'get'` (projects.py L945) → 立即派 Backend (subagent_type: "backend") 修
- 修后 Tester 复测 adjust 路径（不重跑 T7 完整，省成本）
- Wave 4 DevOps 待 R7-3 PASS

## 2026-04-28 17:00 subagent_type symlink 修复完成
- ✅ 验证 `/Users/kaisbabybook/AIFun/xuhuastory/.claude/agents` symlink 存在
- ✅ feedback_use_custom_subagent_type.md 重写（旧"PM 主对话只能用内置 type"结论纠正）
- ✅ MEMORY.md 索引重写
- ✅ 新建 reference_subagent_symlink.md
- TEAM_CHAT + pm-progress/completed.md 历史"general-purpose"引用是事件描述，无需改

## 2026-04-28 16:35 Wave 2.5 D.15 P0 ✅
完整调用链路 10 段全接通（frontend → projects.py → DB → job_manager → pipeline → image_gen → seedream → NB2）
0 处 hardcoded "2:3" 残留 | _ASPECT_RATIO_TO_SIZE 7 比例 | pytest 292/292

## 🆕 2026-04-28 15:35 D.14 决议落地

Founder 同意 D.14 F-Lock-Family **升 P2 + 扩展为家族修复**（outline / characters / scenes 三处同源）：
- 不进本批 Wave 2，作为下批"产品打磨批次"优先项
- 工时 ~25 min frontend（共享 useStageLock hook + 3 处 banner）
- 完整方案 / UX 走查 / 决议背景 见 PENDING.md D.14 + TEAM_CHAT 15:30/15:35

## Wave 2 派发就绪

- D (Backend Sonnet 4.6 effort high): /api/projects/ 加 cover_image_url + shot_count + mood + ISO 时区 (~10min)
- F (Backend Sonnet 4.6 effort high) 与 D 并行: ARCH-1 chapter_scene_images 写入 (~30min, 高风险 18+ 引用先 grep 评估)
- E (Frontend Sonnet 4.6 effort high) 等 D 完成: AuthContext mapProject 读后端新字段 (~10min)
- 总工时 ~45min



## 🆕 TASK-T6-FIXBATCH 进度

详细规划见 `.team-brain/handoffs/PENDING.md` TASK-T6-FIXBATCH 章节（5 R7 + 4 Wave + 12 风险 + 12 暂缓）。

### Wave 状态

| Wave | Agent | 工时 | 状态 |
|------|-------|------|:-:|
| Wave 0 PM 文档 | PM | 10 min | ✅ 12:10 完成 |
| Wave 1.1 Agent A Backend (Sonnet) | 5 子任务 | ~2 hr | ✅ 14:13-15:05 完成（一轮地毯式审查 → 1 修复 round → 二轮深挖通过）|
| Wave 1.1 Agent B Frontend (Sonnet) | 7 子任务 | ~1.5 hr | ✅ 14:14-14:26 完成（一轮通过）|
| **Wave 1.2 Agent C UX-16 (Frontend Opus)** | dynamic route | ~3 hr | ⏳ **准备 spawn** |
| Wave 2 D Backend → E Frontend + F ARCH-1 | dashboard 列表 + chapter_scene_images | ~50 min | ⏳ |
| Wave 3 G Tester T7 真生图 | 端到端验证 + 回归 | ~1 hr + ¥1.5 | ⏳ |
| Wave 4 H DevOps 部署 | push + rsync | ~30 min | ⏳ |

### Wave 1.1 关键产出（已上线代码）

**Backend (4 文件)**:
- `app/services/job_manager.py` — P0-2 mark_completed stage='completed' / P1-2 progress 单调 guard + estimated_remaining_seconds 参数
- `app/services/pipeline_orchestrator.py` — P1-1 9 处 callback stage 名重构 / P1-2 STAGE_DURATIONS + estimate_remaining 函数 / P1-3 freshness check 含 30s buffer / P1-5 character_design 中间态
- `app/api/projects.py` — P1-3 adjust_character Step 7 重生 portrait + 新端点 POST /characters/{id}/regenerate-portrait
- `app/services/reference_image_manager.py` — P1-3 generate_character_multi_refs 加 skip_portrait + seed_image 参数
- `app/api/chapters.py` — P1-2 修复 round 1: import estimate_remaining + /status 调用计算 stage-aware ETA

**Frontend (5 文件)**:
- `frontend/src/lib/url.ts` — 新建 toAbsoluteUrl + SERVER_BASE 共享
- `frontend/src/components/create/StageD.tsx` — P0-1 image src 用 toAbsoluteUrl + onError 占位
- `frontend/src/components/create/StageC.tsx` — P0-3 fetch chapter / P2-2 删 checkpointPreview / P2-4 完成态 + carousel 停 / F-2 真 API / STAGE_LABEL 加 character_design + image_preparation
- `frontend/src/components/create/StageE.tsx` — P1-6 outline.summary 三层 fallback
- `frontend/src/components/ui/BgmPlayer.tsx` — P0-1 audio src 用 toAbsoluteUrl
- `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` — 改用共享 toAbsoluteUrl

### Wave 1.1 教训（已写入 memory + xhteam SKILL.md）

`feedback_carpet_review_deep_dive.md` 永久保存：地毯式审查必须追到调用链路最末端（函数定义 → 调用点 → 参数传递 → 数据流向 → 消费点）。Wave 1.1 第一轮 PM grep 验证函数定义存在就差点放过 estimate_remaining 死代码 + freshness check 缺 30s buffer，Founder 提醒后深挖发现。

xhteam SKILL.md 第四步独立审查 加了"地毯式审查铁律"双保险。

### Wave 1.2 派发计划

**Agent C (Frontend Opus 4.6)** — UX-16 URL 路由 dynamic route 改造：

- 改 `/create` 单页为 `/create/[projectUuid]/[stage]` Next.js dynamic route
- 各 Stage 切换时 router.replace() 同步 URL
- 刷新时根据 URL 还原 state（拉 backend chapter API + project API）
- useGenerationStatus hook 跟 URL 联动
- 浏览器后退按钮行为
- 跟现有 dashboard 详情页 `/dashboard/[storyId]` 路由不冲突

**为什么用 Opus**: 大改造跨多文件，需要深度状态管理思考（feedback memory: spawn_use_sonnet_for_simple_tasks — 深度思考类→ Opus）

**单独 spawn 不混 1.1**: feedback_docs_before_spawn 风险最低做法。

### 协作上下文（给后续 Wave 用）

- backend 新加 stage 名: `character_design`（5-7%）和 `image_preparation`（65-75%）— frontend STAGE_LABEL 已就绪
- backend 新加 endpoint: `POST /api/projects/{project_id}/characters/{char_id}/regenerate-portrait`
- backend /api/projects/{project_id}/chapters/{chapter_number}/status 现返 stage-aware estimated_remaining_seconds
- backend Stage 5 prep 自动 freshness check 30s buffer 复用 portrait

### Wave 2-4 提醒（不在本轮）

- Wave 2: dashboard 列表 backend 加 cover_image_url + shot_count + mood + ISO 时区，frontend mapProject 读字段；ARCH-1 单独 backend agent 做 chapter_scene_images 写入
- Wave 3: Tester T7 真生图（简单生活短篇，避高 sanitize 题材，预算 ≤ ¥1.5）
- Wave 4: DevOps push + rsync VPS（trailing slash 陷阱）

## 历史完成（2026-04-27）

详见 completed.md
