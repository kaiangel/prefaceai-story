# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 📋 当前待处理

---

### TASK-PARALLEL-M1 — 🔥 P0 图像生成并行化改造（2026-04-25 派发）

| 字段 | 内容 |
|------|------|
| **负责人** | PM 派发 → Backend 主实施 → Tester 验收 → DevOps 部署 |
| **优先级** | 🔥 P0（BP 单位经济路线图 M1 节点，最高杠杆事件） |
| **决策依据** | DEC-020（M1 工程并行化优先）|
| **完整路线图** | `.team-brain/analysis/COST_UX_ROADMAP_2026Q2.md` |
| **预计工期** | Backend 1-2 天 + Tester 0.5 天 + DevOps 部署 0.5 天 |
| **预期效果** | 20 张耗时 **13.5 min → ~4.5 min**（达 Midjourney Fast Mode 体验），成本不变 |

#### 背景

Code Forensics Agent（2026-04-25）地毯式审查发现：
- `pipeline_orchestrator.py:524-677` Stage 5 主循环**完全串行**（for + asyncio.sleep(0.5)）
- `max_concurrent_images=2`（run() 签名）和 `IMAGE_MAX_CONCURRENT=3`（config.py:32）**全是死参数**
- `image_generator.py:1475 generate_batch()` 已实现 `asyncio.Semaphore + asyncio.gather()`，**被孤立**
- 实测 20 张 = **807s ≈ 13.5 min**（PROJECT_STATUS R6 数据）

#### Backend 实施清单

**主路径修改**：
1. `pipeline_orchestrator.py:524-677` Stage 5 主循环：替换为调用现有 `image_generator.generate_batch(shots, max_concurrent=3)`
2. Haiku validator（`shot_validator.validate_shot()`）也并行化（每张图后的串行验证 → 并发 gather）
3. 保留 `asyncio.sleep(0.5)` 冷却（在 Semaphore 内部，避免突发）
4. 接入现有 `IMAGE_MAX_CONCURRENT=3` 环境变量（config.py:32），让其真正生效

**风险兜底（用户强调，必须各种情况都覆盖）**：

> NB2 高峰期 429 失败率 ~30%（Agent B 调研，2026-04 数据）。Backend 必须在并行场景下确保 Semaphore 限流 + 退避兜底覆盖**所有失败路径**：

| 失败分支 | 必须的兜底行为 | 验收测试 |
|---------|--------------|---------|
| 单张 429（限流）| `MAX_RETRIES=3` 重试，`RETRY_DELAY=2s × (attempt+1) × 2` 翻倍退避 | 模拟 1 张 429 → 重试成功 |
| 单张 CONTENT_SAFETY | 立即 break + 调 `PromptRewriter` 改写后重试（`MAX_REWRITE_ATTEMPTS=2`）| 模拟 1 张 CS → 改写后成功 |
| 单张永久失败（重试耗尽）| Shot 层 `MAX_SHOT_RETRIES=1`，最终标记失败但不阻塞其他 shot | 模拟 1 张永久失败 → 其余 19 张成功 |
| 多张并发 429 | Semaphore 控制并发 ≤ 3，自动节流 | 模拟 5 张同时 429 → 排队完成 |
| 全部失败 | Pipeline 优雅降级，job 状态正确写入 `failed`，`PipelineCostTracker` 不超 $10 熔断 | 模拟 20 张全失败 → job.status=failed |
| 部分失败（如 3 张失败 17 张成功）| 成功的 17 张正常返回，失败的 3 张占位（image_path=null + error_message），用户可在 Stage D 手动重试 | 模拟混合失败 → 前端 StageD 正确展示 |
| 网络中断 | aiohttp / google-genai SDK 内部 timeout + 重试（确认现有配置）| 模拟网络抖动 → 自愈 |
| Cancel 中途取消 | `cancelRef` 信号能正确传播到所有并发 gather，不留僵尸 task | 用户中途取消 → 所有 task 优雅停止 |

**禁止删除/修改的内容**：
- 现有 `MAX_RETRIES=3` / `RETRY_DELAY=2s` / `MAX_REWRITE_ATTEMPTS=2` / `MAX_SHOT_RETRIES=1` 重试逻辑
- 0.5s 冷却（移到 Semaphore 内部，不删）
- StyleEnforcer / 角色参考图传递链（CLAUDE.md 已强调"参考图传递链必须完整"）

#### Tester 验收清单

**性能验收**：
- [ ] 20 张实测耗时 ≤ 5 min（目标 4.5 min，留 10% buffer）
- [ ] 单张 NB2 调用峰值并发 = 3（不超 IMAGE_MAX_CONCURRENT）

**质量回归（CLAUDE.md 强制要求）**：
- [ ] 3 角色场景一致性 = **100%**（不能掉，teststory6.4 / 6.5 重跑）
- [ ] 6 角色场景一致性 ≥ **90%**（teststory6.6 重跑）
- [ ] 跨题材稳定（现代都市 / 武侠古装 / 写实 / 水墨 各跑 1 个）

**风险路径回归**：
- [ ] 上面 8 个失败分支每个都跑一次模拟测试（注入失败 → 验证兜底行为）

**集成回归**：
- [ ] 全链路 A→E 在 VPS 上跑通（不只是 Backend 单元测试）
- [ ] BgmPlayer / Stage D / 文字叠加都正常

#### DevOps 部署

- [ ] 通过后 push 到 GitHub（必须先 push，再部署 — CLAUDE.md 铁律）
- [ ] rsync 部署 VPS（注意 trailing slash 陷阱，feedback memory 已记录）
- [ ] /api/health 验证容器 healthy
- [ ] 生产环境再跑 1 次完整故事生成验证

#### PM 派发要点（避免歧义，feedback memory "任务派发必须具体化"）

- 派 Backend 时**必须**让其先读：本任务全文 + DEC-020 + COST_UX_ROADMAP_2026Q2.md L1 章节 + CLAUDE.md "角色一致性"和"代码规范"章节
- 任务**Sonnet 4.6** 即可（执行类，不需要 Opus）
- 完成后 Backend 必须更新 backend-progress 三件套（current / context-for-others / completed）
- 验收前先检查 progress 文件 modified time（PM 审查三步顺序）

---

### MVP 后 Pipeline/Frontend 细节修复批 — 💡 P2/P3（2026-04-23 TASK-BUG-FIX-BATCH-1 延出）

| # | 类别 | 描述 | 文件:行 | 优先级 |
|---|------|------|---------|------|
| 1 | Backend | 完成时 job.stage 被写成 "story_generation"，覆盖真实最后 stage（image_generation / bgm 等）| `job_manager.py:302` | P2 |
| 2 | Backend | Stage 6 BGM 生成期间没有 `progress_callback`，前端进度卡 90% 数分钟 | `pipeline_orchestrator.py:687-730` | P2 |
| 3 | Frontend | `imageUrl=null` 预览页 fallback 显示"画面生成中..."，真实失败场景会误导用户 | `StageD.tsx:186-197` | P2 |
| 4 | Frontend | BgmPlayer 显示"暂无配乐"时缺 url strip 引号 fallback（已由 BE-4 根因修复解决，但前端仍该加兜底防御）| `BgmPlayer.tsx` | P3 |
| 5 | Frontend | Shot `<img>` onError 没有占位图（SKIP 模式修复后不再触发，但真实失败场景需要）| `StageD.tsx` | P3 |
| 6 | Frontend | 进度条数字变化无过渡动画，35→65→100 跳变观感生硬 | `StageC.tsx` progress bar | P3 |

**触发条件**: MVP 正式上线前做第二轮打磨

---

### 数据层架构债 — 💡 技术债（2026-04-23 / 04-24 陆续发现）

| # | 描述 | 严重度 |
|---|------|------|
| ~~ARCH-1~~ ✅ | ~~`chapter_scene_images` 表被 18+ 处代码依赖（`chapters.py` L362/458/579/...），但 **Pipeline 完成后从不批量写入**，只有 `regenerate_single_image_task` 失败路径才写一条错误记录。导致 GET /images 永远返回空，单张重生成/局部编辑功能形同虚设~~ **已修 (2026-04-28 Wave 2 Agent F)**：pipeline_orchestrator Stage 5 完成后批量 DELETE+INSERT，job_manager 传 chapter_id | ~~P1（功能缺失）~~ ✅ |
| ARCH-2 | `project_character_references` 表完整定义（12 列），但**整个代码库 0 引用**，是死表 | P2（技术债）|
| ARCH-3 | R8 只有 10 张 shot 图，19 shots 场景需要 mod 循环（已在 2026-04-23 SKIP 分支做 mod 循环）。正式生图时无此问题 | ✅ 已临时修 |
| **ARCH-4** | **`api_cost_logs` 表全时 0 行（2026-04-24 PM 地毯式审查发现）**。代码 grep `api_cost_logs\|ApiCostLog\|INSERT.*api_cost` 在 app/ **0 命中**。schema 已定义（9 列），但没有 SQLAlchemy model 或写入路径。影响: `/api/monitoring/costs/summary` 端点永远返回 0，无法做成本熔断/追踪 | P1（观测性缺失）|

**触发条件**: ARCH-1 在"单张 shot 重新生成"或"批量编辑"功能投产前必修；ARCH-2 可等下一轮数据库清理时删表

---

### DevOps / 配置债 — 💡 P3

| # | 描述 | 文件:配置 |
|---|------|---------|
| OPS-3 | uvicorn nohup stdout 不 flush（缺 `PYTHONUNBUFFERED=1`）导致实时诊断困难，日志需 sleep 等待 buffer | docker/Dockerfile.api or env |

---

### ✅ TASK-BUG-FIX-BATCH-1 — 完成（2026-04-23）

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 完成 — PM 独立审查通过，待 @devops 部署 VPS |
| **Route B @backend** | job_manager.py checkpoint isinstance 判断 + pipeline_orchestrator SKIP 分支复制 R8 写 image_url + Stage 6 credits_used checkpoint + main.py /static/outputs mount + DB chapter id=2 清理 |
| **Route C @frontend** | FE-5 根因（StrictMode completedRef 污染）+ 修复；FE-1 STAGE_LABEL 细化；FE-2 CreateContext full-dedup；FE-3 progress 直信 backend；FE-4 stage 透传 |
| **验证** | pytest 7 passed / /health healthy / /static HTTP 200 / DB clean / npm build 0 error |

---

### 生图模型选型调研 — 💡 技术预研（2026-04-24 完成基线调研）

**调研**: R1 + R2 双 agent 完成 Top 6 深度对比，详见 TEAM_CHAT.md 2026-04-24 TASK-IMAGE-MODEL-RESEARCH

**Top 6 排名（Arena ELO 2026-04-22）**:
1. GPT Image 2 — 1,512 ★ 质量天花板
2. Nano Banana 2 — 1,264 ★ 当前默认
3. Nano Banana Pro — 1,217 ★ 摄影级
4. FLUX 2 Pro — 1,157 ★ LoRA 生态
5. Imagen 4 Ultra — 1,148 ★ 文字渲染
6. Ideogram 3.0 — N/A ★ 文字气泡专项

**最大颠覆点**: GPT Image 2 Medium $0.053/图 + Batch 折扣 $0.027/图 比 NB2 ($0.067) 便宜 **且** Arena ELO 高 248 分 + 文字渲染 99% → 2026-05 GA 后可能直接替代 NB2 作为 Pipeline 默认。

**待决策**（等 GPT Image 2 API 正式 GA）:
- A/B 测试 GPT Image 2 vs NB2 on 条漫场景（特别是文字气泡）
- 若 GPT Image 2 99% 文字准确率验证通过 → 可能**废弃 TextOverlayServiceV2**（后处理叠字）架构

**触发条件**: 2026-05 初 GPT Image 2 API 正式 GA 后 1-2 周内安排测试

---

### ✅ max_tokens=8631 魔法数字统一 — 完成（2026-04-22）

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 完成 — grep 0 代码命中 + pytest passed + /health healthy |
| **改动** | 13 处 `8631 → 16384`（5 个文件：character_designer / alignment_service / story_outline_generator L196 补齐 / storyboard_director / screenplay_writer）|
| **教训** | 首次调查汇报"14 处 + story_outline_generator 已改"不准确。PM 独立地毯式 grep 核对为 13 处 + 半改状态。Backend 本次任务已做自我纠错记录 |

---

### ✅ TASK-MUREKA-PIPELINE-INTEGRATION — 完成（2026-04-21）

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @Backend + @AI-ML + @Frontend + @DevOps + @Tester |
| **前置闸门** | ✅ TASK-HAIKU-QUOTE-EXTRACTION 通过（方案 A mixed v3.2 作为最终版）|
| **完整 TASK 文档** | `.team-brain/handoffs/TASK-MUREKA-PIPELINE-INTEGRATION.md` |
| **Wave 1 状态** | ✅ 完成 — music_hint + extract_story + ffmpeg_post_processor |
| **Wave 2 状态** | ✅ 完成 — 服务层三剑客 + Mureka E2E 跑通 |
| **Wave 3 状态** | ✅ 完成 — @backend REST API (4 端点) + @frontend BgmPlayer + StageD 集成 (build 20 路由 0 错) |
| **Wave 4 状态** | ✅ 完成 — @tester 6P/2W/1S，PM 修 style_preset→get_music_hint bug 两处，Founder 听 3 mp3 确认风格层有辨识度 |
| **VPS 部署** | ✅ 完成（PM 代执行）— commit `b998cbf` push + rsync + MUREKA_API_KEY + docker rebuild + /health healthy |
| **MVP 后 (P3)** | music_hint 在 Haiku 层效用有限、秋梨膏温暖故事金句重试、自定义 BGM 上传 |

---

### music_hint meta-prompt 层效用有限 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 可接受 — Founder 2026-04-21 实际听 3 首 BGM 确认音乐层面有风格差异）|
| **发现** | Wave 4 集成测试 @tester 跑同一年夜饭故事 × 3 风格（韩漫/水墨/赛博朋克）。Haiku 输出的 BGM prompt **几乎完全一样**，music_hint 的关键词（guqin/synth/K-drama）在 Haiku 输出里**0 命中**。但 Mureka 生成的最终 mp3 仍有可听的风格差异 |
| **根因** | 故事 narration+mood（~1500 字）完全压倒 music_hint（~25 字）。V4 哲学推 Haiku 走"身体感觉+故事 mood"，music_hint 被当作次级信息 |
| **缓解方向（未来）** | (A) 把 `{{visual_style_hint}}` 从 user prompt 搬到 system prompt 显眼位置；(B) 加规则"Music genre MUST emerge from visual_style_hint, not default to piano"；(C) 调整 prompt cache 策略（动态部分含 style_hint 放 system 前缀）|
| **触发条件** | MVP 上线后用户反馈"水墨故事配 acoustic guitar 违和"等具体问题再启动 |
| **状态** | 📝 记录 |

---

### 秋梨膏类"温暖动作性故事"金句质量重试机制 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 后，LLM 随机性决定先看实际 BGM 质量）|
| **来源** | Founder 2026-04-21（TASK-HAIKU-QUOTE-EXTRACTION 评审发现）|
| **背景** | Haiku 4.5 在"温暖家庭叙事"（如秋梨膏）故事里连续 3 次测试都偏爱挑"温情动作序列"金句（握手/带回/提着），违反 Quote Selection Protocol 反向清单第 5 条。v3 一次挑对是 outlier |
| **提议机制** | Backend 代码检测金句是否是连续动作叙述（启发式：3+ 个动词连缀 + 无独立画面意象），触发 Haiku 重试一次 |
| **触发条件** | MVP 集成完成后，实际测 BGM 音乐质量，若秋梨膏类故事 BGM 听觉质量被影响再启动 |
| **状态** | 📝 已记录，MVP 后根据实测决定 |

---

### 用户自定义 BGM 上传 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 后）|
| **来源** | Founder 2026-04-18（见 TEAM_CHAT 对 PM "还需要补的 10+ 维度" 第 10 点的决策）|
| **说明** | 用户可上传自己的 mp3 作为 BGM，跳过 Mureka 自动生成。DEC-011 之外的未来功能 |
| **触发条件** | MVP 上线后，根据用户反馈决定优先级 |
| **关联风险** | 上传版权合规性检查、mp3 格式/时长/音质约束、与 Mureka 生成流的切换 UX |
| **状态** | 📝 已记录，MVP 后讨论 |

---

### TASK-API-COST-TABLE — 🔄 @Backend api_cost_logs 建表 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @Backend |
| **来源** | Coordinator 指令 (2026-04-13) |
| **说明** | 在 Aliyun 共享 MySQL 中创建 `api_cost_logs` 表，用于追踪 API 调用成本。表结构需记录：project_id、stage（1-5）、model、input_tokens、output_tokens、cost_usd、created_at |
| **状态** | 🔄 进行中（Background Agent 运行中） |

---

### Resonance 新时间线 — 📝 待 Founder 重新定义

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **指派** | @Resonance（等 Founder 指示后启动） |
| **来源** | 原时间线（500+ 申请）已作废 (2026-03-23)，正式内测启动时间待 Founder 通知 |
| **说明** | Resonance 主战场：抖音"一话故事" → 小红书 → B站。预算：常规 2-3k/月，高 ROI 可提至 20k/月。等 Founder 确认内测启动时间后重新制定具体执行方案 |
| **状态** | 📝 暂缓，待 Founder 重新定义时间线 |

---

### 续写模式 Phase 3 #11 — 📝 待 Founder 决定是否开始设计

| 字段 | 内容 |
|------|------|
| **优先级** | P2（暂缓） |
| **指派** | 待 Founder 决策后再派发 |
| **来源** | 产品路线图 Phase 3 第 11 个功能点 |
| **说明** | 用户在 Stage D 预览完成后可选择"续写"，系统基于当前故事状态继续生成下一集/后续情节。涉及：历史上下文传递、角色记忆、Story Continuation API 设计 |
| **状态** | 📝 等待 Founder 决定是否进入设计阶段 |

---

