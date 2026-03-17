# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 📋 当前待处理

### T29-T37 — ✅ Founder 确认 → R7 E2E 已派发 @Tester (R6 平台级修复)

| 字段 | 内容 |
|------|------|
| **优先级** | P1-P3 |
| **来源** | R6 PM 独立复核 P-R1~P-R10 → Founder 决策 → PM 派发 |
| **Phase 1a** | ✅ 完成 + PM 审查 5/5 PASS |
| **Phase 1b** | ✅ @Backend T29+T32+OB-T29 + @AI-ML T34+T37 全部完成 |
| **Phase 2** | ✅ PM 全量 Code Review 10/10 PASS (03-12 22:15) |
| **Founder 确认** | ✅ 通过 (03-13 10:00) |
| **Phase 3** | ✅ R7 E2E 完成 @Tester (03-13 13:00) — **36/36 PASS** |
| **PM 独立复核** | ✅ 完成 (03-13 14:30) — **有条件通过**: 1 Bug(Shot_08 文字重复) + 2 Prompt 规则缺失 + 3 测试脚本不准 |
| **Founder 反馈** | ✅ 收到 (03-13 15:00) — 6 大板块指示 |
| **PM 分析** | ✅ 完成 (03-13 15:30) — 4 项代码研究 + 10 项任务清单 (T-A~T-J) |
| **交叉核对** | ✅ 完成 (03-13 16:00) — 发现 1 遗漏(PM-3 人群容差) → 新增 T-K → 11 项 |
| **风险评估** | ✅ 完成 (03-13 16:00) — 11 项 × 5 维度，零高风险，T-H 建议 Phase 1 仅日志 |
| **正式派发** | ✅ 已派发 (03-13 16:00) — 11 项 (T-A~T-K)，6 Phase 执行计划 |
| **Phase 1** | ✅ Backend 4项 (17:00) + AI-ML 4项 (17:30) 完成 |
| **Phase 2 Code Review** | ✅ 8/8 PASS (03-13 18:00)，T-D 1 项非阻塞附注 |
| **Phase 3** | ✅ Backend 2项 (19:00) + AI-ML 1项 (18:30) 完成 |
| **Phase 4 Code Review** | ✅ 3/3 PASS (03-13 19:30)，0 附注 |
| **Phase 5** | ✅ Backend T-H-Backend (19:45) 完成 |
| **Phase 6 Code Review** | ✅ 1/1 PASS (03-13 20:00)，1 非阻塞观察 (OB-1) |
| **OB-1 修复** | ✅ @Backend 完成 + PM Review PASS (03-13 20:20/20:35) |
| **DevOps 部署** | ✅ @DevOps 完成 + PM 复核 PASS (03-14 10:30 / 03-16 10:00) |
| **R8 E2E** | ✅ @Tester 完成 (42/44) + PM 复核有条件通过 (03-16 17:00) |
| **N13-FIX** | 🔄 @Backend spouse_of 对称补全 (已派发 03-16 17:00) |
| **IMG-SAFETY AI-ML** | ✅ 全部完成 + PM Review PASS |
| **IMG-SAFETY Backend** | ✅ PM Review PASS (03-16 20:00) |
| **Tester 验证** | ✅ 17/17 PASS + PM 确认 |
| **DevOps 部署** | ✅ TASK-DEPLOY-R8B 完成 + PM 审查 PASS |
| **TASK-REWRITER-CLEANUP** | ✅ @Backend 完成 + PM Review 3/3 PASS (03-17 12:00) |
| **OB 修复** | ✅ OB-1 @AI-ML + OB-2/3/4 @Backend — PM Review 全部 PASS (03-17 15:30) |
| **Dry-run 验证** | ✅ @Tester 7/7 PASS + PM 确认 (03-17 15:30) |
| **执行计划** | ~~全部 Phase~~ → ~~R8~~ → ~~IMG-SAFETY~~ → ~~Tester 17/17~~ → ~~DevOps R8B~~ → ~~Backend REWRITER-CLEANUP~~ → ~~Tester dry-run ✅~~ → **DevOps 部署** |

---

### TASK-BRAND-MANIFESTO — 🔄 已派发 @Frontend (P1, 并行线)

| 字段 | 内容 |
|------|------|
| **优先级** | P1（与 R8 E2E 并行，不互相阻塞） |
| **来源** | Coordinator 代 Founder 指令 (03-16 11:00) |
| **核心文档** | `docs/BRAND_MANIFESTO_EXPLORATION.md` (V2 宣言) |
| **PM 阅读+规划** | ✅ 完成 (03-16 11:30) |
| **PM 方案** | Pipeline 方案 B (精选核心) + About V2 完整版 + 技术标签→About 页 |
| **Founder 确认** | ✅ 3 个决策点全部确认 (03-16 12:00) |
| **PM 文案指引** | ✅ 已派发 @Frontend (03-16 12:00) — Pipeline 5 处改动 + About 5 段改动 |
| **Frontend 实现** | ✅ @Frontend 完成 (03-16 13:00) |
| **PM 审查** | ✅ 全部 PASS (03-16 17:30) |
| **执行计划** | ~~PM 规划~~ → ~~Founder 确认~~ → ~~文案指引~~ → ~~Frontend 实现~~ → ~~PM 审查~~ → **Founder 终审** |

---

