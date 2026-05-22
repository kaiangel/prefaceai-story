# Test15 深度地毯式审查报告

**审查时间**: 2026-05-13 20:10（PM 完成）
**审查范围**: test15 e2e 全程（19:04:31 项目创建 → 19:59:33 Shot 22 重生成功，55 min）
**Founder 输入**: 故事 idea "ICU 9 床植物人 + 8 床老患者跨走廊" / illustration + 悬疑 / 短篇 ≥18 shots
**最终产物**: 23 完整 shots + BGM mp3 + 完整故事流水线全产物
**最终状态**: ✅ Pipeline completed + 23/23 张图（含 Shot 22 用户重生）+ BGM 完美

---

## TL;DR — 一句话结论

Test15 e2e 在**业务层完整跑通**，但暴露了 **15 个 RISK**（13 真 bug + 2 误判撤销），其中 **7 个 P0** 集中在**前后端契约断裂**这一根因模式。Ben 建议的"前后端纠验机制"**精准命中**了这批问题的核心 — 应作为 Wave 8/9 的架构级修复方向。

---

## Ben 建议价值评估（5/13 15:37-15:42 聊天）

### Ben 原话提炼
1. "是不是把前端放在后端的前面去 pipeline" — 提议改流程顺序
2. "可以用一种纠验的机制" — 后端开发改过功能，需要这个告知出来询问需要对应修改前端吗

### PM 评估：极高价值 ⭐⭐⭐⭐⭐

**精准命中根因**: test15 暴露的 15 个 RISK 中，**7 个属于"前后端契约断裂"模式**：

| RISK | 前后端断裂表现 |
|---|---|
| T15-2 | 后端 R4-2 等待 scenes_confirmed → 前端 POST_CHAR_STAGES 包含 screenplay/storyboard 把用户踢走 |
| T15-3 | 后端 R4-2 阶段 storyboard 还没生成 → 前端 /scenes hydrate /storyboard endpoint = 永远 404 |
| T15-4 | 后端 Stage 4 完成立即进入 image_preparation → 前端无 storyboard review window |
| T15-7 | 后端 ETA 阶段切换跳变 → 前端 UX-7 guard 不允许上调 = ETA 不准 |
| T15-8 | 后端 scenes_confirmed=True → 前端 generationSubPhase 不监听 backend status |
| T15-12 | 后端 regenerate 成功 → 前端 failed_shot_count 仍 stale |
| T15-13 | 后端 regenerate 成功 → 5_image_results.json 不回写 + ApiCost project_id=None |

**Ben 提议价值**:
- 不是 7 个零散 bug，是**同一根因的 7 种症状**
- 修单个 bug 治标，建"纠验机制"治本
- 类似企业研发中的"API 契约测试"或"Schema as Source of Truth"

### Ben 建议落地方案（PM 推荐）

#### 方案 A: 后端契约改造 → frontend 自动派生（推荐 ⭐⭐⭐⭐⭐）

**核心原则**: backend status API 成为前端 state 的 single source of truth，frontend state 字段全派生。

具体落地：
```
1. Backend status API 扩展（pipeline_orchestrator + chapters.py）
   - 现有: status / stage / progress / message / estimated_remaining_seconds / failed_shot_count / partial_failure
   - 新增: characters_confirmed / scenes_confirmed / storyboard_ready /
           ui_phase ("input" | "outline_review" | "char_review" | "scene_review" | "shot_generating" | "completed")
   - 新增: hydrate_hints (告诉前端这阶段应该 hydrate 哪个 endpoint)
     - 例: scenes_ready 阶段返回 {hydrate_endpoint: "/screenplay", display_field: "scenes_11"}
     - 例: storyboard 阶段返回 {hydrate_endpoint: "/storyboard", display_field: "shots_23"}

2. Frontend state 改为派生 (createUrl.ts + StageC.tsx)
   - generationSubPhase 从 status.ui_phase 派生（不再 user action 触发）
   - hydrate URL 从 status.hydrate_hints 拿（不再 hardcode）
   - ETA 阶段切换时重置（监听 status.stage 变化）
   - failed_shot_count 直接从 status 读（不本地缓存）

3. 契约 schema 文档化
   - 写 .team-brain/contracts/STATUS_API_CONTRACT.md
   - 包含每个 stage 期望的字段 + frontend 应该做的渲染
   - backend 改 status response → 必须更新契约文档 → frontend 自动同步
```