### 监控告警系统 R4 — 📝 @DevOps 待启动 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @DevOps |
| **来源** | Harness V2 Engineering 计划（DEC-015）中的 R4 监控组件 |
| **说明** | VPS + Pipeline 监控告警系统：① 修复外部 `/api/health` 端点 404 问题（Nginx 路由前缀）② 配置 Uptime Robot 或 Grafana 告警 ③ 6 个 EP Sensor 端点整合进监控看板 |
| **前置** | Harness V2 Phase 1-3 已全部完成 (2026-04-15) |
| **状态** | 📝 已计划，待 DevOps 启动 |

---

### TTS Key 填入 — 🔄 @DevOps 执行中

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @DevOps |
| **来源** | Coordinator 指令 (2026-04-13) |
| **说明** | 火山引擎 TTS（Doubao）配置：将剩余 TTS Key 填入 VPS 环境变量。当前状态：4/6 Key 已配置，需补全 VOLCENGINE_TTS_APPID 等剩余项 |
| **状态** | 🔄 Background Agent 执行中（adda04757d96a67bd） |

---

### TASK-STYLE-EXPANSION — 📝 暂缓 (P1，备忘)

| 字段 | 内容 |
|------|------|
| **优先级** | P1（暂缓） |
| **说明** | 从剩余 80 种风格中筛选适合普通用户的上架风格（预计 25-35 种），补写 StyleEnforcer 规则 + 生成缩略图 |
| **前置** | TASK-STYLE-THUMBNAILS 15 张通过后再启动 |
| **背景** | style_config.py 有 95 种风格，当前仅 15 种有 enforcer 规则并上架 |
| **状态** | 📝 已记录，暂缓 |

---

## ✅ 已归档交接（全部完成）

### 2026-04 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-HARNESS-V2** | **Harness V2 Engineering：GitHub Actions CI + Schema 验证 + $10 成本熔断 + 6 EP Sensor + 监控端点，3 Phase 全完成，VPS PASS** | **2026-04-15** ✅ |
| **TASK-PROMPT-B-DEFAULT** | **Prompt B' 格式设为默认（-46% tokens，盲测 5:4 Founder 偏好），全 VPS 部署** | **2026-04-15** ✅ |
| **TASK-STAGE-D-PRODUCT** | **Stage D 产品逻辑：调整画面（Haiku 重写 image_prompt）+ 编辑文字（编辑 chinese_text）+ 重新生成（re-roll）** | **2026-04-14** ✅ |
| **TASK-PIPELINE-UX-CONNECT** | **Pipeline 前端接通真实 API 轮询（每 2s）+ character_ready 检查点 + 真实用户确认等待** | **2026-04-07** ✅ |
| **TASK-PIPELINE-OPT-R6** | **Pipeline 优化 R1→R6：批处理 + 并行 + 进度显示 + 角色确认检查点，R6 Founder 实测 807s/20shots/零错误** | **2026-04-06** ✅ |
| **TASK-HARNESS-V1** | **Harness V1：PostToolUse pyright/tsc hooks + PreCommit 架构测试 + PrePush 全量测试** | **2026-04-05** ✅ |
| **TASK-DB-LONGTEXT** | **DB 迁移：所有 TEXT→LONGTEXT + characters_confirmed 新列 + pool_recycle 修复** | **2026-04-04** ✅ |
| **TASK-PLOTPOINT-REORDER-FIX** | **情节拖拽元数据跟随修复，Frontend+Backend+Tester 并行，39/39 PASS** | **2026-04-03** ✅ |
| **TASK-CONFIRM-OUTLINE-WIRE** | **StageB confirm-outline 接通 Pipeline（前端调 confirm-outline + start-generation，后端用 confirmed outline 跳过 Stage 1），39/39 PASS** | **2026-04-03** ✅ |
| **TASK-JSON-REPAIR-V3** | **JSON 修复状态机 V3（`_fix_unescaped_quotes()` 正则→状态机，24/24 PASS），4a/4b/4c 修复，VPS 部署** | **2026-04-01** ✅ |
| **TASK-UPLOADER-ENV-FIX** | **5 个 Uploader 环境变量统一修复（NEXT_PUBLIC_API_BASE_URL → NEXT_PUBLIC_API_URL），VPS 部署** | **2026-04-01** ✅ |

### 2026-03 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **T29-T37 全周期** | **R6/R7/R8/T-A~T-K/T11~T28 全系列修复（对话系统+shot质量+角色一致性+气泡+回归测试）** | **2026-03-17** ✅ |
| **TASK-DEPLOY-CLEANUP** | **DevOps 部署 R8B + CLEANUP（rsync + Docker rebuild）** | **2026-03-17** ✅ |
| **TASK-BRAND-MANIFESTO** | **品牌宣言 V2 整合 Pipeline 模块 + About 页重写，Founder 终审通过** | **2026-03-17** ✅ |
| **TASK-STYLE-THUMBNAILS** | **15 张风格缩略图生成 + 压缩集成（1024×1024→400×400 JPEG, 27MB→1MB）** | **2026-03-10** ✅ |
| **TASK-LOGO-REPLACE** | **Header/SubPageHeader/CreateHeader/Footer Sparkles→新 logo，VPS 部署** | **2026-03-16** ✅ |
| **TASK-GIT-PUSH-DUAL-TEAM** | **Git push 59 文件（commit 33eaac6），双团队工作流建立** | **2026-03-19** ✅ |

### 2026-02 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-PROMPT-BUBBLE 全周期** | **TASK-PROMPT-BUBBLE + FOLLOWUP + FOLLOWUP-R2 + BUBBLE-SPEAKER-FORMAT-DEPLOY（气泡对话嵌入 + speaker_format=english）** | **2026-03-06** ✅ |
| **TASK-DEPLOY-PREP** | **VPS + Docker + SSL + Nginx 全部完成，VPS 已上线 prefaceai.mov** | **2026-03-06** ✅ |
| **TASK-F1-F5-FIX 全周期** | **T1-T28 全系列修复 + R4/R5/R6 E2E 验证 + PM 独立复核** | **2026-03-09~14** ✅ |
| **TASK-SHOT-QUALITY-UPGRADE** | **SQ-1~SQ-8 全部完成 + 回归验证 4.36/5 + Bug #5 修复，TASK-GIT-COMMIT-3** | **2026-03-05** ✅ |
| **TASK-STYLE-DESC-REWRITE** | **14 个风格场域式改写，Step 1-4 闭环，Founder 批准为默认策略** | **2026-03-04** ✅ |
| **TASK-E2E-REGRESSION 全周期** | **R2/R3/R4/R5/R6 E2E + F1-F5 深挖 + 平台级改进 T17-T22 + T23-T28** | **2026-03-09~14** ✅ |
| **TASK-NB2-SWITCH** | **NB2 模型切换（gemini-3.1-flash-image-preview），5/5 shots PASS** | **2026-02-27** ✅ |
| **TASK-DIALOGUE-SYSTEM** | **对话系统三层重构（dialogue≥60% 规则），Backend L1 + AI-ML L2+L3** | **2026-02-27** ✅ |
| **TASK-NB2-NATIVE-TEXT** | **NB2 原生文字渲染切换（speaker_format=english），PM Review PASS** | **2026-02-28** ✅ |
| **TASK-CREATE-UPGRADE** | **Frontend P0+P1+P2 全部完成（注册页+工作台+故事详情+StoryCard 等），PM 复验 4.8/5** | **2026-03-03** ✅ |
| **TASK-GIT-COMMIT-2** | **Git 提交 12 天积压变更（3批：926f284+825aece+e05bbd2，67 文件）** | **2026-02-24** ✅ |
| **TASK-SCENE-REF-ASPECT** | **场景参考图宽高比修复 16:9→2:3（DEC-010）** | **2026-02-24** ✅ |
| **TASK-MODEL-UPGRADE** | **7 个服务文件模型全面升级（主力 Sonnet 4.6，备用 Gemini 3 Pro）** | **2026-02-26** ✅ |
| **TASK-STYLE-SLAMDUNK** | **StyleEnforcer 新建 slam_dunk 风格预设（DEC-012）** | **2026-02-26** ✅ |
| **TASK-E2E-TEST-2** | **Slam Dunk + Sonnet 4.6 完整 E2E 测试，PM 复核通过** | **2026-02-27** ✅ |
| **TASK-UI-STAGE-A** | **Stage A 输入界面（故事文本框+篇幅卡片+风格卡片），PM 复验 4.5/5** | **2026-02-26** ✅ |

### 2026-01 及更早

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-LP-PAGES-FIX** | **LP 子页面 4 项修复（PM 复验 4.8/5）** | **2026-02-14** ✅ |
| **TASK-ASPECT-2x3** | **宽高比统一改为 2:3（9 文件 26 处，PM 核验通过）** | **2026-02-14** ✅ |
| **TASK-LP-POLISH** | **Landing Page 2 项代码质量修复（5.0/5）** | **2026-02-12** ✅ |
| **TASK-LP-FIX** | **Landing Page 8 项修复（4.5/5）** | **2026-02-12** ✅ |
| **TASK-GIT-COMMIT** | **Git 提交 LP 修改（a6a0359+08a0e9f，PM 核验通过）** | **2026-02-12** ✅ |
| **HANDOFF-2026-02-12-001** | **TASK-GIT-INIT Git 仓库初始化** | **2026-02-12** ✅ |
| HANDOFF-2026-02-03-001 | Backend 架构重构+核心修复 | 2026-02-03 |
| HANDOFF-2026-02-02-015 | P1 修复（碰撞检测+气泡） | 2026-02-02 |
| HANDOFF-2026-02-02-013 | P0 修复（Speaker 前缀+气泡位置） | 2026-02-02 |
| HANDOFF-2026-01-31-012 | 配置调整 | 2026-01-31 |
| HANDOFF-2026-01-30-011 | 42 张测试脚本 | 2026-01-30 |
| HANDOFF-2026-01-29-010 | Landing Page 交接 | 2026-01-29 |
| HANDOFF-2026-01-22-009 | 条漫完整故事测试 | 2026-01-22 |

---

### TASK-PARALLEL-M1 进度更新 (2026-04-25 16:10)

- ✅ Phase 0 (TASK-RATELIMIT-RESEARCH): max_concurrent=3 安全性确认。报告 `.team-brain/analysis/RATELIMIT_RESEARCH_2026-04-25.md`
- 🟡 Phase 1 (实施): 代码 24/24 测试通过附 3 隐忧（conftest stub / project_id graceful skip / 文档未更新）
- 🔄 Phase 1 round 2: Backend 修隐忧
- ⏸ Phase 2 (Tester): 等 round 2 完成
- ⏸ Phase 3 (DevOps): 等 Phase 2 通过


---

### TASK-PARALLEL-M1 进度更新 (2026-04-27)

- ✅ Phase 0 (RATELIMIT-RESEARCH): max_concurrent=3 安全
- ✅ Phase 1 (实施): 24/24 unit test，pytest 真实 venv
- ✅ Phase 1 round 2 (3 隐忧修): conftest 删 / project_id 映射 / 文档 OK
- ✅ Phase 2 D1 round 1 (旧代码): 暴露 4 production bug (project_id=None / Validator 鉴权 / IncompleteRead / Event loop)
- ✅ Phase 1 round 3 (4 bug 修): pytest 24/24，Bug 2 完全修，Bug 1+4 partial
- ✅ Phase 2 D1 redo: 14/14 全过 8 故事，¥34.3 实花
- 🔄 **Phase 1 round 4 派发 (2026-04-27)**: 修 Bug 1 (1 行 dispatcher) + Bug 5 (图压缩 < 5MB)
- ⏸ Founder 本地+域名测试: round 4 完成后启动
- ⏸ Phase 3 (DevOps 部署): 暂缓，等 Founder 测试通过

### 🆕 Bug 5 (2026-04-25 D1 redo 发现)

ShotValidator 调 Anthropic Claude API 时部分 Seedream PNG 输出超 5MB 上限触发 fail-open。需要图压缩（resize / quality 降低）到 < 5MB 后传 Claude。Round 4 范围内修。


### TASK-PARALLEL-M1 round 4 ✅ 完成 (2026-04-27 11:20 PM 审查通过)

- ✅ Bug 1 dispatcher 1 行修 (image_generator.py L1399 `**_kwargs_copy`)，DB 实证 id 167-181 全 None vs id 182-197 全 12 (integer)
- ✅ Bug 5 ShotValidator 5MB 图压缩路径就位 (shot_validator.py `_compress_for_claude` 渐进 quality+resize)
- pytest 24/24 真实 venv 通过，¥3.5 实证成本

**5 Bug 最终全部解决** (除了 4b aiomysql GC cleanup cosmetic noise，已记入 ERROR_PATTERNS.md EP-017，**留着不修**)

⏸ Founder 本地 + 域名测试 → 决定 Phase 3 部署 VPS


---

### 🆕 MVP 前必修 P1 — UX 改进 2 项 (2026-04-27 Founder 测试 T5 发现)

#### UX-1: Stage C 角色预览盲调（无图调外观）— 修复方案确认

**Founder 04-27 提问**: Stage 2 提前生 portrait 数据/描述/prompt 够不够？

**PM 答**: ✅ 数据充足。Stage 2 LLM 输出的 characters_json 含完整 visual description (name/age/gender/role/详细面部+服装描述)，等同于 Stage 5 现在生 portrait 时的输入。技术上 Stage 2 后立即调 reference_image_manager 生 portrait 完全可行。fullbody 涉及完整服装/姿态/场景上下文，仍可放 Stage 5（依赖 storyboard 信息）。

**修复方案 (确认 A)**: Stage 2 LLM 完成后立即调 Seedream/NB2 生 portrait（每角色 1 张，3 角色 ~¥0.66），让 Stage C 用真 portrait 做卡片。fullbody 仍 Stage 5 生

**现象**: Stage C 角色预览页只展示 LLM 文字描述 + 占位"播放按钮"图标，没有真实 portrait 图。用户面对"换发色 / 换服装 / 更年轻 / 更成熟 / 换风格"按钮无法目测判断，只能盲调文字。

**根因**: Pipeline 设计将 character_refs（portrait + fullbody）放到 Stage 5 一起生（与 scene_refs + shot images 并列）。Stage C 只是 LLM 角色描述确认 checkpoint。

**影响**:
- 用户体验差：盲调外观，反复 try-and-error
- "换发色"等按钮的点击预期与实际行为不一致（用户期望看到图变化，实际只是改文字描述）
- MVP 上线后用户大概率投诉

**修复方案**:
- **方案 A（推荐）**: Stage 2 LLM 角色设计完成后**同时生 portrait**（每角色 1 张 portrait，约 ¥0.66/3 角色），让 Stage C 真有图可看可调。fullbody 仍延后到 Stage 5（因为 fullbody 跟场景/服装强耦合，前置生意义不大）。
- **方案 B**: 砍掉 Stage C 的"换发色 / 换服装"等按钮，UI 改成纯文字调整入口（更诚实，但功能阉割）。

**触发条件**: MVP 前必修 P1（用户体验关键路径）。建议方案 A。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 2 后段、`app/services/character_designer.py`、`frontend/src/components/StageC.tsx`、`reference_image_manager.py`

---

#### UX-2: 故事内部数字一致性问题（**升级 P1，多处 LLM 漂移**）

**现象**: Stage B 大纲编辑页用户改 Plot 1 的关键数字（"二十八对" → "三十二对"），但 Plot 7 末句仍是"烧掉了那本统计**二十八对**新人的小本子"。系统不提示，confirm-outline 后 Stage 3-4 LLM 直接继承这个内部矛盾。

**根因**: confirm-outline 端点只校验 schema（角色数 / 情节点数 / 场景数），不做"语义一致性"检查。LLM 也不会主动跨 plot 比对数字 / 名字 / 时间。

**影响**:
- 用户编辑后下游 LLM 沿用矛盾数据
- Stage D 单镜头编辑可修，但用户得自己挑出错的 shot
- 故事内部的关键数字 / 角色名 / 时间线如果不一致，质量打折

**修复方案**:
- **方案 A（推荐）**: 前端 Stage B 加"前一致性提示"：用户改 Plot N 时若该 plot 有数字 / 角色名出现，前端 highlight 其他 plot 里同样的数字 / 名字让用户检查。**纯前端实现，零后端成本**。
- **方案 B**: 后端 confirm-outline 时跑一次"内部一致性 LLM 检查"（Sonnet 4.6 一次调用，~¥0.05），返警告给前端展示。
- **方案 C**: Stage 3 剧本生成 prompt 里加一段"主动检测 outline 内部矛盾并修正"（最小代码改动，但效果不可控）。

**触发条件**: MVP 前必修 P1。推荐方案 A 优先实施（成本最低 + 用户主导决定要不要改）+ B 兜底（如果用户不仔细看也能挽救）。

**关联文件**: `frontend/src/components/StageB.tsx` (前端校验)、`app/api/projects.py` confirm-outline 端点 (后端校验)、`app/services/screenplay_writer.py` Stage 3 prompt 微调

---


#### UX-3: Stage 切换时前端进度条卡帧不同步

**现象** (2026-04-27 Founder T5 测试发现): backend Stage 3 已完成 + Stage 4 进行中（DB stage_message 已是 `screenplay 35%`），但前端仍显示"正在设计角色 10%"约 2 分钟没变化。视觉上像卡死。

**根因**: 前端 progress polling 频率/缓存策略问题。怀疑：
- polling interval 偏大（如 5s+ 才能看到下一次更新）
- 或 React state 没正确响应 backend stage 切换
- 或 stage_message vs current_stage 不同步显示

**影响**: 用户以为卡死，可能误操作（点取消 / 刷新）

**修复方案**: 排查 `frontend/src/hooks/useGenerationStatus.ts`（或类似）poll 逻辑，确保 stage_message 变化即刻反映到 UI。Polling 间隔建议 ≤ 2s（已是 backend 卡帧节奏）。

**触发条件**: MVP 前 P1。

**关联文件**: 前端 progress polling hook / StageC.tsx / StageD.tsx wait 页


#### ~~UX-4: 等待页 milestone 列表只显示一条不追加~~ — ❌ PM 误判已纠正 (2026-04-27 15:18)

**现象** (2026-04-27 Founder T5 测试发现): Stage 等待页底部绿色 ✓ "已完成里程碑"框只显示 character_ready 那一条 "角色设计完成，请确认角色和场景"。Stage 推进到 screenplay / storyboard 后**没有追加新里程碑**（如 "剧本生成完成"、"分镜生成完成"）。

