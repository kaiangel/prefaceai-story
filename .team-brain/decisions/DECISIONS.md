# 决策记录

> 重要技术和产品决策的永久记录
> 所有 Agent 可查阅，避免重复讨论已决定的事项

---

## DEC-036: Wave 14 (5/15 18:00) — 4 RISK 全修 + anthropomorphic_animal 真根因 + B51 fallback 6 中文来源

**日期**: 2026-05-15 17:55
**决策者**: @Founder (PM 推荐 + Explore audit)
**影响范围**: character_types.py + character_prompt_builder.py + character_designer.py + reference_image_manager.py + storyboard_director.py + story_music_extractor.py + shot_validator.py (7 文件)

### 问题

test19 第三次跑通后 Founder 发现:
- 🔴 Shot 8 是女孩 — 5 角色全画成人类 (anthropomorphic_animal 不被识别)
- 🟡 BGM 失败 ('str' object has no attribute 'get')
- 🟡 ShotValidator IMAGE_TOO_LARGE 5.7MB fail-open (Wave 11.4 设 target 4.5MB binary 但 base64 后超 5MB)
- 🔴 B51 fallback 仍触发 2 次 (Wave 12+13 只修 2/6 中文来源)

PM + Explore agent 双 audit 发现 6 新 RISK.

### 最终决策

✅ Wave 14 全修 4 RISK (P0+P1, 内测前必修):
- AI-ML: RISK-T19-6 anthropomorphic_animal 全栈映射 (5 处代码)
- Backend #1: RISK-T19-8 B51 fallback 6 中文来源真根因
- Backend #2: RISK-T19-5 BGM dict/str 双修 (visual_tone + atmosphere)
- Backend #3: RISK-T19-7 IMAGE_TOO_LARGE 真压缩 (3.5MB target)

POST_BETA: #8 / #13 / #14 / #17 + 新 #27 emotional_arc

### 实证

- 319/319 全 regression PASS
- 0 越权 git status (7 文件)
- Backend 重启 PID 10553 含改动
- Frontend HTTP 200

### 后续

- [x] Wave 14 全完成 + PM 8 维度审查通过
- [ ] Founder 第四次 e2e 测试 test20 (验证 5 动物画成动物 + Stage 4 0 fallback + BGM 真生成 + ShotValidator 真验证)
- [ ] 内测启动决策

---

## DEC-035: Wave 13 (5/15 16:42) — 2 RISK 修 (T19-3 frontend storyboard progress + T19-4 scene_heading 中文)

**日期**: 2026-05-15 16:20
**决策者**: @Founder (PM 推荐方案 C)

### 问题
- Wave 12 atmosphere 修一半 (漏 scene_heading), test19 第二次 Pipeline failed
- Frontend storyboard 阶段 progress 0% 卡死 (Wave 11.4 image_generation 修了, storyboard 没修)

### 决策
方案 C: Backend + Frontend 并行
- Backend: screenplay_writer.py + storyboard_director.py scene_heading 双修 (ENGLISH ONLY + _contains_chinese 替换)
- Frontend: useETA hook + StageC.tsx generationProgressRef live ref + subtitle 全 stage 统一

### 实证
- 261/261 PASS
- test19 第三次跑通 25 shots
- Frontend storyboard progress 真显示 backend 真值

---

## DEC-034: Wave 12 (5/15 15:25-15:55) — 4 RISK 修 (T19-1 atmosphere + T17-8 原地重启 + T19-2 friendly UI + T17-7 后台按钮)

**日期**: 2026-05-15 15:25
**决策者**: @Founder (PM 推荐方案 C: 治根 + 加原地重启 + UI 友好化)

### 问题
test19 5/15 15:13 Pipeline failed at Stage 4: Shot 26 中文 21% (Wave 10.1 atmosphere hotfix 副作用)

### 决策
4 agent 并行修:
- Backend #1 (T19-1 P0): screenplay_writer.py + storyboard_director.py atmosphere 真根因双修
- Backend #2 (T17-8 P0 升级): chapters.py + pipeline_orchestrator.py 加原地重启 endpoint
- Frontend (T19-2 P1 + T17-8 配套): StageC.tsx friendly UI + 原地重启按钮
- Frontend mini (T17-7 P2 升级): StageC.tsx L1144 后台按钮扩展到 storyboard

### 实证
- 243/243 PASS
- test19 原地重启完美工作 (跳过 Stage 1-3 + R4-1/R4-2 等待)

---

## DEC-033: Wave 11 收尾决策 — timeout 配置统一 + actual_elapsed_sec 消费 (2026-05-14 23:30)

**日期**: 2026-05-14 23:30
**决策者**: @Founder (Pre-内测 audit 后)
**影响范围**: app/config.py + app/services/seedream_generator.py + frontend/src/hooks/useETA.ts + StageC.tsx + CreateContent.tsx

### 问题

Pre-内测地毯式 audit (23:00, PM + Explore agent) 找到 2 新 RISK:

1. **RISK-NEW-2 P2**: IMAGE_GENERATION_TIMEOUT 配置不一致
   - config.py L33: 120 (旧 NB2 时代)
   - seedream_generator.py L103: SEEDREAM_TIMEOUT_SEC = 210 (Wave 11.4 改, hardcode)
   - 维护性隐患, 下次改容易漏

