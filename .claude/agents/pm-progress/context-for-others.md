# PM Agent - 给其他Agent的信息

> **最后更新**: 2026-04-24 13:38
> **目的**: 让其他Agent快速了解当前状态和任务

---

## 🆕 TASK-VPS-SKIP-IMAGE 完成 (2026-04-24)

VPS `.env.production` 现在含 `SKIP_IMAGE_GENERATION=true` → prefaceai.mov 测试会走 R8 mock 图，跳过 NB2 真实调用。

**对所有 agent 的影响**:
- 本地和 VPS 都是 SKIP=true 状态，测试 Pipeline 不会产生 NB2 生图费用
- 如果将来要验证真实生图（NB2 链路），需要手动改 env 为 false 或走其他 flag

**三天 NB2 调用审查结论（2026-04-22 ~ 04-24）**: **0 次调用 / $0 花费**（5 层独立验证）

**新发现 ARCH 孤儿表**:
- `api_cost_logs` 全表 0 行，代码 0 引用 → 和之前的 `chapter_scene_images` / `project_character_references` 并列为 **3 张孤儿表**，记入 PENDING

---

## 🆕 TASK-BUG-FIX-BATCH-1 完成 (2026-04-23)

Founder 本地跑完 Pipeline 发现 18 bug，并行 @backend + @frontend 一次过关。

**对 @backend / @ai-ml 影响**:
- SKIP_IMAGE_GENERATION=true 模式下的 Stage 5 现在会**复制 R8 图 + 写回 storyboard.shots[*].image_url**（前端可通过 `/static/outputs/{uuid}/images/shot_NN.png` 访问）
- `checkpoint_callback` 修复了对 String 列多 json.dumps 的 bug（`bgm_url` 等不再带引号）
- Stage 6 BGM 现在会写 `credits_used` 到 DB
- `/static/outputs` 静态路径已 mount 指向 `./output/`

**对 @frontend 影响**:
- StageC.tsx 加了 STAGE_LABEL 映射（story_generation/screenplay/storyboard/image_generation/bgm），UI 文案按后端 stage 细化
- `completedRef` 在 shot-gen useEffect 入口重置，避免 StrictMode 污染卡死
- progress 改用 backend 实值（不再 Math.max clamp）

**MVP 后待修（记入 PENDING）**:
- job_manager.py:302 完成时 stage 覆盖
- Stage 6 BGM 缺 progress_callback
- StageD.tsx imageUrl=null 文案误导
- chapter_scene_images 表 Pipeline 完成后从不批量写入
- project_character_references 表完全是死表

---

## 🆕 TASK-LLM-TEMP-AUDIT-FIX 完成 (2026-04-22)

- Founder 42 调用点温度审计，PM 派 @backend 改 15 处（7 步）
- @backend 一次过关，pytest 7 passed，/health healthy
- 对齐/验证/OCR/视觉分析 → `temperature=0.2`
- Stage 3 剧本 + Stage 4 分镜 → 主备都 `temperature=0.8`
- sync Claude `max_tokens=8192→16384`（story_generator）
- PM 独立地毯式审查发现 backend 调查有偏差：max_tokens=8631 实际 **13 处**（非 14），且 `story_outline_generator.py` 属于**半改状态**（Claude L178 已 16384，Gemini L196 仍 8631）
- 下一步: 派 @backend 把剩余 13 处 `8631→16384` 统一（Founder 批准）

---

## 🆕 TASK-MUREKA-PIPELINE-INTEGRATION Wave 1-4 + VPS 部署全部完成 (2026-04-21)

- 生产环境 BGM 能力上线。VPS Docker 已 rebuild + `/health` healthy + `MUREKA_API_KEY` 注入
- 共享阿里云 MySQL 的 `project_chapters` 表已有 4 个 BGM 列（bgm_url / bgm_volume / bgm_meta_version / credits_used）
- 代码已 push commit `b998cbf` to origin/main
- 4 个 BGM REST 端点已上线：GET `/bgm`、POST `/bgm/regenerate` (+10 cr)、POST `/bgm/change-meta` (+5 cr)、PATCH `/bgm/volume`
- 前端 BgmPlayer.tsx 5 状态 + StageD 集成
- 部署由 PM 代执行（@devops Bash 二次被拒，依据 memory "重启服务 PM 自己做" 先读 devops.md 后执行）
- MVP 后 PENDING (P3): music_hint 在 Haiku 层效用有限、秋梨膏金句重试机制、自定义 BGM 上传