**理想设计**:
```
✓ 大纲生成完成
✓ 角色设计完成，请确认角色和场景
✓ 剧本生成完成
✓ 分镜生成完成
🔄 正在生成画面 N/18
```

**实际**: 只看到 character_ready 那条 ✓，其他 milestone 没出现。

**根因**: 前端 milestone 列表组件可能只订阅了 character_ready 信号或只在初次 stage_message 变更时插入一条，后续 progress_callback 没被正确累计。

**影响**: 用户看不到后端实际有在推进，体感像卡住

**修复方案**: 排查前端 milestone list 累加逻辑（每次 stage_message 变化都 push 一条新记录到列表，去重 by stage_message 字符串）

**触发条件**: ❌ PM 误判，撤销。实际 milestone 列表按 stage 完成事件正常追加。10% 那时只完成 character_ready 1 个事件，所以只显示 1 条；后续 stage 完成后正常追加 ✓ 剧本编写完成等。**不是 bug**

**关联文件**: 前端 wait page milestone list 组件 / `useGenerationStatus.ts`


#### ~~UX-5: StoryboardDirector batch 完成无 progress_callback~~ — ❌ PM 误判已修正 (2026-04-27 15:21): 实际 backend 在每个 scene 完成时**有** progress_callback。Founder 截图证实 milestone 追加正常 (Scene 1/7→2/7→3/7)。真正问题是 UX-6（ETA 算法低估 Stage 4 实际耗时）

**现象** (2026-04-27 Founder T5 测试发现): Stage 4 StoryboardDirector 按 7 个 scene 分批跑（每批 Sonnet 调用 ~40-50s），但**每个 batch 完成时没 progress_callback** 推进 chapter_generation_jobs.progress 字段。仅在 Stage 4 启动时打了一次 progress=39 / message="分镜生成中 (Scene 1/7)..."。结果：跑 5/7 batch 时前端看到的 progress 仍是 39%，message 仍是 "Scene 1/7"，体感卡死。

**修复方案**: `app/services/storyboard_director.py` 在每个 scene batch 完成时调 `progress_callback("storyboard", 39 + (batch_idx / total_batches) × 11, f"分镜生成中 (Scene {batch_idx+1}/{total_batches})...")` 让进度从 39% 平滑推进到 50%。

**关联文件**: `app/services/storyboard_director.py`、`app/services/pipeline_orchestrator.py` Stage 4 调用上下文

**触发条件**: MVP 前 P1（与 UX-3 一起一轮改透前端 wait page + backend stage 进度细化）

#### UX-6: 前端 ETA 在 progress 卡死时无 fallback

**现象**: 当 backend progress 字段长时间不变化（如 1+ min），前端 ETA 公式 `(elapsed / progress) × (1 - progress)` 算出来越来越长（9 → 10 → 11 min），让用户以为越跑越慢。

**修复方案**:
- 方案 A：检测 progress 卡死 30s 不动时，ETA 锁定为最后一次正常计算值（不再增长）。
- 方案 B：ETA 算法换成"按 stage avg time × 剩余 stage 数"，不依赖 progress 字段。
- 方案 C：进度卡死时显示"~"代替具体数字。

**关联文件**: 前端 wait page ETA 计算代码

**触发条件**: MVP 前 P1（独立解决 backend 不修也能改善 UX）


#### UX-7: 整体 ETA 算法需要彻底重做（汇总 UX-3 / UX-6）

**Founder 04-27 T5 测试观察记录**:
```
开始 (Stage 2)         13 min
character_ready 后     20 min  ← 增加（用户阅读时间补进去）
Stage 3 中段           8 min   ← 减少
Stage 3 完成 / Stage 4 启动  9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 min  ← 持续上涨 (Stage 4 实际比估算久)
Stage 4 完成 / Stage 5 启动  6 min   ← 跳到 6 min（Stage 5 启动估算重置）
Stage 5 跑了一会儿        7 min   ← 又开始上涨
```

**核心问题**:
- ETA 没有"全局一致性"，每次 stage 切换重新估算导致跳跃
- ETA 在同 stage 内只单向增长（progress 不动 + elapsed 涨 → ETA 涨），不会因临近完成而稳定下降
- 给用户的体感是"越等越久"而不是"接近完成"，违反用户对加载条的直觉

**应有的体感（重做目标）**:
- ETA 单调下降为主（小幅修正可以，大幅跳变不行）
- 接近 100% 时 ETA 趋近 0
- stage 切换不应让 ETA 跳变（应该是 ETA 持续平滑过渡）

**修复方案选项**:

**方案 A（推荐）**: 后端不再返 estimated_seconds，前端按"基线时间表 + 进度倒推"算
- 维护一份 baseline 时间表（按故事 shot 数 × 每 shot ~1.5 min × stage 权重）
- 前端 ETA = baseline_total × (1 - progress) — 永远跟随 progress 单调下降
- 异常超时时显示"实际比预期久，可能因网络/API 拥堵"提示而不是数字

**方案 B**: 后端按 stage avg 时间累计（不依赖 progress）
- baseline: Stage 1 ~30s, Stage 2 ~2-3 min, Stage 3 ~3-4 min, Stage 4 ~5-6 min, Stage 5 ~6-10 min, Stage 6 ~1-2 min
- ETA = sum(剩余 stage 的 baseline)
- progress 只用于动画，不参与 ETA 计算

**方案 C（最严谨）**: 历史数据驱动
- 收集 100+ 真实生成数据，按 (shots, character count, scene count, style) 维度建估算模型
- 后端启动时按模型预测，运行中按实际耗时校准
- 工程量大，MVP 后做

**临时缓解（MVP 前必做）**:
- 前端 ETA 算法加 monotonicity guard：新 ETA 不允许大于 (旧 ETA - 1.5 × poll interval)
- 也就是说 ETA 至少要按 polling 频率单调下降，杜绝"涨数字"现象
- 即使后端 estimated_seconds 跳变，前端只取下降值

**触发条件**: MVP 前 P1（用户体验关键路径，影响留存）

**关联文件**: 前端 progress polling hook (ETA 计算) / `app/services/pipeline_orchestrator.py` estimated_seconds 字段写入逻辑

**取代/合并**: UX-3 / UX-6 都归入此条统一处理


#### UX-8: 等待页文案 "图像" → "片段"

**现象** (2026-04-27 Founder T5 测试反馈): Stage 5 等待页文案是"已生成 N/18 张图像..."，应改成"已生成 N/18 个片段..."。"图像"对内（开发视角）正确但对用户体感不友好；"片段"更贴合用户心智模型（每张 shot 是叙事片段，不是单纯的图像）。

**修复**: 前端 wait page 文案微调。

**关联文件**: 前端 progress message 显示组件 / `useGenerationStatus.ts` / 后端 `pipeline_orchestrator.py` 中的 `progress_callback("image_generation", X, "已生成 N/M 张图像...")` — 看是后端写死还是前端 i18n 决定改哪边。

**触发条件**: MVP 前 P2（用户体验微调）


#### UX-9: 等待页大标题永远是"正在编写剧本"，不随 stage 变化

**现象** (2026-04-27 Founder T5 测试发现): 不管 backend 进入哪个 stage（screenplay / storyboard / image_generation / completed），等待页大标题都显示"正在编写剧本"。即使 progress=100% / 故事生成完成! / 已生成 18/18 — 标题仍是"正在编写剧本"。

**截图证据**: 100% + "故事生成完成!" + 已生成 18/18 张图像，但顶部大字依然 "正在编写剧本"

**根因**: 前端标题映射可能只在 stage_message 第一次为 "screenplay" 时设置，后续不再更新。或标题逻辑只读 stage 第一次值后缓存了。

**应有行为** (按 stage 切换):
- story_generation: "正在生成故事大纲"
- character_design: "正在设计角色"
- screenplay: "正在编写剧本"
- storyboard: "正在创建分镜"
- image_generation: "正在绘制画面"
- bgm: "正在生成配乐"
- completed: "故事生成完成"

**修复**: 前端 wait page 标题做成纯函数 `getStageTitle(current_stage)`，每次 polling 拉到的 current_stage 都重新映射，不缓存。

**关联文件**: 前端 wait page 组件（StageC/StageD wait 页 / `useGenerationStatus.ts`）

**触发条件**: MVP 前 P1（直接误导用户感知，明显 bug）


#### BE-3 🔴 **CRITICAL P0**: Stage 5 真生图后未写 image_url 到 storyboard JSON

**现象** (2026-04-27 Founder T5 测试发现): Pipeline 完成后 Stage D 预览页**所有 shot 图加载失败**，img alt 显示 "Shot 12" 占位。

**实证**:
```
disk:  output/{uuid}/images/shot_01-18.png ✅ 全部存在
4_storyboard.json: shots[*].image_url = MISSING (全部缺字段) ❌
```

**根因**: Stage 5 真生图分支**没把 image_url 写回 storyboard.shots[*]**。Round 1 修过 SKIP_IMAGE_GENERATION=true 分支的 image_url 写回（pipeline_orchestrator.py SKIP 分支复制 R8 写 image_url），但**真生图分支（IMAGE_GEN_PROVIDER=seedream + SKIP=false）的对应写回逻辑缺失**。

**影响**: **MVP 阻断 bug**。所有用户跑完 pipeline 看不到任何图。

**修复**: `app/services/pipeline_orchestrator.py` Stage 5 主循环（已并行化）中每张 shot 完成后写 `shot["image_url"] = f"/static/outputs/{project_uuid}/images/shot_{NN}.png"` 回 storyboard 字典，最终保存到 4_storyboard.json + chapter.storyboard_json DB 字段。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 5 image generation 完成后的 storyboard update + checkpoint_callback 写 chapter.storyboard_json

**触发条件**: 立即修（P0）— MVP 必修阻断点


#### UX-10: Stage 6 BGM 生成期间无任何 UI 提示

**现象** (2026-04-27 Founder T5 测试发现): Stage 5 18/18 张图完成后，Stage 6 Mureka BGM 生成阶段（~1-2 min）UI 完全没提示"正在生成配乐"。前端进度卡 100% / 文案"故事生成完成!" / 标题仍是"正在编写剧本"，用户以为已结束但实际还在跑 BGM。

**根因**: 已知问题（PENDING 早期记录），Stage 6 BGM 缺 progress_callback。Pipeline 主循环 Stage 5 后直接进 Stage 6 没发 progress 信号给前端。

**修复**: `pipeline_orchestrator.py` Stage 6 启动时调 `progress_callback("bgm", 92, "正在生成配乐...")` + 完成时 `progress_callback("completed", 100, "故事生成完成!")`。

**触发条件**: MVP 前 P1（与 UX-9 一起改透 wait page stage transition）

**关联**: PENDING 早期已记 P2 Backend Stage 6 BGM 生成期间没有 progress_callback

#### UX-11: Pipeline 100% 后未自动跳转 Stage D（卡 ~2 min）

**现象** (2026-04-27 Founder T5 测试发现): Backend 15:35:31 已发 [JobManager] ✅ 生成任务完成，但前端等待页 100% 卡了 ~2 min 才自动跳到 Stage D 预览页。

**根因**: 前端 polling 拉到 `current_stage="completed"` 后没立即 redirect 到 Stage D，可能轮询频率慢或要等下一次 polling tick。

**修复**: 前端 polling 检测到 status=completed 立即 redirect，无需等下一 tick。

**触发条件**: MVP 前 P2（小延迟，但用户等了 30+ min 后这 2 min 显得格外漫长）

#### BE-4: chapter storyboard 端点 404

**现象** (Monitor 抓到): 前端调 `GET /api/projects/{uuid}/chapters/1/storyboard` 返 404 Not Found。

**根因**: 端点不存在或路径错了（可能正确路径是 `/chapters/{n}` 而不是 `/storyboard` 子资源）。

**修复**: 看 frontend 代码确认期望的 URL，对照 backend `app/api/chapters.py` 确认实际注册路径。可能加个端点 alias 或前端改 URL。

**关联文件**: `app/api/chapters.py`、`frontend/src/components/StageD.tsx` (或 fetch 逻辑处)

**触发条件**: 与 BE-3 一并修（MVP 必修）


#### UX-12: 等待页副标题"AI 正在逐张绘制画面"在 Stage 1-4 阶段误导

**现象** (2026-04-27 Founder T5 测试观察): 等待页副标题写"AI 正在逐张绘制画面，可以选择后台生成"，但 Stage 1-4 时根本没在绘制画面（在写大纲/剧本/分镜）。文案与实际不符，进 Stage 5 前都是误导。

**修复**: 副标题做成 stage 感知 — Stage 1-4 显示"AI 正在创作故事"或类似；Stage 5 显示"AI 正在逐张绘制画面"。

**触发条件**: MVP 前 P2

#### ~~UX-13: 等待页静态励志文案~~ — ❌ Founder 04-27 撤销: 这是产品文案告诉用户"中篇支持更长"，不是 bug

**现象** (2026-04-27 Founder T5 测试发现): 等待页中段轮播文案有"中篇模式支持 36 张画面" / "你知道吗？序话支持 28 种视觉风格" 等静态励志短语。但实际故事只有 18 shots（不是 36）。文案是固定励志库，没和当前故事参数绑定。

**修复**: 励志文案库要么去掉具体数字（改泛指"序话支持中长不同长度故事"），要么数字按当前故事参数动态填（"你的故事将由 18 张画面组成"）。

**触发条件**: MVP 前 P2

#### UX-14: 角色预览占位图标用"播放按钮"反直觉 — 合入 UX-1 修复

**现象** (2026-04-27 Founder T5 测试发现): Stage C 角色卡片在确认前没图，占位图标是橙色"播放按钮 ▷"。这是产品全局的图标但在角色场景里**反直觉**（用户期望看到人形 silhouette 头像占位，而不是视频播放图标）。

**修复**: 角色占位图换成人形 silhouette / 半透明头像剪影 / 灰底 + "等待生成"图标。

**触发条件**: MVP 前 P2（与 UX-1 一起改 Stage C 角色页）

#### OBS-1: Seedream 对中文叙事故事 sanitize 触发率偏高

**现象** (2026-04-27 Founder T5 测试观察): 18 shots 中至少 4 张 (shot_06/11/15/16) 触发 InputTextSensitiveContentDetected → sanitize 3 次重试。触发关键词大概率是"红色绸带" "婚礼热闹" "唢呐悲怆"等中国民俗叙事词。

**影响**: 每张被 sanitize 的 shot 增加 78s × N 重试 = +2-4 min 总耗时；额外 ¥0.22 × N 重试成本。中文古风/民俗类故事尤其多发。

**待评估**: 是否值得做"风格预审 + 提前换词"或"sanitize 字典加豫北农村婚礼相关词"先发制人。

**触发条件**: MVP 后观察实际数据再决定（本地 1 次测试样本不够）

#### OBS-2: T5 故事性能 baseline 数据

**记录** (2026-04-27 Founder T5 测试): 18-shot 中篇故事 + 铅笔素描 + Seedream + 3 并发 + 真生图模式实测：
- Stage 1 大纲: ~30s
- Stage 2 角色 LLM: ~1 min
- Stage 3 剧本: ~3 min (7 scenes × 40-50s Sonnet)
- Stage 4 分镜: ~6 min (7 scenes × 40-50s Sonnet)
- Stage 5 真生图: ~10 min (18 shots × 27s 平均 / 3 并发 + sanitize retry)
- Stage 6 BGM: ~1.5 min
- **Total: 36.9 min** (含 ~4 min 用户在 Stage C 确认时间)

**用作**: ETA 算法 baseline 参考（UX-7 修复时用） + Seedream 18-shot 实际成本 baseline (~¥6-8)。

#### OBS-3: 故事内部数字一致性问题（ idea→大纲 LLM 漂移）

**现象** (2026-04-27 Founder T5 观察): 用户输入故事 "统计了二十八对" → LLM 大纲输出 Plot 1 也是"二十八对" → 用户编辑改成"三十二对" → Plot 7 仍是"二十八对"。LLM 在 Plot 7 烧本子时**没看 Plot 1 的数字**，独立用了"二十八对"。

**根因**: Stage 1 outline LLM prompt 没强调"故事内部所有数字/名字/时间必须前后一致"。

**修复**: outline prompt 加一条规则"故事中提及的所有数字/角色名/时间点必须前后保持一致"，或后处理时跑一次自检。

**触发条件**: MVP 前 P2（与 UX-2 一致性校验配合）


#### BE-5 🔴 **CRITICAL P0**: Stage 6 BGM 生成后 bgm_url 没写回 DB（同 BE-3 一类）

**现象** (2026-04-27 Founder T5 测试发现): Stage D 预览页 BgmPlayer 显示 "已消耗 10 credits"（Mureka 真调过 API），但播放按钮按了无声、时长显示 "--:--"、当前位置 "0:00"。BgmPlayer src 为 null。

**实证**:
```
disk:  output/{uuid}/bgm_chapter0.mp3 (3.5 MB) ✅ 存在
/static URL: http://127.0.0.1:8000/static/outputs/{uuid}/bgm_chapter0.mp3 → 200 OK ✅ 可访问
chapter.bgm_url DB 字段: 未写入（推测，导致前端 src=null）
```

**根因**: Stage 6 Mureka BGM 生成完成后**没把 bgm_url 写回 chapter.bgm_url DB 字段**。Round 1 修过 SKIP 模式 + credits_used 写入，但**真生成 BGM 模式下 bgm_url 写回逻辑也缺**（与 BE-3 image_url 同模式）。

**影响**: **MVP 阻断 bug**。所有用户跑完 pipeline 听不到 BGM。

**修复**: `app/services/pipeline_orchestrator.py` Stage 6 BGM 完成后调 `checkpoint_callback("bgm_url", f"/static/outputs/{project_uuid}/bgm_chapter{N}.mp3")` 把 URL 写到 DB chapter.bgm_url。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 6 BGM 完成后 + `app/services/checkpoint_callback`

**触发条件**: 立即修（P0）— MVP 必修阻断点

**关联**: BE-3 image_url 同根因，**两个一起修**（pipeline_orchestrator Stage 5 写 image_url + Stage 6 写 bgm_url）