#### 方案 B: Pre-commit hook 提醒（轻量）

Ben 提议的"后端改过功能告知"可落地为：
- backend agent commit 修改 `app/api/projects.py` 或 `pipeline_orchestrator.py` 时
- pre-commit hook 自动 prompt："此改动涉及 frontend 契约吗？需要同步通知 frontend agent？"
- 强制 commit message 标注 `[frontend-impact: yes/no]`

#### 方案 C: 双团队 sync 会议（Founder + Ben 协调）

每周一次 PM + backend_Ben 同步：
- Backend 这周改了哪些 endpoint
- Frontend agent 需要做哪些跟进
- 用 `.team-brain/handoffs/PENDING.md` 跟踪

---

## Test15 完整时序回放（60 min）

| 时间 | 阶段 | 事件 | 备注 |
|---|---|---|---|
| 0:00 | 启动 | Founder 输入 idea + style=illustration + mood=悬疑 → POST /create-project | project id=32, uuid=60e6fbc6 |
| 0:01 | Stage 1 | StoryOutlineGenerator (Sonnet 4.6) 启动 | |
| 1:39 | Stage 1 ✅ | 大纲生成完成 (96s) | 标题：第二十一个夜晚 |
| 9:04 | Stage B | Founder 点确认大纲 → POST /confirm-outline | T15-11: JSON markdown 包裹解析失败 fallback OK |
| 9:11 | Pipeline 启动 | Job id=17 | has_confirmed_outline=是 |
| 9:38 | Stage 2 | CharacterDesigner (Sonnet 4.6) 启动 | 3 角色 |
| 10:50 | Stage 2 ✅ | 角色设计完成 (72s) | 林晓月/赵老头/陈国栋 |
| 10:55 | UX-1 portraits | 3 portrait 串行生成（Seedream 各 ~35s）| |
| 12:49 | character_ready | Pipeline 等用户确认（R4-1）| 🐛 没生成 fullbody（设计 = 优化 UX）|
| 15:13 | Founder 调发色 | "亚麻青色"（POST /chapters/1/adjust-character） | R7-3 + B57 重生 portrait + fullbody |
| 17:10 | R4-1 ✅ | Founder 点确认角色（等 142s）| B52-fix v3: characters reloaded from DB ✅ |
| 17:14 | Stage 3 | ScreenplayWriter (Sonnet 4.6) 启动 | 分场剧本 |
| 21:44 | Stage 3 ✅ | 剧本完成 (226s, 11 scenes) | 分 2 批生成 |
| 21:49 | **🐛 R4-2 等待** | Pipeline 等用户确认 scenes（但 frontend 显示 storyboard 数据，永远 404）| **RISK-T15-3 暴露** |
| 24:30 | **🐛 RISK-T15-2** | Frontend 把用户从 /scenes 踢回 /generating | **PM 派 Frontend agent 紧急修** |
| 25:00 | Frontend 修复 | Frontend agent 修 createUrl.ts POST_CHAR_STAGES + StageC.tsx text-gen 按钮（RISK-T15-1 + T15-2）| hot reload 生效 |
| 28:55 | PM 强制 confirm | curl POST /confirm-scenes（unblock）| 触发 RISK-T15-8（subPhase 不切 shot-gen）|
| 28:59 | R4-2 ✅ | scenes_confirmed=True | 但 frontend state 仍是 text-gen |
| 29:03 | Stage 4 | StoryboardDirector (Sonnet 4.6) 启动 | 11 scenes 并行 |
| 32:47 | Stage 4 ✅ | 分镜完成 (195s, **23 shots**) | **DEC-028 不截断 ✅**（≥18 上限不强制）|
| 32:50 | image_preparation | 角色 fullbody (3 × ~35s) + scene refs (4 × ~35s) | RISK-T15-4 + T15-5 + T15-6 |
| 37:55 | Stage 5 | 23 shots 并发生成（Semaphore=3）| 平均 ~50s/shot |
| 48:35 | **🐛 Shot 21 T17 失败** | 角色数量不匹配（预期 1, 实际 3）| T17 主动重试 |
| 49:31 | **🐛 Shot 22 IncompleteRead** | 4 次 retry 全失败，最终 ❌ | **RISK-T15-9 误判已修正**：finalize 阶段会汇总 |
| 49:51 | Shot 21 重试 | 仍失败 (预期 1, 实际 4) — 用当前结果 | T17 重试上限 |
| 50:20 | BGM 启动 | Mureka 5 候选 | T14-11 框架验证 |
| 51:30 | BGM ✅ | mp3 写入 (165s 时长, $0.10 estimated) | **piano + drone + no guqin** ✅ |
| 51:40 | Pipeline ✅ | status=completed, partial_failure=True | failed_shot_count=1 (Shot 22) |
| 52:00 | Founder 跳 /preview | Frontend 自动跳 + 显示 "22/23 + 1 张未生成" | partial_failure UX 完美 |
| 54:30 | Shot 22 重生 | 用户点重生 button → Seedream refs=4 | |
| 55:17 | Shot 22 ✅ | 50.17s, sanitize=0, 文件覆盖保存 | 但 failed_shot_count 仍 1 → **RISK-T15-12** |