### TASK-E2E-VALIDATE — ✅ Phase 1 通过（PM 复核 4.3/5，流水线跑通）

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **状态** | ✅ Phase 1 通过（Backend 17:39 完成 → Tester 18:15 验收 4.9/5 → **PM 复核 4.3/5**） |
| **Step 1a** | @backend — ✅ 29/29 shots 100% 成功 |
| **Step 1b** | @backend — ✅ TextOverlay 28/29 正确渲染（1张 none 正确跳过） |
| **Step 2** | @tester — ✅ 7/7 通过（PM 发现角色一致性维度验收不准，实际 ~68%） |
| **PM 复核** | 流水线技术上跑通 ✅，但角色一致性 68%（眼镜丢失 6/19）、narration 86% 过高 |
| **遗留问题** | 纳入 Phase 2：眼镜 prompt 强调(P1) + text_type 分布优化(P1) + 条漫风格(P0) + 模型升级(P0 待决策) |

### TASK-MODEL-UPGRADE — ✅ @Backend 模型全面升级 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | DEC-012 决策 4 → PM 派发 (2026-02-25 18:09) |
| **负责人** | @Backend |
| **说明** | 7 个服务文件：主力 Gemini Flash/Haiku → Sonnet 4.6，备用 → Gemini 3 Pro |
| **状态** | ✅ 完成 (2026-02-26 16:18)，PM 已核验 |

### TASK-STYLE-SLAMDUNK — ✅ @AI-ML 灌篮高手风格预设 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | DEC-012 决策 3 → PM 派发 (2026-02-25 18:09) |
| **负责人** | @AI-ML |
| **说明** | 在 StyleEnforcer 中新建 `slam_dunk` 风格预设 |
| **状态** | ✅ 完成 (2026-02-26 15:56)，PM 已核验 |

### TASK-TEXT-TYPE-OPT — ✅ @AI-ML text_type 分布优化 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | DEC-012 决策 2 → PM 派发 (2026-02-25 18:09) |
| **负责人** | @AI-ML |
| **说明** | Stage 4 prompt: narration ≤30%, dialogue 40-50%, thought 20-25%, none 5-10% |
| **状态** | ✅ 完成 (2026-02-26 15:56)，PM 已核验。实测分布待 E2E 验证 |

### TASK-STYLE-DEFAULT-FIX — ✅ @Backend 默认风格修复 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 反馈 → PM 派发 (2026-02-26 16:43) |
| **负责人** | @Backend |
| **说明** | 4 文件 8 处 `style_preset` 默认值 `"realistic"` → `"anime"` |
| **状态** | ✅ 完成 (2026-02-26 17:33)，PM 核验通过 |

### TASK-MODEL-UPGRADE-RETEST — ✅ @Backend slam_dunk 重跑验证 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 指示 → PM 派发 (2026-02-26 16:43) |
| **负责人** | @Backend |
| **说明** | slam_dunk + Sonnet 4.6 Stage 1-4，20 shots，关键词 20/20 |
| **状态** | ✅ 完成 (2026-02-26 17:33)，PM 核验通过 |

### TASK-E2E-TEST-2 — ✅ @Tester Slam Dunk + Sonnet 4.6 E2E 测试 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 派发 (2026-02-25 18:09)，PM 正式启动通知 (2026-02-26 17:48) |
| **负责人** | @Tester |
| **前置** | ✅ 全部满足 |
| **说明** | 完整 Stage 1→5 + TextOverlay，slam_dunk 风格，7项验收维度 |
| **状态** | ✅ 完成 (2026-02-27 14:33, Tester 4.3/5) + PM 独立复核通过 (15:41) |

### TASK-NB2-SWITCH — ✅ @Backend NB2 模型切换 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 派发 (2026-02-27 15:41)，Founder 确认 |
| **负责人** | @Backend |
| **前置** | 无 |
| **说明** | `image_generator.py:58` PRO_MODEL 改为 `"gemini-3.1-flash-image-preview"`（NB2），API 100% 兼容 |
| **状态** | ✅ 完成 (2026-02-27 16:09, Backend) + PM 核验通过 (16:32) — 5/5 shots, 848x1264, avg 25.9s |

### TASK-SLAMDUNK-COLOR — ✅ @AI-ML slam_dunk 彩色修复+增强 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 派发 (2026-02-27 15:41)，E2E-TEST-2 发现灰度/彩色不统一 |
| **负责人** | @AI-ML |
| **前置** | 无 |
| **说明** | Part A: slam_dunk preset mandatory 加 full color, forbidden 加 grayscale/monochrome; Part B: Stage 4 新增 color_mode 可选字段 |
| **状态** | ✅ 完成 (2026-02-27 16:05, AI-ML) + PM 核验通过 (16:32) |

### TASK-DIALOGUE-SYSTEM — ✅ @AI-ML + @Backend 对话系统三层重构 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 派发 (2026-02-27 15:41)，E2E-TEST-2 发现 dialogue 10%/thought 45% 失衡 |
| **负责人** | @AI-ML (Layer 2+3) + @Backend (Layer 1) |
| **前置** | 无 |
| **说明** | Layer 1: Stage 3 新增 dialogue_beats; Layer 2: Stage 4 text_type 规则重构(dialogue≥60%); Layer 3: 自检规则 |
| **状态** | ✅ 完成 (L1: Backend 16:09, L2+3: AI-ML 16:05) + PM 核验通过 (16:32) |