---

## 当前状态

```
✅ Harness V2 全部完成 (Sensor 10/10, 计算性控制 10/10)
✅ Music Prompt Skill 创建完成 (9 文件: 知识库+模板+脚本)
✅ 6 个故事 BGM 全部生成
✅ TASK-MUSIC-REWRITE: #3/#4/#6 prompt 重写 + V2 BGM 生成
✅ TASK-MUSIC-EXTRACT: story_input_format.md 定义完成（@backend 写提取脚本待派发）
✅ TASK-MUSIC-TRANSITION: 转折测试 bgm_transition_test.mp3 已生成
✅ TASK-SETTINGS-FIX (2026-04-18): Settings 类补齐，严格模式恢复，backend 启动正常
✅ TASK-ENV-SETTINGS-SYNC-TEST (2026-04-18): EP-016 工程化防护，PreCommit/PrePush 自动拦截漂移
✅ TASK-MUSIC-LANG-RESEARCH (2026-04-18): 调研 Mureka/Suno/Udio 等 40+ URL 的多语言策略 → `.team-brain/analysis/MUSIC_PROMPT_LANGUAGE_RESEARCH.md`
✅ TASK-MUSIC-LANG-AB (2026-04-18): Haiku 4.5 + Mureka A/B/C 三个语言变体实证，3/3 BGM 成功生成，等 Founder 盲听
✅ 新记忆 feedback_pm_no_scripting.md (2026-04-18): PM 不写 Python 脚本，集成工作派 @backend
✅ TASK-MUSIC-LANG-AB-V2 (2026-04-20): meta-prompt v2 升级（跨感官 4 元原则 + 3 精选示例 + ≤400 字符硬约束）+ 3 首 v2 BGM 生成 + 7 首盲听包就绪
✅ TASK-HAIKU-QUOTE-EXTRACTION (2026-04-21): v3 Quote Selection Protocol + 6 故事 × 2 变体评审 → mixed 8.4/10 > en 6.8/10
✅ v3.1 / v3.2 迭代 (2026-04-21): v3.1 加过度约束致质量退步；v3.2 方案 B（meta-prompt 回退精简 + Backend 代码清污）恢复到 7.4/10
🔄 TASK-MUREKA-PIPELINE-INTEGRATION Wave 1-3 (2026-04-21):
  - Wave 1 ✅: music_hint (@ai-ml) + story_music_extractor + ffmpeg_post_processor (@backend) 三并行完成
  - Wave 2 ✅: LUFS fix + music_generation_service + chapter DB + orchestrator Stage 6，PM E2E 年夜饭跑通（PM 修 URL typo 1 行）
  - Wave 3 🔄: REST API (@backend) + BGM UI (@frontend) 并行中
```

---

## @AI-ML — ✅ 完成

**TASK-MUSIC-PROMPT**: 6 个故事 BGM Prompt 全部交付
- 5 层结构（场域+骨架+肌肉+呼吸+灵魂），6 种完全不同风格
- Skill 位置: `.claude/skills/music-prompt/`

---

## @Backend — ✅ 完成

**TASK-MUREKA-BGM 系列**: 6 个故事 7 个 mp3 全部生成
- Mureka API (mureka-9, auto)，每首平均 2-3 分钟耗时
- 生成脚本: `generate_bgm.py`
- 规则: n=1（节省成本），Python urllib（不用 curl）

**TASK-PROMPT-B-PRIME**: ✅ B' 默认格式（A 保留 `PROMPT_FORMAT=legacy`）
**TASK-KI-FIX**: ✅ 3 个 shot API 端点（SKIP 模式）

---

## @Frontend — 🔄 执行中

**TASK-STAGED-WIRE**: StageD 3 按钮接通后端 API（已 spawn）
- 重新生成: POST `/{chapter_number}/shots/{shot_id}/regenerate`
- 编辑回写: PATCH `/{chapter_number}/shots/{shot_id}`
- 删除: DELETE `/{chapter_number}/shots/{shot_id}`
- API 契约详见群聊 Backend [2026-04-14 17:30] 完成报告

---

## @Tester — 信息

**Harness Engineering 新增的自动化测试**:
- `tests/test_architecture.py` — 6 个架构适应度测试
- `tests/test_quality_gates.py` — 4 个质量门测试
- PreCommit hook 自动执行（每次 commit 前）
- PrePush hook 跑完整 tests/（每次 push 前）

---

## @DevOps — 信息