2. **RISK-NEW-1 P3**: actual_elapsed_sec 死字段
   - Backend chapters.py L367 真返字段 (Wave 11.3 Backend #3 加)
   - Frontend useETA hook + StageC 都不消费
   - 浪费一次往返字段传输

### 方案选项

**RISK-NEW-2**:
1. **方案 A (选)**: config.py 改 210 + seedream_generator.py 从 settings 读 — 统一控制点
2. 方案 B: hardcode 两边都 210 — 简单但维护性差

**RISK-NEW-1**:
1. **方案 A (选)**: Frontend useETA hook 接收 actualElapsedSec + sanity check (>= 30 min 显示"正在收尾, 请稍候...") — 字段彻底激活
2. 方案 B: 删除 backend 字段 — 浪费已写代码
3. 方案 C: 完全 ignore (保持死字段) — 隐患

### 最终决策

- **RISK-NEW-2**: 方案 A — 统一控制点 (config.py L33 + seedream_generator.py 从 settings 读)
- **RISK-NEW-1**: 方案 A — 11 消费点真接通 + sanity check (>= 30 min "正在收尾")

### 理由

- 配置统一: 维护性最佳, 一行 .env 改 timeout 全生效
- 字段激活: 给用户长尾任务更友好提示, 避免显示过期 ETA 误导

### 实证

- 207/207 全 regression PASS
- npm build 0 errors
- grep "actualElapsedSec" → 11 消费点 (彻底激活)
- grep "IMAGE_GENERATION_TIMEOUT" → 1 个定义点 (config.py L33)

### 后续行动

- [x] Backend mini agent 改 config.py + seedream_generator.py
- [x] Frontend mini agent 改 useETA + StageC + CreateContent
- [x] PM 5 维度审查通过
- [x] Backend 重启含 config 改动
- [x] Frontend clean rebuild
- [ ] Founder 明天 e2e 实测验证

---

## DEC-031: Wave 10.1 atmosphere dict TypeError hotfix (2026-05-14 14:51)

**日期**: 2026-05-14 14:51
**决策者**: @PM + @Backend Sonnet xhigh
**影响范围**: storyboard_director.py (Stage 4 storyboard 生成)

### 问题

test17 Pipeline Stage 4 跑到 Scene 5/6 时报 `TypeError: can only concatenate str (not "dict") to str` at storyboard_director.py L635 `'Atmosphere: ' + atmosphere + '. '`

**真根因**:
- Stage 3 LLM (Claude Sonnet 4.6) 输出 atmosphere 字段是 dict: `{mood, sound_design_hint, temperature_feel}`
- L635 假设 atmosphere = str → dict + str → TypeError
- **Wave 10 T16-4 B58 merge 修复正确**, 但完美保留 atmosphere (dict) 后**意外暴露之前 storyboard_director.py 的隐藏 bug** (schema 演化问题)

### 方案选项

1. **方案 A**: 改 Stage 3 LLM prompt 强制输出 str (大改, 影响其他下游)
2. **方案 B (选)**: storyboard_director.py 加 `_atmosphere_to_str()` helper, 容错 dict / str / None / Any 4 种类型

### 最终决策

**选择方案 B** — Backend agent 紧急 hotfix `_atmosphere_to_str()` helper

```python
# storyboard_director.py L323-341
def _atmosphere_to_str(atm) -> str:
    if not atm: return ""
    if isinstance(atm, str): return atm
    if isinstance(atm, dict):
        mood = atm.get("mood")
        sdh = atm.get("sound_design_hint")
        tf = atm.get("temperature_feel")
        parts = [str(p) for p in [mood, sdh, tf] if p]
        return ", ".join(parts) if parts else json.dumps(atm, ensure_ascii=False)
    return str(atm)
```

### 理由

- 防御式编程: 不假设 LLM 输出字段类型, 容错处理
- 修复点局部 (5-10 行), 风险低
- 不需要回归 Stage 3 prompt
- 单测 atmosphere_dict_compat 10/10 PASS + regression 63/63 PASS

### 实证

- test18 (5/14 14:38-15:57) Stage 4 11 LLM 并行调用 **0 TypeError** ✅
- Pipeline 完整跑通 2908s, 29 shots

### 后续行动

- [x] Backend hotfix + 单测 + regression test
- [x] PM 重启 backend PID 63583
- [x] Founder test18 实证通过
- [ ] PM 加 KEY_LEARNINGS: "Schema 演化暴露隐藏 bug — 上游修复完美 + 字段保留完整 = 暴露下游写死类型 bug"

---

## DEC-032: Wave 11 优先级调整 + P0-P2 内测前 + P3 内测后 (2026-05-14 16:30)

**日期**: 2026-05-14 16:30
**决策者**: @Founder (PM 14 RISK 地毯式 audit 后提议)
**影响范围**: 整个 Wave 11 派活节奏 + 内测启动门槛

### 问题

test18 e2e 暴露 14 个 RISK，PM 提议优先级 (P0-P3)，需要 Founder 拍板：
1. Wave 11 做哪些 (内测前必修)？
2. 哪些可以推迟到内测后？
3. 推迟的怎么防遗漏？

### 方案选项

1. **方案 A**: 只做 P0 (3 RISK), 其他全推迟 (内测启动快但留 11 隐患)
2. **方案 B (选)**: P0 + P1 + P2 都做 (8 RISK), 只 P3 (4 RISK) 推迟到内测后
3. **方案 C**: 全做 14 RISK 再启动内测 (周期长)

### 最终决策

**选择方案 B**: Wave 11 做 P0+P1+P2 (8 RISK), P3 (4 RISK) 内测后做但不能遗漏

### 优先级修订（基于"角色一致性是产品生命线" + 内测目标）

| RISK | 原优先级 | 新优先级 | 理由 |
|---|---|---|---|
| T17-9 R7-3 | P2 | **🔴 P0** | 跟 T18-F 同根因 (角色一致性), 一起修 |
| T18-H ShotValidator 5MB | P2 | **🟡 P1** | 隐藏的角色一致性 audit 失效 |
| T18-J Sync LLM | P2 | **🔵 P3** | 内测 1-10 人不需要, 多用户支持后再做 |

### Wave 11 4 波派活计划

```
Wave 11.1 (2h):  P0+P1 (T18-F + T17-9 + T18-H)
Wave 11.2 (1.5h): P1 (T18-G + T18-E + StageC 配套)
Wave 11.3 (2h):  P1 (T17-5 ETA Backend + Frontend)
Wave 11.4 (3-4h): P2 (T18-A + T18-B + T18-D)
─────────────────────────────────────
Wave 11 总计: ~10h, 修 8 RISK
```

### POST_BETA 防遗漏机制 (5 层)

1. Task list 长期保留 (#7, #8, #13, #14 不删除)
2. 专属文档 `WAVE11_PLAN_AND_POST_BETA_RISKS.md` 永久保留
3. PENDING.md 加 POST_BETA_RISKS 段
4. TODAY_FOCUS.md 内测启动当天提示 PM 排 Wave 12
5. 每月复盘检查 task list

### 后续行动

- [x] PM 修订优先级 + 写入 task list
- [x] PM 写 Wave 11 + POST_BETA 计划文档
- [ ] PM 派 Wave 11.1 (Backend × 2 并行)
- [ ] Wave 11.1 完成后 PM 审查 → 派 Wave 11.2 ...
- [ ] 内测启动前 PM 确认 8 RISK 全修

---

## 决策索引

| 编号 | 日期 | 主题 | 决策者 | 影响范围 |
|------|------|------|--------|---------|
| DEC-001 | 2024-12 | 角色一致性方案 | AI_ML | 图像生成 |
| DEC-002 | 2025-01 | 音频服务选型 | Backend | 音频模块 |
| DEC-003 | 2025-01 | 多 Agent 协作机制 | PM | 全局 |
| **DEC-004** | **2026-01-19** | **设计系统** 🔄 变更中 | **PM + Frontend + 创始人** | **前端UI** |
| **DEC-005** | **2026-01-22** | **内容方向与质量基准** | **创始人** | **全局** |
| **DEC-006** | **2026-01-22** | **条漫MVP产品形态** ⭐ 新 | **创始人** | **全局** |
| **DEC-007** | **2026-02-12** | **Git仓库初始化** ✅ 完成 | **创始人** | **DevOps** |
| **DEC-008** | **2026-02-12** | **Landing Page P0 Pipeline模块方向** ⭐ 新 | **创始人** | **Frontend** |
| **DEC-009** | **2026-02-13** | **参考图预处理（批准方案A）** ✅ 闭环 | **创始人** | **AI-ML + Backend** |
| **DEC-010** | **2026-02-24** | **边缘问题根治：参考图源头统一2:3** ⭐ 新 | **创始人** | **Backend** |
| **DEC-011** | **2026-02-24** | **条漫产品形态定义：交付模式+篇幅选项+短视频模式** ✅ | **创始人** | **全局** |
| **DEC-012** | **2026-02-25** | **Phase 2 四项决策：模型全面升级+灌篮高手风格+text_type优化+角色一致性框架** ⭐ 新 | **创始人** | **全局** |
| **DEC-013** | **2026-02-28** | **Create 页面升级 + 产品方向扩展：7 项功能决策 + 架构设计** ⭐ 新 | **创始人** | **Frontend + 全局** |
| **DEC-014** | **2026-03-03** | **移除 previous_shot_image 传递 (Plan A)** ✅ | **创始人** | **Backend + AI-ML** |
| **DEC-015** | **2026-04-15** | **Harness V2 Engineering：CI/CD + Schema 验证 + 成本熔断 + 监控** ⭐ 新 | **创始人** | **全局** |
| **DEC-016** | **2026-04-15** | **Prompt B' 格式设为默认（-46% tokens，盲测验证）** ⭐ 新 | **创始人** | **AI-ML + Backend** |
| **DEC-017** | **2026-04-14** | **Stage D 产品交互逻辑：调整画面 + 编辑文字 + 重新生成** ⭐ 新 | **创始人** | **Frontend + Backend** |
| **DEC-018** | **2026-04-14** | **Haiku 运行时使用场景澄清：产品运行时轻量 API 调用允许 Haiku** ⭐ 新 | **创始人** | **全局** |
| **DEC-019** | **2026-04-15** | **image_prompt 中文阈值收紧：15% → 5%** ⭐ 新 | **创始人** | **AI-ML + Backend** |
| **DEC-020** | **2026-04-29** | **M1 工程并行化优先（图像生成串行 → 并发）** | **创始人** | **Backend** |
| **DEC-021** | **2026-04-29** | **BP 上写完整 4 层杠杆 + 自建集群路线图** | **创始人** | **PM** |
| **DEC-022** | **2026-05-09** | **不做 gemini-2.5 vs NB2 画质盲测（暂缓）** | **创始人** | **AI-ML** |
| **DEC-023** | **2026-04-28** | **8 个 Agent frontmatter hardcode model + effort（model 分级 + 全员 xhigh）** | **PM + 创始人** | **全 Agent** |
| **DEC-024** | **2026-05-11** | **Scenes 确认作为用户旅程第三停留点（修订 DEC-011）** | **创始人 + PM** | **全栈** |
| **DEC-025** | **2026-05-12** | **T17 ShotValidator 4 层防御（数据契约错配修复，方案 D 自创）** | **AI-ML + 创始人 plan mode 批准** | **AI-ML（核心）+ Backend（P3 后续重构提议）** |
| **DEC-026** | **2026-05-13** | **BGM 通用性框架（style × mood 矩阵 + 文化硬约束）** ⭐ 新 | **创始人 + PM 深挖** | **AI-ML（核心）+ Backend（extract 维度扩展）** |
| **DEC-027** | **2026-05-13** | **后台生成 + 完成通知机制（用户进度页加"后台生成"按钮 + 浏览器 Notification API + dashboard 角标）** ⭐ 新 | **创始人** | **Frontend** |
| **DEC-028** | **2026-05-13** | **StoryboardDirector 不自动截断 shots（移除 O-2 上限，LLM 生成多少跑多少，多出的当送给用户）** ⭐ 新 | **创始人** | **Backend / AI-ML** |
| **DEC-029** | **2026-05-13** | **参考图阶段并行化（跨角色 portrait/fullbody 3 路并行 + 跨 location anchor 多路并行，保留同角色/location 内串行）** ⭐ 新 | **创始人** | **Backend** |
| **DEC-030** | **2026-05-13** | **Wave 9 架构级前后端契约改造（Ben 方案 A）** ⭐ 新 | **创始人 + Ben (合伙人)** | **Backend + Frontend + PM 全局** |

---

## DEC-030: Wave 9 架构级前后端契约改造（Ben 方案 A，5/13 20:25 Founder 批准）

**决策日期**: 2026-05-13 20:25
**决策者**: Founder + Ben (合伙人 CTO) — 联合决策
**触发**: test15 e2e 暴露 13 真 RISK 中 **7 个 (47%)** 属于"前后端契约断裂"模式（详见 `.team-brain/analysis/TEST15_DEEP_AUDIT_2026-05-13.md`）

### Ben 原话（5/13 15:37-15:42 Founder + Ben 微信聊天）

> Ben: "是不是把前端放在后端的前面去 pipeline"
> Kai: "就是现在后端更新的前端没接收到 每个阶段响应的顺序逻辑之类"
> Ben: "可以用一种纠验的机制 — 比如后端开发改过功能，需要这个告知出来询问需要对应修改前端吗"

### test15 实证前后端契约断裂 7 个

| RISK | 前后端断裂描述 |
|---|---|
| T15-2 | Backend R4-2 等待 scenes_confirmed → Frontend POST_CHAR_STAGES 错误踢人 |
| T15-3 | Backend R4-2 阶段无 storyboard → Frontend /scenes hydrate /storyboard = 永远 404 |
| T15-4 (撤销) | 设计原则一致：用户不需要 storyboard review |
| T15-7 | Backend ETA 阶段切换跳变 → Frontend guard 不允许上调 |
| T15-8 | Backend scenes_confirmed=True → Frontend subPhase 不监听 |
| T15-12 | Backend regenerate ✅ → Frontend failed_shot_count stale |
| T15-13 | Backend regenerate ✅ → 5_image_results.json stale + ApiCost project_id=None |

### Wave 9 方案 A：Backend status authoritative + Frontend state 派生

**核心原则**: backend `GET /chapters/{n}/status` API 成为前端 state 的 **single source of truth**，frontend state 字段全派生，不本地缓存。

### Backend 改造（Backend Opus xhigh ~3h）

`app/api/chapters.py` 扩展 `GET /chapters/{n}/status` response：

**新增字段**:
1. `ui_phase`: `"input" | "outline_review" | "char_review" | "scene_review" | "shot_generating" | "completed"` — 告诉前端当前用户应该看哪个 UI
2. `hydrate_hints`: 每阶段告诉前端 hydrate 哪个 endpoint + 渲染哪些字段
   - 例: scenes_ready 阶段返回 `{hydrate_endpoint: "/screenplay", display_field: "scenes_11"}`
   - 例: storyboard 阶段返回 `{hydrate_endpoint: "/storyboard", display_field: "shots_23"}`
3. `characters_confirmed`: boolean — frontend subPhase 派生用
4. `scenes_confirmed`: boolean — frontend subPhase 派生用
5. `storyboard_ready`: boolean — frontend hydrate 判断用
6. `failed_shot_count`: 改为 mid-stage 实时累加（不再 finalize 才汇总，顺解 T15-9）

### Frontend 改造（Frontend Opus xhigh ~3h）

`frontend/src/lib/createUrl.ts` + `frontend/src/components/create/StageC.tsx`:

1. `generationSubPhase` 改为从 `status.ui_phase` 派生（去掉 user action 触发逻辑）
2. hydrate URL 改为从 `status.hydrate_hints` 拿（去掉 hardcode endpoint）
3. ETA 监听 `status.stage` 字段变化时重置 ref（顺解 T15-7）
4. `failed_shot_count` 直接从 status 读，不本地缓存（顺解 T15-12 的 frontend 侧）

### PM 配套（~1h）

写 `.team-brain/contracts/STATUS_API_CONTRACT.md`：
- 每个 stage 期望的字段
- frontend 应该做的渲染
- backend 改 status response → 必须更新契约文档 → frontend 自动同步

### DevOps 配套（~30 min）

`scripts/pre-commit-frontend-impact.sh`:
- backend agent commit 修改 `app/api/projects.py` / `app/api/chapters.py` / `pipeline_orchestrator.py` 时
- pre-commit hook 自动 prompt："此改动涉及 frontend 契约吗？需要同步通知 frontend agent？"
- 强制 commit message 含 `[frontend-impact: yes/no]` label

### Wave 9 顺解的 RISK (4 个，不单独 spawn)

- T15-3 ✅ hydrate_hints 字段
- T15-7 ✅ ETA 监听 stage 切换重置
- T15-8 ✅ frontend state 派生
- T15-9 ✅ status response mid-stage 实时

### 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| Wave 9 改 chapters.py + StageC.tsx → 与 Phase 1 PR-A + Phase 3 T15-11 冲突 | PM 设计 4 Phase 串行/并行混合 (Phase 1 → Phase 3 → Wave 9), chapters.py 严格串行 |
| Wave 9 改 frontend Watcher 逻辑 → 已 e2e 验证过的 character_ready/scenes auto-jump 可能 regression | PM Wave 9 完成后跑 test16 e2e 验证全 checkpoint |
| Wave 9 6-8h 太长 | spawn Opus xhigh effort + 并行 backend/frontend，PM 文档同步进行 |

### 验收标准 (Wave 9 完成后)

1. test16 e2e: 0 或 1 RISK，前后端契约断裂类 RISK = 0
2. STATUS_API_CONTRACT.md 完整 + agent 必读
3. pre-commit hook 在 backend agent commit 时真生效

### 派发计划

详见 TODAY_FOCUS.md "Wave 9 派发矩阵" 段 + TEAM_CHAT.md `[2026-05-13 20:25]` 段

### 备注

- Founder + Ben 联合决策标志双团队第一次架构级深度协作（之前都是各自独立工作）
- 这是双团队 5/13 启动以来最重要的架构决策
- 验证 Ben 5/13 加入后的价值：CTO 级别 + 后端架构经验真带来质变

---

## DEC-026: BGM 通用性框架（style × mood 矩阵 + 文化硬约束）

**决策日期**: 2026-05-13
**决策者**: Founder + PM 深挖 + AI-ML 实施
**实施者**: AI-ML（核心 Template + linter + 4 字段扩展）+ Backend（PM 自修 wiring）

### 背景

test14 实测铁证：用户选 `ink_wash` (水墨) + mood=`悬疑` 的水墨武侠故事，系统生成的 BGM 是"minor key + ambient drone + dissonant cluster on strings" — **纯西式电影氛围**，跟画面**完全割裂**。详 `output/5cbd8ca0-1d47-4c05-a0fe-c7ec4f86b3c6/bgm_prompt_chapter0.txt`。

Founder 5/13 16:09 升级关注："我们要的是**通用性** 我感觉**风格也是要传入的**...在**听感 节奏 韵律等等全维度** 做到更贴切一点？"

### 真根因

4 层断裂:
1. **数据提取层** (`story_music_extractor`) 缺 style_preset / style_category / setting_period / character_dominant_type 4 个 BGM 通用性维度
2. **Template 映射层** (`meta_mixed_v3_quote_picking.md`) 6 桶 mood 映射**只按情绪走**，不考虑视觉风格
3. **文化约束层** (Template 元原则 D) "中国故事承载中国声音记忆"是**软提醒**，不是按 style_category 强制乐器/调式的**硬规则**
4. **后置验证层** (`music_generation_service`) Haiku 输出后**无 prompt linter**，错位的西式 BGM 直接进 Mureka

### 决策

**核心**: BGM 生成应是 **`mood × style × setting × pace × emotion_arc`** 多维度综合。

**4 阶段闭环修复**:

1. **A. 扩展 story_music_extractor 维度** — 加 4 字段 + 82 style_preset → 8 BGM category 映射表 + 3 helper（_derive_style_category / _derive_setting_period / _derive_character_dominant_type）
2. **B. Template 加 6 mood × 5 style_category = 30 cells 二维矩阵** — 每 cell 五维度（Instruments / Scale / Tempo / Rhythm Pattern / Timbre）
3. **C. 元原则 D 升级硬约束** — 8 category MUST/FORBIDDEN 乐器/调式列表
4. **D. Mureka 前 prompt linter** — `_validate_bgm_prompt` 检查 + `_build_repair_hint` 重调 Haiku 1 次

### 验证

- 单元测试 71/71 PASS（含 test14 真实 BGM 触发 linter fail）
- 架构 7/7 PASS（不退化）
- **5 组 Mureka 真测 5/5 PASS** + **Founder 听感"都非常贴切 我很满意"** ✅
  1. ink_wash + 悬疑 → guqin + dizi + 散板 + 留白（test14 fix verified）
  2. digital_painting + 温馨 → acoustic guitar + fingerpicked
  3. cyberpunk + 紧张 → dark synth + glitch + sub-bass + vocoder
  4. picture_book + 治愈 → glockenspiel + music box + harp
  5. ghibli + 热血 → shamisen + taiko + strings + harp

### PM 自修 wiring（5/13 17:18）

3 处 `generate_bgm_for_chapter(` 调用补 `style_preset=project.style_preset`:
- `pipeline_orchestrator.py:1470` (Pipeline 主流程)
- `chapters.py:2109` (regenerate BGM)
- `chapters.py:2236` (change BGM meta_version)

### 关联

- `.team-brain/analysis/BGM_UNIVERSAL_FRAMEWORK_2026-05-13.md` — AI-ML 10 段深度分析
- `.team-brain/handoffs/PENDING.md` RISK-T14-11 — Wave 7 闭环
- `.team-brain/knowledge/KEY_LEARNINGS.md` — "软提醒 vs 硬约束"经验段

---

## DEC-001: 角色一致性技术方案

**日期**: 2024-12-23
**决策者**: @AI_ML + @Backend
**影响范围**: 图像生成模块

### 问题
多场景生成时角色外貌不一致，影响视频连贯性

### 方案选项
1. **Flash-only**: 便宜但一致性 70-80%
2. **Pro-only**: 贵但一致性 95%+
3. **混合方案**: Flash 做准备工作，Pro 做最终生成

### 最终决策
**选择方案 3: 混合方案**

- Stage 1-4: 使用 Gemini Flash (快速、低成本)
- Stage 5 Shot 生成: 使用 Gemini Pro (质量、一致性)
- 参考图生成: 使用 Flash (成本控制)

### 理由
- 成本与质量的平衡 ($9.35 vs $15+)
- Pro 模型在最终生成环节保证一致性
- Flash 在准备环节节省成本

### 后续行动
- [x] 实现混合模型架构
- [x] 验证 100% 3人场景一致性
- [ ] 研究进一步成本优化

---

## DEC-002: 音频服务选型

**日期**: 2025-01-03
**决策者**: @Backend
**影响范围**: 音频模块

### 问题
需要选择 TTS 和语音识别服务

### 方案选项
1. **火山引擎 + OpenAI**: TTS 用火山，ASR 用 Whisper
2. **全火山**: 全部使用火山引擎
3. **全 OpenAI**: 全部使用 OpenAI

### 最终决策
**选择方案 1: 火山引擎 TTS + OpenAI Whisper**

### 理由
- 火山引擎 TTS 中文效果好，音色丰富
- OpenAI Whisper 时间戳精度高
- 成本合理

### 后续行动
- [x] 集成火山引擎 TTS
- [x] 集成 OpenAI Whisper
- [x] 实现时间戳对齐

---

## DEC-003: 多 Agent 协作机制

**日期**: 2025-01-05
**决策者**: @PM
**影响范围**: 全局

### 问题
单 Agent 开发效率低，需要多 Agent 协作

### 方案选项
1. **松散协作**: 各自独立，偶尔同步
2. **紧密协作**: 共享知识库，标准化流程
3. **自动化协作**: 使用 Agent SDK 自动编排

### 最终决策
**选择方案 2: 紧密协作 + 共享知识库**

### 理由
- 项目复杂度适中，不需要过度自动化
- 共享知识库确保信息同步
- 标准化流程降低沟通成本

### 实施
- 建立 /.team-brain/ 共享知识库
- 制定 TEAM_PROTOCOL.md 协作协议
- 每个 Agent 有专属 CLAUDE.md

### 后续行动
- [x] 创建 .team-brain 目录结构
- [x] 编写协作协议
- [ ] 为每个 Agent 创建 CLAUDE.md
- [ ] 试运行并迭代优化

---

## DEC-004: 序话Story 设计系统 🔄 变更中

**日期**: 2026-01-19
**决策者**: @PM + @Frontend + @创始人
**影响范围**: 前端UI、PM验收标准
**状态**: 🔄 **变更中** - 创始人反馈偏好Light模式

### 问题
需要确定序话Story的前端设计系统，确保视觉一致性和用户体验。

### 原方案选项
1. **Light Mode + 传统配色**: 亮色背景，传统蓝色主色
2. **Dark Mode (OLED) + Video-First Hero**: 深色背景，突出视频内容
3. **Glassmorphism 风格**: 毛玻璃效果，现代但可能影响可读性

### 原决策 (已废弃)
~~**选择方案 2: Dark Mode (OLED) + Video-First Hero**~~

### 变更原因 (2026-01-19 16:30)
**创始人反馈**: 偏好 Light 模式，不要 Dark 模式

### 第一轮方案 (已废弃 - 2026-01-19 17:30)
~~仅换色系的三个版本（Clean Flat / Bento Box / Aurora Glass）~~
**废弃原因**：创始人反馈只是换色，布局/交互/动效完全一样，不是"三种完全不同的体验"

### 新方案选项 (全维度差异化)

| 方案 | 布局 | 交互模式 | 动效 | 核心理念 |
|------|------|----------|------|----------|
| **A. Conversational** | 对话气泡 | 聊天式追问 | 消息淡入 | 像跟AI聊天一样创建故事 |
| **B. Card Carousel** | 全屏卡片 | 滑动/拖拽 | 3D翻转/滑动 | 沉浸式，一步只做一件事 |
| **C. Split Panel** | 左右分栏 | 实时预览 | 内容淡入更新 | 所见即所得 |

### 待选择的最终决策
等待 Frontend 实现三个**全维度差异化**的原型后，由创始人选择。

### UX验收标准 (PM验收时检查) - 不变
- [ ] 颜色对比度 ≥ 4.5:1
- [ ] 可点击元素有 cursor-pointer
- [ ] Hover过渡 150-300ms
- [ ] 用Lucide Icons，不用emoji
- [ ] 支持 prefers-reduced-motion

### 后续行动
- [x] Frontend 生成设计系统配置 (Dark版)
- [x] PM 确认并记录决策 (Dark版)
- [x] PM 验收概念原型流程 ✅
- [x] 创始人反馈偏好 Light 模式
- [x] PM 输出三个 Light 模式方案（仅换色）
- [x] Frontend 实现三个换色版本 ⚠️ 被否决
- [x] 创始人反馈需要全维度差异化
- [x] PM 重新定义三个全维度不同的方案
- [x] **Frontend 实现三个全维度差异化原型** ✅ 2026-01-19 18:30
  - `create-story-conversational.html` - 对话式（聊天气泡 + 消息淡入弹跳）
  - `create-story-carousel.html` - 沉浸式卡片（全屏滑动 + 3D翻转）
  - `create-story-split.html` - 实时预览（左右分栏 + 内容淡入更新）
- [ ] **创始人选择最终方案** ← 🔴 当前阻塞点
- [ ] Frontend 应用最终设计系统
- [ ] PM 验收首个UI交付物

---

## DEC-005: 内容方向与质量基准

**日期**: 2026-01-22
**决策者**: @创始人
**影响范围**: 全局（产品方向、内容策略、质量标准）

### 问题
需要明确序话Story的核心内容类型和质量基准，确保产品方向正确。

### 分析来源
创始人提供参考案例：`still_image_storyref/IMG_0804-0818.jpg`（15张图的都市情感短剧）

### 参考案例分析

**故事概述**：情侣因"男友拍照技术差"引发小冲突，女主回忆前任冷暴力后领悟沟通重要性，主动道歉和解。

| 维度 | 参考案例特征 | XuhuaStory能力 | 匹配度 |
|------|-------------|----------------|--------|
| 角色数量 | 2主角 + 1前任（回忆） | 3人场景100%一致性 | ✅ |
| 角色一致性 | 女主15张图外貌高度一致 | Gemini Pro + 参考图 | ✅ |
| 画风 | 韩漫/国漫条漫风格 | 80+风格预设 | ✅ |
| 场景类型 | 街头、夜晚、室内 | 场景参考图系统 | ✅ |
| 叙事结构 | 旁白驱动 + 对话气泡 | TTS + 字幕系统 | ✅ |

### 最终决策

**都市情感短剧是XuhuaStory的主线内容方向**

### 核心内容类型定义

| 类型 | 优先级 | 说明 |
|------|--------|------|
| **都市情感** | P0 | 恋爱、婚姻、职场关系（如参考案例） |
| **家庭生活** | P0 | 亲子、代际冲突、家庭温情 |
| **悬疑反转** | P1 | 短剧常见的"打脸"、"逆袭"情节 |
| **古装/武侠** | P1 | 已验证（teststory6.5） |
| **童话/寓言** | P2 | 儿童向内容 |

### 质量基准（参考案例标准）

| 指标 | 基准要求 |
|------|----------|
| 角色一致性 | 同一角色跨场景外貌100%可辨识 |
| 表情细腻度 | 能表达：委屈、困惑、释然、开心等微妙情绪 |
| 场景连贯性 | 白天/夜晚光影自然过渡 |
| 叙事完整性 | 起承转合完整，情感递进自然 |
| 画风统一 | 15张图风格无漂移 |

### 参考案例存档

```
位置: still_image_storyref/IMG_0804-0818.jpg
类型: 都市情感短剧
角色: 女主（红棕波浪发、浅蓝开衫）、男主（黑短发、蓝夹克）、前任（深色长发、耳钉）
场景: 街头购物→夜晚路灯→回忆闪回→和解牵手
用途: 质量基准测试用例
```

### 后续行动
- [x] 用参考案例故事线测试当前系统生成能力 → 见 DEC-006
- [x] 识别与基准的差距（表情细腻度、闪回效果等） → 见 DEC-006
- [ ] 针对性优化Prompt或流程

---

## DEC-006: 条漫MVP产品形态 ⭐ 新

**日期**: 2026-01-22
**决策者**: @创始人
**影响范围**: 全局（产品形态、技术路线、迭代规划）

### 问题
参考案例（IMG_0804-0818）与当前系统有差距，需要决定产品形态和技术实现路线。

### 差距分析结论

经分析，以下能力**可通过精准Prompt + Gemini生图模型实现**：

| 能力 | 实现方式 | 验证状态 |
|------|----------|----------|
| 文字内嵌（对白/旁白） | Prompt描述文字位置和样式 | 🔴 待测试 |
| 合成特效（分屏/碎片/画中画） | Prompt描述构图 | 🔴 待测试 |
| 情感符号（问号/汗滴） | Prompt描述 | 🔴 待测试 |
| 表情细腻度 | 精确Prompt描述表情 | 🔴 待测试 |
| 镜头构图多样性 | Prompt描述机位和景别 | 🟢 已验证 |

### 最终决策

#### 1. 产品形态
**条漫优先，短视频保留**

| 形态 | 优先级 | 说明 |
|------|--------|------|
| **条漫** | P0 MVP | 静态图 + BGM，用户翻页浏览 |
| **短视频** | P1 保留 | TTS + 字幕，自动播放（后续迭代） |

#### 2. 文字呈现
**图片内嵌文字优先**

| 方式 | 优先级 | 说明 |
|------|--------|------|
| **图片内嵌** | P0 | 通过Prompt让模型生成带文字的图 |
| **TTS + 字幕** | P1 保留 | 后续短视频模式使用 |

#### 3. 生图模型
**先用Flash测试**

```
测试模型: gemini-2.5-flash-image
验证目标: 文字内嵌、特效合成、表情细腻度
成功后: 评估是否需要Pro模型
```

#### 4. 音频
**BGM服务待选型**

```
当前: 无BGM
目标: 找到合适的BGM服务商API
状态: 后续任务
```

### 可用风格（13种预设）

| 风格ID | 显示名 | 适用场景 |
|--------|--------|----------|
| `realistic` | 写实摄影 | 都市情感 |
| `cartoon` | 卡通动画 | 轻松喜剧 |
| `pixar_3d` | Pixar 3D | 家庭温情 |
| `anime` | 日式动画 | 青春校园 |
| `ghibli` | 吉卜力 | 治愈系 |
| `illustration` | 数字插画 | 通用 |
| `watercolor` | 水彩 | 文艺清新 |
| `children_book` | 儿童绘本 | 童话寓言 |
| `manga` | 日漫 | 热血/搞笑 |
| `oil_painting` | 油画 | 复古文艺 |
| `cyberpunk` | 赛博朋克 | 科幻 |
| `ink` | 中国水墨 | 古风武侠 |
| `pixel` | 像素艺术 | 怀旧游戏 |

**注**：参考案例风格接近 `illustration` 或需新增韩漫风格

### 后续行动

#### Phase A: 故事测试 ✅ 全部完成 (2026-01-22)
- [x] **@PM**: 定义测试验收标准 ✅ `docs/COMIC_MVP_TEST_ACCEPTANCE_CRITERIA.md`
- [x] **@AI-ML**: 设计文字内嵌Prompt模板 ✅ `docs/COMIC_MVP_PROMPT_TEMPLATES_NO_TEXT.md`
- [x] **@Backend**: 用 `gemini-2.5-flash-image` 测试 ✅ `tests/test_comic_full_story.py`
- [x] **@Tester**: 验收测试结果 ✅ **28/30 = 93.3% 通过**

**验收结果**: 角色一致性5/5 | 风格一致性5/5 | 文字可读5/5 | 情感强调3/5⚠️ | 回忆场景5/5 | 故事完整5/5

#### Phase B: 条漫MVP（下阶段）
- [ ] 修复红色强调支持中文感叹号 `！！！`
- [ ] 升级情感强调为LLM驱动
- [ ] 将V2方案集成到主流程
- [ ] 实现条漫输出格式
- [ ] BGM服务选型

#### 保留项（短视频模式）
- [ ] Phase 4 视频合成能力保留
- [ ] TTS + Whisper对齐能力保留
- [ ] 5-10分钟短视频后续迭代

---

## DEC-007: Git仓库初始化

**日期**: 2026-02-12
**决策者**: @创始人
**影响范围**: DevOps、全局（版本控制基础设施）

### 问题
项目运行至v0.6.6，Phase 1-4已完成，Phase 5进行中，但项目目录至今没有git版本控制。无法回溯代码变更、无法搭建CI/CD、存在代码丢失风险。

### 方案选项
1. **本地git init**: 仅初始化本地仓库，建立版本控制基础
2. **本地init + GitHub远程**: 同时建立远程仓库，支持CI/CD
3. **暂不处理**: 等Phase 5完成后再统一处理

### 最终决策
**选择方案 1: 仅本地git init**

### 理由
- 解决最紧急的问题：建立版本控制，锁住当前代码状态
- 远程仓库涉及GitHub账号、权限、CI/CD配置，是Phase 6的事
- 当前所有Agent空闲，是执行的好时机
- 最小化范围，不引入不必要的复杂性

### 关键约束
- 分支策略：当前阶段只用 `main`
- .env.example 必须补全后再commit（当前缺 OPENAI_API_KEY、VOLCENGINE 三个变量）
- .gitignore 必须在 `git add` 之前配置正确
- 安全红线：.env、test_output/、venv/、node_modules/、*.db 不能进仓库

### 后续行动
- [ ] PM 制定详细执行方案 (负责人: @PM)
- [ ] DevOps 执行 git init (负责人: @DevOps)
- [ ] PM 核验结果 (负责人: @PM)

---

## DEC-008: Landing Page P0 Pipeline模块方向

**日期**: 2026-02-12
**决策者**: @创始人
**影响范围**: Frontend（Landing Page Pipeline模块重新设计）

### 问题
PM验收Landing Page发现P0问题：Frontend实现的Pipeline.tsx展示了5阶段技术流水线（故事大纲→角色设计→分镜脚本→画面生成→成品输出），但架构文档明确要求模块3 FrameSpark™引擎"保持神秘感，不暴露技术流程"。

### 方案选项
1. **Option A（品牌叙事）**: 按架构文档设计，Pipeline改为FrameSpark™品牌氛围模块，不暴露5阶段流程，用品牌叙事+视觉动效传递"一句话变故事"的magic感
2. **Option B（技术展示）**: 保留当前5阶段流水线展示，更新架构文档以匹配实现，文案调整为用户语言

### 最终决策
**选择 Option A：品牌叙事路线**

### 理由
- 目标用户是无技术背景的短视频创作者，不关心内部技术流程
- 暴露5阶段流程削弱了FrameSpark™品牌的magic感
- 竞品（Midjourney、Sora）都展示结果和体验，不暴露技术栈
- 模块4（差异化卖点）已在传递产品价值，模块3不需要重复技术说明
- FrameSpark™品牌的价值在于"用户不需要知道里面有什么，只需要知道它很强"

### 后续行动
- [ ] PM 制定详细修复方案并分配给 Frontend
- [ ] Frontend 重新设计 Pipeline.tsx 为品牌氛围模块
- [ ] Frontend 同步修复 P1/P2 问题
- [ ] PM 复验

---

## DEC-009: 参考图预处理（批准方案A）

**日期**: 2026-02-13
**决策者**: @创始人
**影响范围**: AI-ML + Backend（边缘问题优化）

### 问题
参考图宽高比（Jerry=0.730, CC=0.778）与目标 9:16（0.5625）差距 17-22%，可能加剧 Gemini API 的边缘留黑/留白问题。AI-ML 提出在代码中添加自动裁剪逻辑。

### 方案选项
1. **方案A（AI-ML提案，PM推荐）**: 在 ImageGenerator.generate_image() 中添加~10行预处理代码，运行时动态裁剪
2. **方案B**: 在 ReferenceImageManager.get_references_for_scene() 中实现

### 最终决策
**批准方案A**

### 理由
- 完全同意 AI-ML 和 PM 的分析逻辑和代码方案
- 成本极低（~10行代码）、风险极低、有潜在改善效果
- 方案A 可根据目标 aspect_ratio 动态匹配，更灵活

### 执行计划
1. @Backend 在 ImageGenerator.generate_image() 中实现预处理代码（参考 AI-ML 在 `ai-ml-progress/context-for-others.md` 中提供的建议代码）
2. @AI-ML 从边缘问题 shot（01/17/22/34/35/36/39/42）中指定 2-3 个用于对比测试
3. 用 `test_output/manualtest/teststory_CCJerry/character_refs/` 下现有参考图跑对比测试，保留原图
4. @Tester 对比验证效果

### 后续行动
- [x] PM 制定执行方案并分配任务 ✅
- [x] Backend 实现代码 ✅
- [x] AI-ML 指定测试 shot 编号 ✅
- [x] 对比测试验证效果 ✅
- [x] PM 汇总报告 ✅

### 闭环结论 (2026-02-24)

**任务闭环。** 5步全部完成。测试结果：效果"无变化~略有改善"（shot_34白边从~4%→~2-3%，shot_36/22无变化）。Tester建议保留代码，Founder同意。预处理代码保留作为安全网。

**边缘问题后续方案**：不走"后处理边缘检测+裁剪"，改为从源头统一参考图宽高比（见 DEC-010）。

---

## DEC-010: 边缘问题根治 — 参考图源头统一 2:3

**日期**: 2026-02-24
**决策者**: @创始人
**影响范围**: Backend（scene_reference_manager.py）

### 问题
TASK-ASPECT-2x3 已将角色参考图（reference_image_manager.py）从 `1:1` 改为 `2:3`，但 `scene_reference_manager.py` 不在修改清单中，可能遗漏了场景参考图的宽高比统一。

参考图和 shot 宽高比不一致是 Gemini 边缘留白/留黑的可能原因之一。从源头统一比例比后处理裁剪更干净。

### 最终决策
**排查并修复 scene_reference_manager.py 的宽高比设置，统一为 2:3。**

### 理由
- 参考图（角色+场景）都是 Gemini 生成的，完全可以指定宽高比
- 参考图与 shot 统一为 2:3，从源头消除比例不匹配
- 比"后处理边缘检测+裁剪"更简洁、更根本
- DEC-009 的预处理代码保留作为双重保险

### 后续行动
- [ ] PM 排查 scene_reference_manager.py 宽高比设置
- [ ] 如有遗漏，Backend 修复为 "2:3"
- [ ] PM 核验

---

## DEC-011: 条漫产品形态定义 — 交付模式 + 篇幅选项 + 短视频模式

**日期**: 2026-02-24
**决策者**: @创始人
**影响范围**: 全局（产品形态、前端交互、后端生成逻辑）

### 问题
需要明确条漫产品的用户交付形式、用户如何控制故事篇幅、以及短视频模式的参数设计。

### 最终决策

#### 1. 交付形式（两种并行）

| 模式 | 交付内容 | 说明 |
|------|---------|------|
| **打包下载** | 参考图（角色+场景）+ 带文字 shot 图 + BGM | 用户可二次创作 |
| **视频下载** | with_text shot 图 + BGM → 合成视频 | 直接可发布 |

#### 2. 条漫模式 — 用户选择"故事篇幅"

用户看到的选项（不暴露 scene/shot 等专业术语）：

| 选项 | Shot 数 | 定位 |
|------|---------|------|
| 快闪 | ~10 张 | 一个片段、一个瞬间 |
| 短篇 | ~18 张 | 一个完整小故事（默认推荐） |
| 中篇 | ~36 张 | 有起承转合的完整叙事 |

#### 3. 短视频模式 — 用户选择"视频时长"

每 4 秒对应 1 个 shot：

| 选项 | 时长 | Shot 数 |
|------|------|---------|
| 短 | 15 秒 | ~4 张 |
| 中 | 1 分钟 | ~15 张 |
| 长 | 3 分钟 | ~46 张 |

#### 4. 专业参数（未来迭代预留）

`duration_minutes`、`min_scenes`、`min_shots` 等专业参数留作未来高级设置，初期不暴露给用户。目标用户是无技术背景的创作者，初期只需"篇幅选择"即可。

### 理由
- 用户关心的是"讲什么故事"和"要多长"，不是 scene 数或 shot 数
- "~10 张图"、"~18 张图"对条漫用户是直觉可感知的结果描述
- 两种交付模式覆盖不同需求：打包下载给想二次创作的用户，视频下载给想直接发布的用户
- 专业参数留给未来迭代，避免初期过度复杂化

### 架构策略
- 当前 Phase 2.0 五阶段流水线保留为备用架构，未来动态视频生成时复用
- 系统内部将用户的"篇幅选择"翻译为合适的 scene 数和拆分参数

### 用户旅程框架（Founder 批准）

五阶段用户旅程，详见 `CLAUDE.md` "用户旅程设计" 章节：

| 阶段 | 用户动作 | 系统动作 |
|------|---------|---------|
| **A. 输入** | 故事创意（必填）+ 篇幅选择 + 视觉风格 | — |
| **B. 确认** | 可选调整：角色/情节/结局/情绪基调（均可跳过） | 自动生成故事大纲 |
| **C. 生成** | 只看进度条 | Stage 1-5 全自动执行 |
| **D. 预览** | 局部微调：重新生成单张/编辑文字/换BGM/删shot | 展示完整作品 |
| **E. 交付** | 选择下载方式 | 打包下载 或 视频合成下载 |

核心原则：用户只当"制片人"——决定方向，系统执行专业制作。默认全自动，有追求的用户可在 B 和 D 阶段深度调整。

### 后续行动
- [x] PM 将 DEC-011 纳入产品需求文档 ✅
- [ ] **Phase 1: 端到端流水线验证** — @Backend 跑 1-2 个完整条漫（~18 shots）通过 Stage 1→5
- [ ] **Phase 2: 产品层实现** — Backend(篇幅映射+输出打包) + Frontend(用户旅程UI) + AI-ML(prompt适配) + Tester(验收)

---

## DEC-012: Phase 2 四项决策 — 模型升级 + 灌篮高手风格 + text_type 优化 + 角色一致性框架

**日期**: 2026-02-25
**决策者**: @创始人
**影响范围**: 全局（后端模型配置、AI-ML prompt、风格预设、角色系统设计）

### 问题
Phase 1 E2E 验证通过（PM 复核 4.3/5），但发现 4 项需优化的问题：角色一致性仅 68%、narration 占比 86% 过高、写实风格不适合条漫、故事吸引力可提升。

### 最终决策

#### 决策 1: 角色一致性系统框架

将角色特征分为两类，建立系统性设计思路：

**Identity Anchors（身份锚点，锁定不变）**: 面部骨骼结构、身体比例、肤色、标志性特征（如眼镜/疤痕）、基础服装设计

**Narrative Variables（叙事变量，6层动态变化）**:
1. 情绪层 — 表情、眼神、肢体语言
2. 物理状态层 — 疲劳、伤痕、汗水、温度反应
3. 装备层 — 服装变化、道具持有/位置、配饰佩戴
4. 环境交互层 — 光影、天气痕迹、环境附着
5. 可见度层 — 全身/半身、正面/侧面、遮挡/倒影/剪影
6. 时间层 — 成长、衰老、磨损、季节变化

此外，确保代码正确传入角色参考图（portrait + fullbody）给每个 shot。

#### 决策 2: narration 占比优化

采纳 PM 建议，@AI-ML 优化 Stage 4 prompt。目标分布：dialogue 40-50% / thought 20-25% / narration ≤30% / none 5-10%。

#### 决策 3: 下次测试风格 — 灌篮高手 (Slam Dunk)

不用韩漫，改用从未测试过的灌篮高手漫画风格。需在 StyleEnforcer 中新建 `slam_dunk` 预设。

#### 决策 4: LLM 模型全面升级

**所有文本生成**切换为 Claude Sonnet 4.6（不仅 Stage 1+3）：

| 项目 | 当前 | 升级后 |
|------|------|--------|
| 主力文本模型 | Gemini 3 Flash | **Claude Sonnet 4.6** (`claude-sonnet-4-6`) |
| 备用文本模型 | Claude Haiku 4.5 | **Gemini 3 Pro** |
| 生图模型 | Gemini Pro Image | 不变 |
| 参考图模型 | Gemini Flash Image | 不变 |

完全弃用 Claude Haiku 和 Gemini Flash 用于文本生成。

**成本影响**：文本生成 ~$0.35-0.43/故事，仅增加总成本 <5%（$9.35 → $9.70-9.78）。

### 理由
- 角色一致性框架：治标（加强眼镜描述）不如治本（系统性区分 anchors vs variables）
- Sonnet 4.6：大纲+剧本+分镜全面提升，成本增量极小
- 灌篮高手：测试从未用过的风格，验证 StyleEnforcer 跨风格能力
- narration 优化：观众代入感从"旁观者"变成"当事人"

### 后续行动
- [ ] @Backend: TASK-MODEL-UPGRADE — 7 个文件模型配置切换
- [ ] @AI-ML: TASK-STYLE-SLAMDUNK — 灌篮高手风格预设
- [ ] @AI-ML: TASK-TEXT-TYPE-OPT — text_type 分布优化
- [ ] @AI-ML: TASK-IDENTITY-DESIGN — 角色一致性框架文档
- [ ] @Tester: TASK-E2E-TEST-2 — Slam Dunk + Sonnet 4.6 E2E 测试
- [ ] @Frontend: TASK-UI-STAGE-A — Stage A 输入界面
- [ ] @DevOps: TASK-GIT-COMMIT-3 — 阶段性 git 提交
- [ ] 🆕 评估 Nano Banana 2 (`gemini-3.1-flash-image-preview`) 替代 Pro 用于 Shot 生图 — 详见 `docs/NANO_BANANA_2_RESEARCH.md`（待 Founder 决策 DEC-013）
- **Phase 3 任务（2026-02-27 15:41，Founder 6 项决策确认）**:
  - [x] ✅ TASK-E2E-TEST-2 Tester 4.3/5 + PM 独立复核通过
  - [x] ✅ @Backend: TASK-NB2-SWITCH — PRO_MODEL 改为 NB2 (16:09 完成, PM 核验 16:32)
  - [x] ✅ @AI-ML: TASK-SLAMDUNK-COLOR — slam_dunk 灰度修复 + color_mode 增强 (16:05 完成, PM 核验 16:32)
  - [x] ✅ @AI-ML + @Backend: TASK-DIALOGUE-SYSTEM — 三层对话系统重构 (16:05+16:09 完成, PM 核验 16:32)
  - [x] ✅ @Backend: TASK-TEAM-UNIFORM — Stage 2 团队着装一致性规则 (16:09 完成, PM 核验 16:32)
  - [x] ✅ @Tester: TASK-NB2-TEXT-TEST — NB2 中文渲染 A/B 测试 (Tester 16:55, PM 复核 17:24) → Founder 决策方案 B
  - [x] ✅ @Backend: TASK-SPEAKER-PREFIX — TextOverlay 智能前缀处理 (16:09 完成, PM 核验 16:32)
- **Founder 方案 B 决策 (2026-02-27 17:24)**:
  - 全面切换 NB2 原生文字渲染（旁白/对话/心理描述全部由 NB2 在图像中渲染）
  - TextOverlay 代码完整保留作为备用方案（不删除任何功能）
  - 新增开关 `use_native_text=True`（默认原生渲染，可切回 TextOverlay）
- **Phase 4 任务 (2026-02-27 17:24 PM 派发)**:
  - [x] ✅ @Backend: TASK-NB2-NATIVE-TEXT (P0) — PM 核验通过 (2026-02-28 10:25)，代码+输出全部符合规格
  - [x] ✅ @Tester: TASK-AB-STYLE-DESC (P2) — PM 核验通过 (2026-02-28 11:15)，B组(场域式) 4.5 vs A组(命令式) 4.17，待跨风格验证
  - [x] ⚠️ @Backend: TASK-NATIVE-TEXT-ROBUSTNESS (P2) — PM 核验 PARTIAL PASS (2026-02-28 11:15)，image_generator.py 关键字回退不一致
- **Phase 4 后续任务 (2026-02-28 11:15 PM 派发，Founder 3项决策)**:
  - [x] ✅ @Backend: TASK-ROBUSTNESS-FIX (P1) — 完成 (11:31) + PM 核验通过 (14:52)，3/3 修复点完全一致
  - [x] ✅ @AI-ML: illustration 场域式 style_description 改写 — 完成 (11:30) + PM 核验通过 (14:52)
  - [ ] 🔄 @Tester: TASK-CROSS-STYLE-TEST (P2) — 前置已满足，PM 已通知启动 (14:52)
  - [ ] @DevOps: TASK-GIT-COMMIT-3 — 等 CROSS-STYLE-TEST + Founder 决策 + 代码定稿

---

## DEC-013: Create 页面升级 + 产品方向扩展 — 7 项功能决策 + 架构设计

**日期**: 2026-02-28
**决策者**: @创始人
**影响范围**: Frontend + 全局（产品功能定义、前端架构、用户旅程扩展）

### 问题
Phase 5 前端已完成 LP 主页 + 10 子页面 + Create/Login（44 文件），但 Create 页面功能有限（仅 idea + 3 篇幅 + 8 风格）。Founder 提出 7 项升级需求，PM 独立分析后提出 5 个澄清问题，Founder 全部回答确认。

### PM 独立分析

#### 逐点技术可行性评估

| # | 需求 | 后端现状 | 可行性 |
|---|------|---------|--------|
| 1 | 角色参考图上传 | `reference_image_manager.py` 有 `set_reference()` 可注入，无 API endpoint | ✅ 需新建 API |
| 2 | 场景参考图上传 | `scene_reference_manager.py` 有 interior/exterior 逻辑 | ✅ 需新建 API |
| 3 | 故事文档上传 | `story_outline_generator.py` 仅接受 `idea: str` | ✅ 前端提取文本 |
| 4 | 宽高比选择 | `image_generator.py` 已支持动态 `aspect_ratio` | ✅ pipeline 有 5 处硬编码需改 |
| 5 | 长篇连续故事 | max shots = `max(23, target_duration*8)` | ✅ 需 epic 映射 + continuation API |
| 6 | 风格扩展 | 16 预设 + `_build_generic_prefix()` | ✅ 自定义需 LLM 分析 |
| 7 | NB2 vs TextOverlay | NB2 已集成，`use_native_text=True` | ✅ 前端无感 |

**Per-shot 参考图上限计算**：5 chars × 1 fullbody + 2 scene refs + 1 previous_shot = 8，远低于后端 13 上限

#### PM 补充关联点

1. **账户系统优先级提升** — 续写/历史/上传管理都依赖用户账户
2. **存储规划** — 先本地，后对象存储
3. **Stage A/B 边界** — A 管输入材料，B 管确认/调整大纲
4. **成本影响** — AI 提取角色信息 + 自定义风格分析增加 API 成本

### PM 澄清问题 + Founder 回答

| 问题 | 回答 |
|------|------|
| Q1: 角色信息提取方式？ | AI 自动提取（可用 Haiku，产品运行时允许） |
| Q2: 故事文档解析深度？ | 先浅层（提取文本 → 当 idea 传入） |
| Q3: 宽高比 per-story 还是 per-shot？ | Per-story only（16:9 或 2:3） |
| Q4: 长篇续写模式？ | 两种：自动续写 + 用户指导续写 |
| Q5: 预设与自定义风格关系？ | 互斥（选预设清空自定义，反之亦然） |

### 最终决策

#### 决策 1: 角色参考图上传
- 用户上传 1 张图 → AI 自动提取角色信息（可用 Haiku）
- 系统自动补全 portrait + fullbody 两张参考图
- 最多 5 个角色（上传 + 系统生成合计）
- 与场景参考图分开入口

#### 决策 2: 场景参考图上传
- 独立入口（非角色入口）
- 最多 8 个场景
- 用户上传 1 张 → 系统补全 interior/exterior

#### 决策 3: 上传故事文档
- **浅层方案优先**：前端提取文本 → 当作 idea 传入后端
- 支持格式：md / txt / PDF
- 不做深层解析（不提取角色/场景/情节结构）

#### 决策 4: 宽高比选择
- Per-story 级别，非 per-shot
- 两个选项：16:9（横屏）或 2:3（竖屏/抖音）
- 后端 `aspect_ratio` 参数已支持动态值

#### 决策 5: 长篇连续故事
- 新增第 4 个篇幅选项：**长篇 epic**（max 36 shots/generation）
- 两种续写模式：自动续写（系统自动生成后续章节）+ 用户指导续写（用户提供方向后生成）
- 需要账户系统支持（保存历史/续写状态）

#### 决策 6: 风格系统升级
- 16 个预设风格全部可见（从 8 → 16）：realistic, cartoon, pixar_3d, anime, ghibli, illustration, watercolor, children_book, manga, slam_dunk, korean_webtoon, oil_painting, cyberpunk, ink, pixel
- 新增自定义风格上传：用户上传参考图 → Sonnet 4.6 分析 → 提取风格关键词
- **预设与自定义互斥**

#### 决策 7: 渲染策略
- **NB2 原生渲染为主**，TextOverlay 仅作备用
- 前端无需关心此区分

#### 决策 8: 其他确认
- 账户系统优先级提升（续写/历史/上传的前置条件）
- 存储：先本地，后续迁移对象存储
- 前端先用 Mock 数据独立开发
- CLAUDE.md "禁止 Haiku" 规则仅适用于开发 Agent，产品运行时可用 Haiku

### 架构设计

- **状态管理**：React Context + useReducer（零新 npm 依赖）
- **Provider 层级**：AuthProvider (root) → CreateProvider (/create/*)
- **页面模式**：page.tsx (Server, metadata) + Content.tsx (Client, "use client")
- **动画**：Framer Motion delay递增 + layoutId Spring + AnimatePresence

### 理由
- 7 项功能升级都基于后端已有能力或可扩展能力，技术可行性已验证
- React Context + useReducer 维持零新依赖原则
- Mock 数据优先策略允许前后端独立开发
- 3 阶段实施（P0 → P1 → P2）风险可控

### 后续行动
- [x] @Frontend: TASK-CREATE-UPGRADE P0 — 16 文件（9新建+7修改）✅ PM 复验 4.8/5 (2026-03-02)
- [x] @Frontend: TASK-CREATE-UPGRADE P1 — 7 文件（4新建+3修改）✅ PM 复验 4.7/5 (2026-03-02)
- [x] @Frontend: TASK-CREATE-UPGRADE P2 — 14 文件（10新建+4修改）✅ 完成 (2026-03-03)，待 PM 复验
- [ ] @Backend: 后续为前端提供 API endpoints（P0 完成后）

---

## DEC-014: 移除 previous_shot_image 传递 (Plan A)

**日期**: 2026-03-03
**决策者**: @Founder（采纳 PM 建议）
**影响范围**: Backend (image pipeline) + AI-ML (Stage 4/5 prompts)

### 问题
Shot 生成时，系统将前一个 shot 的输出图像作为 "环境参考" (Image 1) 传入下一个 shot。PM 独立分析发现这导致三个严重问题：
1. **构图感染**：模型复制前序 shot 的角度/构图/色调，30 度法则严重违反
2. **链式放大**：29 shots 串行传递 = 误差累积，到后期 shots 构图僵化
3. **跨场景 Bug**：代码无 `location_id` 变化检测，转场时传入错误场景图像

### 方案选项
1. **方案 A (PM 推荐)**: 完全移除 previous_shot_image 传递。场景参考图 + 文字 prompt 提供环境连续性
2. **方案 B**: 仅同场景传递（检测 location_id 变化，变了就不传）
3. **方案 C**: 保持传递，增强 MUST VARY 指令（与模型倾向对抗，不可靠）

### 最终决策
**选择方案 A: 完全移除 previous_shot_image 传递**

### 理由
- 场景参考图 (interior/exterior anchor) 已覆盖环境连续功能 — 这是它的设计初衷
- Text prompt 已包含光线/氛围描述 — 文字比图像更精确可控
- 彻底消除构图感染 — 不是 "缓解" 是 "根治"
- 释放 1 个参考图位 — 3 人场景从 8 张减到 5 张（配合 SQ-2 智能选择），模型负担大幅减轻
- 打断误差链 — 每个 shot 独立构图，不受前序影响
- 实现最简 — 传 None 即可，不需要新增逻辑
- 完全可逆 — 如果测试发现环境不一致，随时可以加回来

### 后续行动
- [ ] @Backend: SQ-8 — 移除 previous_shot_image 传递（pipeline_orchestrator.py, image_generator.py, storyboard_prompts.py）
- [x] @PM: SQ-7 — 更新 CLAUDE.md 第 2.2 节 + guide 第 656 行 + Pro→NB2 规则 ✅ (2026-03-04)
- [ ] @Tester: Step 7 — A/B 对比验证（环境连续性是否受影响）

---

## DEC-015: Harness V2 Engineering — CI/CD + Schema 验证 + 成本熔断 + 监控

**日期**: 2026-04-15
**决策者**: @创始人
**影响范围**: 全局（工程质量保障体系）

### 问题
Harness V1（PostToolUse pyright/tsc hooks + PreCommit 架构测试 + PrePush 全量测试）已建立本地质量门控，但缺少：① 云端 CI 验证 ② Pipeline 数据格式校验 ③ 成本失控保护 ④ 生产运行监控

### 最终决策
**实施 Harness V2 Engineering，4 大能力全面建立**

#### 能力 1: GitHub Actions CI
- 每次 push 触发：pyright 类型检查 + tsc 编译检查 + pytest 架构测试
- 失败阻断 merge

#### 能力 2: Pipeline Schema 验证
- `pipeline_schemas.py`：OutlineSchema、ScreenplaySchema、CharacterSchema、ShotSchema
- Stage 1→2 边界、Stage 3→4 边界强制 schema 校验
- 字段缺失/类型错误立即报错

#### 能力 3: $10 成本熔断器
- 单次 pipeline 运行成本超 $10 自动中断
- 防止提示词 bug 导致无限 token 消耗

#### 能力 4: 6 EP Sensor + 监控端点
- 6 个 Endpoint Sensor（EP-1~EP-6）：pipeline 各阶段关键指标采集
- `/api/monitor/sensors` 端点暴露实时数据
- 为后续 R4 监控告警系统（DEC-015 延伸任务）奠基

### 执行结果
3 Phase 全部完成：Phase 1（CI + Schema，commit 87aeaa4）→ Phase 2（成本熔断 + EP Sensor，commit ea0edb1）→ Phase 3（PreCommit + PrePush + VPS 部署，VPS PASS）

### 后续行动
- [x] Phase 1-3 全部完成 ✅
- [ ] R4 监控告警：修复外部 `/api/health` 404 + 配置告警服务（见 PENDING.md 监控告警 R4）

---

## DEC-016: Prompt B' 格式设为默认（-46% tokens，盲测验证）

**日期**: 2026-04-15
**决策者**: @创始人
**影响范围**: AI-ML（storyboard_prompts.py）+ Backend（image_generator.py）

### 问题
AI-ML 开发了 Prompt B' 格式（在 A 格式基础上压缩冗余，去掉重复的风格前缀块、精简 IMAGE 编号说明等），token 消耗降低 46%。需要决定是否替换 A 格式成为默认。

### 验证过程
- A vs B' 盲测：Founder 在不知道来源的情况下对 10 对图像逐对评分
- 结果：B' 5 分，A 4 分（5:4，B' 略胜）
- 视觉质量无可感知下降，成本降低 46%

### 最终决策
**B' 格式正式设为默认，替代 A 格式**

### 理由
- 盲测验证视觉质量无退步（5:4 Founder 甚至略偏好 B'）
- -46% tokens → 每故事成本从 ~$3.70（A 格式）降至 ~$3.40（短篇）
- 更短 prompt 减少模型注意力稀释，反而有助于关键指令权重
- 代码更简洁，维护成本降低

### 成本影响（更新后官方数据）
- 短篇（3 角色，21 shots，NB2 + B' + Sonnet 4.6）：**~$3.40/故事**
- 中长篇满配（6 角色，45 shots）：**~$6.82/故事**

### 后续行动
- [x] B' 格式部署为默认 ✅
- [x] VPS 部署生效 ✅
- [x] CLAUDE.md 成本数据更新 ✅

---

## DEC-017: Stage D 产品交互逻辑 — 调整画面 + 编辑文字 + 重新生成

**日期**: 2026-04-14
**决策者**: @创始人
**影响范围**: Frontend（Stage D 预览页）+ Backend（/api/shots/adjust 端点）

### 问题
Stage D 预览页需要明确"用户能对单张 shot 做什么"的三种操作的精确行为定义，防止前后端理解不一致。

### 最终决策
**Stage D 三种操作行为定义**

| 操作 | 触发 | 执行者 | 行为 |
|------|------|--------|------|
| **调整画面** | 用户输入文字描述修改意图 | Backend + Haiku API | Haiku 根据用户描述重写当前 shot 的 `image_prompt`，然后重新调用 NB2 生图 |
| **编辑文字** | 用户直接编辑文字框 | 纯前端 | 修改 shot 的 `chinese_text`（旁白/对话），不触发任何 API 调用 |
| **重新生成** | 用户点击按钮 | Backend | 用当前 `image_prompt`（不修改）重新调用 NB2 生图，相当于 re-roll |

### 理由
- "调整画面" 用 Haiku 而非 Sonnet 4.6：轻量 prompt 改写任务，Haiku 足够胜任，成本低
- "编辑文字" 纯前端：用户改 TTS 文字不涉及图像，无需后端参与
- "重新生成" 简单 re-roll：用户对构图随机性不满，保持 prompt 不变换随机种子

### 后续行动
- [x] Backend 实现 `/api/shots/adjust` 端点 ✅
- [x] Frontend Stage D 三种操作 UI 完成 ✅
- [ ] Tester 验收 Stage D 完整流程

---

## DEC-018: Haiku 运行时使用场景澄清 — 产品运行时轻量 API 调用允许 Haiku

**日期**: 2026-04-14
**决策者**: @创始人
**影响范围**: 全局（模型使用规范）

### 问题
CLAUDE.md 中明确"禁止 Haiku"，但 DEC-017 的 Stage D "调整画面" 需要用 Haiku 做轻量 prompt 改写。两者存在表面矛盾。

### 最终决策
**规则澄清：禁止 Haiku 仅针对开发 Agent 子代理，产品运行时允许 Haiku 用于轻量任务**

### 规则重申

| 场景 | 规则 | 理由 |
|------|------|------|
| 开发 Agent（Task 工具、代码生成、文档分析等子代理） | ❌ 禁止 Haiku，最低 Sonnet 4.6 | 开发质量要求高，Haiku 与 Opus 差距大 |
| 产品运行时 API 调用（Stage D 画面调整、分类标注、轻量分析等） | ✅ 允许 Haiku | 成本优化合理，用户不感知模型差异 |

### 适用的产品运行时 Haiku 调用场景
- Stage D "调整画面"：Haiku 改写 `image_prompt`（DEC-017）
- 角色参考图信息提取（DEC-013 决策 1）
- 未来其他轻量分类/标注任务

### 后续行动
- [x] CLAUDE.md 规则说明已更新（"子代理模型规则"章节） ✅
- [x] TEAM_CHAT.md 已通知全体 Agent ✅

---

## DEC-019: image_prompt 中文阈值收紧 — 15% → 5%

**日期**: 2026-04-15
**决策者**: @创始人
**影响范围**: AI-ML（Stage 4 StoryboardDirector prompt 规则）+ Backend（image_generator.py 校验）

### 问题
Stage 4 生成的 `image_prompt` 被要求全英文（CLAUDE.md 规定），但允许少量中文（如中文名字、传统建筑专名）。原阈值 15% 过宽松，导致部分 prompt 混入大量非必要中文词汇，影响 Gemini NB2 图像生成质量。

### 最终决策
**中文字符比例阈值从 15% 收紧为 5%**

### 理由
- 15% 阈值在 100 字符的 prompt 中允许 15 个中文字，过于宽松
- 5% 已足够容纳合理的中文专名（如"陈默 (Chen Mo)"、"汉服"等）
- 更低的中文比例 = 更好的 NB2 响应质量（英文 prompt Gemini 理解更准确）
- Harness V2 的 Schema 验证将自动捕获超阈值的 prompt

### 允许的中文例外（5% 以内）
延用 CLAUDE.md 已有规定：中文人名、传统建筑专名、传统服饰专名、传统美食/店铺、画面内书法/题字、节日视觉元素文字

### 后续行动
- [x] Stage 4 prompt 规则更新（中文 ≤5% 强制规则）✅
- [x] image_generator.py 中文比例校验更新为 5% ✅
- [x] Harness V2 Schema 验证已覆盖此规则 ✅

---

## DEC-020: M1 工程并行化优先（图像生成串行 → 并发）

**日期**: 2026-04-25
**决策者**: @Founder + @Coordinator
**影响范围**: Pipeline / Stage 5 图像生成 / UX

### 问题
Code Forensics Agent（2026-04-25）地毯式审查发现：
- `pipeline_orchestrator.py:524-677` Stage 5 主循环**完全串行**（for 循环 + `await asyncio.sleep(0.5)`）
- `max_concurrent_images=2`（run() 签名）和 `IMAGE_MAX_CONCURRENT=3`（config.py:32）**全是死参数**，从未被读取
- 现成 `image_generator.py:1475 generate_batch()` 已实现 `asyncio.Semaphore + asyncio.gather()`，**被孤立**，pipeline 不调用
- 实测 20 张耗时 **807s ≈ 13.5 min**（PROJECT_STATUS R6 数据）

### 方案选项
1. **方案 A**：立即并行化（M1 落地，工程量 1-2 天）—— 接入 generate_batch()，并发 3
2. **方案 B**：等 Pre-A 后再做（等更复杂的批量优化方案出来）
3. **方案 C**：跳过并行化，直接做 Gemini Batch API（异步队列）

### 最终决策
**选择方案 A：立即并行化（M1 优先）**

### 理由
- **工程量极小**：generate_batch() 已实现且测试过，pipeline 主路径只需替换 for 循环
- **零成本 UX 跃迁**：13.5 min → ~4.5 min（达到 Midjourney Fast Mode 体验），不变成本
- **BP 价值大**：Q1 KR 直接可写"单条耗时 4 min（已实测）"
- **不依赖外部条件**：Google NB2 Batch API 当前有 Bug 卡死（forum 多帖证实，2026-04 无修复公告），方案 C 不可行
- **风险已知**：NB2 高峰期 429 失败率 ~30%（Agent B 数据），现有重试代码已覆盖，需在并行场景下确保 Semaphore 限流 + 退避兜底覆盖所有失败路径

### 后续行动
- [ ] PM 派 Backend：详细规格见 PENDING `TASK-PARALLEL-M1`
- [ ] Backend 实现：`pipeline_orchestrator.py` Stage 5 接入 generate_batch()，并发 3
- [ ] Backend 兜底：429 / 限流 / 部分失败 / 全部失败的所有分支测试覆盖
- [ ] Tester 回归：3 角色一致性 ≥ 100%、6 角色 ≥ 90% 不掉
- [ ] PM 审查后 DevOps 部署 VPS

---

## DEC-021: BP 上写完整 4 层杠杆 + 自建集群路线图

**日期**: 2026-04-25
**决策者**: @Founder
**影响范围**: BP（天使轮，500-800 万 RMB）/ 单位经济叙事

### 问题
当前单条成本 $1.85，Pro ¥199/月（10 条配额）毛利率 ~30%，远低于 SaaS 行业 70-80% 基准。BP 要不要写"自建集群"这条 M18+ 路线？

### 方案选项
1. **方案 A**：完整 4 层杠杆 + M18 自建集群 → 85% 毛利路线图
2. **方案 B**：只写 M0→M12 短期路径（30%→76%），不提自建集群

### 最终决策
**选择方案 A：完整 4 层杠杆 + 自建集群路线图**

### 理由
- 天使 VC 看路线图比 Pre-A 还重要 —— "我们 18 月之后怎么办"必须有答案
- "成本工程化"是 Pre-A 投资人最喜欢听的故事 —— 可预期、可量化
- CTO Ben 的"0→上亿年收入"经验 + AI/NLP 背景，让"自建集群"在团队可信度上立得住
- 4 层杠杆中只要 1-2 条命中即可推动毛利率，反脆弱
- 完整路线图 + 不画饼，VC 不会觉得"M18 80%"是空话

### 后续行动
- [x] 在 `docs/BP_SUPPLEMENT_2026-04-23.md` 加第 6 节《单位经济与成本工程》（含 4 层杠杆表 + 18 月曲线 + 4 段叙事）
- [x] 在 `.team-brain/analysis/COST_UX_ROADMAP_2026Q2.md` 创建详细路线图（每层杠杆的实施细节）
- [ ] 路线图按 M3 / M6 / M9 / M12 / M18 节点跟踪进度

---

## DEC-022: 不做 gemini-2.5 vs NB2 画质盲测（暂缓）

**日期**: 2026-04-25
**决策者**: @Founder
**影响范围**: 成本路径选择 / 图像模型选型

### 问题
gemini-2.5-flash-image Batch API 可用（NB2 Batch 卡死时的替代路径），单图 $0.0195（vs NB2 $0.067，**降 71%**）。要不要做 30 张盲测看画质降级是否可接受？

### 方案选项
1. **方案 A**：派 AI-ML 跑 gemini-2.5 vs NB2 30 张盲测，确定能否降级换 71% 折扣
2. **方案 B**：不做盲测，NB2 是产品力护城河，画质不降级

### 最终决策
**选择方案 B：不做盲测，NB2 不降级**

### 理由
- NB2 的 ~95% 多角色一致性 + 100% 3 人场景一致性是序话产品力护城河
- gemini-2.5 画质明显降低（Agent B 调研多源证实）
- 序话不打价格战，对标可灵 ¥66/月走"高质等 15min"路线证明国内市场吃这套
- Founder 的 UI/UX 审美强 + 内测用户对画质敏感，降级风险高于收益
- M3 Credits 制 + L1 工程并行化已能把毛利率推到 53% / UX 到 4 min，不需要画质降级

### 后续行动
- [ ] 关注 Google 是否修 NB2 Batch Bug（每月一次复测 forum + Console 自测）
- [ ] 若 NB2 Batch 修复 → 引入"章节预生成"等部分场景 batch（混合双轨，仅 B 端 / API）
- [ ] C 端实时主路径**永远不降级**到 gemini-2.5

---

## DEC-023: 8 个 Agent frontmatter hardcode model + effort（model 分级 + 全员 xhigh）

**日期**: 2026-04-28
**决策者**: @Founder
**影响范围**: 所有 Founder 团队 Agent（含 Coordinator）spawn 默认行为

### 问题
- 8 个 agent `.md` frontmatter 全部 `model: opus` 默认 — 跟 `feedback_spawn_use_sonnet_for_simple_tasks.md`（执行类用 Sonnet 4.6）原则冲突
- 全部没设 `effort` 字段 — spawn 时继承 session 默认（medium）
- 自定义 subagent_type symlink 修复后（DEC 2026-04-28），可以利用 frontmatter 自动注入这些参数

### 验证
- claude-code-guide agent 确认官方文档（https://code.claude.com/docs/en/sub-agents.md L234-256）支持 `effort` 字段
- 取值：`low / medium / high / xhigh / max`
- spawn 时不显式传 → 用 frontmatter 默认；显式传 → 覆盖

### 最终决策

**全员 effort: xhigh + model 分级**：

| Agent | model | effort | 理由 |
|-------|-------|--------|------|
| ai-ml | opus | xhigh | 深度 prompt 推理 |
| pm | opus | xhigh | 协调推理 |
| xuhuastory-boss-coordinator | opus | xhigh | 协调推理（产品级 lead）|
| backend | sonnet | xhigh | 执行类（成本 5x 优化）|
| devops | sonnet | xhigh | 执行类 |
| frontend | sonnet | xhigh | 执行类 |
| tester | sonnet | xhigh | 执行类 |
| resonance | sonnet | xhigh | Founder 暂时选 Sonnet（原 Coordinator 建议 opus） |

### 理由
- effort xhigh：质量第一（Founder 偏好，feedback_opus_47_and_effort_max.md 支持）
- model 分级：执行类降到 Sonnet 节省 5x 成本（feedback_spawn_use_sonnet_for_simple_tasks.md）
- 真正复杂的架构改造：spawn 时**显式传** `effort: max` 临时覆盖（max 仅 Opus 4.7 可用）

### 已知风险
- ⚠️ **xhigh 可能是 Opus 4.7 专属**（slash command 提示"(Opus 4.7 only)"）。Sonnet agent 写 effort: xhigh 可能 silent 降级到 high / 报错 / 被 ignore — 不知道哪种。最差也就是 Sonnet 5 个 agent 跑 high 而不是 xhigh，**不会比之前差**
- 改 frontmatter 默认值会影响所有未来 spawn — 需要监控质量/成本变化
- 之前一些场景默认 opus 可能现在自动降到 sonnet — 如果某 task 质量下降，spawn 时显式 `model: opus` 覆盖

### 后续行动
- [x] 8 个 agent frontmatter 已修改（grep 校验通过）
- [x] DEC-023 记录
- [ ] TEAM_CHAT @all 通知（Coordinator 在做）
- [ ] coordinator-progress 三件套更新（Coordinator 在做）
- [ ] 监控 1-2 周内 spawn 质量/成本变化
- [ ] 如发现 Sonnet xhigh 实际不生效（token usage 跟 high 没差异）→ 调整为 high

---

## DEC-024: Scenes 确认作为用户旅程第三停留点（修订 DEC-011）

**日期**: 2026-05-11
**决策者**: Founder（test12 实测发现 + /xhteam 拍板）+ PM 落地
**影响范围**: 用户旅程 Stage B / Pipeline 时序 / DB schema / 前后端 API 契约

### 问题

DEC-011 原设计 Stage B 有 outline + characters 两处用户停留点。但 test12（2026-05-11）+ B42（2026-05-09）+ B50（2026-05-11）反复发现：
- 前端 ScenePreview 完整设计已存在（scene-preview sub-phase + 组件 + URL /scenes + reducer + 倒计时）
- 后端长期断裂 4 处（无 confirm-scenes 端点 / 无 scenes_confirmed 字段 / Pipeline Stage 3 后无 pause / 前端 heuristic 兜底）
- 用户失去场景调整权（输入"晨跑遇到男生"→ 生成"早 8 点路口"，没机会改成"下班路上"）

### 方案选项

1. **方案 A（采纳）**: scenes 确认作为第三停留点（与 outline + characters 对等）— 60s 倒计时兜底
2. **方案 B**: 不停留，跳过用户确认（PM 18:10 误判 "by-design"，被 Founder 反驳）
3. **方案 C**: 停留但不可编辑，只展示（妥协方案，不能修改 → 用户失去场景调整权）

### 最终决策

**方案 A** — 完整恢复 scenes 用户停留点：
- 用户能看 11 个场景中文描述 + 编辑某个场景 description + 保存修改 + 主动点"确认场景，继续"
- **60 秒倒计时兜底**（Founder 决策，防用户走开导致卡死）
- Pipeline R4-2 wait loop **1800 秒超时兜底**（与 R4-1 一致）

### 实施（Wave 6 完成）

- DB: `projects.scenes_confirmed` Column + Alembic 005 backfill（已跑完 Stage 4 的老项目自动设为 TRUE）
- API: `POST /chapters/{n}/confirm-scenes` + `ConfirmScenesRequest(modified_scenes?)`
- Pipeline: R4-2 wait loop（参照 R4-1，1800s 超时）+ scenes_json reload from DB
- Frontend: hydrate 改读真字段（不再 heuristic）+ ScenePreview 编辑能力 + 60s 倒计时 + 调真 API
- 前后端联调通过 PM 第四步审查

### 影响

- **CLAUDE.md 用户旅程章节**需更新（Stage B 三停留点）
- **历史 PEND** B42 / B50 / BUG-SCENES-CONFIRM-MISSING 全部由本决策闭环

### 后续行动

- [ ] Tester 跑 3 轮分阶段回归（B52 cascade / Scenes 确认 / 全流程）
- [ ] CLAUDE.md 用户旅程章节追加 scenes 确认描述
- [ ] PENDING.md 删除 BUG-SCENES-CONFIRM-MISSING 条目（Tester 验证通过后由 PM 删）

---

## DEC-025: T17 ShotValidator 4 层防御（数据契约错配修复，方案 D 自创）

**日期**: 2026-05-12
**决策者**: AI-ML（自创方案 D）+ 创始人 5/12 22:00 plan mode 批准
**影响范围**: AI-ML 核心修复（shot_validator.py + storyboard_prompts.py）+ Backend P3 后续重构提议

### 问题

test13 实测（项目 `70eed512-...`，5/12 13:56-15:53）暴露 ShotValidator 对 Stage 4 LLM 写的 `composition.foreground/background` 长描述句（90-366 chars）误判率 **11%**（Shot 6 fail + Shot 15 边缘 PASS）。根因 5 层调用栈追踪后锁定为：

- Stage 4 LLM 把 `composition.foreground/background` 写成构图描述句（产品所需，帮 Seedream 生有纵深的画面）
- pipeline_orchestrator.py:1068-1080 把这两字段当离散道具列表（`key_props`）传给 ShotValidator
- Haiku 试图对长描述做"严格字面匹配"判断，找不到完整对应大概率返 false
- 旧阈值 `missing > 50% → fail` 放大误判触发 Pipeline retry

数据契约错配，不是 LLM bug，不是 Haiku 模型能力问题，不是阈值"50%"不合理。

### 方案选项

| 方案 | 改什么 | 评分 | 说明 |
|------|--------|------|------|
| **A 放宽阈值** | `missing > 50%` → `missing > 80%` | ❌ 2/10 | 治标不治本，未来 4+ probes 仍触发 |
| **B 减少 LLM 强制要素** | 改 Stage 4 prompt 让 composition 字段写得更短 | ❌ 1/10 | 错位 — 缩短描述会降低 Seedream 生图质量，违反"宁可贵不可烂"准则 |
| **C 失败后改 prompt 重试** | Pipeline 检测到 fail 后让 LLM 重写 image_prompt 再生 | ❌ 3/10 | +$0.04/fail；不解决 Haiku 误判；改 pipeline_orchestrator 超 AI-ML 权限 |
| **D 自创 4 层组合防御** | 净化 + lenient prompt + 阈值放宽 + 文档防御 | ✅ 9/10 | 治本（解决数据契约错配），不破坏 LLM 行为，不超权限 |

### 最终决策

**方案 D 4 层组合防御**：

| 层 | 改什么 | 文件 |
|----|--------|------|
| **D-1 净化层** | `_sanitize_prop_probe()` 长描述（>80c）在第一个修饰词位置截断保留前置核心名词 | `app/services/shot_validator.py` L93-140 |
| **D-2 Prompt 层** | `VALIDATION_PROMPT_PROPS` 升级为 LENIENT semantic matching mode + "When in doubt, mark true" | `app/services/shot_validator.py` L177-200 |
| **D-3 阈值层** | 旧 `missing > 50%` → 新 `≥2 probes 且 100% 全失`，部分缺失只 log；双键 fallback 兼容 Haiku 行为漂移 | `app/services/shot_validator.py` L392-429 |
| **D-4 文档防御** | 新增 `COMPOSITION_FIELD_SEMANTICS_NOTE` 常量（仅文档不注入 LLM）说明字段语义 + 给未来重构方向 | `app/prompts/storyboard_prompts.py` L818-842 |

### 越权说明（重要）

**PM 5/12 16:30 派活时给的是 A/B/C 三选一**，AI-ML 在职责范围内（`app/services/shot_validator.py` + `app/prompts/storyboard_prompts.py` 都在白名单）**自创方案 D**，理由：

1. A/B/C 都不能根治"数据契约错配"的真因（A 治标 / B 错位 / C 超权限）
2. 方案 D 完全在 AI-ML 文件白名单内（不动 pipeline_orchestrator.py）
3. 4 层防御互补，单层失效另外三层兜底
4. 单元 29/29 + 架构 7/7 PASS 验证逻辑正确

**Founder 5/12 22:00 plan mode 批准认可**: agent 在权限边界内独立判断更优解是合理的，下次类似情况：
- AI-ML 应该敢于自创方案
- 但 SendMessage 时要**明确说明越权 + 给出对比理由 + 测试证据**让 PM/Founder 决策
- 不要默认照单全收 PM 派的方案选项

### 实施 + 验证

- ✅ 改 2 文件 + 备份 `.bak-20260512-d3-pre`
- ✅ 单元验证 29/29 PASS（Phase 1 净化 14 + Phase 2 阈值 11 + Phase 3 test13 真数据回放 4）
- ✅ pytest test_architecture 7/7 PASS
- ✅ py_compile 双文件 PASS
- ⚠️ 端到端 LLM 真测待 PM 协调 @tester 跑 test14 验证 fail 率从 11% → 目标 < 2%

### 后续行动

- [x] 单元 29/29 PASS + 架构 7/7 PASS + 备份完整 + 文档常量到位（5/12 16:45 完成）
- [ ] PM 重启 backend 让改动生效
- [ ] Tester 跑 test14 真 LLM 验证（目标 fail 率 < 2%）
- [ ] Backend P3 后续重构（PENDING.md 加 BUG-DATA-CONTRACT-COMPOSITION-AS-PROPS）— 让 Stage 4 LLM 输出离散 `narrative_props` 字段，下游不再读 composition 描述句
- [ ] T17 fail 率监控（PM 周报）

### 关联文件

- 完整分析: `.team-brain/analysis/T17_VALIDATOR_FIX_ANALYSIS.md`（9 段，含 5 层根因 + 4 选 1 评分 + 验证证据 + 5 风险点 + 经验复盘）
- Plan 文件: `~/.claude/plans/moonlit-imagining-sunset-agent-ae7cb617fb97038e8.md`（D3 实施记录）
- KEY_LEARNINGS 经验段: "数据契约错配比 prompt 写得差更隐蔽"

---

## 决策模板

```markdown
## DEC-XXX: [主题]

**日期**: YYYY-MM-DD
**决策者**: @角色
**影响范围**: [模块/全局]

### 问题
[要解决什么问题]

### 方案选项
1. **方案A**: [描述]
2. **方案B**: [描述]

### 最终决策
**选择方案 X: [名称]**

### 理由
- 理由1
- 理由2

### 后续行动
- [ ] Action 1
- [ ] Action 2
```

---

## [2026-05-18] DEC-040 RISK-T20-3 招牌污染方案 A

**问题**: scene_reference_manager.py `_detect_signage_name` keyword fallback 过度激进, 把含 "楼/店/铺/坊/馆/堂..." 的 location display_name 整段当招牌注入 scene_ref prompt, 污染所有 shot.

**实证**: test18 outline 4 location 中"陈默租住楼的雨夜楼道口"被 keyword "楼" 命中 → 整段渲染为中文招牌 → Shot 5/8/13 全部污染.

**Universal 影响**: 含上述关键词的所有中文场景 (办公楼/教学楼/出租屋/茶馆/书坊/教堂等) 都会被误判.

**Founder 选 方案 A**: 完全删除 keyword fallback, 信任 Stage 1 outline LLM 的 signage_text 字段决策.

**理由**:
- Stage 1 LLM 已经做了正确决策 (test18 实证: 3 个空 + 1 个"万象珠宝")
- Keyword 方案永远修不完 (新故事类型一定还会翻车)
- 信任 LLM 决策最 universal

**实施**: backend agent 删除 _detect_signage_name L746-757, 保留 L744-745. 4 universal Tester 用例通过.

## [2026-05-18] DEC-041 TASK-T20-FIXBATCH 5 P0+P1 并行修

**Founder 决策**: 5 阻断级 RISK 一起修, 确保无冲突.

**派活分配** (3 agent 并行, 0 文件冲突):
- Backend (Sonnet 4.6 xhigh): T20-3 招牌污染 → `scene_reference_manager.py`
- Frontend (Sonnet 4.6 xhigh): T20-2 ETA UX 3 bug → `useETA.ts`
- AI-ML (Opus 4.7 max): T20-7+T20-1+T20-4 串行 → `storyboard_director.py`

**完成结果**: 3 agent 全部完成, PM 5 维度审查通过.

**配套后置**: T20-6 (ShotValidator universal 缺陷) 等 T20-7 修完后看效果再决定方案.


## [2026-05-18] DEC-042 RISK-T20-9 真根因更深 (Backend #1 纠正 PM audit)

PM TEST18_SECOND_RUN_AUDIT 把 T20-9 根因归到 "Frontend useETA.ts hardcoded STAGE_BUDGET 1440". Backend #1 agent 地毯式查后发现:
1. backend `estimated_remaining_seconds` 字段早已存在 (chapters.py:366)
2. frontend useETA L187 已 prefer backend value
3. **真问题**: chapters.py:344 fallback hardcoded `stage_progress=0.5` + per_shot=60s 过乐观

**修复**: per_shot 60→80 (双源 pipeline_orchestrator + job_manager), 用真实 progress 计算 fallback, 加 actual_shot_count + max_concurrent 字段供 frontend 兜底用

**实测**: 19 shots × 80 / 3 = 506s vs 实测 540s = 低估 6% (上次 42%)

**Ben 教训 #2 实证**: PM 表象诊断 ≠ 真根因, agent 地毯式深查代码更精准. 这正是 "工作量越大越要严" 原则的实证.


## [2026-05-19] DEC-043 RISK-T20-10 方案 C (Optional + per-type model_validator) + 5+ 下游统一收敛 CharacterPromptBuilder

**根因 (Explore agent 地毯式 5 维度查实证)**:
- Wave 14 RISK-T19-6 修了 LLM prompt 让 anthropomorphic_animal 用 species/fur_color 等动物字段 (5 处映射)
- 但 CharacterSchema Pydantic (pipeline_schemas.py CharacterPhysical) 仍强制 human-only 字段 (skin_tone/face_shape/hair_color/hair_style required)
- + 5 处下游 consumers (storyboard_service.py 2 函数 + storyboard_prompts.py 2 函数 + pipeline_orchestrator.py 1 函数) hardcoded human 字段
- 18/19 种非 human character_type 全受影响

**决策方案 C** (混合 A 主 + B 兜底):
- physical 所有 sub-field 改 Optional (允许任意字段)
- 加 `model_validator(mode='after')` 根据 character_type 动态检查"至少一组核心字段满足"
- 类型增加成本最低 (只加一行 dict entry), 校验严格度可控

**必须同时收敛 5+ 处下游 consumers**:
- 全部 dispatch 到 Wave 14 已建的 `CharacterPromptBuilder.build_character_prompt()` (19 种类型完整支持)
- 消除重复实现, 一处修改全栈生效

**Universal 测试用例**: 10 cases 覆盖 5+ character_type (human/anthropomorphic_animal/robot/fantasy_creature/supernatural/vehicle_character/insect/miniature/edge cases)


## [2026-05-19] DEC-044 产品最终形态确定: shots + BGM (无 TTS / 无朗读旁白) + 旁白融入 shot

**Founder 5/19 16:08 重大决策** (test17 v2 实测后):

### 确定的产品形态
- **最终交付**: shots (含画面内文字: dialogue 气泡 + thought 心理 + narration caption) + BGM
- **不再使用**: TTS 旁白朗读 + 视频合成 (Phase 4.5 暂缓)
- **理由**: 当前形态已经很好, 用户可视化文字 + BGM 已能承载完整故事

### 暴露的通病 (新 P0 RISK-T20-21)
- 用户脱旁白故事**晦涩不易懂** (Founder 原话)
- 根因: ScreenplayWriter 输出的 narration_segment 含 30-40% 关键情节信息, 但旁白不再被用户看到
- 产品决策 (无 TTS) 和 Pipeline prompt (Stage 3 假设有旁白朗读) 脱节

### 重构方向 (非 Pipeline 层, prompt 工程层)
1. **Stage 3 ScreenplayWriter prompt 重构**: 旁白不再"全文写", 关键情节信息融入:
   - shot 内 dialogue (角色对话气泡)
   - shot 内 thought (心理活动黑底白字)
   - shot 内 narration caption (顶部白底黑字短旁白 / 底部黑底白字)
2. **Stage 4 StoryboardDirector prompt 配套**: 每 shot 必须有足够可视化文字让用户"光看就知道情节"
3. **TextOverlayServiceV2 验证**: 多对话气泡 + 多心理 + 顶部+底部双 caption 是否支持
4. **Frontend UI 文案**: Preview "旁白(只读)" → "描述(只读)" (这里是用户可调整画面描述的地方)

### Owner 分工
- **AI-ML (Opus 4.7 max thinking)**: prompt 重构主战场 (RISK-T20-21)
- **Backend**: 配套服务集成 (如需 TextOverlay 扩展)
- **Frontend**: UI 文案改 + Preview 描述展示
- **Tester**: 端到端故事可读性验证 (关闭旁白栏后用户能否完整理解情节)

### 验收标准
关闭旁白文字栏, 用户只看 shot 图 + 心理/对话/caption, **能完整理解故事情节**.

### 影响
- shot 内文字密度会**增加** (这是预期, 不是 bug)
- ScreenplayWriter 输出格式不变 (向后兼容), narration_segment 变短, dialogue/thought/narration 字段填得更丰富
- 内测前必修 (P0)


## [2026-05-19] DEC-045 Wave 4 派活 — test19 实证后内测前 7 项修

**Founder 5/19 22:30 决策**: test19 端到端测试发现 6 新 RISK + 3 KEY_LEARNINGS 待加. 内测前必修 P0 + 可延后 P2 **都要修**.

### 7 项 RISK 全修分组

**AI-ML (Opus 4.7 max thinking, 4 任务 1 session 串行)**:
1. **T20-26 P0**: PromptRewriter Haiku prompt 改 replace 策略 + 强制 strip 暗黑题材敏感词 (ghost/double-exposure/overlap/merging/deceased emerges) — KEY_LEARNINGS #37 + #38 实证落地
2. **Stage 4 prompt 加 Seedream 敏感词避开规则**: storyboard_prompts.py 强制 LLM image_prompt 不含 ghost/double-exposure 等敏感词, 用安全替代 (虚化/记忆/光晕/倒影) — KEY_LEARNINGS #37 落地
3. **T20-21 v2**: Stage 3 ScreenplayWriter prompt 提升 dialogue/thought 长度 24→35 字 (test19 Founder 反馈"过于简短不够通俗易懂")
4. **T20-27 P1 (升级)**: Stage 3/4 prompt 强制 text_overlay 必填 + Pipeline fallback (overlay 空时用 narration_segment) — test19 Shot 13 关键转折 overlay 缺失

**Backend (Opus 4.7 default, 1 任务)**:
1. T20-26 P0 配合 AI-ML: 改 regenerate 流程实现 replace 策略 (用 AI-ML 改的 Haiku prompt, 真重写不追加)

**Frontend (Opus 4.7 default, 3 P2 任务 1 session 串行)**:
1. **T20-24 P2**: useETA / progress bar 真接 backend `progress` 字段 (test19 Stage 2 早期卡 0% bug)
2. **T20-25 P2**: createUrl.ts 修 confirm-characters 后跳错 (test19 跳 /scenes 加载 20s → /generating)
3. **T20-11.v2 P2**: /outline 页面 polling 优化 (test19 累积 76 个 404 routine warn)

**PM 自己**:
- KEY_LEARNINGS #37/#38/#39 (本批已加)
- TEAM_CHAT 派活消息 + 收尾消息
- PM-progress 三件套 + TODAY_FOCUS + PROJECT_STATUS

**Tester 跳过**: Founder 5/19 22:30 决定 "最后测试还是让我手动测试最好" — 不 spawn Tester agent.

### 冲突避免

- AI-ML 4 项都 prompt 工程, 内部串行 (screenplay_prompts.py + storyboard_prompts.py + shot_prompt_rewriter Haiku prompt)
- Backend T20-26 跟 AI-ML 协调 (用 AI-ML 改的 Haiku prompt)
- Frontend 3 项不同文件 (useETA.ts + createUrl.ts + outline page)

### 时间线

- Day 1 (今天 22:30 起): PM 补文档 + 3 agent 并行 spawn
- Day 2: PM 审查 + 修复循环 (最多 2 轮)
- Day 3: Founder 手动测 + 决定内测启动

### 验收标准

- 7 项 RISK 全 closed
- KEY_LEARNINGS #37/#38/#39 加入 (PM 本批已加)
- Founder 手动跑新故事 (建议 test20 暗黑题材) 验证 Shot 15 同类场景不再 content_safety 失败 + 文字通俗易懂 + frontend progress 准确 + 路由不跳错


## [2026-05-21] DEC-047 T21-NEW-7 Stage 4.5 scene_image_preparation 引入 — 场景视觉确认作为用户旅程独立停留点 (Founder 决方案 D)

**Founder 5/21 18:25 决策** (test21 cyberpunk e2e 后 + 5 选项分析):

### 背景

test21 流程中 Founder 发现一个产品逻辑断裂:
- /scenes 页面在 R4-2 阶段做的是"情节确认" (用户调整 plot_points 走向)
- 但页面文案错位为"场景确认", placeholder "描述你想要的场景氛围" 让用户以为能改场景视觉
- 实际场景视觉 (interior/exterior anchor 参考图) 是 Stage 5 内部 5a.5 隐式生成, 用户从未审查就直接进 Shot 阶段
- 如果场景参考图不对 → Shot 全错, 用户中途无救生口

**用户原话** (Founder): "情节确认其实在大纲环节就有了 如果选B (改文案) 这样是不是重复了 能不能走和角色参考图预览一样的逻辑 等场景参考图生成后显示在前端scenes页面, 可以让用户查看、修改、重新生成、确认等等, 也有倒计时60s"

### 5 选项分析

| 选项 | 内容 | 决策 |
|------|------|------|
| A | 真"场景"功能 — Frontend + Backend + AI-ML 协作让用户改场景属性, Pipeline 用新场景重新生 image_prompt | ❌ 太重 |
| B | 只改文案 — Frontend 改 "场景确认" → "情节确认", placeholder 改 "调整情节走向". 0 功能改 | ❌ 与大纲环节重复, 真问题没解 |
| C | 双显示 — 上半显示场景属性 (只读) + 下半情节可编辑 | ❌ 复合界面体验混乱 |
| **D** | **场景参考图真预览 + 编辑 + 重生 + 60s 倒计时** (镜像 characters 页面对偶设计) | ✅ **Founder 选** |
| E | 直接跳到 Shot 后预览每个 Shot 视觉 (跳过场景层) | ❌ 用户已过两个停留点, Shot 失败救生口太晚 |

### 方案 D 真做改造

**Pipeline 架构**:
- 新增 **Stage 4.5 `scene_image_preparation`** (在 Stage 4 完成 + Stage 5 之前)
- 真生成所有 interior + exterior anchor 参考图 (复用 SceneReferenceManager 现有逻辑)
- 写 `chapter.scene_references_json` (新字段)
- 进入 **R4-3 wait loop** 等用户确认 (轮询 `project.scene_references_confirmed`, 超时 1800s)
- 与 R4-1 (characters) / R4-2 (scenes) 对称模式

**Stage 5 简化**:
- 场景参考图已在 Stage 4.5 完成 → Stage 5 image_preparation 只剩 fullbody + shots 调度
- ETA baseline 420s → 270s (5a 不再耗时生成场景)
- 5a.5 改 "复用 Stage 4.5 scene_ref_manager", 保留兜底路径

**3 新 endpoint** (镜像 characters 模式):
1. `GET /chapters/{n}/scene-references` — 返回场景参考图列表
2. `POST /chapters/{n}/scenes/{location_id}/regenerate-reference` — 重生单个场景参考图 (interior/exterior/both, 支持 user_edit)
3. `POST /chapters/{n}/confirm-scene-references` — R4-3 闸门, 解锁 Stage 5

**STATUS_API_CONTRACT v1.3 → v1.4 升级**:
- 新 ui_phase `scene_references_review` (R4-3 等待状态)
- 新字段 `scene_references_ready` + `scene_references_confirmed`
- 9 状态机 (原 8 状态机)
- hydrate_hints 新映射: scene_references_review → /scene-references endpoint

**DB schema**:
- `projects.scene_references_confirmed` (Boolean, default=False)
- `project_chapters.scene_references_json` (LONGTEXT, nullable=True)
- Alembic migration 006_add_scene_references_t21_new7
- Backfill: 已完成 Stage 5+ 老项目 scene_references_confirmed=True

**Frontend (Wave II)**:
- StageC.tsx 真改造 — 场景参考图卡片 (interior + exterior) + 编辑 + 重生 + 60s 倒计时
- 镜像 characters 页面对偶设计

### 关键设计原则

1. **"情节确认" ≠ "场景视觉确认"**: 两者真不同概念
   - 情节确认在大纲环节 + R4-2, 文字层面
   - 场景视觉确认在 R4-3, 视觉层面 (interior/exterior 真图)
   - 都给用户停留点, 让用户审美统一
2. **对偶设计美学**: characters 页面 (R4-1, 角色视觉确认) ↔ scene-references 页面 (R4-3, 场景视觉确认)
3. **DEC-014 / DEC-009 保留**: regenerate exterior 时用 interior 作参考图 (一致性逻辑保留)
4. **向后兼容**: 老 frontend 不消费新字段 → 仍走 legacy heuristic. R4-3 超时 1800s 自动继续, 防卡死.

### 验收

- 51 backend pytest PASS (T21-NEW-3/4/5/6/7 全覆盖)
- e2e Founder 跑 test22 (fairytale 美人鱼, aquatic schema fallback T21-NEW-2 实证 + Stage 4.5 真完整)
- 用户实测真见场景参考图卡片 + 60s 倒计时 + 编辑/重生真生效

### 关联

- KEY_LEARNINGS #46 (用户操作 = 真相): T21-NEW-5 文案"全身参考图"明确语义同源思想
- T21-NEW-3/4/5/6: Wave 5 配套 (restart UX, cache-buster, stage_message 细化, sub-stage UX)
- Ben 5/13 STATUS_API_CONTRACT 协议: v1.4 升级让 Ben 看新契约

---

## [2026-05-20] DEC-046 Wave 5 派活 — T20-28 v3 通用叙事原则重构 (15 原则 + 8 cluster + 85% KPI)

**Founder 5/20 09:00 决策** (看 storyrefs/story1 12 张参考漫画 + 跨题材深度讨论后):

### 背景
test19 Wave 4 T20-21 v2 (35 字 hard cap) Founder 仍反馈"不通俗易懂". 真根因不是字数, 是**风格 + 视角 + 留白哲学** (KEY_LEARNINGS #40).

### Wave 5 派活: AI-ML Opus 4.7 max thinking (T20-28 v3 通用叙事原则)

**原则架构**:
- **核心 6 原则** (所有 genre 通用): 视角 + 风格 + 强调 + 留白 + 互补 + 极简
- **补充 9 原则** (跨题材): 角色锚定/关系/跳转/结构/预期/多对话/副线/象征/文化
- **按 8 cluster 聚类映射** (LLM 由 style/题材自动选 TOP 5 关键原则):
  - C1 强情感代入 (恋爱/家庭/治愈)
  - C2 悬念反转 (悬疑/恐怖)
  - C3 奇幻冒险 (魔幻/异世界)
  - C4 童话绘本
  - C5 古风历史 (武侠/仙侠/历史)
  - C6 科幻
  - C7 喜剧吐槽
  - C8 现实题材 (都市/职场/医疗/法律)

### 验收 KPI: 整个故事 ≥ 85% 可读 (Founder 真人测)

Founder 跑 5-6 个跨题材测试样本 (PM 推荐), 主观验证:
- 关闭旁白栏, 只看 shot 图 + dialogue + thought + caption
- 整个故事 ≥ 85% 能理解 (主线 + 情感 + 关键 plot point)
- 留 15% 给想象/思考 (画面留白)
- **不一刀切**: 不同题材用不同关键原则 (LLM 自决定)

### 跨题材测试样本 (PM 推荐, Founder 选)

PM 推荐 6 样本覆盖 6 cluster (~120 字/样本, 短篇 18 shots):
1. **xuhuastorytest20_romance** (C1 恋爱): 程序员办公室暗恋
2. **xuhuastorytest20_horror** (C2 悬疑恐怖): 电梯镜中人
3. **xuhuastorytest20_wuxia** (C5 古风武侠): 剑山派师妹复仇
4. **xuhuastorytest20_fairytale** (C4 童话): 小熊与苹果女孩
5. **xuhuastorytest20_scifi** (C6 科幻): AI 客服与儿子
6. **xuhuastorytest20_urban** (C8 都市): 8 年没修的咖啡机

Founder 选 2-3 个亲自测 (不必全 6 个), 验证 85% KPI.

### 修复方向 (AI-ML)

1. 重写 `app/prompts/screenplay_prompts.py`:
   - 加 VIEWPOINT_SELECTION_RULES (style → 视角 cluster mapping)
   - 加 STYLE_LANGUAGE_MAPPING (style → 风格规则)
   - 加 NARRATIVE_RHYTHM_RULES (shot 位置 → 文字密度策略)
   - 加 EMPHASIS_RULES (emphasis_words 标准 — 关键名词/动词/数字/转折点)
2. 重写 `app/prompts/storyboard_prompts.py`:
   - 加 IMAGE_TEXT_COMPLEMENT_RULES (避免重复 image_prompt 已表)
   - 加 MINIMAL_DIALOGUE_RULES (1-3 字 OK)
   - 加 CHARACTER_ANCHORING_RULES (多角色防混淆)
   - 加 TIMELINE_JUMP_MARKER_RULES (时间跳转标记)
3. Backend `TextOverlayServiceV2` 配合:
   - 支持 emphasis_words 标红/加粗渲染 (新加 prompt 字段 → frontend overlay 显示)
4. 真跑 5-6 跨题材测试样本 mock (LLM 不调真 API), 验证:
   - 不同 cluster 真用不同 TOP 5 原则
   - LLM 自评 "可读性 %" 工具 (Stage 3 后自评)
   - 文字密度合理 (不一刀切)
5. 加新 KEY_LEARNINGS #40 已加 (PM 本批)

### Tester 跳过, Founder 手动测
不 spawn Tester. Wave 5 完成后通知 Founder 选 2-3 跨题材样本亲自测 85% KPI.

### 预计 1-2 天
P0 阻塞内测启动, 高强度重写 prompt + cluster 映射设计 + 跨题材验证.


## [2026-05-21 22:55] DEC-048 T22-NEW-3 Layer 1 Identity Anchor Framework v1.0 长期架构治本 — 不走 hotfix patch (Founder 决策)

### 背景: test22 美人鱼 e2e 暴露 P0 通用性灾难

- Shot 9-14 珊瑚 hair_color 完全不一致 (schema sea-green / portrait 粉红 / shot prompt dark)
- 20/20 shot 真 0 个用对 sea-green hair (100% miss)
- 深挖 storyboard_prompts.py L904 根因: "建议性 hint" (Format examples ... replace [hair_color] with the actual value) 被 LLM 完全自由发挥
- 不止 hair_color, 不止珊瑚, 不止美人鱼 — 跨 19 character_types × 80+ styles × 任意题材, character schema 完全不传递到 image prompt

### 通用性扩展 (LLM-generated visual narrative 根本性问题)

LLM 创意能力 vs 严格一致性张力 — "建议性 hint" 永远被 LLM 创意绕过. 同问题出现在所有 LLM-generated visual content 工具 (Midjourney/Sora/Runway).

不止 character, 同样问题在:
| 应该固定 Anchor | LLM 自由发挥 | 同类问题 |
|---|---|---|
| character physical (hair/face/skin/marks) | "dark/blonde" generic | ✅ 已发现 |
| character clothing core | 不一定固定 | 🚨 待验 |
| location identity (magic forest 真什么光/季节?) | 自由 | 🚨 同样 |
| props signature (shell harmonica 真什么样?) | 自由 | 🚨 同样 |
| style mandatory (children_book 必须水彩) | shot 11/13 漂 3D Pixar | ✅ 已发现 |
| time_of_day / lighting continuity | 自由 | 🚨 可能漂 |

### Founder 决策: 不走 Layer 2 hotfix patch, 选 Layer 1 长期架构治本

**Founder 理由 (5/21 22:50-22:55 原话)**:
- "我还是偏向之前你说的'选项: C 长期架构'这种根治的方式"
- "通用故事角度去研究、深挖、思考和分析，而不是只修这一个或者这一类故事"
- 接受内测延后 1-2 day 等真根治

### Layer 1 实施计划 (Wave 6 主线, 1-2 day)

#### 1. Identity Anchor Framework v1.0 接入

`docs/CHARACTER_IDENTITY_FRAMEWORK.md` v1.0 早写好 (DECISIONS L1010 提到), 未实施. 分离:

- **Identity Anchors (锁定不变)**: hair_color / face_shape / skin_tone / distinctive_marks / clothing_core / style_signature / location_signature / props_signature / time_continuity
- **Narrative Variables (LLM 创意层)**: pose / expression / camera_angle / camera_distance / emotion / interaction

覆盖全 19 character_types + 80+ styles 统一框架.

#### 2. Backend post-process 强注入 (架构层, 绕过 LLM 决策)

Stage 4 LLM 生 image_prompt 后, 自动 prepend:

```
[CHARACTER IDENTITY ANCHORS — MUST APPEAR AS DESCRIBED]
char_001 Coral: deep sea-green long flowing hair (past waist, pearl pins), iridescent fair skin, vivid ocean blue almond eyes
char_002 A-Hai: ash-blonde short hair, sun-tanned skin
char_003 Sea-Witch: silver-white spiraling long hair, lavender-pale skin

[STYLE MANDATORY]
children_book watercolor: soft pastel, hand-drawn texture, NO 3D Pixar, NO realistic rendering

[LOCATION ANCHORS]
loc_001 underwater_palace: bioluminescent coral, soft blue-green ambient light

[SCENE]
{LLM 生成的 image_prompt — 允许创意但 anchor 不可改}
```

覆盖 character / style / location / props / time_of_day 5 维度 anchor.

#### 3. PromptValidator 新增 (Validation 层升级)

生图前 grep prompt 包含 character schema 关键字 (hair_color 字面值 / skin_tone / 等), 不通过 auto-correct (re-inject anchor).

#### 4. 跨题材 baseline regression (CI 持续防退化)

19 character_types × 随机 5 styles baseline test, grep 100% 含 character schema 关键字.

#### 5. STATUS_API_CONTRACT v1.5 升级 (如需要)

#### 6. 派工

- AI-ML Opus 4.7 xhigh — Identity Anchor Framework 设计
- Backend Opus 4.7 xhigh — post-process 强注入 + PromptValidator
- Tester Sonnet 4.6 xhigh — 跨题材 baseline regression

### 验收 KPI

- T22-NEW-3 shot prompt 100% 含 character schema 关键字 (grep 验证)
- 跨题材 regression 19 type × 5 style PASS
- e2e 重跑 test22 + scifi/horror/wuxia 多题材, 角色 signature 一致

### 不影响内测启动? 影响 — Founder 接受延后等真根治

**关联**: DEC-046 v3 narrative readability + DEC-047 Stage 4.5 + KEY_LEARNINGS #50/#51

**影响范围**: AI-ML (Stage 4 prompts 重构) + Backend (image_generator post-process 注入 + PromptValidator) + Tester (跨题材 baseline) + 共 1-2 day 工时

---

## [2026-05-22 19:30] DEC-049 Layer 1 portrait path wire + BW_STYLES 扩展位 (Wave 9, TASK-T22-NEW-10)

### 背景

680 行 9 维度 audit (`T22_NEW_10_PORTRAIT_LAYER1_AUDIT_2026-05-22.md`) 发现: Layer 1 Identity Anchor 已 wire 到 shot path (Backend Wave 7)，但 portrait path (`_build_portrait_prompt`) 从未 wire，portrait 颜色靠 StyleEnforcer mandatory 关键词，无 anchor 约束 → portrait 颜色不稳定 → 参考图本身颜色错误 → shot 有 anchor 也无法纠正。

### 决策内容

**DEC-049-1: portrait path 必须 wire Layer 1 anchor**
- 实施位置: `reference_image_manager._build_portrait_prompt()` enforced_prompt 赋值后
- 调用: `inject_identity_anchors(characters_in_scene=[character], location=None, style_preset=..., props=None, time_continuity=None)`
- 防御性: try/except 兜底，Layer 1 失败不阻塞 portrait 生成
- 状态: ✅ Wave 9 AI-ML 已实施 (2026-05-22 19:30)

**DEC-049-2: BW_STYLES 扩展位 + is_bw_style() helper**
- `StyleEnforcer.BW_STYLES: set = set()` — 当前为空，未来加真黑白风格名进 set
- `StyleEnforcer.is_bw_style(style_name) -> bool` — `_bw` 后缀 OR `BW_STYLES` 成员触发 skip
- 理由: 黑白风格 (如 manga_bw) 无彩色 anchor 可注入，skip 避免 anchor block 内容为空或误导
- 状态: ✅ Wave 9 AI-ML 已实施

**DEC-049-3: fullbody path 同 root cause — ✅ 已实施 (Wave 9.1, 2026-05-22 20:30)**
- `_build_reference_prompt()` (`reference_image_manager.py`) 已 wire Layer 1，镜像 W9-1 portrait pattern
- Layer 1 三路统一: shot path (W7) + portrait path (W9) + fullbody path (W9.1) 全部 wire
- 验证: `test_layer1_fullbody_injection.py` 6/6 PASS + 252/252 总量 0 退化

### 验证

- 4 彩色风格 (manga/children_book/cyberpunk/ink) portrait prompt 含 IDENTITY_ANCHOR_MARKER ✅
- _bw 后缀风格 portrait prompt 不含 IDENTITY_ANCHOR_MARKER ✅
- BW_STYLES 显式注册成员同样 skip ✅
- is_bw_style() helper 防御 non-string 返回 False ✅
- Wave 7+8+9 全量 500/500 PASS, 0 退化 ✅

### 关联

DEC-048 (Layer 1 Framework) + TASK-T22-NEW-10 + KEY_LEARNINGS #57 (跨路径 wire 一致性)
