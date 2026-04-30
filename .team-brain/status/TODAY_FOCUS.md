# 今日重点 (2026-04-28)

> 每天更新，所有 Agent 开工前必读
> **当前状态**: 🔄 TASK-T6-FIXBATCH Wave 0 PM 文档收尾完成 → 准备 spawn Wave 1.1 (A+B 并行)

### 🆕 12:10 更新
- T6 端到端测试 (10:57-11:50) 完成，pipeline 跑通但暴露大量 bug
- 17 条新 bug + 整合 PENDING 旧账 22 项 = **39 项总修复**（详见 PENDING.md TASK-T6-FIXBATCH）
- Founder 决策: 全部要修 + Wave 1 风险最低分两阶段 + ARCH-1 进 Wave 2 + Tester T7 真生图（控制成本）+ UX-16 dynamic route 方案 A

### 4 Wave 执行规划

| Wave | Agent | 工时 | 状态 |
|------|-------|------|:-:|
| Wave 0 PM 文档 | PM | 10 min | ✅ 完成 12:10 |
| Wave 1.1 A Backend + B Frontend 并行 | Sonnet × 2 | A ~2hr + B ~1.5hr | ⏳ 准备 spawn |
| Wave 1.2 C Frontend Opus (UX-16) | Opus | ~3hr | ⏳ 待 1.1 |
| Wave 2 D Backend + E Frontend + F ARCH-1 | Sonnet × 3 | ~50 min | ⏳ |
| Wave 3 G Tester T7 真生图 | Sonnet | ~1hr + ¥1.5 | ⏳ |
| Wave 4 H DevOps 部署 | Sonnet | ~30 min | ⏳ |

### T6 测试核心发现

**完整 pipeline 跑通**: ✅ 21 shots + Mureka BGM + 3 portrait 真生成 + max_concurrent=3 并行实证（~5 min）
**暴露阻塞 bug**: 🔴 StageD 预览图全 404 + 配乐不响（R7-12，root cause: StageD 缺 toAbsoluteUrl 转换）
**完成时大标题倒退**: 🔴 status='completed' 时 backend 把 stage 重置回 story_generation（R7-9 / B-6）
**Stage label 系统性滞后**: 🟠 ~4 分钟（progress_callback 用上一个 stage 名 — R7-5 + 架构 A-1）

### 高风险点（详见 PENDING.md A.1-D.3 共 12 条）

1. 🔴 角色一致性回归 — Agent A 严禁动 image_generator/storyboard_prompts/seedream_generator
2. 🟠 R7-3 + R7-4 必须配套修
3. 🟠 character_ready 切换时机改 → 加新 stage character_design
4. 🟠 UX-16 单独 spawn (Opus)，不混 Wave 1.1
5. 🟠 ARCH-1 18+ 处既有引用 → 抽到 Wave 2

### T6 关键数据

- T6 project uuid: `3c39ffb0-ae87-4e41-83fd-967838e45ccd` (project_id=15, chapter_id=4)
- 21 shots + 3 portrait + BGM 全部生成完成（DB ✓ 文件 ✓）
- BGM-1 illustration → "polished contemporary, piano-led" 字典命中 ✅
- OBS-4 user_selected_mood='治愈' 持久化到 DB ✅
- TASK-PARALLEL-M1 max_concurrent=3 实测生效 ✅

---

## 昨日 (2026-04-27)

### TASK-T5-FIXBATCH ✅
- 14 修复 + R5 ChapterStory schema + R6 dashboard 详情页 7 bug 全部完成
- 211/211 backend tests + npm build 20 routes 0 errors
- T6 测试今日验证全部端到端

### TASK-T5-FIXBATCH-R7 候选 ✅ 已诊断
- R7-1 Dashboard 列表 4 bug + R7-2 详情页 5 按钮 4 mock 已记 PENDING
- R7-1 → 进 Wave 2，R7-2 → 暂缓 MVP 后

### TASK-PARALLEL-M1 round 4 ✅
- Bug 1 dispatcher + Bug 5 图压缩 全修
- T6 实测验证 max_concurrent=3 生效，21 shots ~5 min

---

## 待办（不在 T6-FIXBATCH 内）

- TASK-API-COST-TABLE Background Agent 进行中
- TTS Key 填入 Background Agent 进行中
- 监控告警 R4 / TASK-STYLE-EXPANSION / 续写 Phase 3 / Resonance 时间线 — 暂缓

---

### 🆕 15:15 更新

**Wave 1.1 全部 PASS** — Agent A Backend (5 子任务一轮地毯式深挖 + 1 修复 round) + Agent B Frontend (7 子任务一轮通过)。

**关键教训**: PM 审查 grep 验证函数定义存在 ≠ 函数被调用。第一轮差点放过 estimate_remaining 死代码 + freshness check 缺 30s buffer。Founder 提醒后深挖追到调用链路最末端发现 — `feedback_carpet_review_deep_dive.md` memory + xhteam SKILL.md 第四步铁律双保险。

**已上线代码（10 文件）**:
- Backend 5: pipeline_orchestrator / job_manager / projects / reference_image_manager / chapters
- Frontend 5: 新建 lib/url.ts + StageC/StageD/StageE/BgmPlayer/StoryDetailContent

**Wave 1.2 准备 spawn**: Agent C (Frontend Opus 4.6) UX-16 dynamic route 单独跑（不混 1.1）。

---

### 🆕 15:35 更新