---

## RISK-T15-X 完整审查 (15 个 — 13 真 bug + 2 撤销/修正)

### 🔴 P0 已修 (2 个)

#### ✅ RISK-T15-1 — /generating text-gen 阶段错显"后台生成"按钮
- **根因**: `StageC.tsx:943` 渲染条件含 text-gen 分支
- **修复**: Frontend agent 5/13 19:30 删 text-gen + 5 行 subtitle 文案
- **验证**: ✅ hot reload 生效

#### ✅ RISK-T15-2 — scenes checkpoint 被 createUrl reconcile 完全绕过 [P0 CRITICAL]
- **根因**: `createUrl.ts:118-125` POST_CHAR_STAGES 包含 screenplay + storyboard
- **修复**: Frontend agent 5/13 19:30 移除两项
- **验证 (PM 5/13 20:08 grep)**: ✅
```ts
const POST_CHAR_STAGES = new Set([
  "image_preparation",
  "image_generation",
  "bgm",
  "completed",
]);
```
- **e2e 验证**: ✅ Founder 确认角色后自动跳 /scenes 且不被踢

---

### 🔴 P0 待修 (5 个)

#### RISK-T15-3 — scenes_ready 阶段 frontend hydrate /storyboard 永远 404 [P0 CRITICAL]
- **根因**: Backend Pipeline R4-2 在 Stage 3 后立即等待用户确认（**不跑 Stage 4**），但 frontend `/scenes` 页面 hydrate `/storyboard` endpoint（Stage 4 后才有数据）→ 永远 404
- **业务影响**: 用户在 /scenes 看 "场景还在生成中" 转圈 8+ min 直到 R4-2 timeout
- **临时 unblock**: PM 5/13 19:33 curl POST /confirm-scenes 强制解
- **永久修复方向**:
  - Backend: `GET /story` 在 scenes_ready 阶段返回 `3_screenplay.json` 的 11 scenes
  - 或新加 `GET /screenplay` endpoint
  - Frontend: /scenes 页面 hydrate 改用上者
- **Ben 建议匹配度**: ⭐⭐⭐⭐⭐ — 经典前后端契约断裂
- **派发**: Backend + Frontend Sonnet xhigh ~30 min

#### RISK-T15-4 — 用户没有 storyboard review window [P0 设计缺失]
- **根因**: Stage 4 完成后 Pipeline 立即进入 image_preparation，frontend Watcher 也立即把用户从 /scenes 跳到 /generating
- **业务影响**: 用户没机会 review 23 shots（构图/镜头/角色配置）→ 无法删除/重生不喜欢的镜头规划
- **修复方向**:
  - Backend: 加 R4-3 / B59: Stage 4 完成后等待 user POST /confirm-storyboard
  - 或者：合并 R4-2 + R4-3 为单个"先 screenplay 后 storyboard"两 sub-state 检查点