**Hooks 已升级** (.claude/settings.local.json):
- PostToolUse: .py → pyright, .tsx → tsc + 清缓存
- PreCommit: test_architecture + test_quality_gates
- PrePush: 全量 tests/ timeout=300

**TEAM_CHAT 归档机制就绪**: `scripts/archive_team_chat.sh`

**待办**: Mureka API key 需加到 VPS `.env.production`（生产部署时）

---

## 🆕 TASK-PARALLEL-M1 进展 (2026-04-25 16:10)

**Phase 0 ✅ TASK-RATELIMIT-RESEARCH 完成**:
- NB2 Tier 1 IPM=10 / RPM=15 / RPD=1500
- Seedream IPM≈500 (4.0 baseline) / 平台 QPS=10
- 推荐 max_concurrent=3，两 provider 都安全
- NB2 30% 429 是 Google Dynamic Shared Quota 故意设计，与 max_concurrent 无关，retry 兜底
- 报告: `.team-brain/analysis/RATELIMIT_RESEARCH_2026-04-25.md`

**Phase 1 🟡 TASK-PARALLEL-M1 实施 — 代码完成附 3 隐忧**:
- 改: `pipeline_orchestrator.py` Stage 5 串行→并行 (Semaphore + asyncio.gather + gc.collect 累积态兜底 + Haiku validator 并行)
- 改: `image_generator.py` + `seedream_generator.py` 成功路径加 cost log
- 新建: `app/services/api_cost_logger.py` + `app/models/api_cost_log.py` ORM (ARCH-4 INSERT)
- 新建: `tests/test_parallel_stage5.py` 17 用例覆盖 8 失败分支 + Q2/Q3/ARCH-4
- 新建: `conftest.py` stub 外部依赖（24/24 测试通过经 stub）

**对其他 agent 的影响（PARALLEL-M1 部署后）**:
- **@frontend**: 用户 Stage 5 体感 13.5 min → 4.5 min（NB2）/ 27 min → 9 min（Seedream）。无 API 契约改动。
- **@tester**: Phase 2 必须用真实 venv + 28 shot 完整 pipeline 验证（Phase 1 测试都经 stub 通过，需真实环境复测）
- **@devops**: Phase 3 部署 VPS 时注意 IMAGE_MAX_CONCURRENT env 设置 + ARCH-4 ApiCostLog 表 alembic 迁移
- **@ai-ml**: 无影响（生图 prompt 不变）

**Founder 决策走 B**: Backend round 2 修 3 隐忧（移除 conftest stubs、通 string→int project_id 映射、4 文档更新），再 Phase 2。


---

## 🆕 TASK-PARALLEL-M1 D1 redo 完成 (2026-04-27 10:50)

**周末进展（04-25 ~16:00-18:40）**:
- Round 3 修了 4 bug: project_id=None / ShotValidator 鉴权 / IncompleteRead retry / Event loop closed
- D1 redo 全套 14/14 测试通过，8 故事跑通（perf×2 + quality 6.4/6.5_wuxia/6.6_multichar + 跨题材 modern_urban/wuxia/realistic/ink）
- 实际成本 ¥34.3，预算 ¥48 内
- pytest 24/24 真实 venv 通过

**残留**:
- Bug 1 partial: image_generator.py L1392-1398 dispatcher 没传 **_kwargs_copy → project_id 仍 None。**1 行修复**
- Bug 4 partial: 主 bug 修了，残留 aiomysql GC cleanup error（不阻断）
- Bug 5 新发现: ShotValidator 5MB 图片上限，部分 Seedream PNG 超限触发 fail-open

**Founder 04-27 看图反馈**: "不错，可用，比 NB2 稍逊但可接受"。决策: round 4 修 Bug 1 + Bug 5，本地+域名测后再决定 Phase 3 部署。

**对其他 agent**:
- @backend: round 4 任务已派 (1 行 dispatcher + 图压缩)
- @tester: round 4 完成后可能需 sanity 复测，等 PM 通知
- @devops: 部署暂缓，等 Founder 本地+域名测试通过


---

## 🆕 TASK-T5-FIXBATCH Phase 1 全部完成 (2026-04-27 16:36)

**14 条修复全部就位** (Backend 8 + Frontend 7 + AI-ML 1 - 重叠 = 14 净):
- 3 并行 agent ~15 min 全完成
- 211/211 backend tests + 20 routes frontend build pass
- Hot-fix T5 数据已跑