#### BGM-1 🔴 outline schema 缺 music_hint 字段（Wave 1 设计字段未实施或被回滚）

**现象** (2026-04-27 Founder T5 测试发现): T5 豫北农村悲伤民俗故事的 BGM 不贴切——听起来像温情怀旧 acoustic 而不是悲怆民俗（应有唢呐+二胡）。

**根因**:
- outline JSON 实际 keys: `mood, emotional_arc, narrative_pace, visual_tone, ...`
- **缺**: `music_hint` 字段（Wave 1 原设计 95 风格各对应一个 hint）
- Haiku 仅靠 `visual_style_hint=pencil_sketch` 推 BGM 风格
- "铅笔素描"传达"轻柔/怀旧/纸感" → Haiku 推成 acoustic guitar / piano，而非悲怆民俗 (应是二胡/唢呐)
- 这正是 PENDING 早期记的 P3 "music_hint 在 Haiku 层效用有限" 的实例

**实证**:
- `app/services/music_generation_service.py` Wave 4 流程完整跑通（meta_version=mixed v3.2，Haiku 747 chars，Mureka 64s succeeded）
- 但 Haiku 输入缺 music_hint 字段，导致输出 BGM prompt 偏离故事真实情绪基调

**修复方案**:
- **方案 A（推荐）**: 在 outline schema 加 `music_hint` 字段 + outline LLM prompt 强调"按风格 + mood + emotional_arc 综合给出 BGM 关键词（如『悲怆唢呐 + 二胡 + 民乐』）"。Stage 1 LLM 直接输出，story_music_extractor 透传给 Haiku。
- **方案 B**: 把 visual_style_hint 改成 `music_style_hint`（独立字段），让用户在 Stage A 选风格时**单独选 BGM 风格**（轻柔/悲怆/史诗等 6-8 种）。
- **方案 C**: 维护一份 95 风格 → music_hint 的字典（AI-ML 早期设计过），后端 Stage 1 后用 visual_style_preset 查表填 outline.music_hint。**最低成本**。

**触发条件**: MVP 前 P1（直接影响 BGM 质量，T5 实测验证 Wave 1 设计字段缺失）

**关联**: 取代 PENDING 早期 P3 "music_hint 在 Haiku 层效用有限" — 实际是字段缺失，不是效用有限

**关联文件**: `app/services/story_outline_generator.py` (outline schema + prompt) / `app/services/story_music_extractor.py` (字段读取) / 95 风格 music_hint 字典


#### ~~UX-15: Stage C 角色 adjust latency~~ — ❌ Founder 04-27 撤销: 估计是沟通间 latency，不是 bug

**现象** (2026-04-27 Founder T5 测试发现): Stage C 焦小顺卡片点"重新生成"后立即截图，描述仍显示"瘦高"（旧），但 backend 已成功改成"匀称"。Founder 等几秒后/刷新后看到正确"匀称"。前端没有立即 re-fetch + re-render。

**根因**: 前端 adjust 成功 callback 后没立即 refresh character data，依赖下一次 polling 才同步。

**修复**: adjust 成功后 immediately re-fetch character data（或 backend 返回 updated character → 前端直接用 response 数据更新 React state）。

**触发条件**: MVP 前 P2

#### OBS-4: Stage B "情绪"字段持久化路径未明

**待 Founder 确认** (2026-04-27): Founder 在 Stage B 编辑大纲时选择了情绪"至于"（疑似笔误 → 应是"释然"或某个枚举值）。但 outline JSON 里没看到 `emotional_tone` 字段（只有 `mood`, `emotional_arc`）。需要排查：
- "情绪"选择是否真传到 backend
- 持久化到 outline 的哪个字段
- Stage 6 Haiku 是否读取了这个值
- 如果是 typo，Stage B 是否应该用枚举下拉而非自由输入

**触发条件**: 与 BGM-1 一起排查（同属 outline schema 完整性问题）

#### OBS-5: 部分功能本次 T5 测试未覆盖

**未测路径** (2026-04-27 Founder T5 测试范围之外):
- Stage C "换发色 / 换服装 / 更年轻 / 更成熟 / 换风格" 5 个微调按钮的实际效果（仅测了自由输入"重新生成"）
- "后台生成，去做别的" 按钮 — 是否真能离开页面后回来继续看进度
- BgmPlayer "换一首"（5 credits）/ "重新生成"（10 credits）按钮
- Stage D 单 shot 编辑 / 重新生成 / 删除（之前 TASK-STAGED-WIRE 接通）
- "确认交付" → 下载漫画包 / 导出视频 流程

**触发条件**: MVP 前必须每条都端到端测一次（建议组合到下次 T6/T7 测试）


#### UX-2 升级补充 (2026-04-27 PM 深挖证据)

**T5 故事内部数字 3 重漂移实证**:
| 位置 | 数字 | 说明 |
|---|---|---|
| 用户原 idea | 28 对 | 输入 |
| Stage B 用户编辑 Plot 1 | **32 对** ✅ | 用户改的，Plot 1 真正生效 |
| Plot 7 LLM 没同步 | **28 对** ❌ | LLM 跨 plot 漂移（**真不一致**）|
| shot_03 chinese_text | **第 33 个叉** ✅ | Founder 04-27 纠正：32 + 即将再吹的 1 次 = 33，**叙事逻辑合理，不是漂移** |

**真实问题（PM 误判已纠正）**: 只是 Plot 1 (32) ↔ Plot 7 (28) 不一致一处。shot_03 的 33 是正确戏剧推演（"已统计 32 个，下一次吹百鸟朝凤就是第 33 个"），LLM 把握剧情数字递进逻辑没错。

**修复方案**:
- **方案 A1（前端校验）**: Stage B 用户改 Plot N 数字时高亮其他 plot 中相同数字
- **方案 A2（后端 outline 内部一致性 LLM check）**: confirm-outline 时跑 Sonnet 4.6 检测内部矛盾，Plot 1 改了 Plot 7 也跟改

**触发条件**: MVP 前 P2（降级，问题局限于 outline 内部 plot 间一致性，不涉及 Stage 3/4 LLM 数字漂移）

#### UX-11 重定义 (2026-04-27 Founder 反馈)

**Founder 答**: 100% 后卡 ~2 min 的本质是 BGM stage 完成信号没传给前端，做好 Stage 6 BGM 完成后立即 progress_callback("completed", 100, "故事生成完成") + 前端检测到立即 redirect Stage D，问题就解决。

**修复方案确认**:
- backend `pipeline_orchestrator.py` Stage 6 BGM 写完 chapter.bgm_url 后立即 `progress_callback("completed", 100, "故事生成完成")`
- 前端 polling 检测到 `current_stage="completed"` → 立即 redirect Stage D，不等下一 tick

**关联**: 与 UX-10 (BGM 期间无提示) + BE-5 (bgm_url 写回) 同一处改

#### UX-14 合入 UX-1 (2026-04-27 Founder 反馈)

**Founder 反馈**: silhouette = 人形剪影/灰底人形占位图。Founder 倾向方案 A — Stage 2 提前生真 portrait，直接用真图当 Stage C 卡片，不需要 silhouette。

**结论**: UX-14 不再需要单独修，**完全合入 UX-1**：Stage 2 提前生 portrait 后 Stage C 卡片用真 portrait（不再有占位图标问题）

#### OBS-4 升级 P1 bug (2026-04-27 PM 深挖实锤)

**Founder 04-27 反馈**: Stage B 选择的"情绪"想写的是 **"治愈"**（healing）。

**实证**: outline JSON 全文 grep "治愈" → **0 命中**。
- outline.mood = "感人"（generic 默认值）
- outline.emotional_arc = anxious_superstitious_dread → bittersweet_self_confrontation（LLM 自己定的，跟"治愈"完全不一致）
- 故事最终基调（外婆面馆 + 妻子离开 + 漫长悲怆）也跟"治愈"不沾边

**根因（推测）**:
- Stage B "情绪选择"前端控件值未传给 backend
- 或传给 backend 但被丢弃
- 或传给 outline LLM 但 LLM 用 mood/emotional_arc 自定义未读用户偏好
- 与 BGM-1 同属 "outline schema 字段缺失或不传到 LLM" 一类

**修复方案**:
- 排查 Stage B 前端"情绪"控件 → confirm-outline API 链路
- backend confirm-outline 端点是否接收并存"情绪"字段（如 emotional_tone）
- outline LLM prompt 是否注入用户选定的情绪基调
- 修通后 outline.mood / emotional_tone 字段就反映用户选择

**升级**: P1 bug（影响故事核心情绪基调，同 BGM-1 严重）

#### OBS-5 处理结论 (2026-04-27 Founder 反馈)

**Founder**: "可以修复优化更新后下一次测" — 不阻塞当前修复批次，下一次 T6/T7 测试覆盖。


---

### 🆕 TASK-T5-FIXBATCH 14 条修复全部完成 (2026-04-27 16:36)

**状态**: 🔄 修复完成 → 待 @tester Phase 2 端到端验证 + Founder 主观验收

**Phase 1 完成内容**:
| 类别 | 条目 | 修复者 |
|---|---|---|
| P0 (3) | BE-3 / BE-4 / BE-5 | @backend ✅ |
| P1 后端 | BGM-1 / OBS-4 / UX-10/11 / UX-1+14 | @backend ✅ |
| P1 前端 | UX-7 / UX-9 / UX-11(FE) / UX-1(FE) | @frontend ✅ |
| P1 AI-ML | BGM-1 字典 (95 风格) | @ai-ml ✅ |
| P2 后端 | UX-2 A2 outline 一致性 LLM check | @backend ✅ |
| P2 前端 | UX-2 A1 / UX-8 / UX-12 | @frontend ✅ |

**测试验收**:
- ✅ Backend: 211/211 unit tests (7 architecture + 17 parallel + 187 music_hint)
- ✅ Frontend: npm run build 20 routes 0 errors

**Phase 2 待启动**: @tester
- T6 全新故事端到端跑通验证 14 条修复
- OBS-5 未测路径覆盖 (5 个微调按钮 / 后台生成 / BGM 换一首/重新生成 / Stage D 单 shot 编辑 / 确认交付)


#### UX-16 ✅ Create 页 URL dynamic route — 已修复 (2026-04-28 15:06 Wave 1.2 Agent C)

**完成实现**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage 6 枚举值 (outline / characters / scenes / generating / preview / delivery)

**新建/改动文件**:
- 新建 `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` — Dynamic route 入口 + isUrlStage 校验 404
- 新建 `frontend/src/lib/createUrl.ts` — URL ↔ state 映射 + reconcileBackendVsUrl 决策树
- 改 `frontend/src/app/create/CreateContent.tsx` — hydrate hook + state↔URL 双向同步（push/replace 区分 + echo guard + completion guard）
- 改 `frontend/src/contexts/CreateContext.tsx` + `frontend/src/types/create.ts` — HYDRATE_FROM_BACKEND action

**验收**:
- ✅ npm build 21 routes 0 errors
- ✅ HTTP smoke: 6 valid stages 200, invalid 404, dashboard 不破坏
- ✅ 4 核心场景 trace: F5 刷新 / 浏览器后退 / 复制链接 / 跨 stage 切换全过

**详细完成报告**: TEAM_CHAT 2026-04-28 15:06 条目 + frontend-progress/completed.md

**已知遗留**: hydrate 后 StageC START_GENERATION reset progress 短闪 ~1.6s（轻微，下批优化）


#### UX-17 P1 Stage E 预览页右侧故事文本显示 original_idea 而非用户编辑后大纲

**现象** (2026-04-27 Founder T5 测试发现): Stage E 项目预览页右侧故事描述区域显示用户原始 idea 文本（"统计了二十八对"），即使用户在 Stage B 编辑大纲改成"三十二对"，预览页仍显示原 idea。

**实证**:
- `project.original_idea` = "...统计了二十八对..." (用户原文)
- `chapter.summary` = "《百鸟朝凤》不能给活人吹" (短标题)
- `outline.plot_points[0].content` = "...三十二对..." (用户 Stage B 改的)
- 截图右侧显示 = `project.original_idea` (含"二十八")

**根因**: Stage E 前端组件读 `project.original_idea` 字段做故事描述展示，没读用户编辑后的 `outline.summary` / `outline.confirmed_outline_json` 等综合内容.

**预期行为**: 预览页应展示**用户最终确认后的故事内容**（如 outline.summary 或 chapter.summary 详细版），不是用户灵感笔记原文.

**修复方案**:
- **方案 A**: 前端 Stage E 改读 `outline.summary` 或 `chapter.summary` (详细版) 字段
- **方案 B**: 后端在 chapter 表加 `final_synopsis` 字段（综合 plot_points + summary 的最终故事介绍），Stage 4 完成后写入. 前端读这字段
- **方案 C**: 前端用 outline.plot_points 拼接生成"故事简介"显示

**触发条件**: MVP 前 P1（用户编辑没在最终产物体现，违反"所见即所得"原则，跟 BGM-1 / OBS-4 / UX-2 同一类）

**关联文件**: `frontend/src/components/StageE.tsx` (或预览页组件) / `app/api/chapters.py` (如方案 B)



---

## TASK-T5-FIXBATCH-R5 ChapterStory Schema Hotfix ✅ 完成 (16:50)

**根因**: ChapterStory Pydantic schema 跟 chapter.scenes_json 实际字段分叉 → 41 validation errors → /chapters/{n}/story 端点 500
**修复**: app/schemas/chapter.py 删 SceneInfo / CharacterInfo, scenes/characters 改 list[dict[str, Any]]
**验证**: 211/211 pytest + /story 401 (auth) 不再 500

---

## TASK-T5-FIXBATCH-R6 Stage E dashboard 详情页 7 Bug (17:20 派发)

| Bug | 严重度 | Owner | 状态 |
|-----|:-:|:-:|:-:|
| A 故事不存在闪 10s | P0 | frontend | 派发中 |
| B shots 7 vs 18 (fetch 错 endpoint) | P0 | frontend | 派发中 |
| C 缩略图全黑 (imageUrl null hardcoded) | P0 | frontend | 派发中 |
| D summary 显示标题非大纲 | P1 | frontend + backend | 派发中 |
| E 情绪基调硬编"待生成" | P1 | frontend + backend | 派发中 |
| F 角色无 portrait | P1 | frontend | 派发中 |
| G 无 BGM player | P2 | frontend | 派发中 |

**串行派发**: backend (5-8 min) → frontend (20-25 min)

**关联文件**:
- backend: `app/schemas/project.py` + `app/api/projects.py`
- frontend: `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` + `frontend/src/types/create.ts`



---

## TASK-T5-FIXBATCH-R7 候选 (2026-04-27 21:00 PM 深度诊断)

> Founder R6 修复后验收 dashboard，发现 dashboard **列表卡片** + **详情页 5 按钮** 仍有问题。R6 仅修了 `dashboard/[storyId]/StoryDetailContent.tsx` 详情页，**没碰列表页**和**modal 实现**。

### ✅ R7-1 P1 Dashboard 列表卡片 4 个 bug — 全部完成 ✅ (Backend Agent D 2026-04-28 16:00 + Frontend Agent E 2026-04-28 16:30)

**文件**: `frontend/src/contexts/AuthContext.tsx` `mapProject()` 函数 (L67-80)
**也涉及**: `frontend/src/components/dashboard/StoryCard.tsx` (展示组件)

**根因清单**:

| # | 现象 | 根因 (位置) | 验证证据 |
|---|------|-----------|---------|
| 1 | 缩略图永远是橙色 logo 占位 | AuthContext.tsx L71 `coverImageUrl: "/brand/logo-48.png"` hardcoded | 没读 storyboard.shots[0].image_url |
| 2 | 故事列表"0 shots" 永远显示 | AuthContext.tsx L74 `shotCount: 0` hardcoded | mapProject 仅 fetch `/api/projects/`，没 fetch chapter / storyboard 数据 |
| 3 | 时间显示 "4/27 07:10"（北京下午测试时） | backend `created_at = datetime.utcnow()` 字符串没带时区标记 → 前端 `toLocaleDateString("zh-CN")` 按 UTC 渲染 | UTC 07:10 + 8h = 北京 15:10（接近测试时段） |
| 4 | "共 0 张画面" 数据卡片永远 0 | DashboardContent.tsx L27 `totalShots = stories.reduce((sum, s) => sum + s.shotCount, 0)` | 因 #2 hardcoded 0 → 累加永远 0 |

**修复方案**:
- **方案 A 推荐 (后端扩列表端点)**:
  - backend `GET /api/projects/` 响应每条加 `cover_image_url` (storyboard.shots[0].image_url) + `shot_count` (storyboard 长度) + `mood` (confirmed_outline.mood)
  - frontend mapProject 直接读这些字段
  - backend datetime 序列化用 `.isoformat() + "Z"` 或 ISO with timezone
- **方案 B (前端额外 fetch)**:
  - 不改后端，前端在 mapProject 后并行 fetch 每个 project 的 storyboard endpoint — N+1 query 风险大，不推荐

**预估**: backend ~10 min + frontend ~10 min = ~20 min 串行

**Frontend Agent E 完成内容 (2026-04-28 16:30)**:
- `AuthContext.tsx` `ApiProject` 接口加 `cover_image_url / shot_count / mood`；`mapProject()` 用 `toAbsoluteUrl()` 转封面 + fallback logo + 读 shot_count + mood + ISO Z 时间直接赋值
- `types/create.ts` `StoryCard` 加 `mood: string | null`
- `StoryCard.tsx` metadata 行 mood badge 条件渲染
- `mock-data.ts` 6 条 mock 补 mood 字段
- npm build 21 routes 0 errors ✅

### 🟡 R7-2 P2 详情页右上角 5 按钮 4 个 Mock 占位

**文件**: `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` + 各 modal 组件

**实情清单**:

| 按钮 | 真实功能 | 文件 | 状态 |
|-----|---------|------|:-:|
| ❤️ 点赞 | `setIsFavorite` 仅 local state，无 API persist | StoryDetailContent.tsx L324 | ❌ Mock |
| 🔗 分享 | ShareModal 用 `Date.now()` 生 fake link `/s/{时间戳}` | components/ui/ShareModal.tsx L15 mockLink | ❌ Mock |
| 📋 做同款 | `router.push /create?style=...&length=...` 真路由 | StoryDetailContent.tsx L297-299 | ✅ 真 |
| ⬇️ 导出 | ExportModal `onExport` callback 空函数 `() => {}` | StoryDetailContent.tsx L485 | ❌ Mock |
| 🎬 合成视频 | VideoSynthesisModal 仅 setInterval 模拟 progress 动画，无真合成 | components/ui/VideoSynthesisModal.tsx L17-25 | ❌ Mock |

**修复方案**:
- 点赞: backend `/api/projects/{id}/favorite` toggle endpoint + projects 表加 `is_favorite` 列
- 分享: backend 生 share token + 公开页面（`/s/{token}` 真路由）— 中等工作量
- 导出: backend `/api/projects/{id}/export?format=...` 打包 zip 返回（图片 / 图+音频 / 全部素材）— 大工作量
- 合成视频: 调 ffmpeg 拼接 shots + BGM + 旁白（需 TTS pipeline 接通） — 大工作量，可能整体留给 MVP 后

**触发条件**: MVP 后讨论（不阻塞 MVP，因为详情页核心展示已 OK）

### 📊 T5 老数据局限说明（已知）

T5 项目 (uuid `283bd407-0e64-43bb-b2eb-8f6b4063c4af`) 是 R6 修复**之前**创建的：
- `characters_json[*].portrait_url=None` → silhouette fallback 生效（**预期**，T6 新故事会有真 portrait，因为 UX-1 修了 Stage 2 portrait 提前生成）
- `confirmed_outline.user_selected_mood=None` → fallback 到 `confirmed_outline.mood="感人"`（OBS-4 是新逻辑，T5 没经过新流程）

### ✅ T5 详情页旁白验证（PM 直查 DB 实证不是 bug）

Founder 怀疑旁白可能"瞎编"或"按 scene 复用"，PM 直查 DB 证伪：

```
shot[0] scene_id=2 narration_segment[:50]='管家是个惯于用沉默施压的人，那叠钞票拍下去...'
shot[1] scene_id=2 narration_segment[:50]='门缝里，焦小顺的一只眼睛圆睁着，左手腕上那条褪色的红腕带...'
shot[2] scene_id=2 narration_segment[:50]='那一夜漫长得像是被人刻意拉长，焦立河坐在那叠钱和那把唢呐之间...'
```

- 同 scene_id=2 但 3 个 shot narration_segment **完全不同**
- Stage 4 storyboard director 给每个 shot 单独写旁白
- 前端 L116 `narrationSegment: shot["narration_segment"]` 直读 storyboard 真字段
- **结论**: 旁白功能完全正确，无需修复

### 🟢 T6 新 pipeline 测试 — 完全可以立即跑

**理由**:
- R6 仅改 `app/schemas/project.py` + `app/api/projects.py` + `dashboard/[storyId]/StoryDetailContent.tsx` + `frontend/src/types/create.ts`
- R6 **未碰** pipeline 任何代码（image_generator / storyboard_service / pipeline_orchestrator 等 mtime 全是 R4-R5）
- 创建流程 StageA→E 跟 dashboard 详情页是**两套独立组件**，零交互
- 跑 T6 的预期效果（前面 T5-FIXBATCH 14 + R5 + R6 全部生效）:
  - 真 portrait (UX-1 修了 Stage 2 portrait 提前生成)
  - user_selected_mood 持久化 (OBS-4)
  - 真 image_url 写回 (BE-3)
  - 真 bgm_url 写回 (BE-5)
  - 正确风格的 BGM (BGM-1 + 95 风格字典)
  - ETA 单调下降 / 大标题随 stage / 文案"片段" / 100% 自动跳 Stage D (UX-7/9/8/11)

**已知 T6 caveat**:
- 跑完进 dashboard **列表**仍显示 "0 shots" + 时区错（R7-1 未修）
- 但点进**详情页**完全正确（18 shots + 真 portrait + 200 字大纲 + 真 mood + BGM）



---

## 🟡 P2 Frontend `sharp` missing in production mode (2026-04-27 21:10 monitor 触发)

**现象**: frontend npm start (production standalone) 模式下 next/image 渲染时报错：
```
⨯ Error: 'sharp' is required to be installed in standalone mode for the image optimization to function correctly.
Read more at: https://nextjs.org/docs/messages/sharp-missing-in-production
```

**触发频率**: 每次 next/image 组件渲染都会触发（dashboard logo / StoryCard 缩略图等），9+ 次/页面加载

**影响**:
- ⚠️ 控制台日志噪音
- ✅ 实际图片仍能 fallback 显示（next/image 优化失败后回退原始 URL）
- 🔍 next/image 优化未生效（图片不会被自动 resize / format 转换 / lazy load 优化）

**根因**: Next.js 14 standalone production mode 要求 `sharp` 库做图片优化。`package.json` dependencies 没装 sharp。本地 dev 模式（`npm run dev`）不需要，但 `npm start` (production) 需要。

**修复 (1 行)**:
```bash
cd frontend && npm i sharp
# 重启 frontend
```

**触发来源 (非本次 R6)**: 旧代码已有 next/image 调用：
- `frontend/src/app/dashboard/DashboardContent.tsx` (L41 logo)
- `frontend/src/components/dashboard/StoryCard.tsx` (cover image)
- 其他 layout 组件

R6 改动 StoryDetailContent.tsx 用的是 `<img>` 标签（非 next/image），未新增 next/image 调用。

**触发条件**: P2 — 不阻塞功能（图片仍能显示），仅控制台噪音 + 优化失效。本次干净重启时一并修复（npm i sharp）。



---

## 🟠 R7-3 + R7-4 配套修复 (2026-04-28 11:18 T6 实测发现)

### 背景
T6 测试时 Founder 在 StageC 用 `/characters/{id}/adjust` 调整林晓苗"马尾辫→黑长直发"，但发现：
1. Backend `adjust_character()` (app/api/projects.py L684-822) 只更新 description / physical / clothing 字段，**不重新生成 portrait** → 老 portrait_v1（马尾辫）跟新描述（黑长直发）不一致
2. Stage 5 prep `generate_character_multi_refs()` 无条件重生 portrait + fullbody，**Stage 2 提前生的 portrait 被浪费**

### R7-3 P1 — adjust API 触发 portrait 重生
**文件**: `app/api/projects.py` `adjust_character()` L684-822
**修复**: L810 后补：
```python
# 7. 重新生成 portrait（用新描述）
from app.services.reference_image_manager import ReferenceImageManager
_ref_manager = ReferenceImageManager()
_portrait_result = await _ref_manager.generate_character_reference(
    character=updated_char_with_id,
    project_style=ProjectStyleConfig(style_preset=project.style_preset),
    image_generator=image_generator,  # 需要从 dependency injection 拿
    ref_type="portrait",
)
if _portrait_result.get("success") and _portrait_result.get("pil_image"):
    _portrait_path = os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
    _portrait_result["pil_image"].save(_portrait_path)  # 覆盖老 portrait
    chars_list[char_index]["portrait_url"] = f"/static/outputs/{project_id}/character_refs/{char_id}_portrait.png"
    chars_list[char_index]["updated_at"] = datetime.utcnow().isoformat()  # 给 R7-4 用
    chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
```
**工时**: ~10 min

### R7-4 P2 — Stage 5 prep 复用最新 portrait（freshness check）
**文件**: `app/services/pipeline_orchestrator.py` L585-615 (Stage 5 prep loop) + `app/services/reference_image_manager.py` `generate_character_multi_refs()` L164-236
**修复**:
1. pipeline_orchestrator Stage 5 prep loop：传入已有 portrait 作 seed_image 跳过 portrait 重生
   ```python
   for char in char_list:
       char_id = char.get("id")
       existing_portrait = char.get("portrait_url")
       portrait_seed = None
       if existing_portrait:
           local_path = existing_portrait.replace("/static/", "static/")
           if os.path.exists(local_path):
               portrait_mtime = os.path.getmtime(local_path)
               char_updated_at = char.get("updated_at_ts", 0)
               if portrait_mtime > char_updated_at:
                   portrait_seed = Image.open(local_path)  # 复用
       
       await ref_manager.generate_character_multi_refs(
           character=char, ..., 
           seed_image=portrait_seed,  # 传入则跳过 portrait 生成
           skip_portrait=portrait_seed is not None,  # 新增参数
       )
   ```
2. `generate_character_multi_refs()` 加 `skip_portrait` 参数：
   ```python
   if not skip_portrait:
       portrait_result = await self.generate_character_reference(..., ref_type='portrait')
   else:
       portrait_image = seed_image  # 用传入的复用 portrait
   # fullbody 部分不变
   ```
**工时**: ~15 min

### 成本节省 (NB2 $0.067/张)

| 场景 | 现状 | R7-3 only | R7-3 + R7-4 |
|------|:-:|:-:|:-:|
| 用户不 adjust | 3 张/角色 (浪费 1) | 3 张 (浪费 1) | 2 张 ✅ |
| 用户 adjust 1 次 | 3 张 (portrait 不一致) | 4 张 (浪费 1) | 3 张 ✅ |
| 用户 adjust N 次 | 3 张 (不一致) | 3+N 张 (浪费 1) | 2+N 张 ✅ |

每 T6 类项目（3 角色）省 ~$0.20 NB2 成本。

### 验证 T6 现状
- T6 (project_id=15) char_003 林晓苗:
  - 11:03:55 portrait_v1 (马尾辫) 已生 ✅
  - 11:12:15 adjust 写描述"黑长直发" ✅，**portrait 仍是 v1 马尾辫** (R7-3 未修)
  - Stage 5 prep 时 portrait_v2 会用新描述覆盖 v1（current behavior, R7-4 未修就会发生这次浪费）
- 最终 18 shots 林晓苗 = 黑长直发 (因 fullbody 用 portrait_v2 作 ref)

### 必须配套修
**警告**: 单修 R7-3 不修 R7-4 反而**增加浪费**（adjust 重生 + Stage 5 又重生 = 两次重画）。这两条必须一起修。



---

## 🔴 R7-5 P1 Stage label system-wide 错位 (2026-04-28 11:21 T6 实测发现)

**现象**: Founder T6 测试时 Stage 3 ScreenplayWriter 已在跑（11:20:10 启动），但前端大标题显示"正在设计角色"。

**根因 (pipeline_orchestrator.py)**: 3 处 progress_callback 都用"上一个 stage 名"而不是"即将进入的 stage 名"：

| Line | 当前 | 应改为 |
|------|------|--------|
| L338 | `progress_callback("story_generation", 5, "大纲生成完成，正在设计角色...")` | `progress_callback("character_design", 5, ...)` |
| L488 | `progress_callback("screenplay", 35, "剧本编写完成，正在创建分镜...")` | `progress_callback("storyboard", 35, ...)` |
| L528 | `progress_callback("storyboard", 65, "分镜创建完成，正在生成图像...")` | `progress_callback("image_generation", 65, ...)` |

**实际影响**: 整个 pipeline 大标题滞后一个 stage：

| 实际 backend 跑 | 当前显示 | 正确显示 |
|------|------|------|
| Stage 2 角色 | "正在生成故事大纲" | "正在设计角色" |
| Stage 3 剧本 | "正在设计角色" | "正在编写剧本" |
| Stage 4 分镜 | "正在编写剧本" | "正在创建分镜" |
| Stage 5 真生图 | "正在创建分镜" | "正在绘制画面" |
| Stage 6 BGM | "正在绘制画面" | "正在生成配乐" |

**触发条件**: 体验 P1（用户始终看到比实际滞后一阶段的标题），MVP 前必修

**工时**: ~5 min backend 改 3 行

**关联**:
- 已知 Phase 1 修 UX-9 时漏改这 3 处
- 实际这是 progress_callback 的"语义模式"问题 — 应该在 stage 启动时设新 label，不是完成时回头设



---

## 🟡 R7-6 P2 StageC checkpointPreview 文案错位 (2026-04-28 11:28 T6 实测)

**现象**: Founder T6 测试时 progress 从 39% 一次性跳到 65%（Stage 4 完成 → Stage 5 启动），中间 55-63% 区间一闪而过，触发显示"即将到达角色预览检查点"，但用户**早已经过角色预览**（Stage 2 → character_ready 时已过，那时 progress=10%）。

**文件**: `frontend/src/components/create/StageC.tsx` L209-214

```ts
const checkpointPreview = (() => {
  const progress = state.generationProgress;
  if (progress >= 55 && progress <= 63) return "即将到达角色预览检查点";
  return null;
})();
```

**根因**: 老代码 stale — 假设 progress 55-63% 区间是角色预览检查点。实际 pipeline 架构已变：
- 角色预览检查点 = Stage 2 完成 = `character_ready` stage = progress 10%
- progress 55-63% 实际是 Stage 4 分镜尾声 → Stage 5 真生图启动
- 二者完全错位，misleading 用户以为还要回去看角色

**修复方案**:
- **方案 A 推荐**: 直接删除 `checkpointPreview` 这段（L209-214 + L调用处），整段语义已死
- **方案 B**: 改成 `if (stage === "character_design" && progress < 10)` 仅在角色设计前才显示

**触发条件**: P2 体验，仅在 progress 跨 55-63% 区间瞬间出现，多数用户可能注意不到，但增加困惑

**工时**: ~3 min frontend

**关联**: 这种"老代码假设跟新架构错位"在 pipeline 多次重构后是常见 patten — R7-5 也是同类（progress_callback stage 名跟实际 stage 错位）



---

## 🟠 R7-7 P1 ETA 算法 stage 速率差异 (2026-04-28 11:32 T6 实测)

**现象**: Founder T6 进度 65%（Stage 5 真生图刚启动）时 ETA 显示"1 分钟"，但实际真生图 18 张 max_concurrent=3 至少需要 ~5 min。**严重低估**。

**根因**: `frontend/src/components/create/StageC.tsx` L177-186 fallback 线性外推：
```ts
const totalEstimated = elapsed / (progress / 100);
const remaining = totalEstimated - elapsed;
```
假设速率均匀，但实际不同 stage 速率差异巨大：
- Stage 3 剧本（10-35%）：1 min → 速率快（25%/min）
- Stage 5 真生图（65-90%）：5 min → 速率慢（5%/min）
- 算法用 Stage 1-4 平均速率算到 Stage 5，错估为 1 min

**关键发现**: Frontend L173-176 已预留 backend 主导路径：
```ts
const backendSec = backendEstimatedSecondsRef.current;
if (backendSec !== null && backendSec > 0) {
  rawSec = backendSec;
}
```
但 backend 没给 `estimated_remaining_seconds` 字段。

**修复方案 (推荐 A — backend 主导)**:
- `app/services/pipeline_orchestrator.py` 在每次 `progress_callback` 时计算 stage-specific ETA：
```python
STAGE_DURATIONS = {
    "story_generation": 60,
    "character_design": 120,
    "screenplay": 60,
    "storyboard": 300,
    "image_generation": 300,
    "bgm": 120,
}
def estimate_remaining(current_stage: str, stage_progress: float) -> int:
    seq = ["story_generation","character_design","screenplay","storyboard","image_generation","bgm"]
    idx = seq.index(current_stage)
    remaining = STAGE_DURATIONS[current_stage] * (1 - stage_progress)
    for s in seq[idx+1:]:
        remaining += STAGE_DURATIONS[s]
    return int(remaining)

# progress_callback 改 signature 加 estimated_remaining_seconds
await progress_callback(stage, progress, message, estimated_remaining_seconds=...)
```
- `app/services/job_manager.py` 写入 `job.estimated_remaining_seconds` (新列) 或 status response 直接返
- `app/api/chapters.py` `/status` 返回 `estimated_remaining_seconds` 字段
- frontend 自动 pickup（已就绪）

**工时**: ~15 min backend + 0 frontend

**触发条件**: P1 体验 — ETA 严重低估让用户以为快好了，等 5 倍时间会失耐心

**关联**:
- UX-7（已修，monotonicity guard）只保证 ETA 不增长，不解决速率不均
- 跟 UX-3（卡帧不同步）部分关联



---

## 🔴 R7-5 补充 — Stage 5 prep 阶段实测滞后量 (2026-04-28 11:34 T6)

### Founder 实测：滞后 ~4 分钟

| 时间 | Backend 实际工作 | Frontend 大标题 | 状态 |
|------|----------------|--------|:-:|
| 11:30:00 | Stage 4 分镜完成 → Stage 5 prep 启动（生场景参考图）| "正在创建分镜" | ❌ |
| 11:30-11:34 | Stage 5 prep 4 分钟（场景参考图 / fullbody / 角色 refs setup）| "正在创建分镜" | ❌ |
| 11:34:20 | Shot 1/21 真生图启动 → backend 设 stage="image_generation" | "正在绘制画面" | ✅ |

**滞后量**: ~4 分钟。整个 Stage 5 prep 期间用户看到的都是"正在创建分镜"，跟实际 backend 工作不符。

### R7-5 更深本质（不止 3 行修复）

之前 PENDING 列了 3 处 progress_callback (L338/L488/L528) stage 名错位。**实际更深问题**: 整个 progress_callback 设计模式 — **都在 stage 完成时设 stage 名（命名为已完成的 stage）**，不是 stage 启动时设新 stage 名。

这导致：
- Stage 5 prep 工作（场景参考图 / fullbody）持续 ~4 分钟，期间 stage 还是上一个 "storyboard"
- 用户体感：每个阶段切换都滞后 stage 真正切换时间 1-4 分钟

### 推荐架构修复（升级版）

**方案 B**（升级 R7-5）：拆分 stage 粒度 + stage 启动时立刻设
- 加 `image_preparation` stage（场景参考图 + fullbody，progress 65-75%）
- 加 `image_generation` stage（真 shots 生成，progress 75-90%）
- 每个 stage 入口立刻调 progress_callback 设新 stage 名
- 不在 stage 完成时设上一个 stage 名

**最简方案 A**（已记 R7-5 的 3 行修）只解决"label 错位"，不解决"滞后量"。

工时：方案 B ~30 min backend（增 stage + 改 4-5 处 callback）



---

## 🆕 TASK-T6-FIXBATCH (2026-04-28 T6 测试发现 + 规划)

