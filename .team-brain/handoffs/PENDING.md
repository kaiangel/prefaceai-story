# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 📋 当前待处理

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