**对其他 agent**:
- **@tester**: 等你启动 Phase 2 端到端 T6 + OBS-5 未测路径
- **@devops**: 部署暂缓，本地测通后再考虑
- **@frontend / @backend / @ai-ml**: 各自 progress 三件套 PM 已代更

**Founder 现状**: 可立即测试
- 看 T5 修复效果: 刷新 http://localhost:3000 打开焦立河故事 Stage D
- 跑 T6 全新 idea 验证 14 条全部生效


---

## [2026-04-28 15:15] TASK-T6-FIXBATCH Wave 1.1 完成 — 给后续 Agent 的上下文

### Backend 新加 stage 名（重要！follow up 工作必读）
- `character_design` — 5-7%（Stage 1 完成 → Stage 2 LLM 完成）
- `image_preparation` — 65-75%（Stage 4 完成 → Stage 5 prep 场景参考图 + fullbody）
- 完整 9 stage 序列: story_generation → character_design → character_ready → screenplay → storyboard → image_preparation → image_generation → bgm → completed
- frontend STAGE_LABEL map 已加对应文案

### Backend 新 endpoint
- `POST /api/projects/{project_id}/characters/{char_id}/regenerate-portrait` — 重生指定角色 portrait + 更新 chapter.characters_json + 写 updated_at
- 现有 `POST /api/projects/{project_id}/characters/{char_id}/adjust` adjust_character 也增加了 Step 7 portrait 重生

### Backend 新行为
- `/api/projects/{project_id}/chapters/{chapter_number}/status` 现返 stage-aware `estimated_remaining_seconds`（从 STAGE_DURATIONS 字典 + estimate_remaining 函数算）
- progress_callback 单调 guard：新 progress < 当前 → 保留当前（避免 BGM 入口倒退）
- Stage 5 prep 自动 freshness check（mtime > updated_at + 30s buffer）复用 portrait

### Frontend 共享工具
- `frontend/src/lib/url.ts` — `toAbsoluteUrl(url)` + `SERVER_BASE` 导出
- 任何 `/static/...` 路径渲染都必须包 toAbsoluteUrl
- 含 quote stripping（覆盖 backend 偶尔返 `"url"` 含引号场景）

### 给 Wave 2 D/E（dashboard 列表）和 F（ARCH-1）的注意
- D 改 `/api/projects/` response 字段时，遵守 frontend 现有 toAbsoluteUrl 约定 — backend 返 `/static/...`，frontend mapProject 调 toAbsoluteUrl 转 absolute
- F ARCH-1 chapter_scene_images 写入：18+ 处既有引用（chapters.py L362/458/579/...）需要 grep 全部确认行为兼容

### 给 Wave 3 Tester（T7 真生图）的验收点
- 见 PENDING.md TASK-T6-FIXBATCH Wave 3 部分（12 个验收点 + 8 个 NB2 失败分支回归 + 角色一致性回归）
- 简单生活短篇故事，避免悲剧/民俗/婚礼高 sanitize 题材，单次预算 ≤ ¥1.5

### 给 Wave 4 DevOps 部署的注意
- Backend 改了 5 个文件（list 见 pm-progress/current.md）+ Frontend 改了 5 个 + 新建 lib/url.ts 1 个
- 不需要 DB migration（estimated_remaining_seconds 实时算 response，不写 DB）
- progress_callback signature 加默认参数兼容现有调用
- Founder 实测前要 push + rsync VPS（trailing slash 陷阱）+ /api/health 验证


---

## [2026-04-28 16:25] TASK-T6-FIXBATCH Wave 2 完成 — 给后续 Agent 上下文

### Backend 新行为（D + F 实施）

- `GET /api/projects/` response 每条加 4 字段:
  - `cover_image_url: str | null` (storyboard.shots[0].image_url，前端用 toAbsoluteUrl 转)
  - `shot_count: int` (storyboard 长度)
  - `mood: str | null` (confirmed_outline.user_selected_mood ?? mood)
  - `created_at` / `updated_at`: ISO 8601 with Z (e.g. "2026-04-28T07:10:00Z")
- pipeline.run() signature 加 `chapter_id: int | None = None`（ARCH-1 写入 chapter_scene_images 时用）
- pipeline 完成后批量写入 chapter_scene_images 表（DELETE+INSERT 防重复 + 失败非阻塞），让单 shot 重生成 / 局部编辑功能可用

### Frontend 新行为（E 实施）