> **范围**: T6 端到端测试 (10:57-11:50) 暴露 + PENDING 旧账整合 = 39 项修复
> **Founder 决策 (2026-04-28 ~12:00)**: 全部要修，Wave 1 风险最低分两阶段，ARCH-1 抽到 Wave 2，Tester T7 真生图（控制成本），UX-16 用方案 A dynamic route

### T6 新发现 5 条（R7-8 ~ R7-12）

#### 🟡 R7-8 P2 — Stage 5→6 切换 progress 倒退 95% → 92%
- **现象**: T6 11:44 Stage 5 真生图 21/21 完成（前端 95%）→ Stage 6 BGM 启动后倒退到 92%
- **根因**: `app/services/pipeline_orchestrator.py` L968 `progress_callback("bgm", 92, ...)` 写死 progress=92，覆盖 Stage 5 最后到的 95%。UX-7 monotonicity guard **只管 ETA 不管 progress**
- **修复**: BGM 入口 progress 改成 `max(current_progress, 92)`，并升级 UX-7 加 progress 单调 guard（架构层 A-4）
- **工时**: 5 min（与 P1-2 合并）

#### 🔴 R7-9 P0 — 完成时大标题倒退到"正在生成故事大纲"
- **现象**: T6 11:45 status='completed' 时前端大标题显示"正在生成故事大纲" + tip "把你最喜欢的电影情节用一句话描述..."
- **根因实锤**: `job.current_stage = 'story_generation'`（应 `'completed'`） — backend mark_completed 把 stage 重置回 Stage 1
- **关联**: 与 PENDING 早期 "MVP 后 P2 #1" (`job_manager.py:302`) 是**同一根因**，本次升级到 P0
- **修复**: `app/services/job_manager.py` mark_completed 设 `stage='completed'`，前端 STAGE_LABEL["completed"] 已就绪
- **工时**: 5 min

#### 🟡 R7-10 P2 — 完成态副标题文案冲突
- **现象**: 100% 时同时显示"即将完成" + "故事生成完成！"（两个 UI 区域读不同源）
- **根因**: 一个区域读 progress 阈值（>95%→"即将完成"），一个读 message（"故事生成完成"）。状态机不统一
- **修复**: `frontend/src/components/create/StageC.tsx` 统一读 message，stage='completed' 直接走完成态
- **工时**: 5 min

#### ⚪ R7-11 P3 — 100% 完成后 carousel tip 还在 rotation
- **现象**: 完成态弹"把你最喜欢的电影情节用一句话描述..." 与场景脱节
- **根因**: `frontend/src/components/create/StageC.tsx` CAROUSEL_TIPS setInterval 没在 stage='completed' 时停止
- **修复**: useEffect 依赖加 stage，completed 时 clearInterval
- **工时**: 3 min

#### 🔴 R7-12 P0 — StageD 预览图 + 配乐全部 404（**Founder 当前阻塞**）
- **现象**: T6 跳转后 21 张 shots 全显示破图标，配乐 0:00 / --:-- 不响
- **根因实锤**: `frontend/src/components/create/StageD.tsx` L186-188 `<img src={currentShot.imageUrl}>` + bgm src 缺 `toAbsoluteUrl()` 转换。浏览器把 `/static/...` 解析为 `http://localhost:3000/static/...` → frontend port 没代理 static → 404
- **实证**: backend HTTP `localhost:8000/static/outputs/.../shot_01.png` 返 200 / 3MB / bgm 3.6MB ✅。Dashboard 详情页 `StoryDetailContent.tsx` L121 已有 `toAbsoluteUrl(rawImageUrl)` 工作正常 — StageD 漏了
- **关联**: 与 PENDING 早期 "MVP 后 P2 #3" (StageD imageUrl=null fallback) 同文件不同问题，本次升级到 P0
- **修复**: StageD 引入 `toAbsoluteUrl()` 包裹所有 `/static/...` 路径
- **工时**: 10 min

### F-1 P0 — StageC 角色预览看不到 portrait（T6 早期发现）
- **现象**: T6 11:08 StageC 全 silhouette 占位，DB 实际 3 个 portrait 全已写入
- **根因**: `frontend/src/components/create/StageC.tsx` L295-309 `character_ready` handler 读 `state.outline.characters` 取 `c.portrait_url`，但该字段写在 `chapter.characters_json` 不在 outline → 永远 null
- **修复方案 A**: character_ready 触发后 fetch `/api/chapters/{n}/story` 拿 chapter.characters，从那里读 portrait_url
- **工时**: 15 min

### F-2 P1 — StageC 角色卡刷新按钮 mock
- **文件**: StageC.tsx L732-735 `handleRegenerate()` 是纯 mock setTimeout 2s
- **修复**: 接 backend `/api/projects/{id}/characters/{char_id}/regenerate-portrait` 端点（与 R7-3 backend 一并实现）
- **工时**: 15 min（与 R7-3 backend 联调）

---

## 📋 修复总规划（4 Wave）

### Wave 0 — PM 文档收尾 ✅ (2026-04-28 12:05 进行中)
- PENDING.md 写本任务（本条目）
- TEAM_CHAT.md / pm-progress / TODAY_FOCUS 更新

### Wave 1 第一阶段 — Backend A ✅ + Frontend B ✅ 并行完成 (2026-04-28)

#### 🟦 Agent A (Backend Sonnet 4.6) ✅ 完成 + 修复 round 1 完成 ✅
集中修 pipeline_orchestrator + job_manager + projects.py + reference_image_manager（避免 merge 冲突）：

