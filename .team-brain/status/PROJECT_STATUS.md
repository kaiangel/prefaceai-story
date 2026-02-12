# 序话Story 项目状态看板

> 最后更新: 2026-02-03 17:30
> 更新者: PM

---

## 项目总览

```
项目名称: 序话Story - AI条漫/短视频生成系统
目标: 用户输入创意 → 自动生成可发布的条漫或短视频
当前版本: v0.6.6
当前主线: 🔴 V3验收存在遗漏，需P0修复
核心内容: 都市情感短剧 (DEC-005)
产品形态: 条漫优先 → 短视频保留
Pipeline品牌: FrameSpark™
```

---

## Phase 进度

| Phase | 名称 | 状态 | 进度 | 负责 Agent |
|-------|------|------|------|-----------|
| 1 | 故事生成 | ✅ DONE | 100% | Backend |
| 2 | 图像生成 | ✅ DONE | 100% | Backend + AI_ML |
| 3 | 音频对齐 | ✅ DONE | 100% | Backend |
| 4 | 条漫MVP技术验证 | ✅ **完成** | 100% | PM + AI-ML + Backend + Tester |
| 4.5 | 视频合成 | 🔄 WIP | 5% | Backend |
| 5 | 前端开发 | 🟢 **WIP** | 30% | Frontend (Landing Page 基础版本完成) |
| 6 | 优化部署 | ⏳ TODO | 0% | DevOps |

---

## 本周重点 (2026-02-02 ~ 02-08)

### 🟡 P0 - 架构重构 + 通用性修复 (2026-02-03) **进行中**

**背景**: PM独立复核发现：
1. V3验收存在7类问题遗漏
2. **更严重**：TextOverlayService在8个测试文件中重复定义，主服务目录没有

**执行顺序（最新状态）**:
```
1️⃣ Backend 架构重构+核心修复 ✅ 完成
        ↓
2️⃣ AI-ML Prompt优化 ✅ 完成
        ↓
3️⃣ Tester V4验收 ✅ 完成 (4.5/5)
        ↓
4️⃣ PM独立综合复核 ✅ 完成 ⭐⭐⭐
   └── 发现3个P0问题仍未解决
        ↓
5️⃣ 等待Founder审核并决策 ← 当前
        ↓
6️⃣ V5修复任务分配
        ↓
7️⃣ Tester V5验收
```

**任务状态**:

| 阶段 | 任务 | 负责人 | 状态 |
|------|------|--------|------|
| 架构 | ARCH-1: 创建主服务 | Backend | ✅ |
| 架构 | ARCH-2: 整合最佳实现 | Backend | ✅ |
| 架构 | ARCH-3: 测试文件迁移 | Backend | ✅ |
| 核心 | CORE-1: strip_speaker_prefix | Backend | ✅ |
| 核心 | CORE-2: 气泡透明度 | Backend | ✅ |
| Prompt | 边缘填充约束 | AI-ML | ⏳ 待执行 |
| Prompt | 亲密行为约束 | AI-ML | ⏳ 待执行 |

**V3发现的7类问题处理进度**:
| # | 问题 | 负责人 | 状态 |
|---|------|--------|------|
| 1 | 黑边(3) | AI-ML | ⏳ PROMPT-1 |
| 2 | 白边(5) | AI-ML | ⏳ PROMPT-1 |
| 3 | 气泡重叠(3) | Backend | ✅ |
| 4 | Speaker前缀(8) | Backend | ✅ CORE-1 |
| 5 | 遮挡脸(2) | Backend | ✅ |
| 6 | 亲密行为(3) | AI-ML | ⏳ PROMPT-2 |
| 7 | 透明度(全部) | Backend | ✅ CORE-2 |

**Backend架构重构完成 (14:30)**: 删除 ~2075 行重复代码，所有故事类型自动受益
**AI-ML任务分配完成 (15:00)**: PROMPT-1 边缘填充 + PROMPT-2 亲密行为

**交接文档**: `HANDOFF-2026-02-03-001`
**全维度分析**: `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW_GENERALITY.md`

---

### ✅ 已完成 - Kai与Cici故事V2初步验收 (2026-01-31)

**结果**: V2验收通过 (41/42 = 97.6%)，但Founder发现10+类新问题需修复

| 问题类型 | V1 | V2 | 修复效果 |
|---------|-----|-----|---------|
| AI空白气泡 | 20+ | 0 | ✅ 100% |
| 留白/留黑 | 10+ | 0 | ✅ 100% |
| AI乱码文字 | 5+ | 0 | ✅ 100% |
| **新问题** | - | 10+类 | 🟡 修复中 |

---

## 上周重点 (2026-01-22 ~ 01-29)