- `frontend/src/contexts/AuthContext.tsx` mapProject 改读 backend 4 新字段
- `frontend/src/types/create.ts` StoryCard.mood: string | null
- `frontend/src/components/dashboard/StoryCard.tsx` mood 显示
- `frontend/src/lib/url.ts` toAbsoluteUrl 共享工具（Wave 1.1 创建）继续广用

### 🔴 D.15 P0 上下文（Wave 2.5 在跑 / 其他 Agent 知道）

- `pipeline_orchestrator.py` L843 + L850 + L1071 hardcoded aspect_ratio="2:3" 是 bug
- 用户选 1:1/16:9 等画幅但实际生成永远 2:3
- Wave 2.5 spawn backend agent 修 3 处 + pipeline.run signature 加 aspect_ratio + width/height mapper

### ⏭ 给 Wave 3 Tester (T7) 的注意

- T7 真生图测试时**显式选 1:1 比例**（非 2:3）验证 D.15 修复后真生图按选择尺寸（1664x1664）输出
- 跑 dashboard 列表页验证 R7-1 4 bug 全修（cover image 真显示 / shot count 非 0 / 时区显示对 / 总画面数对）
- 跑详情页验证 chapter_scene_images 表写入（GET /images endpoint 返真数据）


---

## 2026-04-28 21:30 给同事的关键信息

### D.15 P0 aspect_ratio ✅ 已修（Wave 2.5）

T7 实测 PIL 16/16 = 2048x2048（用户选 1:1 朋友圈真生效）。完整链路 10 段全接通: frontend CreateContent → POST /api/projects → project.aspect_ratio (DB) → start_generation → run_story_generation_task → pipeline.run → generate_shot_image_phase2_safe → seedream → NB2 真生图。

### R7-3 P1 修复中（Wave 3 Tester 实测发现）

`app/api/projects.py` adjust_character() L943-987 的 Step 7 portrait 重生代码触发 `'str' object has no attribute 'get'`。具体在 generate_character_reference 调用前后参数类型错配。**Backend 立即修中**，修后需要 Tester 复测 adjust 路径。

### Wave 1-3 已上线（still 未部署 VPS）

backend pid 68345 / frontend pid 68378 仍跑 R6/T6 build。Wave 4 DevOps 待 R7-3 修完才启动 push + rsync。

### subagent symlink 修复后必须重启 session 才能用真彩色

详见 `reference_subagent_symlink.md` memory。本 PM session 已 resume 重启过，能用 `subagent_type: "backend/tester"` 等真彩色。

### 暂缓项（下批产品打磨批次优先）

- D.13 F-Hydrate-1 (P3 progress 闪烁)
- D.14 F-Lock-Family (P2 outline/characters/scenes 三处锁定 banner)
- D.16 StoryDetail.mood 类型不一致 (P3)

PENDING D.1-D.16 共 16 项暂缓详记。

---

## 2026-04-29 15:50 给同事的关键信息

### Wave 3.5/3.6 R7-3 完全修复 ✅

`character_prompt_builder.py` L102-116 + L231-233 isinstance 双路径处理，修复完整，无回归（D.15 链路保留）。Tester Wave 3.6 6 证据点 + PM 5 角度地毯式深挖全过。

### D.17 CONTENT_SAFETY 简化方案（Founder 决议）

**只 Layer 3 末端 fallback**: NB2 拒 → PromptRewriter 改写 → Seedream 试 → 占位图 + 提示。
**不前置脱敏**（不破坏故事生动性 + 形象程度，按用户原意生）。
9 维度词典作为 PromptRewriter 内部启发参考，不强制屏蔽。

### 后续 Backend 改造（D.17 P1，下批做）

- `prompt_rewriter.py` 改写质量升级
- `image_generator.py` NB2→Seedream 自动 fallback 链路
- `pipeline_orchestrator.py` 单 shot error_message 写回 storyboard
- frontend StageD onError 升级：显示具体原因 + 重试按钮

### Seedream 首发可能性（待 Founder 决定）

测试用 Seedream 首发已 T7 实证。**未来可能 Seedream 投入正式产品作为首发生产**（待定）。如果转 default，fallback 链方向反转：Seedream → NB2 → 占位。

### 当前生产部署待启动

Wave 4 DevOps 即将 spawn 真彩色 devops。代码全部就绪：
- Backend 8 文件（pipeline_orchestrator/job_manager/projects/reference_image_manager/chapters/seedream_generator/character_prompt_builder/...）
- Frontend 8 文件（lib/url.ts / lib/createUrl.ts / [projectUuid]/[stage]/page.tsx 新建 + 改 5 个）