### TASK-TEAM-UNIFORM — ✅ @Backend 团队着装一致性 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | PM 派发 (2026-02-27 15:41)，E2E-TEST-2 发现队友球衣颜色不一致 |
| **负责人** | @Backend |
| **前置** | 无 |
| **说明** | Stage 2 CharacterDesigner 新增规则 5 "团队/组织着装一致性" |
| **状态** | ✅ 完成 (2026-02-27 16:09, Backend) + PM 核验通过 (16:32) |

### TASK-NB2-TEXT-TEST — ✅ @Tester NB2 中文渲染 A/B 测试 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | PM 派发 (2026-02-27 15:41)，Founder 确认 |
| **负责人** | @Tester |
| **前置** | ✅ TASK-NB2-SWITCH 已完成 + PM 核验通过 (16:32) |
| **说明** | 5 shots × 2 组：A组 TextOverlay vs B组 NB2 原生渲染，4 维度对比 |
| **状态** | ✅ 完成 (Tester 16:55, A=4.2 B=3.8) + PM 独立复核 (17:24, A=3.8 B=4.1) → Founder 决策：方案 B 全面切换 |

### TASK-NB2-NATIVE-TEXT — ✅ @Backend NB2 原生文字渲染切换 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 方案 B 决策 → PM 派发 (2026-02-27 17:24) |
| **负责人** | @Backend |
| **前置** | 无 |
| **说明** | `image_generator.py` 新增 `build_native_text_prompt()` + `use_native_text=True` 参数，TextOverlay 完整保留 |
| **状态** | ✅ 完成 (Backend 17:50) + PM 核验通过 (02-28 10:25) — 5/5 shots, 848x1264, avg 45.0s |

### TASK-AB-STYLE-DESC — ✅ @Tester 场域式 vs 命令式 A/B 测试 (P2)

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | Coordinator 建议 + Founder 同意 → PM 派发 (2026-02-27 17:24) |
| **负责人** | @Tester |
| **说明** | slam_dunk 5 shots A/B，B 组（场域式）胜出 4.5 vs 4.17 |
| **状态** | ✅ Tester 完成 (10:46) + PM 核验通过 (11:15)。**待跨风格验证后统一决策** |

### TASK-NATIVE-TEXT-ROBUSTNESS — ⚠️ @Backend 原生文字分类逻辑优化 (P2)

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | PM 核验 TASK-NB2-NATIVE-TEXT 时发现 → PM 派发 (2026-02-28 10:25) |
| **负责人** | @Backend |
| **说明** | 3 文件协同修改完成，但 PM 核验发现 image_generator.py 关键字回退与 text_overlay_service.py 不一致 |
| **状态** | ⚠️ PARTIAL PASS — 需 TASK-ROBUSTNESS-FIX 修复后 PM 复核 |

### TASK-ROBUSTNESS-FIX — ✅ @Backend 关键字回退逻辑修复 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | PM 核验 TASK-NATIVE-TEXT-ROBUSTNESS 发现 → PM 派发 (2026-02-28 11:15) |
| **负责人** | @Backend |
| **说明** | image_generator.py `build_native_text_prompt()` 补充 `"：\""` 检查 + `"内心"` → `"内心："` |
| **状态** | ✅ 完成 (Backend 11:31) + PM 核验通过 (14:52) — 3/3 修复点与 text_overlay_service.py 完全一致 |

### TASK-CROSS-STYLE-TEST — ✅ @Tester illustration 跨风格 E2E 测试 (P2)

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | Founder 决策 → PM 派发 (2026-02-28 11:15) |
| **负责人** | @Tester |
| **前置** | ✅ 全部满足 |
| **说明** | illustration + 完整 E2E (32 shots) + 场域式 vs 命令式 A/B。都市情感《拿铁上的告白》。一石三鸟：场域式泛化性 + DIALOGUE-SYSTEM 对话占比 + NB2 跨风格 |
| **状态** | ✅ Tester 完成 (02-28 16:31) + PM 独立核验通过 (03-02) — B组胜出 4.38 vs 3.88，DIALOGUE-SYSTEM 28.1% EXPECTED FAIL（暗恋题材结构性），等待 Founder 决策 |

### TASK-CREATE-UPGRADE — ✅ P0+P1+P2 全部完成, P2 待 PM 复验

| 字段 | 内容 |
|------|------|
| **优先级** | ✅ P0+P1+P2 全部完成 |
| **来源** | DEC-013 决策 → PM 计划制定 (2026-02-28 18:07) |
| **负责人** | @Frontend |
| **P0 状态** | ✅ 完成 (03-02) — 16 文件 (9新建+7修改), PM 复验 4.8/5 |
| **P1 状态** | ✅ 完成 (03-02) — 7 文件 (4新建+3修改), PM 复验 4.7/5 |
| **P2 状态** | ✅ 完成 (03-03) — 14 文件 (10新建+4修改), **PM 复验通过 4.8/5** (P3×1 + P4×3 不阻塞) |
| **P2 内容** | 注册页 + 工作台 + 故事详情 + StoryCard + StoryGrid + EmptyState + UserMenu + Header集成 + 登录链接 |
| **实施计划** | 详见 `.claude/plans/drifting-wiggling-wolf.md` |