### ✅ P0 - 条漫MVP技术验证 (DEC-006) **已完成**
- [x] **@PM**: 定义故事测试验收标准 ✅ `docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md`
- [x] **@AI-ML**: 设计文字内嵌Prompt模板 ✅ + 无文字Prompt模板 ✅
- [x] **@Backend**: 用 `gemini-2.5-flash-image` 测试 ✅ + TextOverlayServiceV2 ✅
- [x] **@Tester**: V1验收（文字乱码）❌ → V2验收 ✅ + 交叉验证（古风武侠）✅
- [x] **@PM**: 更新技术文档 CLAUDE.md ✅

**结论**: 无文字Prompt + 后处理叠加方案验证成功，可集成到主流程

### ✅ P0 - 条漫完整故事测试（15图）**已完成** 🎉
- [x] **@PM**: 分析参考案例、设计新故事《最后一碗面》✅
- [x] **@AI-ML**: 完善15图Prompt和文字脚本 ✅ `docs/COMIC_FULL_STORY_SCRIPT.md`
- [x] **@Backend**: 创建测试脚本 ✅ `tests/test_comic_full_story.py`
- [x] **@Tester**: 验收完整故事 ✅ **28/30 = 93.3% 通过**

**验收结果**: 角色一致性5/5 | 风格一致性5/5 | 文字可读5/5 | 情感强调3/5⚠️ | 回忆场景5/5 | 故事完整5/5
**待优化**: 红色强调支持中文感叹号 `！！！`
**交接**: `HANDOFF-2026-01-22-009` ✅ | **验收报告**: `test_output/comic_full_story_test/acceptance_report.md`

### 🟢 P0 - Landing Page 实现 (2026-01-29) **基础版本完成**
- [x] **@Frontend**: Next.js 14 项目初始化 ✅
- [x] **@Frontend**: 7个模块组件实现 ✅
- [x] **@Frontend**: 条漫素材集成 ✅
- [ ] **@PM**: 验收 Landing Page ⏳

**预览**: http://localhost:3000

### 🟡 P1 - 保留任务
- [ ] Phase 4: 视频合成 (Backend) - **保留，后续短视频模式需要**

### ⚪ P2 - 暂缓
- [ ] API 文档整理 (Backend)
- [ ] 6人场景一致性优化方案 (AI_ML)
- [ ] Docker 配置 (DevOps)

---

## 各模块状态

### Backend (后端)
```
状态: 🟢 正常
当前任务: Phase 4 视频合成设计
阻塞: 无
待解决: FFmpeg 集成方案选型
```

### Frontend (前端)
```
状态: 🟢 活跃 - Landing Page 实现中
更新时间: 2026-01-29 21:00
阻塞: 无

当前任务 (P0):
  1️⃣ Landing Page 实现 ← 🆕 当前任务
     - 交接文档: .team-brain/handoffs/HANDOFF-2026-01-29-010-LANDING-PAGE.md
     - 架构文档: docs/LANDING_PAGE_ARCHITECTURE.md
     - 视觉规范: docs/LANDING_PAGE_VISUAL_SPEC.md

待做:
  2️⃣ Next.js 项目初始化
  3️⃣ TASK-RESILIENCE-001-C: 友好失败提示

已完成:
  - UI/UX Pro Max Skill 安装
  - 序话Story设计系统生成
  - 技术栈确认 (Next.js 14 + shadcn/ui)
  - ✅ 三个全维度差异化原型 (2026-01-19)

已了解项目进展:
  - 产品形态: 条漫优先（静态图翻页）
  - 条漫MVP技术验证: 93.3%通过
  - TASK-RESILIENCE-001-A/B: 已完成 ✅
```

### Tester (测试)
```
状态: 🟢 正常
当前任务: 维护回归测试
阻塞: 无
待解决: E2E 测试框架选型
```

### AI_ML (AI/ML)
```
状态: 🟢 正常
当前任务: 角色一致性监控
阻塞: 无
待解决: Pro 模型成本优化
```

### DevOps (运维)
```
状态: ⚪ 未启动
当前任务: 待启动
阻塞: 等待 Phase 4/5 完成
待解决: 云服务选型
```

---

## 内容方向与质量基准 (DEC-005) ⭐ 新增

### 核心内容类型

| 类型 | 优先级 | 验证状态 |
|------|--------|----------|
| **都市情感** | P0 | ✅ 参考案例分析完成 |
| **家庭生活** | P0 | 待验证 |
| **悬疑反转** | P1 | 待验证 |
| **古装/武侠** | P1 | ✅ teststory6.5验证 |

### 质量基准参考案例