- **派发**: Backend + Frontend Opus xhigh ~1h（设计 + 实现）

#### RISK-T15-8 — generationSubPhase 不监听 backend scenes_confirmed [P0 UX]
- **根因**: frontend `generationSubPhase` 只通过 user click handlers 切换。PM 直接 POST /confirm-scenes 时 subPhase 不变 → 后台按钮不显示
- **业务影响**: 用户错过"后台生成"按钮 + 任何 PM unblock / hot reload / state 丢失场景都会触发
- **修复方向**: Frontend 加 useEffect 监听 backend status.scenes_confirmed 自动切 subPhase
- **Ben 建议匹配度**: ⭐⭐⭐⭐⭐ — frontend state 应从 backend 派生
- **派发**: Frontend Sonnet xhigh ~20 min

#### RISK-T15-12 — Shot regenerate 成功后 failed_shot_count 不递减 [P0]
- **根因**: `app/api/chapters.py` shot regenerate endpoint 成功后没更新 chapter_generation_jobs.failed_shot_count + 没重新评估 partial_failure
- **业务影响**: Frontend /preview 一直显示 "22/23 张生成成功，1 张未生成"，即使实际 23/23 ✅
- **验证 (PM 19:59 实证)**: shot_22.png 已写入 + DB 仍显示 failed=1
- **修复方向**: regenerate endpoint 成功 path：`job.failed_shot_count -= 1; job.partial_failure = (job.failed_shot_count > 0)` + commit DB
- **派发**: Backend Sonnet xhigh ~15 min

#### 🆕 RISK-T15-13 — Shot regenerate 不回写 5_image_results.json + ApiCost project_id=None [P0]
- **新发现 (PM 5/13 20:08 audit)**: 
  - Shot 22 重生后 `5_image_results.json` 中 Shot 22 仍 `success=False, error="IncompleteRead..."`
  - regenerate 路径 ApiCostLogger 记 `cost=$0.0300, stage=Stage 5 Shot 22, project_id=None`（应是 32）
- **业务影响**: 
  - 5_image_results.json 是 frontend 读 shot 状态的来源之一 → 长期数据 stale
  - 成本归属失败 → 项目 32 实际花费 $0.72 但 ApiCost 表只算 $0.69
- **修复方向**: regenerate endpoint 路径
  - 读 5_image_results.json → 找 shot_id=N → 改 success=True, error=None, image_path=新文件
  - ApiCostLogger 调用传 project_id=project.id
- **派发**: Backend Sonnet xhigh ~15 min（与 T15-12 同 PR）

---

### 🟡 P1 待修 (3 个)

#### RISK-T15-7 — Frontend ETA 计算被 UX-7 guard 过激压缩
- **根因**: `StageC.tsx:257-262` UX-7 monotonicity guard 强制 ETA 永远不上调
- **业务影响**: backend 真实 ETA 350s，frontend 显示 "1 分钟"，用户体感被骗
- **修复方向**: 监听 backendStage 字段，stage 切换时重置 lastEtaSecondsRef
- **派发**: Frontend Sonnet xhigh ~15 min

#### RISK-T15-10 — Shot 21 因 T17 ShotValidator 不匹配被重生（修正认知）
- **修正认知 (PM 5/13 20:08 audit)**: 不是 race condition，是 **T17 ShotValidator 主动重试**
  - 第一次：expect 1 char, Seedream actual 3 chars → T17 retry 触发
  - 第二次：actual 4 chars → 达最大重试 → 用当前结果
- **真根因**: Shot 21 narration "走廊里短暂出现压低的声音与移动的脚步" 被 Seedream 理解为多人
- **修复方向**: 
  - prompt_engineering: Shot 21 image_prompt 强调 "ONLY Lin Xiaoyue, footsteps are off-screen sound"
  - 或 T17 retry 增加 prompt rewrite 机制（不只重试同 prompt）