**D.14 F-Lock-Family 升 P2 + 家族扩展** (Founder 决议):
- 不进本批 Wave 2，作为下批产品打磨批次优先项
- 范围: outline / characters / scenes 三处同源（Agent C completion guard 只覆盖 completion 后，没覆盖 generating 中段后退）
- 修复成本 ~25 min frontend，详见 PENDING D.14

**Wave 2 spawn 准备就绪** — D Backend + F Backend ARCH-1 并行 + E Frontend 等 D 完成。

---

### 🆕 16:25 更新

**Wave 2 全 PASS**:
- D Backend (4 字段 + ISO 时区 + N+1 避免) 一轮通过
- F Backend (ARCH-1 chapter_scene_images 写入 + 19 处引用评估全兼容) 一轮通过
- E Frontend (mapProject 读字段 + StoryCard mood) 一轮通过 + P3 小遗漏 D.16 (StoryDetail.mood 类型不一致)
- npm build 21 routes 0 errors / pytest 211/211

**🔴 Wave 2 审查地毯式深挖暴露 D.15 P0 用户体验灾难**:
- pipeline_orchestrator.py L843+L850+L1071 hardcoded aspect_ratio="2:3" 是真生图实参（不是元数据）
- T6 Founder 选 1:1 朋友圈 → 21 shots 全 2:3，之前没对比就过了
- 教训永久保存: feedback_aspect_ratio_user_perception.md + MEMORY.md 索引

**Wave 2.5 准备 spawn**: Founder 选 A — 立即修 D.15 (~30 min Backend) → 再进 Wave 3 Tester

---

### 🆕 17:25 更新（@coordinator）

**subagent_type symlink 修复 + memory 地毯式清理**：
- `feedback_use_custom_subagent_type.md` 全文重写（旧"PM 主对话只能用内置 type"删除）
- `MEMORY.md` 索引同步（PM 协作）+ `reference_subagent_symlink.md` 新建（PM 协作）
- 验证：spawn `subagent_type: "backend"` UI 绿色 + 0 tool_uses + 2.8s 完成

**系统级影响**：所有 Founder agent 现在可直接 spawn 彩色自定义 subagent_type，派活 prompt 不再需 paste 角色身份。PM 17:15 已用真彩色 `tester` spawn Wave 3。

---

### 🆕 17:50 更新（@coordinator + @founder）

**8 Agent frontmatter 升级**（DEC-023）：
- ai-ml / pm / coordinator → `opus + xhigh`
- backend / devops / frontend / tester / resonance → `sonnet + xhigh`
- spawn 时不显式传则用 frontmatter 默认；显式传可覆盖

**理由**：deep reasoning 类保 opus / 执行类降 sonnet 节省 5x 成本 + 全员 xhigh 提质。详见 DECISIONS DEC-023。

**风险**：xhigh 可能是 Opus 4.7 专属，Sonnet 5 个 agent 实际可能跑 high。监控 1-2 周。

---

### 21:30 更新 — Wave 3 完成 + R7-3 立即修

**Wave 3 Tester (真彩色 subagent_type: "tester") T7 真生图验收**:
- 11 PASS / 1 FAIL / 0 未触发
- D.15 P0 完美修复（PIL 实测 16/16 = 2048x2048）
- 1 FAIL: R7-3 portrait 重生 `'str' object has no attribute 'get'` (projects.py L945 附近)

**Founder 决议 选项 A**: 立即 spawn Backend 修 R7-3 → Tester 复测 adjust 路径 → 再进 Wave 4 部署

**理由**: R7-3 跟 D.15 同类"用户操作但实际没生效"，按 D.15 升 P0 的态度不带病上线。

---

## 2026-04-29 15:50 跨日更新

Wave 3.5 R7-3 修复 + 3.6 Tester 复测全 PASS。D.17 CONTENT_SAFETY 简化为只 Layer 3 末端 fallback。

**当前状态**: TASK-T6-FIXBATCH 17 项原始修复 + R7-3 全部完成 → Wave 4 DevOps 部署准备 spawn 真彩色 devops。

**今日工作**: 详见 daily-sync/2026-04-29.md

---

### 17:00 跨日总结 — TASK-T6-FIXBATCH 完整结案 🎉

9 Wave 全部 PASS / 16 文件代码改动 / push 到 main / VPS 部署 / Ben 通知 / 生产 T8 4 验收 PASS。

**新发现 D.18 P3** — NB2/Seedream 尺寸字典不一致，用户视觉无影响（仍是 1:1），仅 DB 元数据。

**下一步**: 进入下一批"产品打磨批次" — 详见 PENDING D.13-D.18 + R7-2 + ARCH-2 + OPS-3。

**用户视角故事讲解**: 详见 TEAM_CHAT 17:00 PM 总结。

---

## 2026-04-29 17:35 Wave 5.1 启动 + 二次修订 D.17

**关键铁律确立**: Pipeline 必须用单一生图模型，不可 NB2/Seedream 混合（永久 memory `feedback_pipeline_single_model_only.md`）

**Wave 5.1 spawn 状态**:
- 🟦 Backend (subagent_type "backend") D.17 移除 fallback + 5 子任务: 🔄 运行中 (~3 hr)
- 🟩 Frontend (subagent_type "frontend") D.14 三 banner + 7 子任务: 🔄 运行中 (~2 hr)
- 🟨 AI-ML (subagent_type "ai-ml") O-1: ✅ 17:33 完成