```
位置: still_image_storyref/IMG_0804-0818.jpg
类型: 都市情感短剧（15张图完整故事）
故事: 情侣因拍照技术差吵架 → 女生回忆前任冷暴力 → 领悟沟通重要性 → 和解
角色: 女主（红棕波浪发）、男主（黑短发）、前任（深色长发）
用途: 系统生成能力测试基准
```

### 待验证项 ✅ 已全部验证

- [x] 用参考案例故事线测试当前系统 ✅ V2方案验证通过
- [x] 表情细腻度是否达标 ✅ 4/5 良好
- [x] 回忆闪回效果是否可实现 ✅ 5/5 优秀（Shot 07-10 柔光效果）

---

## 关键指标

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| 角色一致性 | 100% (3人) | ≥95% | 🟢 |
| 单故事成本 | $9.35 | <$5 | 🟡 |
| 测试覆盖率 | ~70% | >80% | 🟡 |
| API 响应时间 | ~2s | <1s | 🟡 |

---

## 技术债务

| 编号 | 描述 | 优先级 | 状态 |
|------|------|--------|------|
| TD-001 | Pro 模型成本过高 | P2 | 待处理 |
| TD-002 | 缺少 API 文档 | P1 | 待处理 |
| TD-003 | 日志系统不完善 | P3 | 待处理 |

---

## 里程碑

| 里程碑 | 目标日期 | 状态 |
|--------|---------|------|
| Phase 3 完成 | 2025-01-05 | ✅ |
| 概念原型流程验收 | 2026-01-19 | ✅ |
| **设计系统确定** | 2026-01-19 | 🔄 原型已完成，等待创始人选择 |
| Phase 4 MVP | 2026-01-25 | 🔄 |
| Phase 5 MVP | 2026-01-31 | 🔄 待设计系统确定后启动 |
| 内测版本 | 2026-02-15 | ⏳ |

---

## 更新日志

### 2026-02-05 10:00
- **[Founder] 抖音运营指南完成** 🆕
  - 账号设置：名称「一话故事」、介绍「用一组图，讲一个故事」
  - 头像设计：2个Gemini 3 Banana Pro生图prompt（书+漫画格子+火花）
  - 《最后一碗面》完整发布方案：标题/描述/hashtag/封面/BGM
  - 交付物：`docs/DOUYIN_BRAND_GUIDE.md`

### 2026-02-03 21:30
- **[Backend] TASK-RENAME-KAI-TO-JERRY 完成** ✅
  - 172处"Kai"替换为"Jerry"
  - shot_12验证成功，显示"你好，Jerry"
  - 验证了通用工具的角色替换能力

### 2026-02-03 17:45
- **[Tester] V5验收完成** ✅
  - 评分：4.9/5（较V4的4.5/5显著提升）
  - 42/42 shots生成成功
  - Backend修复 4/4 通过，AI-ML修复 4/5 通过
  - 遗留：shot_34边缘填充问题(P1)

### 2026-01-30 11:00
- **[PM] Kai与Cici故事42张分镜大纲完成** ✅
  - 完成12幕42张详细分镜大纲
  - 每个Shot包含：场景/构图/对话/旁白/内心独白
  - 4个情感重点镜头：心动(10-11)、牵手(29)、拥抱(38)、脸颊之吻(40)
  - 交接文档已更新，通知 @AI-ML 开始设计Prompt
  - 交接文档：`.team-brain/handoffs/HANDOFF-2026-01-30-011-CC-KAI-STORY.md`

### 2026-01-30 10:00
- **[PM] Kai与Cici恋爱故事测试任务启动** 🆕
  - 接收创始人提供的恋爱故事需求
  - 分析角色参考图（Kai、Cici韩漫风格）
  - 确认视觉风格：Korean Webtoon Style
  - **重要**：参考图仅用于脸部特征，服装用故事中描述的

### 2026-01-29 19:30
- **[PM] Landing Page 架构定稿** 🎨
  - 与创始人讨论 Landing Page 设计方向
  - 阅读竞品分析（通义万相、Vidu、OiiOii、MovieFlow、HeyGen）
  - 确定首页形态：展示型（全屏条漫展示）
  - 确定主题模式：Dark Mode
  - 确定 Pipeline 品牌名：**FrameSpark™**
  - 设计7个模块的信息架构
  - 选择 Hero 区条漫素材（都市亲情+赛博朋克各4张）
  - 交付物：`docs/LANDING_PAGE_ARCHITECTURE.md`
  - 下一步：细化视觉规范（配色、字体、间距、动效）