- **派发**: AI-ML Sonnet xhigh ~30 min（prompt 调整）

#### RISK-T15-11 — Client uncaught "Unknown error" 无 stack
- **来源 (PM 5/13 20:08 audit)**: `client.log 11:56:25 uncaught | generating | "Unknown error"` (BGM 阶段)
- **根因猜测**: Frontend 某个 background promise reject 没 catch / Notification API permission denied / Watcher fetch error
- **业务影响**: P2 — 不影响功能，但 swallow 错误本身是 bug
- **修复方向**: 加 window.onerror 全局 handler + 加 stack trace
- **派发**: Frontend Sonnet xhigh ~20 min

---

### 🟡 P2 待修 (2 个)

#### RISK-T15-5 — image_preparation 重新生成 portrait（应该 skip）
- **根因**: `pipeline_orchestrator.py:966` `generate_character_multi_refs(skip_portrait=False)` 没传 skip_portrait=True
- **影响**: 浪费 ~$0.09 (3 张 portrait × $0.03) + ~1.5 min 时间
- **派发**: Wave 8 RISK-T14-10 参考图并行化时一并修

#### RISK-T15-9 — Shot retry mid-stage failed_shot_count 不实时（已修正非 critical）
- **修正认知 (PM 5/13 19:57)**: 不是永远断裂，是 Pipeline finalize 阶段汇总。Stage 5 中途 failed=0 是 UX 问题
- **业务影响**: 用户中途看 progress 时不知道部分失败
- **派发**: Backend Sonnet xhigh ~20 min（增加 mid-stage 实时累加）

---

### 🆕 P2 新发现 (1 个) + 撤销 (1 个)

#### 🆕 RISK-T15-14 — storyboard.shots[].characters_in_scene 字段为空
- **新发现 (PM 5/13 20:08 audit)**: 4_storyboard.json 中 Shot 21 + Shot 22 的 `characters_in_scene=[]` + `shot_type=""`
- **但**: 实际 image_prompt 文本含 "EXACTLY 1 character" — T17 读 prompt 文本工作正常
- **影响**: 下游消费方（统计、frontend 显示）如果用 shot.characters_in_scene 字段 → 空数据 = bad
- **检查清单**: grep 全 frontend 看哪些组件用 storyboard.shots[].characters_in_scene
- **派发**: Backend Sonnet xhigh ~10 min（Stage 4 输出 schema 修复）

#### ❌ RISK-T15-6 撤销 — scene_refs 只 4 张是设计正确
- **撤销原因 (PM 5/13 20:08 audit)**: 4 个 location 都是 indoor（ICU 病房 / 走廊 / 护士站 / 储物间角落），没有 outdoor 需求
- **设计正确**: SceneReferenceManager 只生成需要的 anchor 类型
- **撤销**: 不是 bug，不需要派发

---

## 5 维度根因分类

| 维度 | RISK 数 | 占比 |
|---|---|---|
| **前后端契约断裂** | 7 (T15-2, 3, 4, 7, 8, 12, 13) | **47%** ⭐ Ben 建议核心 |
| 单端代码 bug | 3 (T15-1, 11, 14) | 20% |
| Prompt/模型问题 | 1 (T15-10) | 7% |
| 设计 / 中途状态 UX | 2 (T15-5, 9) | 13% |
| 误判修正/撤销 | 2 (T15-6, T15-9 部分) | 13% |

**结论**: Ben 提议的"前后端纠验机制"如果落地，能预防/早期发现 **47% 的本次发现的 bug**。

---

## 验证通过项 (✅ 不需要修)