### TASK-SPEAKER-PREFIX — ✅ @Backend 智能说话者前缀 (P2)

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | PM 派发 (2026-02-27 15:41) |
| **负责人** | @Backend |
| **前置** | P0/P1 任务完成后 |
| **说明** | TextOverlayService 智能前缀处理：画面可见角色→剥离前缀，画外音→保留前缀 |
| **状态** | ✅ 完成 (2026-02-27 16:09, Backend) + PM 核验通过 (16:32) |

### TASK-UI-STAGE-A — ✅ @Frontend Stage A 输入界面 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | DEC-011 用户旅程 → PM 派发 (2026-02-25 18:09) |
| **负责人** | @Frontend |
| **说明** | 故事创意文本框 + 篇幅三选一卡片 + 风格卡片网格（Mock 数据先行） |
| **状态** | ✅ 完成 (2026-02-26 16:00)，PM 复验 4.5/5 |

### TASK-IDENTITY-DESIGN — ✅ @AI-ML 角色一致性框架文档 (P2)

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | DEC-012 决策 1 → PM 派发 (2026-02-25 18:09) |
| **负责人** | @AI-ML |
| **说明** | 输出 `docs/CHARACTER_IDENTITY_FRAMEWORK.md`，Identity Anchors + 6层 Narrative Variables |
| **状态** | ✅ 完成 (2026-02-26 15:56)，PM 已核验 |

### ✅ Founder 决策 DEC-012 — 已决策 (2026-02-25)

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 已决策，PM 已派发 Phase 2 任务 |
| **决策 1** | 角色一致性：Identity Anchors + Narrative Variables 系统框架 |
| **决策 2** | narration 优化：@AI-ML 优化 Stage 4 prompt (目标 ≤30%) |
| **决策 3** | 风格：灌篮高手 (Slam Dunk) 漫画风 — 非韩漫 |
| **决策 4** | **所有文本生成** → Claude Sonnet 4.6，备用 Gemini 3 Pro，弃用 Haiku+Flash |

### TASK-DIALOGUE-DENSE-TEST — ✅ @Tester 完成 (P0, Step 1)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 决策 (2026-03-02) → PM 正式派发 (03-02 16:00) |
| **负责人** | @Tester |
| **前置** | 无（代码环境不动） |
| **说明** | 家庭晚餐争吵题材 E2E 测试（完整 Stage 1→5），验证 DIALOGUE-SYSTEM 在对话密集型故事中的表现。29 shots，illustration 场域式，核心指标 dialogue ≥60%。 |
| **状态** | ✅ 完成 (03-02 17:32, dialogue 79.3% PASS) + Founder 审查 29 shots + PM 独立分析完成 (03-03) |
| **结果** | dialogue 79.3% ✅ / 29/29 shots / 37.2s/shot / 角色一致性 ~95% / 零 text bleeding |
| **Founder 发现** | 4 项：角色一致性(Shot04/29) + 生图违和感(Shot05-07) + Shots太含蓄 + Pro模型规则过时 |
| **后续** | → TASK-SHOT-QUALITY-UPGRADE (Step 5) |

### TASK-STYLE-DESC-REWRITE — ✅ 全部完成 (Step 1-4 闭环)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | Founder 决策 (2026-03-02) → PM 正式派发 (03-02 16:00) → Founder 修正为串行 (03-02 16:31) |
| **负责人** | @AI-ML |
| **前置** | ✅ TASK-DIALOGUE-DENSE-TEST 已完成 (03-02 17:32) |
| **说明** | 14 个风格 style_description 场域式改写。**直接修改 `style_enforcer.py`**（含 style_description + 必要的 mandatory/forbidden 微调）+ 其他必要 prompt 文件。6 句结构标准见 TEAM_CHAT 16:00 派发消息。不再需要先输出文档。 |
| **Step 2 结果** | ✅ AI-ML 完成 (03-03): 15/15 风格改写，1 文件修改 (style_enforcer.py)，Python 加载 + enforce_prompt 验证通过 |
| **Step 3 PM Review** | ✅ 全部通过 (03-03 17:11): 15/15 PASS (含 slam_dunk 修复确认) |
| **Founder 决策** | ✅ 场域式批准为默认策略 (03-03 17:18) |
| **Step 4 Tester** | ✅ ink 4.2/5 + realistic 4.575/5 (03-03 18:05) |
| **Step 4 PM核验** | ✅ ink 4.1/5 + realistic 4.7/5, 与 Tester ±0.2 (03-04 10:26) |
| **状态** | ✅ **全部完成** — Step 1-4 闭环，场域式已落地 |

### TASK-SHOT-QUALITY-UPGRADE — ✅ 回归验证 PASS + PM 独立复核 4.36/5 → Bug #5 修复 → TASK-GIT-COMMIT-3 (P0, 8 项)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 审查 DIALOGUE-DENSE-TEST → PM 分析 → Founder 决策确认 (03-03) |
| **前置** | ✅ TASK-STYLE-DESC-REWRITE Step 1-4 全部完成 + PM 核验通过 (03-04) |
| **DEC-014** | ⭐ Founder 采纳 Plan A: 完全移除 previous_shot_image 传递 → 新增 SQ-8 |
| **Backend 预研** | ✅ 完成 (03-03): SQ-1/2/6 全部理解到位，准备就绪 |
| **说明** | **8 项** shot 生成质量改进（原 7 项 + SQ-8 新增） |

**8 项改进明细**：