### 2026-01-28 10:30
- **[Frontend] 上下文同步完成**
  - 读取TEAM_CHAT.md (~3000行)，了解所有项目进展
  - 任务优先级确认（创始人）：方案选择 → 项目初始化 → TASK-RESILIENCE-001-C
  - 更新所有progress文件：current.md、context-for-others.md、completed.md
  - 已了解：TASK-RESILIENCE-001-A/B 由 @Backend + @AI-ML 完成

### 2026-01-22 (深夜) 🆕 新任务启动
- **[PM] 条漫完整故事测试任务分配**
  - 分析参考案例 (IMG_0804-0818) 15图故事结构
  - 设计全新测试故事《最后一碗面》（父女亲情 + 日系温暖插画）
  - 创建任务交接 HANDOFF-2026-01-22-009
  - 任务链：AI-ML(脚本) → Backend(测试) → Tester(验收)
  - 文档：`docs/COMIC_FULL_STORY_TEST_PLAN.md`

### 2026-01-22 (晚间) ⭐ 重大里程碑
- **[PM] 条漫MVP技术验证全部完成** 🎉
  - V2验收：原测试5/5通过，交叉验证（古风武侠+水墨）5/5通过
  - 技术方案：无文字Prompt + 后处理叠加（TextOverlayServiceV2）
  - 文档更新：CLAUDE.md 新增「条漫文字渲染」技术方案章节
  - **当前状态**：临时方案（后续可切换高级模型原生渲染）
  - **待办**：情感强调升级为LLM驱动

### 2026-01-22 (下午)
- **[PM] 条漫MVP故事测试验收标准完成** ✅
  - 交付物: `docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md`
  - 5个验收维度: 文字内嵌、合成效果、表情细腻度、风格一致性、角色一致性
  - MVP通过条件: 综合分 ≥ 3.5 且所有单项 ≥ 3分
- **[创始人] 条漫MVP产品形态决策** ⭐ DEC-006
  - 产品形态: 条漫优先，短视频保留
  - 技术路线: 文字内嵌通过Prompt+Gemini生图实现 → 后改为后处理叠加
  - 测试模型: `gemini-2.5-flash-image`
- **[全体] V2迭代完成**
  - AI-ML: 无文字Prompt模板 ✅
  - Backend: TextOverlayServiceV2 ✅
  - Tester: V2验收 + 交叉验证 ✅

### 2026-01-22 (上午)
- **[创始人] 内容方向与质量基准确定** ⭐ DEC-005
  - 核心内容类型: 都市情感短剧 (P0)
  - 提供参考案例: `still_image_storyref/IMG_0804-0818.jpg`
  - 质量基准: 角色一致性、表情细腻度、场景连贯性、画风统一
- [全局] 所有Agent进度文件同步更新
- [Side Test] 书籍解说实验正式关闭

### 2026-01-19 18:30
- **[Frontend] 三个全维度差异化原型已完成** ✅
  - `create-story-conversational.html` - 对话式（聊天气泡布局 + 消息淡入弹跳）
  - `create-story-carousel.html` - 沉浸式卡片（全屏滑动 + 3D翻转切换）
  - `create-story-split.html` - 实时预览（左右分栏 + 内容淡入更新）
- [Frontend] 等待创始人选择最终方案

### 2026-01-19 17:30
- **[PM] 三个换色版本被否决** ⚠️
  - 创始人反馈：仅换色，布局/交互/动效完全一样，不是真正不同的体验
  - 重新定义三个全维度差异化方案：
    1. Conversational（对话式）
    2. Card Carousel（沉浸式卡片）
    3. Split Panel（实时预览）
- [PM] 已在TEAM_CHAT通知Frontend重做

### 2026-01-19 17:00
- [Frontend] 三个Light换色版本完成（Clean Flat / Bento Box / Aurora）
- **⚠️ 随后被创始人否决**

### 2026-01-19
- [Frontend] 创建故事页面概念原型完成 (Dark Mode原版)
- [Frontend] UI/UX Pro Max Skill 安装完成
- [Frontend] 序话Story设计系统生成：Dark Mode + Plus Jakarta Sans
- [Frontend] 设计Token确定：主色#3B82F6，CTA色#F97316
- **[PM] 设计系统正式确认** ⭐ DEC-004
- [PM] 接收UX验收能力升级
- [PM] 确认Mock先行策略，前端不再阻塞
- [Side Test] 书籍解说视频流程验证通过 (Tester)
- [Side Test] 图片生成测试 3/3 成功 (Tester)
- [PM] 书籍解说Side Test评估：技术可行，暂不纳入主线
- 修复测试脚本模型配置

### 2026-01-15
- [Side Test] 书籍解说视频Prompt模板完成 (AI-ML)
- [Side Test] 测试脚本编写完成 (Backend)

### 2025-01-05
- 初始化团队协作系统
- Phase 3 音频对齐完成