### 已 Wave 7 修过且 test15 实证通过
| Wave 7 RISK | test15 验证 | 实证 |
|---|---|---|
| T14-4 动态 ETA | ✅ | ETA 按 actual_shot_count 算 (1439s 启动 → 350s image_gen) |
| T14-5-v2 in-stage progress update | ✅ | screenplay 11%→22%→35% 涨 + msg 累积 "Scene 1→11/11" |
| T14-6 handleConfirmCharacters 直跳 /scenes | ✅ | 角色确认后 router.replace 正确 |
| T14-7 GET /story endpoint | ✅ | hydrate 链路工作 |
| T14-8 watcher 4 stages auto-jump | ✅ | character_ready → /characters 自动跳 |
| T14-9 不截断 26+ shots | ✅✅✅ | **23 shots 全跑（旧 18 上限会截 5 张）** |
| T14-11 BGM 通用性 | ✅✅✅ | piano + cello + drone, 无 guqin/dizi/erhu, 完美 western_realistic |
| T14-12 后台按钮 message stream | ✅ | "角色参考图 1/3 → 2/3 → 3/3" 累积 |
| T14-13 inconsistency_warnings banner | ⚠️ | LLM JSON 解析失败 fallback OK，未真触发 banner（次要 P2）|
| B52-fix v3 | ✅ | "characters reloaded from DB after R4-1 confirm" |
| B57 同步重生 fullbody | ✅ | 林晓月调发色后 portrait+fullbody 联动重生 |
| R7-3 portrait 重生 | ✅ | "char_001 肖像已重生成" |
| DEC-028 不截断 | ✅✅✅ | "[StoryboardDirector] DEC-028: 总 shots=23（不截断，全量进 pipeline）" |
| partial_failure UX | ✅ | frontend 正确显示 "22/23 张生成成功，1 张未生成" |
| 单 shot 重生 | ✅ | shot_22.png 重生 50.17s 成功（refs=4，加了 1 个 ref）|

### BGM T14-11 prompt 完整验证

`bgm_prompt_chapter0.txt` 内容（截选）：
```
# BGM Haiku Prompt — chapter 0 — meta_version: mixed
# User selected mood: 悬疑
# Story title: 第二十一个夜晚

Minor key, sparse and held. Like listening through walls at 3 AM — 
a single muffled pulse that shouldn't exist but won't stop. 
Ambient drone, low and patient... One dissonant piano note, dampened...
Sparse percussion — irregular, breath-driven, one strike then nothing for bars.
```

✅ **piano + drone + minor key + sparse**（western_realistic 分支正确）
✅ **没有任何 guqin / dizi / erhu / 中国传统乐器**
✅ 包含 user_selected_mood "悬疑" + story quotes 引用

---

## 修复优先级矩阵

### 立即派 (next test 前必须，~2h)
| RISK | Agent | 用时 | PR |
|---|---|---|---|
| T15-3 + T15-4 | Backend + Frontend Opus xhigh | 1h | PR-A: scenes/storyboard checkpoint 双修 |
| T15-12 + T15-13 | Backend Sonnet xhigh | 30 min | PR-B: regenerate 回写双修 |
| T15-8 | Frontend Sonnet xhigh | 20 min | PR-C: subPhase backend-authoritative |

### 短期 (本周内)
| RISK | Agent | 用时 |
|---|---|---|
| T15-7 | Frontend Sonnet xhigh | 15 min |
| T15-11 | Frontend Sonnet xhigh | 20 min |
| T15-14 | Backend Sonnet xhigh | 10 min |

### 中期 (Wave 8)
| RISK | Agent | 用时 |
|---|---|---|
| T15-5 + T14-10 | Backend Sonnet xhigh | 45 min |
| T15-9 | Backend Sonnet xhigh | 20 min |
| T15-10 prompt | AI-ML Sonnet xhigh | 30 min |

### 架构级 (Wave 9+ — Ben 建议落地)
| 项 | Agent | 用时 |
|---|---|---|
| Backend status API 扩展（ui_phase + hydrate_hints）| Backend Opus xhigh | 3h |
| Frontend state 派生改造 | Frontend Opus xhigh | 3h |
| STATUS_API_CONTRACT.md 文档 | PM | 1h |
| Pre-commit hook (frontend-impact label) | DevOps | 30 min |

---

## KEY_LEARNINGS 总结（写入 .team-brain/knowledge/KEY_LEARNINGS.md）