| 编号 | 改进项 | 执行者 | 涉及文件 |
|------|--------|--------|----------|
| SQ-1 | 参考图文字标注（PIL 叠加角色名+类型，**不含 previous_shot**） | @Backend | reference_image_manager.py, scene_reference_manager.py |
| SQ-2 | 智能参考图选择（每角色1张，根据shot_size选portrait/fullbody） | @Backend | pipeline_orchestrator.py, image_generator.py, storyboard_prompts.py |
| SQ-3 | Stage 3 对话明确化规则（关键剧情词显式表达） | @AI-ML | ScreenplayWriter prompt |
| SQ-4 | Stage 4 叙事性视觉道具 + 空间纵深指令 | @AI-ML | StoryboardDirector prompt |
| SQ-5 | Stage 4 连续镜头全维度运镜差异化 + composition数据结构增强 | @AI-ML | StoryboardDirector prompt + storyboard结构 |
| SQ-6 | Shot Transition Validator（30度法则+景别/角度检测） | @Backend | storyboard_service.py |
| **SQ-7** | **✅ CLAUDE.md + guide Pro→NB2 + DEC-014 文档更新 (11+8=19处)** | **@PM** | **CLAUDE.md, shot_transition_improvement_guide.md** |
| **SQ-8** | **移除 previous_shot_image 传递 (DEC-014 Plan A)** | **@Backend** | **pipeline_orchestrator.py, image_generator.py, storyboard_prompts.py** |

**执行顺序**:
```
Step 5 (并行): ✅ 全部完成 — 5a @PM(SQ-7) + 5b @AI-ML(SQ-3,4,5) + 5c @Backend(SQ-1,2,6,8)
Step 6: ✅ @PM review 全部代码变更 — 8/8 SQ PASS (03-04 12:00)
Step 7: ✅ @Tester A/B 对比验证 PASS (B 4.27/5 vs A 3.58/5, +19.3%)
PM 独立复核: ✅ 完成 — SQ 改进有效 + 发现 4 Bug (P1×1+P2×2+P3×1)
TASK-SHOT-QUALITY-BUGFIX: ✅ 4 Bug 修复完成 + PM Code Review 4/4 PASS
回归验证: ✅ @Tester 4.36/5 + @PM 独立复核 4.36/5 (差异 0)
→ @AI-ML Prompt 优化: ✅ PM Review PASS
→ @Backend Bug #5 修复: ✅ PM Review PASS
→ Founder 确认: ✅
→ @DevOps TASK-GIT-COMMIT-3 (4daad77): ✅ 7 文件
→ @DevOps Batch A/B/C (131 文件) + push  ✅ 完成
→ @Backend TASK-SHOT10-REGEN ✅ + Bug #6 ✅ → PM 审查 + Founder 碰撞 → TASK-BUBBLE-SIMPLIFY ✅ 测试完成
→ PM Docker Compose 审查 PASS + Cloudflare SSL Full (Strict) 配置完成  ← 当前
```

### TASK-SHOT10-REGEN — ✅ 完成 + Bug #6 发现并修复

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | Founder 指示 → PM 派发 (2026-03-05 10:36) |
| **负责人** | @Backend |
| **状态** | ✅ 完成 (15:17) — shot_10 生成成功 + Bug #6 修复。PM 审查: Bug #5 PASS, 角色一致性 PASS, **Bug #6 气泡定位不够可靠** |

### TASK-BUBBLE-SIMPLIFY — ✅ 测试完成 → Founder 新证据 → TASK-PROMPT-BUBBLE 派发

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **来源** | PM 审查 Bug #6 + Founder 碰撞 → PM 派发 (2026-03-05 15:55) |
| **负责人** | @Backend |
| **测试结果** | 3 组均未渲染气泡 — 原因不是 NB2 能力不足，而是 prompt 架构导致对话指令被淹没 |
| **Founder 新证据** | Gemini 网页版实测: 漫画+写实两种风格均成功渲染指定中文对话气泡 |
| **PM 分析修正** | 初始结论（NB2 能力边界）被推翻 → 问题是 ~9000 字 prompt 中对话权重 < 1% |
| **状态** | ✅ 已闭环 → 后续由 TASK-PROMPT-BUBBLE 接棒 |

### TASK-PROMPT-BUBBLE — ✅ AI-ML 完成 + PM 审查 PASS + 后续任务派发

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 实测 + PM 分析 → PM 派发 (2026-03-05 19:00) |
| **负责人** | @AI-ML |
| **说明** | 方向 2+3 融合: 对话气泡融入场景描述 + 精简 prompt 冗余。2 × 10-shot 不同风格验证 |
| **AI-ML 完成** | ✅ (2026-03-05): 20/20 成功, 14/14 对话嵌入, `build_dialogue_scene_embed()` + System Instruction 精简 |
| **PM 审查** | ✅ PASS (2026-03-05 22:46): 20 张图片逐一查看 + 代码深度审查 + 6 项侧效评估（均低风险） |
| **状态** | ✅ 主体完成 → 后续 TASK-PROMPT-BUBBLE-FOLLOWUP |