| 项 | 描述 | 文件 | 状态 |
|----|------|------|------|
| P0-2 | mark_completed 设 stage='completed' 不是 story_generation (R7-9 / 旧 P2 #1) | `job_manager.py:302` | ✅ |
| P1-1 | Stage label 重构方案 B：拆 image_preparation/image_generation 粒度 + stage 入口立即 callback (R7-5 + B-3 + B-4 + 架构 A-1) | `pipeline_orchestrator.py` 多处 | ✅ |
| P1-2 | ETA backend 主导：STAGE_DURATIONS 字典 + estimate_remaining() + /status 返 estimated_remaining_seconds + UX-7 升级管 progress 单调 (R7-7 + R7-8 + B-7 + 架构 A-4) | `pipeline_orchestrator.py` + `job_manager.py` | ✅ |
| P1-2 修复 | **ETA 链路接通**：chapters.py /status 实际调用 estimate_remaining()，旧 elapsed 逻辑替换 | `app/api/chapters.py` L21 + L143-156 | ✅ 修复 round 1 |
| P1-3 | adjust 重生 portrait + Stage 5 prep freshness check (R7-3 + R7-4 必须配套) | `app/api/projects.py adjust_character()` + `pipeline_orchestrator.py Stage 5 prep` + `reference_image_manager.py generate_character_multi_refs()` | ✅ |
| P1-3 修复 | **freshness check 30s buffer**：`_portrait_mtime > (_char_ts + 30)` | `pipeline_orchestrator.py` L645 | ✅ 修复 round 1 |
| P1-5 | character_ready 等 portrait 全成 + characters_json 写完才设（架构 A-3） | `pipeline_orchestrator.py` Stage 2 末 | ✅ |

**合计 ~1.5-2 hr + 修复 round 1 (~20min)**

#### 🟩 ✅ Agent B (Frontend Sonnet 4.6) — 完成 2026-04-28 14:30
集中修 StageC + StageD + Stage E + BgmPlayer：

| 项 | 描述 | 文件 | 状态 |
|----|------|------|------|
| P0-1 | StageD image/bgm 全部走 toAbsoluteUrl (R7-12 + 旧 P2 #3) | `StageD.tsx` | ✅ |
| P0-3 | StageC character_ready 后 fetch chapter.characters_json 拿 portrait_url (F-1) | `StageC.tsx` | ✅ |
| P1-6 | Stage E 读 outline.summary 不是 original_idea (UX-17) | `StageE.tsx` | ✅ |
| P2-2 | 删除 StageC checkpointPreview L209-214 stale 区间 (R7-6) | `StageC.tsx` | ✅ |
| P2-4 | 完成态副标题统一 + carousel tip 停止 rotation (R7-10 + R7-11) | `StageC.tsx` | ✅ |
| F-2 | 角色卡刷新按钮接真 API（与 Agent A P1-3 联调） | `StageC.tsx` | ✅ 前端就绪，等 Agent A P1-3 |
| 旧 P3 4-6 | BgmPlayer url 引号 strip + Shot onError 占位图 + 进度条 spring 动画 | `BgmPlayer.tsx` + `StageD.tsx` + `StageC.tsx` | ✅ |
| STAGE_LABEL | character_design + image_preparation 两个新 stage 标签 | `StageC.tsx` | ✅ |

**新建**: `frontend/src/lib/url.ts` — toAbsoluteUrl() 共享工具（StageD/BgmPlayer/StageC/StoryDetailContent 全引用）
**npm build**: ✅ 20 routes 0 errors

**合计 ~1.5 hr**

#### 🟦 Agent A 与 Agent B 协作约束
- Agent A 增加新 stage 名 `image_preparation` → 必须告诉 Agent B 让它在 STAGE_LABEL map 加 `image_preparation: "正在准备画面"`
- Agent A 增加 `estimated_remaining_seconds` 字段 → Frontend 已就绪 pickup（StageC L173-176），不需要改
- Agent A `/api/projects/{id}/characters/{char_id}/regenerate-portrait` 端点契约 → Agent B 在 F-2 用

### Wave 1 第二阶段 — UX-16 URL 路由 ✅ 完成 (2026-04-28 15:06 Agent C Opus 4.7)

#### 🟪 Agent C (Frontend Opus 4.7) — UX-16 dynamic route
- ✅ **P0-4 UX-16**: dynamic route `/create/[projectUuid]/[stage]` 实施完成
- ✅ **方案选择**: 单 dynamic route + 6 stage 枚举（不是 6 嵌套路由），详尽 trade-off 见 TEAM_CHAT
- ✅ **新建**: `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` + `frontend/src/lib/createUrl.ts`
- ✅ **改造**: CreateContent.tsx + CreateContext.tsx + types/create.ts
- ✅ **验收**: npm build 21 routes 0 errors，4 核心场景 trace 通过
- ✅ **风险防护**: lastPushedUrlRef echo guard + derivedFromState 短路 + completion guard 三层防护避免反馈环
- **实际工时**: ~1.5 hr

### Wave 2 — Backend D + Frontend E 串行 + ARCH-1 单独修

#### ✅ Agent D (Backend Sonnet) — Dashboard 列表后端字段 (2026-04-28 16:00)
- **P1-4 R7-1 backend**: ✅ 完成 — `/api/projects/` 每条新增 cover_image_url + shot_count + mood + ISO 时区时间
- **修改文件**: `app/schemas/project.py` + `app/api/projects.py`
- **pytest**: 24/24 ✅（architecture 7 + parallel_stage5 17）

#### 🟩 Agent E (Frontend Sonnet) — Dashboard 列表前端读字段（等 D 完成）
- AuthContext.tsx mapProject 改读后端新字段
- **工时**: 10 min

#### ✅ Agent F (Backend Sonnet) — ARCH-1 chapter_scene_images 写入 (2026-04-28 15:50)
- **P1-7 ARCH-1**: ✅ 完成 — pipeline 完成后批量写入 chapter_scene_images 表
- **修改文件**: `app/services/pipeline_orchestrator.py` + `app/services/job_manager.py`
- **pytest**: 211/211 ✅

### Wave 3 — Tester 验收 ✅ 完成 (2026-04-28 21:00 Agent G)

#### ✅ Agent G (Tester Sonnet) — T7 真生图端到端验证完成

**T7 UUID**: `631eef3c-4a26-413a-bcb1-1f038d176e85` | 故事: "深夜灯火" | 2 角色，16 shots，插画风，1:1 | 花费: ~¥3.50

**12 项验收汇总**: 11 PASS / 1 FAIL / 0 未触发

- [x] StageC character_ready 后 portrait 显示（P0-3）— PASS
- [FAIL] adjust 角色后 portrait 自动重生（R7-3 P1-3）— FAIL，非阻塞异常 `'str' object has no attribute 'get'` at projects.py L987，portrait mtime 不变
- [x] Stage label 实时跟随（P1-1）— PASS，6 阶段全观察到
- [x] ETA 单调下降（P1-2）— PASS，855s→270s→0s
- [x] progress 不倒退（R7-8）— PASS
- [x] 完成时 current_stage='completed'（R7-9）— PASS
- [x] 完成态副标题不冲突（R7-10）— PASS
- [x] 100% 后 carousel tip 停止（R7-11）— PASS
- [x] StageD shots + BGM 可访问（P0-1）— PASS
- [x] Stage E 读 outline.summary（P1-6）— PASS
- [x] URL /create/[uuid]/[stage] 路由（P0-4）— PASS
- [x] Dashboard 封面+shot 数+北京时区（P1-4）— PASS
- [x] D.15 P0 shot 尺寸 = 2048x2048（PIL 实测 16/16）— PASS

**新 Bug**: R7-3 portrait 重生 P1 bug — @backend 需修 `app/api/projects.py` adjust_character() 约 L945，`updated_char` 类型错误

**回归观察**: 角色一致性主观评估良好；风险路径未本次触发（Seedream 全程 16/16）

**详细验收报告**: TEAM_CHAT.md [2026-04-28 21:00]

### Wave 4 — DevOps 部署

#### ✅ Agent H (DevOps Sonnet) — 完成 2026-04-29
- [x] push GitHub — commit 84a2d35（Wave 1.1+1.2+2+2.5+3.5 全批，16 文件）
- [x] 通知 Ben — `.team-brain/team_ben/TEAM_CHAT.md` 后端改动清单已 append
- [x] rsync VPS — `rsync -avz app/ vps:/opt/xuhua-story/app/` + `rsync -avz frontend/ vps:/opt/xuhua-story/frontend/`（trailing slash 正确）
- [x] Docker rebuild + force-recreate api + frontend — `docker compose build --no-cache api frontend` → `docker compose up -d --force-recreate`
- [x] `/health` 验证 200 ✅
- [x] 生产 T8 完整故事验证 — UUID a3966a40-6d27-42c0-a7cf-109729e453e7，1:1 朋友圈，16 shots NB2 真生图，status=completed

**验证结果**:
- D.15: PIL 实测 1024x1024（1:1 正方形，不再 hardcoded 2:3）✅
- R7-1: cover_image_url + shot_count=16 返回正常 ✅
- R7-3: portrait mtime +45s（adjust 后真实重生）✅
- UX-16: GET /create/{uuid}/preview → HTTP 200 ✅

---

## 🚦 暂缓项（不进本批）

| 项 | 原因 |
|----|------|
| R7-2 5 按钮 mock 接真功能（点赞/分享/导出/合成视频）| 工作量大，MVP 上线后做 |
| ARCH-2 死表清理 | 下次 DBA cleanup 一并 |
| OPS-3 PYTHONUNBUFFERED | 下次 docker rebuild 一并 |
| 监控告警 R4 / TASK-STYLE-EXPANSION / 续写 Phase 3 / Resonance 时间线 | 已暂缓 |
| T-1 milestone "片段"漏改 / T-2 storyboard_director 内部 callback / O-1 OBS / O-2 短篇 21 shots cap | 文案/OBS 类小 bug，凑齐一批改 |
| OBS-1 Seedream sanitize 触发率统计 | MVP 后观察实际数据 |
| OBS-3 outline LLM 一致性规则 | 凑前端 UX-2 校验一起做 |


---

## ⚠️ TASK-T6-FIXBATCH 风险与注意点（全维度，毫无遗漏）

### A. 代码层面风险

#### A.1 🔴 角色一致性回归 — 高风险
- **风险**: Agent A 改 `pipeline_orchestrator.py` 多处（stage label / ETA / Stage 5 prep portrait 链 / character_ready 切换时机）涉及 CLAUDE.md 列为高风险的文件
- **影响**: 可能破坏现有的角色一致性传递链（portrait → fullbody → shots reference）
- **缓解**:
  1. Agent A spawn prompt 必须包含 CLAUDE.md "角色一致性"章节作为强制必读
  2. Agent A 严禁动 `image_generator.py` / `storyboard_prompts.py` / `seedream_generator.py` / `style_enforcer.py` / `reference_image_manager.generate_character_reference()`（只能动 `generate_character_multi_refs()` 加 freshness check）
  3. Wave 3 Tester 必须跑全回归测试：3 角色 100% / 6 角色 ≥90% / 4 题材稳定（CLAUDE.md 铁律）
  4. 派发任务时显式列出"禁止删除/修改的内容"

#### A.2 🟠 progress_callback signature 兼容性
- **风险**: Agent A P1-2 给 `progress_callback` 加 `estimated_remaining_seconds` 参数，但 pipeline_orchestrator 有数十处调用，全部要兼容
- **缓解**: 用 default value `estimated_remaining_seconds: int | None = None`，已有调用不需改

#### A.3 🟠 character_ready 切换时机改了 → 前端 polling 行为变化
- **风险**: Agent A P1-5 让 Stage 2 等 portrait 全成才设 `character_ready`。前端 StageC `useGenerationStatus` polling 检测到 `character_ready` 立刻 redirect 到角色预览页。改了之后前端可能会在 Stage 2 多等 30-60s 才进 StageC，**Founder 体感是 progress 卡 5-10% 更久**
- **缓解**:
  1. 加新 stage `character_design` 让 backend 在 LLM 输出完成（但 portrait 还在生）时设 `character_design` (progress 6%)，等 portrait 全成才升 `character_ready` (progress 10%)
  2. Frontend Agent B 在 STAGE_LABEL map 加 `character_design: "正在生成角色画像"`
  3. 让 Founder 知道这是预期行为（"在 portrait 全准备好之前不会进入 StageC"是好事，不是 bug）

#### A.4 🟠 Stage 5 prep freshness check 复用 portrait → 文件 mtime 时间戳依赖
- **风险**: Agent A P1-3 加 freshness check 用 `os.path.getmtime(local_path)` vs `char.get("updated_at_ts")` 比较。Linux/Docker 可能有时区差异 / 文件系统 mtime 精度差异
- **缓解**:
  1. char 用 ISO datetime 字符串记录 `updated_at`，转 unix timestamp 比较（统一 UTC）
  2. 加 30s buffer（mtime 比 updated_at 晚 30s 才认为 fresh，避免边界情况）
  3. fallback 逻辑：mtime 取不到则当作不 fresh，重生（保守）

#### A.5 🟡 R7-3 + R7-4 必须配套修
- **风险**: 单修 R7-3（adjust 重生 portrait）不修 R7-4（Stage 5 prep freshness check）会**反而增加浪费**：用户 adjust 1 次 → portrait 重生 1 次 + Stage 5 prep 又重生 1 次 = 浪费 1 次（~$0.067）
- **缓解**: Agent A 任务清单 P1-3 写明"两条必须一起修，不能只完成一条"

#### A.6 🟠 UX-16 dynamic route 改造可能引入新 bug
- **风险**: UX-16 改 `/create` 单页为 `/create/[projectUuid]/[stage]` 涉及：
  - Next.js dynamic route 配置
  - 各 Stage 组件 URL 同步（`router.replace()` 时机）
  - 刷新时根据 URL 还原 state（要拉 backend chapter API + project API + character_ready 状态）
  - useGenerationStatus hook 跟 URL 联动
  - 浏览器后退按钮行为
- **缓解**:
  1. Agent C 单独 spawn（不与其他改动同 PR），用 Opus 4.6 深度思考
  2. Wave 1 第二阶段（A+B 跑通后才 spawn C）
  3. 验收时强制测：F5 刷新 / 浏览器后退 / 复制链接打开 / 跨 stage 切换 4 个核心场景
  4. 与 dashboard 详情页 `/dashboard/[storyId]` 路由不冲突（不在同 path prefix）

#### A.7 🟠 ARCH-1 改动大 — 18+ 处既有引用
- **风险**: ARCH-1 让 chapter_scene_images 表 pipeline 完成后批量写入。但代码 18+ 处依赖该表（`chapters.py` L362/458/579/...），现有 GET 都返空。改了之后这些端点行为会变（开始返真数据），可能触发既有前端 bug
- **缓解**:
  1. 抽到 Wave 2 单独做（已采纳 Founder 决策），不混 Wave 1
  2. Agent F spawn prompt 列出 18+ 处引用文件，要求 grep 全部确认行为兼容
  3. 单 shot 重生成功能验收（Wave 3 Tester 项）

### B. Agent 协作风险

#### B.1 🟠 三个 agent 并行 spawn → context 错位
- **风险**: Agent A / B / C 同时跑可能不知道对方在改什么
- **缓解**:
  1. **Wave 1 不并行 spawn 三个，分两阶段**:
     - 阶段 1: A + B 并行（互不冲突，A 改 backend，B 改 frontend）
     - 阶段 2: C 单独（A+B 完成且通过审查后才 spawn）
  2. 每个 spawn prompt 包含完整必读清单 + 文件权限边界
  3. PM 在群聊提前公告本批次 spawn 的所有 agent + 各自范围

#### B.2 🟠 Backend ↔ Frontend API 契约
- **风险**: A 加 `image_preparation` stage / `estimated_remaining_seconds` 字段 / `regenerate-portrait` 端点。B 必须知道这些
- **缓解**: 在 spawn prompt 显式列出契约，A 完成后通过 SendMessage 直接告诉 B

#### B.3 🟡 越权风险
- **风险**: PM 反复落入"自己写代码"陷阱（feedback memory: pm_no_scripting）
- **缓解**: PM 严禁动代码，全部派 agent

### C. 测试与部署风险

#### C.1 🟠 T7 真生图测试成本控制
- **风险**: Founder 同意 Tester 跑 T7 真生图，但 NB2 ¥0.067/张 × 18 张 + Mureka 10 credits + LLM ≈ ¥1.2-1.5/次。如果 sanitize 触发率高，成本翻倍
- **缓解**:
  1. **T7 故事选简单生活短篇**（不要悲剧/民俗/婚礼/古装 — 高 sanitize 触发题材，参考 OBS-1）
  2. 选短篇模式（≤ 18 shots，不让 LLM 像 T6 那样跑到 21）
  3. 跑前确认 PipelineCostTracker $10 熔断生效
  4. 单次预算 ≤ ¥1.5
  5. 失败重试不超过 1 次

#### C.2 🟠 progress_callback signature 改 → 旧 chapter status 端点消费方
- **风险**: 加 `estimated_remaining_seconds` 字段后，老 frontend / 老移动端可能不识别（虽然现在只有 web）
- **缓解**: 用 Optional 字段，old client 可以忽略

#### C.3 🟠 部署节奏
- **风险**: Wave 4 部署若不规范会出事故
- **缓解**:
  1. 必须先 push 再部署（铁律 — feedback memory）
  2. rsync 注意 trailing slash 陷阱（feedback memory）
  3. 阿里云共享 MySQL 不能改 schema（job_manager 加字段需 Alembic 迁移）
  4. 部署前 PM 自己跑 /api/health 验证 + 通知 Ben（feedback memory: 后端改动事先提醒）

#### C.4 🟡 DB schema 迁移
- **风险**: P1-2 ETA 方案如果选择"在 chapter_generation_jobs 表加 estimated_remaining_seconds 列"会需要 Alembic 迁移
- **缓解**:
  1. 推荐方案: **不加 DB 列**，只在 status response 实时计算返回（无状态，零迁移成本）
  2. Agent A spawn prompt 写明优先用 in-memory / response-only 方案

### D. 文档与流程风险

#### D.1 🟠 Spawn 前文档未更新
- **缓解**: PM 严格按 xhteam 协议 Wave 0 先更 PENDING/TEAM_CHAT/progress，再 spawn（feedback memory: docs_before_spawn）

#### D.2 🟠 审查跳过群聊重读
- **缓解**: 审查时 PM 严格按 feedback memory: review_read_chat_first

#### D.3 🟠 越权检测
- **缓解**: 审查时 PM 检查 modified files 是否在 spawn prompt 允许范围

---

## 📦 TASK-T6-FIXBATCH 暂缓项（不进本批，详细记录在案）

> 本节细化每条暂缓项：项名 + 优先级 + 暂缓原因 + 触发条件 + 关联文件 + 后续路径

### D.1 R7-2 — 详情页 5 按钮 4 个 Mock 接真功能
- **优先级**: P2
- **暂缓原因**: 工作量大（涉及 backend favorite endpoint + share token 端点 + export zip + ffmpeg 视频合成），且不阻塞 MVP 核心展示路径。Founder 认可详情页核心展示已 OK
- **包含子项**:
  - ❤️ 点赞: backend `/api/projects/{id}/favorite` toggle + projects 表加 `is_favorite` 列（小工作量）
  - 🔗 分享: backend 生 share token + 公开页面 `/s/{token}`（中等工作量，要 server-side render）
  - ⬇️ 导出: backend `/api/projects/{id}/export?format=...` 打包 zip 返回（大工作量，需 zip stream + 选择哪些资源）
  - 🎬 合成视频: ffmpeg 拼接 shots + BGM + TTS narration（最大工作量，需 TTS pipeline 接通）
  - 📋 做同款: 已是真功能，无需修
- **触发条件**: MVP 上线后讨论用户实际诉求优先级，可能选择性实施（例如先做点赞 + 分享，导出/视频留更后）
- **关联文件**:
  - `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` L324 / L297-299 / L485
  - `frontend/src/components/ui/ShareModal.tsx` L15
  - `frontend/src/components/ui/VideoSynthesisModal.tsx` L17-25
  - 待新建 backend: `app/api/share.py` / `app/api/exports.py` / `app/services/video_synthesis.py`
- **后续路径**: MVP 后 Founder 决定优先级 → 拆 4 个独立 TASK 派发

### D.2 ARCH-2 — project_character_references 死表清理
- **优先级**: P2 技术债
- **暂缓原因**: 死表不影响功能（无 SQLAlchemy model 引用），仅占 DB schema 空间。清理需要 Alembic drop migration 操作 production DB，风险大于收益
- **触发条件**: 下次 DBA cleanup（与其他遗留表一并）
- **关联**: schema 定义文件（待 Backend agent 后续 grep 定位）
- **后续路径**: Ben 主导的 DBA 季度清理任务，列入 backlog

### D.3 OPS-3 — uvicorn nohup PYTHONUNBUFFERED=1
- **优先级**: P3 DevOps 配置债
- **暂缓原因**: 仅影响诊断便利性（实时 tail log 需 sleep 等 buffer），不影响生产功能
- **触发条件**: 下次 docker rebuild 一并加 ENV 变量
- **关联文件**: `docker/Dockerfile.api`（待确认）or `docker-compose.yml` env 配置 or VPS .env
- **后续路径**: 下次 DevOps 部署时补 1 行 `ENV PYTHONUNBUFFERED=1`

### D.4 监控告警系统 R4
- **优先级**: P1（已暂缓）
- **暂缓原因**: Harness V2 Phase 1-3 全部完成后 R4 单独留作监控阶段。当前 MVP 修复批优先级更高
- **触发条件**: MVP 上线后 1-2 周内，根据 VPS 实际运行情况启动
- **包含**: ① 修复外部 `/api/health` 404（Nginx 路由前缀） ② 配置 Uptime Robot 或 Grafana ③ 6 个 EP Sensor 端点整合
- **关联**: DEC-015 Harness V2
- **后续路径**: 派 DevOps 启动

### D.5 TASK-STYLE-EXPANSION
- **优先级**: P1（已暂缓）
- **暂缓原因**: 前置 TASK-STYLE-THUMBNAILS 15 张通过后才启动。当前 95 风格只有 15 种上架（有 enforcer 规则 + 缩略图）
- **触发条件**: 缩略图 15 张全通过 + Founder 确认从剩余 80 种中再选哪 25-35 种
- **关联**: `app/services/style_config.py` 95 风格 + `style_enforcer.py` 规则
- **后续路径**: Founder 选风格 → 派 AI-ML 写 enforcer 规则 + 派设计/AI 生缩略图

### D.6 续写模式 Phase 3 (#11)
- **优先级**: P2（已暂缓）
- **暂缓原因**: 产品路线图 Phase 3，需 Founder 决定是否进入设计阶段
- **触发条件**: Founder 决策后再派发设计/实施
- **关联**: 涉及 Story Continuation API / 历史上下文传递 / 角色记忆机制
- **后续路径**: Founder 启动 → 派 PM 主导设计 → 派 backend 实施

### D.7 Resonance 时间线
- **优先级**: P2（已暂缓）
- **暂缓原因**: 原"3-4 周拿 500 申请"时间线已作废（2026-03-23），等内测启动时间
- **触发条件**: Founder 通知正式内测启动后重新制定
- **关联**: Resonance Agent / 抖音"一话故事" / 小红书 / B站
- **后续路径**: Founder 通知 → Resonance Agent 重新制定执行方案

### D.8 文案 / OBS 类小 bug 批（待凑齐一批改）
- **优先级**: P3
- **包含**:
  - **T-1**: milestone "已生成 X/21 张图像..." 漏改"片段"（UX-8 修复漏掉 milestone 区域）— 文件 `StageC.tsx` milestone 渲染 + backend message
  - **T-2**: storyboard_director scene 内部 callback 频率太低（message 卡 "Scene 1/7" 实际跑到 4/7）— 文件 `app/services/storyboard_director.py` 内部 callback
  - **T-3**: "中篇模式支持 36 张画面" tip 在短篇生成时弹（产品决策有意为之，UX-13 已撤销，记录不修）
  - **O-1 OBS**: UX-2 LLM 偶发 JSON 解析（Unterminated string col 414，已兜底吞掉）— OBS 应统计频率，超阈值再修
  - **O-2 P3**: Stage 4 LLM 给短篇生 21 shots（预期 18）— storyboard_director cap 上限 ≤ stories.shot_count
- **暂缓原因**: 单条修都太小，凑齐一批一并 PR 提高效率
- **触发条件**: 累计 5+ 条小 bug 时凑批派 frontend / backend / ai-ml 一次性修
- **关联**: 各自文件如上

### D.9 OBS-1 — Seedream 中文叙事 sanitize 触发率
- **优先级**: P3 OBS（MVP 后观察）
- **暂缓原因**: 本地 1 次 T5 测试样本不够（4/18 触发），需要更多生产数据决定是否值得做"风格预审 + 提前换词"
- **触发条件**: MVP 后累计 100+ 真实生成数据，统计触发率 + 关键词分布，超阈值（如 >20%）再启动
- **关联文件**: `app/services/sanitize_helper.py`（待 backend 加） + `seedream_generator.py` retry path
- **后续路径**: OBS 数据驱动决策，可能做"中文民俗词字典"或"风格预审 LLM"

### ✅ D.10 OBS-3 — outline LLM prompt 加内部一致性规则（Wave 5.1 AI-ML 已完成 2026-04-29 17:33）
- **优先级**: P2 → **已修复**
- **修复实施**: `app/services/story_outline_generator.py` L415-427 加"故事内部一致性规则（MANDATORY — 输出前必须自检）"覆盖数字/角色名/时间地点物件三类一致性 + 自检指令（以 plot_point 1 为准）。L512-538 JSON 解析三 fallback 加 logger.warning + brace-extract 附 200 字符预览。
- **PM 地毯式审查**: 6 角度通过（mtime/规则文本/logger.warning 三处/_build_prompt 调用链路/三件套 mtime/索引标记）
- **pytest**: 7/7 PASS 不退化

### D.11 BGM-related P3 (PENDING 早期记录)
- **music_hint meta-prompt 层效用有限**: P3，等 MVP 用户反馈"水墨故事配 acoustic guitar 违和"再启动
- **秋梨膏温暖故事金句质量重试机制**: P3，等实际测 BGM 质量决定
- **用户自定义 BGM 上传**: P3，等用户反馈

### D.12 续写 / Phase 3 / Resonance 等产品功能（已记 D.6 D.7，提醒别忘）

### D.13 F-Hydrate-1 — Hydrate 后 progress 短闪烁（2026-04-28 Wave 1.2 Agent C 主动暴露）
- **优先级**: P3
- **现象**: 用户 F5 刷新或复制链接打开 `/create/[uuid]/generating` 时，hydrate 把 backend progress 还原到 React state，但 StageC text-gen useEffect 入口 `START_GENERATION` action 会 reset progress=0；~1.6s 后 polling 拉到真值恢复 — 短闪烁
- **暂缓原因**: 只是 1.6s 视觉闪烁，不影响功能正确性。Wave 1.2 大改造不能再扩范围
- **修复方向**: StageC text-gen useEffect 入口加 hydrate guard — 检测 state.generationProgress > 0 时跳过 START_GENERATION reset
- **触发条件**: MVP 后 Founder 体验时若觉得闪烁明显，启动修复
- **关联文件**: `frontend/src/components/create/StageC.tsx` text-gen useEffect 入口段（~L260-280）
- **后续路径**: 派 frontend agent 加 ~5 行 guard

### D.14 F-Lock-Family — confirmed 后中段后退到 outline/characters/scenes 没警告（2026-04-28 Founder 确认 P2 + 家族扩展）

- **优先级**: 🟠 **P2**（Founder 2026-04-28 15:35 确认升级，理由见下"决议背景"）
- **范围（家族 bug，3 处同源）**:
  - StageB `/outline` — 大纲已确认后未锁定
  - StageC char-preview `/characters` — 角色已确认后未锁定
  - StageC scene-preview `/scenes` — 场景已确认后未锁定

- **现象**: 用户 pipeline 中段（generationStatus === "generating"）按浏览器后退，URL 回到上述 3 个 stage 任一页面，看到熟悉的"编辑/确认"按钮。但 backend confirmed_outline / characters_confirmed / scenes_confirmed 已写入 + Stage 后续已基于此跑，用户再改无效

- **决议背景（2026-04-28 PM 深度论证 + Founder 确认）**:
  - **触发频率**: UX-16 Wave 1.2 实施后浏览器后退真能用了 → ~10-15% 用户路径会触发（trackpad 双指误触 / 鼠标侧键 / 好奇）
  - **用户损失**: 误以为可编辑 → 改了 → 没生效 → 困惑/愤怒（"产品在敷衍我"），比 P3 类小 bug 严重得多
  - **产品诚实性**: UX-16 承诺"能后退能复制能 F5"，如果后退看到 editable UI 但实际不可编辑 → 承诺打折
  - **修复成本极低**: 方案 A ~25 min（3 处 banner + 共享 lock hook + 隐藏编辑按钮）
  - **跟现有 P2 项同类严重度**: OBS-3 outline LLM 一致性 / R7-2 详情页 5 mock — F-Lock-Family 跟 OBS-3 同类（避免用户看到矛盾结果），明显比 R7-2 mock 严重（mock 用户能感知"按了没反应"，本 bug 用户以为生效实际没生效更隐蔽）

- **修复方案 A（推荐，3 处共享 hook）**:
  ```ts
  // 新建 frontend/src/hooks/useStageLock.ts
  function useStageLock(stage: 'outline' | 'characters' | 'scenes') {
    const { state } = useCreate();
    const isLocked =
      state.generationStatus === 'generating' || state.generationStatus === 'complete';
    return isLocked;
  }
  ```
  - StageB / StageC char-preview / StageC scene-preview 三处：
    - 顶部黄色 banner: "📌 大纲/角色/场景 已确认，AI 正在创作画面。如需修改请新建项目"
    - 内容只读显示（隐藏 input/textarea，改用纯文本展示）
    - 编辑/调整按钮隐藏或灰掉
    - "确认/开始绘制" 按钮替换为"返回创作进度"按钮（点击 router.replace `/create/[uuid]/generating` 或 `/preview` 取决于当前状态）

- **修复方案 B（备选，工作量大）**: 后端加 `/api/projects/{uuid}/reset` 端点重置 pipeline + 清理 storyboard / images / bgm + 允许重启 — 成本高（~2 hr backend + 浪费已生成 ¥1.5 数据）

- **暂缓原因**: 不是 P0/P1 阻塞 MVP，但是产品打磨批次的优先项。Wave 1-4 完成 + T7 测试通过后，启动下一批"产品打磨批次"时优先做

- **触发条件**: Wave 1-4 + T7 完成后启动下一批 — 优先级靠前

- **关联文件**:
  - 新建 `frontend/src/hooks/useStageLock.ts`
  - `frontend/src/components/create/StageB.tsx`（如果存在 — 否则在 confirm 阶段渲染处）
  - `frontend/src/components/create/StageC.tsx`（char-preview + scene-preview 双处）
  - `frontend/src/contexts/CreateContext.tsx`（确认 state.generationStatus 字段语义稳定）

- **后续路径**: 派 frontend agent (Sonnet 4.6 effort high) ~25 min 加共享 hook + 3 处 banner + 隐藏编辑入口

- **完整 UX 走查（修复后用户体验）**: 见 `.team-brain/TEAM_CHAT.md` 2026-04-28 15:30 PM 详细论证

---



---

## TASK-T6-FIXBATCH Wave 1.2 UX-16 ✅ 完成 (2026-04-28 15:25)

### 实施详情

- **URL 命名方案**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage ∈ {outline, characters, scenes, generating, preview, delivery}（6 枚举）
- **新建 2 文件**: `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` + `frontend/src/lib/createUrl.ts`
- **改 3 文件**: `frontend/src/app/create/CreateContent.tsx` + `frontend/src/contexts/CreateContext.tsx` + `frontend/src/types/create.ts`
- **3 层反馈环避免**: lastPushedUrlRef echo guard + derivedFromState 短路 + completion guard
- **npm build**: 21 routes 0 errors

### Agent C 主动暴露 2 遗留（P3 后续追踪）

1. **F-Hydrate-1**: Hydrate 后 StageC text-gen useEffect 入口 START_GENERATION 会 reset progress=0，~1.6s 后 polling 真值恢复 — 短闪烁。建议加 hydrate guard 优化（progress 已 hydrate 时跳 START_GENERATION）
2. **F-Outline-Lock-1**: 用户用浏览器后退到 `/outline` 想再编辑大纲，但 confirm-outline 已不可逆，StageB 未警告。建议加"已确认仅展示"提示 banner

### Wave 1.2 PASS 后下一步

进入 Wave 2 (Backend D + Frontend E + Backend F)。


### ~~D.15~~ ✅ aspect_ratio hardcoded → 修复完成（2026-04-28 Wave 2.5 Backend）
- **状态**: ✅ **已修复（Wave 2.5 Backend，2026-04-28）**
- **修复范围**:
  1. `seedream_generator.py` `_ASPECT_RATIO_TO_SIZE` 补 `3:4` / `4:3`（现 7 种比例，覆盖 frontend 全部 4 个选项）
  2. `pipeline_orchestrator.py` `run()` 加 `aspect_ratio: str = "2:3"` 参数（默认值向后兼容）
  3. `pipeline_orchestrator.py` L852: `generate_shot_image_phase2_safe(aspect_ratio=aspect_ratio)`（不再 hardcoded "2:3"）
  4. `pipeline_orchestrator.py` ARCH-1 写入块: `width/height/aspect_ratio` 从 `_ASPECT_RATIO_TO_SIZE` 动态查（不再 hardcoded）
  5. `job_manager.py` `run_story_generation_task()` 加 `aspect_ratio` 参数 + `pipeline.run()` 传值
  6. `projects.py` `_run_generation_in_background()` 加 `aspect_ratio` 参数
  7. `projects.py` `start_generation()` 传 `project.aspect_ratio or "2:3"`
- **验证**: pytest 292/292 passed（非 API 集成测试）✅
- **完整调用链路**: frontend POST /start-generation → projects.py（project.aspect_ratio）→ _run_generation_in_background → run_story_generation_task → pipeline.run() → generate_shot_image_phase2_safe → seedream/NB2 真生图 ✅

### D.16 types/create.ts StoryDetail.mood 跟 StoryCard 不一致（2026-04-28 Wave 2 E 审查发现）
- **优先级**: P3 文案/小 bug 杂项批
- **现象**: `frontend/src/types/create.ts` L170 `StoryCard.mood: string | null`（E 改）vs L201 `StoryDetail.mood: string`（E 漏）。StoryDetail extends StoryCard，子类型 override 更严格类型合法但逻辑不一致
- **不阻塞**: runtime 有 dashboard 详情页 StoryDetailContent.tsx R6 修的三层 fallback (user_selected_mood ?? mood ?? "—")，null 时不会 crash
- **修复方向**: L201 改成 `mood: string | null`
- **触发条件**: 凑齐文案/小 bug 一批改时一并修
- **关联文件**: `frontend/src/types/create.ts` L201
- **后续路径**: 凑下批 P3 文案修复批一并 1 行修复

---

## ✅ R7-3 P1 portrait 重生 bug — Wave 3.5 修复完成（2026-04-28 21:42）

**真因（Wave 3 Tester 发现 + Wave 3.5 Backend 深挖）**: 不在 adjust_character() Step 7 本身，是下游 `app/services/character_prompt_builder.py` `_build_human_description()` + `build_face_description()` 对 `physical/clothing/human` 字段直接调 `.get()`。T7 实测 LLM adjust 后这些字段保留为 **str 格式**（不是嵌套 dict），触发 `'str' object has no attribute 'get'`，被 try/except 吞掉，portrait 静默不重生。

**修复（仅改 1 文件，非高风险）**: `app/services/character_prompt_builder.py`
- `_build_human_description()` L102-116 _raw 变量 + isinstance(dict) 检查 + isinstance(str) fallback append
- `build_face_description()` L231/233 第 2 处同样 isinstance 防御

**实证（4 角度独立验证）**:
- ✅ pytest 24/24 不退化
- ✅ backend pid 27834 重启后真跑新代码（旧 pid 12059 已不监听 port）
- ✅ adjust API 实测：portrait mtime 20:37:34 → 21:42:03（+65min，文件真重写）
- ✅ DB chapter.characters_json[0].portrait_url + updated_at 真更新
- ✅ D.15 P0 aspect_ratio 链路完全保留无回归

**待办**: Tester 复测 adjust 路径独立验证（spawn 中），通过后进 Wave 4 DevOps 部署。

**Wave 3.6 Tester 独立复测 PASS（2026-04-29 15:12）**: 6 证据点全通过，str.get() 错误消除，portrait mtime 21:42:03→15:10:47，DB updated_at 2026-04-29T07:10:47Z，HTTP 200 1489KB，log 无异常。Wave 4 DevOps 部署可以启动。附带 P3: char_002 七岁小孩触发 CONTENT_SAFETY（独立问题，非 R7-3 bug）。

---

### D.17 CONTENT_SAFETY 脱敏策略族（2026-04-29 Founder 脑洞 + Wave 3.6 Tester 触发）

**起源**: BUG-2026-04-29-001 — Tester 复测 R7-3 时 char_002（七岁小孩"小宝"）adjust 触发 NB2 CONTENT_SAFETY 拦截（"7-year-old boy + red swollen eyes"）。Founder 提醒"还有其他方面需要类似脱敏策略吗"，PM 脑洞发散到 9 大维度。

**核心洞察**: 用户主观选择 → idea → Stage 1 outline LLM → Stage 4 storyboard prompt → NB2/Seedream 真生图，任何一环失守都拒。用户感知是"我故事就这样写了为什么生不出图"，跟 D.15 同类用户体验灾难（用户操作没生效）。

### 9 大脱敏维度（按风险 × 触发频率排序）

#### 🔴 P0 MVP 前必修

| # | 维度 | 触发示例 | 策略 |
|---|------|---------|------|
| **D.17.1** | 儿童角色（BUG-2026-04-29-001 实证）| `7-year-old + red swollen eyes`、儿童+受伤/哭闹/虐待 | 年龄 < 18 自动屏蔽负面身体词 → "若有所思/看着窗外" |
| **D.17.2** | 中文民俗（OBS-1 同源，T5 实证 4/18 触发）| 婚礼+红绸、唢呐悲怆、葬礼+白幡 | 民俗场景词改"传统装饰/民乐/告别仪式" |
| **D.17.3** | 暴力/受伤 | 流血、伤口、武器、打斗 | "血"→"汗"、"伤口"→"疲态"、"武器"→"工具" |

#### 🟠 P1 重要但部分有 fallback

| # | 维度 | 策略 |
|---|------|------|
| D.17.4 | 真实人物/名人脸（用户上传角色参考图）| 上传时脸部检测 + 名人识别 → 警告用户 |
| D.17.5 | 品牌/IP/版权角色（用户写"哈利波特那种小巫师"）| 词典屏蔽 + 引导改"魔法少年/卡通老鼠" |
| D.17.6 | 政治/历史/宗教敏感 | 硬词典直接拒接受 + 显式提示"不支持" |

#### 🟡 P2 长尾但用户痛点

| # | 维度 | 策略 |
|---|------|------|
| D.17.7 | 心理/医疗负面（抑郁/自杀/癌症）| 温情化："抑郁"→"心事重重"、"自杀"→"想离开" |
| D.17.8 | 性别/性向/年龄敏感词（紧身、丰满、性感）| "修身、健美、有魅力" |
| D.17.9 | 场景/职业敏感（监狱/夜店/性工作者）| "监狱"→"老房子"、"夜店"→"霓虹咖啡馆" |

### 修复方案（2026-04-29 15:50 Founder 决议简化 — 只 Layer 3 末端 fallback）

**Founder 反馈原文（重要保留）**:
> "我感觉有点过头，'7岁小孩眼眶红肿'我觉得不算是什么敏感内容，否则故事的生动性以及形象程度怎么保证？所以我觉得只要最后一层 'Layer 3 — 末端 fallback（生图被拒）'就好"

**核心原则**:
- 不主动脱敏（不破坏故事生动性 + 形象程度）
- 用户怎么写就怎么生
- 只在生图层真被拒时才兜底

### 唯一实施方案 — Layer 3 末端 fallback 链

```
Stage 5 真生图：
  NB2 调用
    ├─ ✅ 成功 → 写入 storyboard.shots[i].image_url，正常推进
    └─ ❌ CONTENT_SAFETY 拒 →
         PromptRewriter.rewrite(prompt) 自动改写
           ├─ ✅ 改写后 NB2 成功 → 正常推进
           └─ ❌ 改写后仍拒 →
                Seedream 试（不同审查阈值，可能比 NB2 宽松或严格）
                  ├─ ✅ 成功 → 正常推进
                  └─ ❌ 仍拒 →
                       占位图（灰底 + 警示图标）
                         + storyboard.shots[i].error_message="该画面因 AI 安全审查无法生成"
                         + 前端 StageD 提示用户"如不满意可微调画面文字"
```

### 实施细节

| 项 | 现状 | 待改 |
|----|------|------|
| `app/services/prompt_rewriter.py` PromptRewriter | 已存在（MAX_REWRITE_ATTEMPTS=2）| 升级改写质量（不只重写表层，按 9 维度分类替换更精准）|
| NB2 → Seedream 切换 | 现有架构 NB2 是 default，Seedream 是 fallback | 链路接通：NB2 拒 + 改写仍拒 → 自动切 Seedream，记录在 image_results.json 标记切换原因 |
| 占位图 + 提示 | StageD 现有 onError handler（Wave 1.1 P3-5）| 升级：error_message 字段从 backend 透传 + 前端显示具体原因 + 给用户重试按钮 |

### 关联文件

- `app/services/prompt_rewriter.py` 改写质量升级（参考 9 维度作为内部启发，不强制规则）
- `app/services/image_generator.py` NB2→Seedream 自动 fallback 链路
- `app/services/pipeline_orchestrator.py` 单 shot 失败 error_message 写回 storyboard
- `frontend/src/components/create/StageD.tsx` 失败 shot UI 显示具体原因 + 重试按钮

### 9 维度词典作为参考保留（不强制脱敏）

D.17.1-9 共 9 维度作为 PromptRewriter 升级时**内部参考启发**（让改写更精准），**不**作为前置过滤规则强制屏蔽用户输入。例如 PromptRewriter 收到拒了的 prompt 含"7岁小孩 + 红眼"，可启发"试试'7岁小孩 + 若有所思'"作为改写候选 — 但只在被拒后用，不主动改写用户原意。

### 触发条件

MVP 前 P1（不带病上线，Wave 4 部署前不做，作为下批产品打磨批次第 1 项）。

### 重要备注 — Seedream 首发可能性

**当前**: NB2 是 default 首发，Seedream 是 fallback
**未来可能**: Seedream 投入正式产品作为**首发生产**（待 Founder 确定）

**含义**:
- 如果 Seedream 转 default 首发，fallback 链改成 `Seedream 默认 → 拒 → NB2 fallback → 拒 → 占位`
- 测试用 Seedream 首发已经 T7 实证（D.15 P0 修复 PIL 16/16 通过 Seedream 生成）
- D.17 实施时需要考虑 default model 灵活配置（settings.IMAGE_GEN_PROVIDER 现已支持切换）

### 关联现有 PENDING

- **OBS-1** Seedream 中文叙事 sanitize 触发率 → 改用 Layer 3 fallback 后 OBS-1 现象不阻塞（自动 fallback）
- **R7-3** 修复 portrait 重生 + 但 adjust 调用 image_gen 仍可能撞 CONTENT_SAFETY → 同样走 Layer 3 fallback 处理
- **BUG-2026-04-29-001** 七岁小孩 CONTENT_SAFETY → Layer 3 fallback 完美兜底

---

### D.18 SceneImage width/height 元数据跟实际生成模型尺寸不一致（2026-04-29 Wave 4 T8 部署发现）

**优先级**: P3 元数据准确性

**现象**: T8 生产环境用 NB2 生 1:1 朋友圈，实际尺寸 1024×1024。但 SceneImage 元数据 width/height 从 `_ASPECT_RATIO_TO_SIZE["1:1"]="2048x2048"` 派生 → DB 写的是 2048×2048（错值）。

**根因**: D.15 修复时把 width/height 从 hardcoded 1664/2496 改成字典派生，但字典是 Seedream 标准（2048×2048），不是 NB2 标准（1024×1024）。

**影响**: 
- 视觉层面: 用户看到 1:1 ✅（D.15 P0 用户承诺保住）
- DB 元数据层面: width/height 不准（影响后续单 shot 重生成或局部编辑用 SceneImage 元数据作 prompt 参数时）

**修复方向**: model-aware width/height 派生
```python
SIZE_BY_MODEL = {
    "nb2": {"1:1": (1024,1024), "2:3": ...},
    "seedream": {"1:1": (2048,2048), "2:3": (1664,2496), ...},
}
width, height = SIZE_BY_MODEL[settings.IMAGE_GEN_PROVIDER][aspect_ratio]
```

**触发条件**: P3，与 D.15 同批未来"model 灵活配置"工作一起做（Seedream 转首发生产决议后）

**关联**:
- D.15 P0 ✅ 用户视觉承诺保住，本条仅元数据
- D.17 Layer 3 fallback 实施时也要 model-aware
- Seedream 首发可能性（PENDING D.17 备注）— 如果转 Seedream default，字典反而准了

---

### 🔴 D.17 二次修订（2026-04-29 17:25 Founder 决策最终版）

**之前两版方案均作废**（D.17 P3 三层架构 / Layer 3 fallback Seedream），最终方案：

**核心原则**: 全 pipeline 单一模型一致，**移除 NB2↔Seedream 自动切换**，失败用智能提示帮用户改 prompt。

**理由**: NB2 vs Seedream 视觉风格差太多。pipeline 内任一张图回退另一模型会破坏 18 张统一性，用户细看大概率发现异类。

**修复范围（必须删除现有混合 fallback）**:
1. `app/services/image_generator.py` L796-801 `generate_shot_image()` dispatcher fallback_callback 删除
2. `app/services/image_generator.py` L1389-1398 `generate_shot_image_phase2_safe()` dispatcher fallback_callback 删除
3. `app/services/seedream_generator.py` L720-740 `_run_fallback()` 改成返 sanitize_failure error，不调 NB2

**修复后流程**:
```
首选模型（NB2 or Seedream，看 settings.IMAGE_GEN_PROVIDER）
  ├─ ✅ 成功 → 返回
  └─ ❌ CONTENT_SAFETY 拒
        ↓
        PromptRewriter 改写 prompt（首选模型内）
        再调首选模型
          ├─ ✅ 成功 → 返回
          └─ ❌ 仍拒
                ↓
                [新增] prompt_safety_advisor.py Haiku 分析失败 prompt
                生成"建议改 X 为 Y"提示
                ↓
                占位图 + storyboard.shots[i].error_message + safety_advice
                ↓
                Frontend StageD 显示提示 + "改一下文字"按钮
```

**新建文件**: `app/services/prompt_safety_advisor.py`
- 接收: 失败 prompt + 失败 reason（CONTENT_SAFETY 类）
- 调用: Haiku 4.5 quick check
- 返回: { "suspected_terms": [...], "suggested_changes": [...], "user_message": "你的画面文字 'XXX' 触发了 AI 安全审查，可能因 'YYY'，建议改成 'ZZZ' 后重试" }

**全 pipeline 受影响环节**: portrait（Stage 2 UX-1）/ fullbody（Stage 5 prep）/ scene_anchor（Stage 5 prep）/ shots（Stage 5 真生图 18 张）— 全部走单一模型，无回退。

**Wave 5.1 实施中** — Backend agent 负责。

---

### ✅ O-1 + OBS-3 — Wave 5.1 AI-ML 完成（2026-04-29 17:33）

`app/services/story_outline_generator.py` L415-427 加内部一致性规则 + L512-538 JSON fallback OBS warning。详见 ai-ml-progress.

---

## ✅ Wave 5.1 完整 PASS（2026-04-29 19:30 PM 21+ 角度地毯式审查通过）

主索引完成标记:
- D.13 F-Hydrate-1 ✅
- D.14 F-Lock-Family ✅
- D.16 mood 类型 ✅
- T-1 milestone 文案 ✅
- D.17 二次修订 fallback 删除 + 智能提示 ✅
- D.18 SIZE_BY_MODEL ✅
- O-2 cap ✅
- T-2 scene callback ✅
- R7-2 点赞/分享/公开页（除导出/视频外）✅
- O-1 outline 一致性 ✅（Wave 5.1 早完成）

待: Wave 5.2 DevOps 部署（pytest + Alembic 002 upgrade head + push + rsync VPS + 通知 Ben）