### 1. 前后端契约必须从设计阶段对齐
**教训**: test15 47% 的 bug 都是前后端契约断裂。Wave 7 修了 T14-1~T14-13，但都没触及"backend Pipeline 设计意图 → frontend state machine"的对接断层。

**应用**: 任何新 backend stage / R4-X checkpoint / endpoint 设计时，必须同步设计 frontend 对应的 hydrate 路径、URL state、subPhase 切换信号。Wave 9 架构级修复必做。

### 2. PM unblock 操作绕过 frontend 揭示 frontend state 设计缺陷
**教训**: PM 直接 curl POST /confirm-scenes 解 R4-2，但 frontend generationSubPhase 没切 → 后台按钮不出。这暴露 frontend state 不是从 backend status 派生（应是）。

**应用**: 任何 frontend state 字段，第一原则是"能否从 backend authoritative state 派生"。如果能，必须派生不缓存。

### 3. ETA monotonicity guard 不应阻止合法跳变
**教训**: UX-7 设计时假设 ETA 单调下降，没考虑 Pipeline 多阶段切换时 backend ETA 会按新 stage duration 上调。

**应用**: UX 平滑性 guard 必须有"信号源切换"逃生口。监听 stage 字段变化时重置 ref。

### 4. shot regenerate 是事务，必须更新所有相关持久层
**教训**: regenerate 写了 disk shot_22.png 但漏了：
- chapter_generation_jobs.failed_shot_count
- 5_image_results.json
- ApiCostLogger.project_id

**应用**: regenerate / adjust / 任何"修改既有数据"endpoint 必须列清单：哪些表/文件/日志会受影响。代码 review 强制检查清单。

### 5. T17 ShotValidator 重试不应静默使用最后结果
**教训**: Shot 21 T17 两次 retry 都失败（角色数量不匹配），但最终"使用当前结果"且无任何用户可见警告。

**应用**: T17 用尽 retry 后应：
- 在 5_image_results.json 标 `validation_failed=True`
- 在 status response 增加 `validation_warnings` 字段
- frontend /preview 显示 ⚠️ "Shot 21 角色数量与预期不符，建议手动重生或编辑 prompt"

### 6. Ben 的"前后端纠验机制"建议价值 ⭐⭐⭐⭐⭐
**教训**: 不能逐个修 bug，要从契约设计层面预防一类 bug。

**应用**: Wave 9 架构级改造采纳方案 A（backend status authoritative + frontend 派生）+ 方案 B（pre-commit hook frontend-impact label）+ 方案 C（PM + backend_Ben 周同步）。

---

## 后续 Action Plan

### Founder 决策点
1. **是否采纳 Ben 建议方案 A** — 架构级 backend status authoritative 改造（Wave 9 ~6h）？
2. **修复批次划分** — 立即派 PR-A/B/C（~2h），还是先派 PR-B/C 解 P0 再说？
3. **再测 test16** — 修完后立即跑 test16 验证 + 验收 /preview 剩余功能（BGM 试听 / 删 shot / 编辑文字 / 下载）？

### PM 已做
- ✅ 12 个 RISK 全记 PENDING.md
- ✅ 本审查报告 `.team-brain/analysis/TEST15_DEEP_AUDIT_2026-05-13.md`
- ✅ Ben 建议价值评估 + 落地方案 3 选项
- ✅ 5 维度根因分类
- ✅ 修复优先级矩阵

### PM 待做（Founder 批准后）
- 写 KEY_LEARNINGS.md 6 条新经验
- 写 TEAM_CHAT.md test15 收尾消息
- 更新 PENDING.md（标 T15-1/T15-2 ✅，加 T15-13/T15-14 详情，撤销 T15-6）
- spawn agent 派发 PR-A/B/C

---

**审查完成时间**: 2026-05-13 20:10
**审查方式**: PM 5 维度地毯式 — 代码层 + 流程层 + 设计意图 + 历史回溯 + 延伸推断
**报告产出**: 此 .md (5 维度, 15 RISK, Ben 建议价值评估 + 落地方案)