### TASK-PROMPT-BUBBLE-FOLLOWUP — ✅ 完成 + PM 审查 + Founder 决策 → R2 派发

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | PM 审查 TASK-PROMPT-BUBBLE 发现交付缺口 → PM 派发 (2026-03-05 22:46) |
| **负责人** | @AI-ML |
| **AI-ML 完成** | ✅ (2026-03-06 11:00): 任务1 精确测量(8%精简) + 任务2 A/B/C 30张 |
| **PM 审查** | ✅ (2026-03-06 11:33): 任务1 PASS + 任务2 有条件PASS(3问题: C组幽灵气泡+B/C无参考图+死代码) |
| **Founder 决策** | 补测B/C有参考图 + 代码修复等补测后 + 繁体→多语言约束 |
| **状态** | ✅ 已闭环 → 后续由 TASK-PROMPT-BUBBLE-FOLLOWUP-R2 接棒 |

### TASK-PROMPT-BUBBLE-FOLLOWUP-R2 — ✅ 完成 + Founder 决策 speaker_format=english

| 字段 | 内容 |
|------|------|
| **优先级** | P0(补测) + P1(繁简约束) |
| **来源** | Founder 决策 + PM 派发 (2026-03-06 11:33) |
| **负责人** | @AI-ML |
| **AI-ML 完成** | ✅ (2026-03-06 14:10): 30/30 成功，三组 avg 4.4 refs/shot，text_language=zh-CN 生效 |
| **PM 审查** | ✅ (2026-03-06 14:45): C 组淘汰(shot_07 乱码)，B 组推荐(语言一致+扩展性) |
| **Founder 决策** | ✅ speaker_format='english' 确定 |
| **状态** | ✅ 已闭环 → 后续 @Backend 生产代码修改 |

### TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY — ✅ 完成 + PM Code Review PASS

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 决策 speaker_format=english + PM 派发 (2026-03-06 14:45) |
| **负责人** | @Backend |
| **Backend 完成** | ✅ (2026-03-06 14:56): `image_generator.py:848-853` 传入 3 参数 |
| **PM Code Review** | ✅ (2026-03-06 15:26): 12 维度零问题 PASS |
| **状态** | ✅ **闭环** — speaker_format 全链路完成 |

### TASK-DEPLOY-PREP — ✅ Founder 批准 → TASK-DEPLOY-EXEC 实际部署中

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | PM + Founder |
| **负责人** | @DevOps |
| **Step 1** | ✅ VPS 环境检查 (10 维度 PASS) |
| **Step 2** | ✅ Docker Compose 方案 (PM 审查 PASS, 6 项修改建议) |
| **SSL** | ✅ Cloudflare Full (Strict) + Origin Certificate (到期 2041) |
| **Step 3** | ✅ 更新完成 + PM 二次审核 PASS (4/4 落实 + Nginx HTTPS 8 维度验证) |
| **Founder 批准** | ✅ (2026-03-06 16:15) |
| **TASK-DEPLOY-EXEC** | ⏳ @DevOps 执行 VPS 实际部署 (Step 1-4) |
| **前置 D1** | Frontend `next.config.mjs` output: 'standalone' — DevOps 遇到时通知 PM |
| **状态** | ⏳ @DevOps 执行中 |

### TASK-E2E-REGRESSION — ✅ 分析完成 → 修复完成 → PM Code Review PASS → 待 Tester E2E 验证

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 派发 (2026-03-06 16:00) |
| **负责人** | @Tester |
| **Tester 完成** | ✅ (2026-03-06): 20/20 shots 成功, 4.63/5 |
| **PM 深度分析** | ✅ (2026-03-06 17:30): 发现 P0 架构缺陷 + 5 项问题 |
| **Backend 修复** | ✅ (2026-03-09): Issue #2 模型配置 + style_preset 回退 (4 处) |
| **AI-ML 修复** | ✅ (2026-03-09): Issues #1/#3/#4/#5 (10 处) |
| **PM Code Review** | ✅ (2026-03-09 12:00): 14/14 PASS, 0 阻塞 |
| **Founder 决策** | Stage 1-4 备用模型统一 Flash (2026-03-09) |
| **TASK-BACKUP-MODEL-FLASH** | ✅ @Backend 完成 (11:07, 3文件12处 Pro→Flash) |
| **TASK-E2E-REGRESSION-R2** | ✅ @Tester 完成 (14:00, 20/20, 4.65/5) |
| **PM 独立复核** | ✅ 完成 (15:00, 4.63/5, 5 新发现 F1-F5) |
| **PM F1-F5 深挖** | ✅ 完成 (15:39, 7 项修复任务 T1-T7 已派发) |
| **Step 4 Code Review** | ✅ 22/22 PASS (17:30) + 3 非阻塞观察 (OB-6/7/8) |
| **Step 5 派发** | ⏳ @Tester TASK-E2E-REGRESSION-R3 (2 故事 × 10 shots, 10 维度) |
| **状态** | 🟡 **Step 5 E2E 验证中** — 等 Tester 完成后 PM Step 6 独立复核 |

### E2E 回归 6 项问题修复状态（R1 已闭环）

| # | Issue | 严重性 | 修复 | Code Review |
|---|-------|--------|------|------------|
| 1 | text_overlay 缺失 | P0 | ✅ AI-ML (schema+rules+dialogue_beats) | ✅ PASS |
| 2 | DEC-012 模型未落地 | P1 | ✅ Backend (Claude primary, Gemini fallback) | ✅ PASS |
| 3 | SQ-1 标签泄露 | P1 | ✅ AI-ML (DO NOT reproduce label text) | ✅ PASS |
| 4 | 单角色三只手 | P2 | ✅ AI-ML (Rule #9 两路径) | ✅ PASS |
| 5 | NB2 乱码文字 | P2 | ✅ AI-ML (TEXT-FREE system instruction) | ✅ PASS |
| 6 | Story B 第 3 角色缺失 | P3 | N/A (测试设计问题) | N/A |

### TASK-F1-F5-FIX — 🟡 Step 6 完成 → Step 7 修复中 (T1-T10 PASS + T11-T16 新增)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | PM 独立复核 F1-F5 深挖 (03-09) + Step 6 PM 独立审查 (03-10) |
| **状态** | ✅ **R4 验收通过** — Step 9 Tester 14/16 PASS + Step 10 PM 独立审查确认 → 平台级改进计划 (S1-S6) |

**10 项修复任务**：

| # | 任务 | 负责人 | P | 涉及文件 | Step | 状态 |
|---|------|--------|---|---------|------|------|
| T1 | Stage 3 dialogue_beats type + 覆盖 | @AI-ML | P0 | screenplay_writer.py | 1 | ✅ PASS |
| T2 | Stage 4 MAPPING RULES 增强 | @AI-ML | P0 | storyboard_director.py | 1 | ✅ PASS |
| T3 | Stage 3 plot_points 1:1 硬约束 | @AI-ML | P0 | screenplay_writer.py | 1 | ✅ PASS |
| T4 | pipeline dialogue TextOverlay 跳过 | @Backend | P0 | pipeline_orchestrator.py | 1 | ✅ PASS |
| T5 | _validate_storyboard() speaker 检查 | @Backend | P1 | storyboard_director.py | 3 | ✅ PASS |
| T6 | build_dialogue_scene_embed() speaker 降级 | @Backend | P1 | image_generator.py | 3 | ✅ PASS |
| T7 | _rebalance_text_types() 分布后处理 | @Backend | P2 | storyboard_director.py | 3 | ✅ PASS |
| T8 | pipeline compound type 拆分渲染 | @Backend | P2 | pipeline_orchestrator.py | 3 | ✅ PASS |
| T9 | use_native_text 参数同步 | @Backend | P3 | pipeline_orchestrator.py | 3 | ✅ PASS |
| T10 | Stage 3 thought 比例强化 | @AI-ML | P3 | screenplay_writer.py | 3 | ✅ PASS |

**执行顺序**：
```
Step 1 (并行): @AI-ML T1+T2+T3 + @Backend T4              ✅ 完成
Step 2: PM Code Review                                      ✅ 14/14 PASS
Step 3 (并行): @Backend T5+T6+T7+T8+T9 + @AI-ML T10       ✅ 完成
Step 4: PM Code Review                                      ✅ 22/22 PASS + 3 非阻塞观察 (OB-6/7/8)
Step 5: @Tester E2E 验证 (2 故事 × 10 shots)               ⏳ 已派发
Step 6: PM 独立复核                                          ✅ 完成 (03-10)
Step 7 Phase 1: @Backend T11+T12+T16 / @AI-ML T13+T15       ✅ 完成
Step 7 Phase 2: @AI-ML T14                                    ✅ 完成
Step 8: PM Code Review                                        ✅ 5/6 PASS + 2 修复项
Step 8.5: @Backend T13-INT + T12-UNIFY                        ✅ 完成 + PM 复核 PASS
全局 Double-Check: PM                                          ✅ 通过 + CLAUDE.md 修正
PRO_MODEL 命名修复: @Backend                                   ✅ 完成 + PM 确认 PASS
Step 9: E2E R4 @Tester                                        ✅ 14/16 PASS + 2 PARTIAL
Step 10: PM 独立深度审查                                       ✅ 同意 Tester 判定，R4 验收通过
→ T17-T22 平台级改进 Phase 1                                   ✅ 全部完成
→ Phase 2: PM Code Review                                      ✅ 6/6 PASS + T17-FIX 完成
→ Founder 决策                                                  ✅ T17 异步已改 / T18 保守留着
→ Phase 3: R5 E2E 回归                                         ✅ 20/21 PASS + 1 PARTIAL
→ PM 独立深度审查 R5                                             ✅ 6 项平台系统性问题 (P-S1~P-S6)
→ 安全评估 + 模型检查 + 成本分析                                  ✅ 全部通过
→ T23-T28 派发 (参考图NB2+关系表+标题校验+对话规则+Stage4增强+道具检测)  ✅ 已派发
→ Phase 1: @Backend T23+T24+T28 / @AI-ML T25+T26+T27             ✅ 全部完成
→ Phase 2: PM Code Review T23-T28                                 ✅ 4 PASS + 2 Bug PM修复
→ Founder 确认                                                     ✅ 通过
→ Phase 3: @Tester R6 E2E (1故事, 27维度, 全新题材)               ✅ 27/27 PASS 满分
→ PM 独立复核                                                      ✅ 完成 (21/27 PASS, 9项平台级发现)
→ Founder 决策 P-R1~P-R9                                           ⏳ 等 Founder
```

**Step 7 新增任务 (T11-T16)**:

| # | 任务 | 负责人 | P | 状态 |
|---|------|--------|---|------|
| T11 | 移除参考图 PIL 标签 | @Backend | P0 | ✅ PASS |
| T12 | TextOverlay native_text 模式修复 | @Backend | P0 | ✅ 有条件 PASS (T12-UNIFY 待合并) |
| T13 | 条漫叙事自足 prompt | @AI-ML | P1 | ✅ 常量 PASS / ⚠️ 集成待完成 (T13-INT) |
| T14 | 角色风格统一 (reference_image_manager.py) | @AI-ML | P1 | ✅ PASS |
| T15 | NB2 气泡重复抑制 | @AI-ML | P2 | ✅ PASS |
| T16 | OB-6 降级分支补充 | @Backend | P3 | ✅ PASS |

### TASK-LOGO-REPLACE — ⏳ @Frontend 全站 Logo 替换 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 直接派发 → Coordinator 转达 (2026-03-16) |
| **负责人** | @Frontend |
| **前置** | 无（资源文件已就绪 `frontend/public/brand/`） |
| **说明** | 4 个组件 Sparkles→新 logo。双版本体系：Header 用 D_v1 加粗版(线条)，Favicon 用 D_v2 圆形(实心) |
| **修改范围** | Header.tsx, SubPageHeader.tsx, CreateHeader.tsx, Footer.tsx |
| **资源更新** | ⚠️ 2026-03-16 16:00 资源已优化（加粗+二值化+圆形favicon），用最新文件 |
| **验收** | 全页面走查，所有 logo 位置显示新图标 + favicon 为圆形 |
| **状态** | ⏳ 待 @Frontend 执行（资源已就绪 v2） |

### TASK-BRAND-MANIFESTO — 📋 @PM 品牌宣言前端整合 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **来源** | Founder 指令 → Coordinator 派发 (2026-03-16) |
| **负责人** | @PM（规划+文案审核）→ @Frontend（实现） |
| **前置** | PM 完整阅读 `docs/BRAND_MANIFESTO_EXPLORATION.md` |
| **说明** | 品牌宣言 V2 整合到首页 Pipeline 模块（主战场）+ About 页重写（保留核心团队）+ 技术标签迁移 |
| **Founder 指示** | ① Pipeline 需考虑认知负荷（全量 vs 精选） ② About 页除团队外可全面重写 ③ 技术标签找新位置 |
| **关键文档** | `docs/BRAND_MANIFESTO_EXPLORATION.md`（V2 宣言 + 深度分析） |
| **状态** | 📋 待 @PM 阅读文档 + 制定实施计划 |

### TASK-STYLE-THUMBNAILS — ⏳ @AI-ML 15 种风格缩略图生成 (P0)

| 字段 | 内容 |
|------|------|
| **优先级** | P0 |
| **来源** | Founder 指令 → Coordinator 派发 (2026-03-10) |
| **负责人** | @AI-ML |
| **前置** | 无（与 E2E R4 并行，不阻塞主线） |
| **说明** | 为 create 页面 15 种视觉风格生成 NB2 缩略图。统一场景（城市街头年轻女生），只变风格。1:1 宽高比，中文命名，prompt 保存 |
| **交付物** | `test_output/manualtest/style_thumbnails/` — 15 张 PNG + 15 份 prompt |
| **验收** | Founder 人工审图 → 通过后 @Frontend 集成到 create 页面 |
| **状态** | ⏳ 待 @AI-ML 执行 |

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

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-GIT-COMMIT-2** | **Git提交12天积压变更 (3批: 926f284+825aece+e05bbd2, 67文件)** | **2026-02-24 11:42** ✅ |
| **TASK-SCENE-REF-ASPECT** | **场景参考图宽高比修复 16:9→2:3 (DEC-010)** | **2026-02-24 11:37** ✅ |
| **TASK-REF-PREPROCESS** | **参考图预处理 5步闭环 (DEC-009, 代码保留作安全网)** | **2026-02-24** ✅ |
| **TASK-LP-PAGES-FIX** | **LP子页面4项修复 (PM复验通过 4.8/5)** | **2026-02-14 17:35** ✅ |

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-ASPECT-2x3** | **宽高比统一改为 2:3（9文件26处，PM核验通过）** | **2026-02-14 11:01** ✅ |
| **TASK-LP-POLISH** | **Landing Page 2项代码质量修复（PM复验通过 5.0/5）** | **2026-02-12 16:11** ✅ |
| **TASK-LP-FIX** | **Landing Page 8项修复（PM复验通过 4.5/5）** | **2026-02-12 15:45** ✅ |
| **TASK-GIT-COMMIT** | **Git提交LP修改+文档 (Step1 a6a0359 + Step2 08a0e9f, PM核验通过)** | **2026-02-12 17:27** ✅ |
| **HANDOFF-2026-02-12-001** | **TASK-GIT-INIT Git仓库初始化** | **2026-02-12** ✅ |
| HANDOFF-2026-02-03-001 | Backend 架构重构+核心修复 | 2026-02-03 |
| HANDOFF-2026-02-02-015 | P1修复（碰撞检测+气泡） | 2026-02-02 |
| HANDOFF-2026-02-02-013 | P0修复（Speaker前缀+气泡位置） | 2026-02-02 |
| HANDOFF-2026-01-31-012 | 配置调整 | 2026-01-31 |
| HANDOFF-2026-01-30-011 | 42张测试脚本 | 2026-01-30 |
| HANDOFF-2026-01-29-010 | Landing Page 交接 | 2026-01-29 |
| HANDOFF-2026-01-22-009 | 条漫完整故事测试 | 2026-01-22 |
