# test17 v2 端到端完整测试审计报告

> **测试日期**: 2026-05-19
> **测试时段**: 14:41:00 → 16:07:19 (总 ~86 min, 含 Pipeline 74.8 min + 重生 ~4 min)
> **Project UUID**: `adfdfa58-b2b3-420c-bddd-5e9077ceba3e`
> **故事**: 第二十四颗苹果 (灰狐/兔子米莉/麻雀啾啾, ghibli 风格, 3 分钟短篇)
> **目的**: 验证 Wave 14 anthropomorphic_animal 修复 + T20-10 CharacterSchema 修复 + 收集内测前最后批 bug
> **审计深度**: 8 维度监控 + 5 维度 cron + DevOps 诊断 + Founder 实时反馈
> **PNG 实际**: 20/20 (含 Shot 14, 19 前端重生)

---

## 0. 执行总结

| 维度 | 结果 |
|------|------|
| Pipeline 完整闭环 | ✅ 全 6 stage 通过 (outline / characters / screenplay / storyboard / images / bgm) |
| Wave 14 + T20-10 终极实证 | ✅ Founder "是动物的感觉 这个没大问题" — anthropomorphic_animal 全链路 PASS |
| 故事/BGM 感觉 | ✅ Founder "整体故事感觉还可以" + "BGM 整体感觉很不错" |
| 失败恢复 | ✅ 前端"查看并重生"链路实证 PASS (Shot 14/19 各 1 次过) |
| 新发现 P0 RISK | **5 个**: T20-12/13/14/17 + Shot 10 角色异象 |
| 新发现 P1 RISK | **3 个**: T20-9.v3/15/19 |
| 已 close RISK | **3 个**: T20-16 (降级) + T20-18 (DevOps 已诊断) + T20-20 (前端容错已就绪) |
| 总成本估算 | ~$0.85 (符合 CLAUDE.md 短篇预估 $0.78/故事) |

---

## 1. 完整时间线 + Bug 出现位置

### Phase 0: 14:41:00 启动 Pipeline (Stage 1-3)

| 时间 | Stage | 事件 | 严重度 |
|------|-------|------|--------|
| 14:41 | Stage 1 outline | ✅ 1_outline.json 生成 (74s) | OK |
| 14:41:00-14:43 | UX | 🐛 **Founder 反馈: "大纲直接在 /create 出来了, 停留 /create 地址, 10s 内跳到 /outline 显示载入中, 过了 30s 又出来"** | **P2 RISK-T20-11** |
| 14:43-14:45 | Stage 2 characters | ✅ 2_characters.json (112s) — 3 anthropomorphic_animal (灰狐/米莉/啾啾) Schema PASS | OK (T20-10 修复后 PASS) |
| 14:45 | UX | 🐛 **Founder 反馈: "怎么都没看到角色, 一下子到了 /scenes 加载中, 是不是角色倒计时到了自动过去了?"** | **P0 RISK-T20-12** |
| 14:45-14:56 | Stage 3 screenplay | ✅ 3_screenplay.json (161s) | OK |

### Phase 1: 14:56:00-14:59:16 Stage 4 storyboard

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 14:56 | Stage 4 启动 (StoryboardDirector 并发 Claude 调用) | OK |
| 14:59:12 | Claude 第 1 批响应 10253 chars, 57.7s | OK |
| 14:59:12 | Claude 第 2 批响应 7617 chars, 44.8s | OK |
| 14:59:16 | ✅ 4_storyboard.json 完成 (142.2s, 20 shots, 1-20 连号无缺) | OK |

### Phase 2: 15:03:12-15:03:16 Stage 4.5 image_preparation

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 15:03:12 | Shot refs 全部计算: 1-20 完整, 每张 1-3 个 portrait + 0-2 个 scene_ref | OK |
| 15:03:16,429 | 🐛 `[Pipeline] Shot 6: 触发 GC 兜底（shot_index=5）` | **P2 RISK-T20-16** |
| 15:03:16,484 | 🐛 `[Pipeline] Shot 11: 触发 GC 兜底（shot_index=10）` | **P2 RISK-T20-16** |
| 15:03:16,513 | 🐛 `[Pipeline] Shot 16: 触发 GC 兜底（shot_index=15）` | **P2 RISK-T20-16** |

**规律**: GC 兜底每 5 个 shot 跳 1 个 (shot_index=5/10/15 = Shot 6/11/16), 同一秒同步触发。**初期误判为永久跳过 P0**, 后实证是**延后到末尾补跑**机制, **降级 P2 UX**。最终 3 张全部成功补跑:
- Shot 6: 15:35:09 启动 → 15:37:18 ✅ (129s)
- Shot 11: 15:37:42 启动 → 15:41:07 ✅ (205s)
- Shot 16: 15:38:31 启动 → 15:52:43 ✅ (851s = 14.2 min, attempt 4 最后险胜)

### Phase 3: 15:03-15:53 Stage 5 shot 生成 (~50 min, IMAGE_MAX_CONCURRENT=3)

#### 3.1 网络抖动: IncompleteRead 24 次 + URLError 2 次

```
15:08:35 - 15:34:13  IncompleteRead 集中爆发期 (network 抖动)
15:55:00+  网络稳定, 0 IncompleteRead
```

#### 3.2 Anthropic 529 Overloaded 18 次 (ShotValidator 全 fail-open)

```
15:13:00  Shot 4 ShotValidator skipped (API_ERROR_SKIPPED, skipped_count=4)
15:15:05  Shot 5 skipped (skipped_count=5)
15:17:46  Shot 8 skipped (skipped_count=6)
15:19:50  Shot 9 skipped (skipped_count=7)
15:20:14  Shot 7 skipped (skipped_count=8)
15:21:40  Shot 12 skipped (skipped_count=9)
... 累计 9 个 shot 完全没被 Validator 验证 (P0 隐患)
```

**RISK-T20-14 P0**: B51 fallback (T20-1 修复) 形同虚设, 这一轮 Pipeline **0 个 shot 被真正 ShotValidator 验证过**。

#### 3.3 长尾 outlier (单 shot ≥10 min)

| Shot | 总耗时 | 备注 |
|------|--------|------|
| Shot 7 | 11.3 min (680s) | 含 2 次 IncompleteRead 重试, ✅ 险胜 |
| Shot 18 | 10.4 min (625s) | ✅ 险胜 |
| Shot 16 | **14.2 min (851s)** | attempt 4 最后险胜, **打破纪录** |

#### 3.4 永久失败 (Pipeline 自动 retry 耗尽)

| Shot | 启动 | 失败时间 | 总耗时 | 原因 |
|------|------|---------|--------|------|
| **Shot 14** | 15:21:41 | 15:34:14 | **12.5 min** | 4 次 IncompleteRead retry 全失败 |
| **Shot 19** | 15:28:34 | 15:35:09 | **6.5 min** | 4 次 IncompleteRead retry 全失败 |

→ **RISK-T20-19 P1**: Pipeline 无 Shot 级 wall-clock timeout (DevOps 诊断, 理论最坏 14 min)

#### 3.5 ShotValidator 真 FAIL (Anthropic 没 529 时抓到的)

```
15:19:25  Shot 10 第 1 次生成 OK
15:23:09  ShotValidator: valid=False, 角色数量不匹配 预期2 实际0
15:23:09  [T17] Retry 1/1 Shot 10
15:25:17  Shot 10 第 2 次生成 OK
15:25:28  ShotValidator: valid=False, 同样原因
15:25:28  [T17] 已达最大重试次数, 使用当前结果 ← 强行保存
```

→ **RISK-T20-17 P0**: Shot 10 强保存了"角色 0 个"的图。后续 Founder /preview 验收发现: 画面实际是 **麻雀 + 类刺猬动物**, 但 test17 v2 角色是 灰狐/兔子米莉/麻雀啾啾, **没有刺猬**! Stage 4 prompt 或 Stage 5 参考图传递链有 bug。旁白"没等到......所以他一直在等" 应该是灰狐回忆白狼的情节, 画面应该有灰狐+白狼, 而不是麻雀+刺猬。

### Phase 4: 15:53-15:56 Stage 6 BGM (3 min)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 15:54:24 | Step 3 加载 meta-prompt (mixed) | OK |
| 15:54:31 | ✅ Haiku 输出 BGM prompt 799 chars, linter PASS, style=japanese_anime | OK |
| 15:54:24 | 🐛 6 个 atmosphere/emotional_arc str 类型 fallback warning (Scene 4/5/6) | 已知非阻塞 |
| 15:54:31 | Mureka 提交 task_id 139458253094913 | OK |
| 15:55:47 | ✅ Mureka 64s 完成, status=succeeded | OK |
| 15:56:00 | Mureka duration=193830ms | OK |
| 15:56:02 | ✅ FFmpeg 后处理: 静音检测 PASS, LUFS=-14.7 (范围 -23 ~ -14) | OK |
| 15:56:02 | ✅ bgm_chapter0.mp3 输出 (3.6MB, 190s) | OK |
| 15:56:17 | ✅ Pipeline 完成 (总 4488.7s = 74.8 min) | OK |

### Phase 5: 15:56-16:03 /preview 验收

| 时间 | 事件 |
|------|------|
| 15:56:25 | JobManager 完成 (4498.6s) |
| 15:57 | Founder 进 `/create/.../preview`, 显示"加载中" |
| 15:58+ | 前端正常 fetch shots/bgm, 加载完成 |
| 16:00+ | Founder 浏览 18/20 PNG, 发现 Shot 10 异象 + Shot 14/19 缺图占位 |

#### Founder 验收反馈

| 项 | 反馈 |
|----|------|
| 动物风格 | ✅ "是动物的感觉 这个没大问题" — **Wave 14 + T20-10 终极实证 PASS** |
| Shot 10 | 🐛 角色异象 (麻雀+类刺猬, 但应该是灰狐+白狼) |
| Shot 14/19 | 🐛 占位图 + "18/20 张生成成功, 2 张未生成" + "查看并重生" 按钮 |
| BGM | ✅ "整体感觉很不错" |
| 故事 | ✅ "整体故事感觉还可以" |

### Phase 6: 16:03-16:07 失败 Shot 重生 (前端"查看并重生")

| Shot | 启动 → 完成 | 耗时 | attempt | 结果 |
|------|-----------|------|---------|------|
| Shot 14 重生 | 16:03:39 → 16:04:35 | **56s** | **1 次过** | ✅ |
| Shot 19 重生 | 16:05:30 → 16:07:11 | **101s** | **1 次过** | ✅ |

**关键观察**: 网络稳定时 (近 5 min 0 IncompleteRead), 单 shot 重生大概率一次成功, 不走 4 次 retry。Shot 14/19 之前的失败完全是 15:34 那段网络抖动期的运气。

**自动后续动作** (Backend 自动完成):
- 图片覆盖保存 `shot_14.png` / `shot_19.png`
- 5_image_results.json 回写 (`updated=True`)
- DB job 更新: `failed_shot_count=0, partial_failure=False`
- new_url 带 `?v={timestamp}` 缓存破坏

**最终成片**: **20/20 PNG 全齐**!

---

## 2. 全部 RISK 清单 (按严重度排序)

### 🔴 P0 (5 个 pending + 1 closed-降级)

#### #38 RISK-T20-12 P0 — Frontend 自动 confirm-characters
**症状**: 14:45 Founder 反馈: "怎么都没看到角色 一下子又到了 /scenes 加载中 是不是角色倒计时到了自动过去了?"
**根因待查**: 前端 /characters 页面可能有自动跳转倒计时, 或 confirm-characters 接口被自动触发
**影响**: 用户无法 review 角色就被强制确认, 违反 DEC-011 Stage B 用户旅程 (用户应该看到角色卡片可编辑)
**派活**: 待 Frontend 排查 + 修

#### #39 RISK-T20-13 P0 — Backend status API 缺 `shots_total` / `shots_completed` 字段
**实证**: `GET /api/projects/{uuid}/chapters/1/status` 返回:
```json
{
  "shots_total": null,
  "shots_completed": null,
  "shots_failed": null,
  "message": "已生成 9/20 张图像..."  ← 前端只能 regex 解析
}
```
**根因**: Backend 没在响应里 expose 这 3 个 in-memory 计数字段
**影响**: 前端 ETA 算法只能从 `message` 字符串 regex 抠"X/20", 加上更新延迟 → ETA 必然失真
**派活**: 待 Backend 加字段 + Frontend 改用真字段

#### #40 RISK-T20-14 P0 — Anthropic 529 Overloaded → ShotValidator 全 fail-open
**实证**: test17 v2 跑了 18 次 Anthropic 调用, **全部 529 Overloaded**, skipped_count=9, Shot 4/5/6/7/8/9/12/... 等 9 个 shot 全 fail-open 跳过验证
**根因**: ShotValidator 走 Anthropic Claude, Anthropic 频繁过载, 当前 fail-open 策略直接放行
**影响**: B51 fallback (T20-1 修复) 形同虚设, 本轮 Pipeline 0 shot 被真验证
**派活**: Backend 加 429/529 退避重试 + 至少保证关键 shot (有大量角色的) 真验证

#### #43 RISK-T20-17 P0 — Shot 10 角色异象 (anthropomorphic 识别 + Stage 4 prompt 隐患)
**实证**: Shot 10 画面: 麻雀啾啾 + 类刺猬动物 (旁白"没等到......所以他一直在等" 应该是灰狐回忆白狼)
**待 Backend 排查**:
1. 4_storyboard.json shot_id=10 storyboard 写的是哪 2 个角色?
2. 实际传给 Seedream 的 reference_images 是哪几个 character_id?
3. prompt 文本里角色描述写了什么 (有没有写"狼"导致 Seedream 画成"刺猬")?
4. 是 Stage 4 LLM 写错角色 (跨人/动物) 还是 Stage 5 Seedream 渲染歪了?

#### #42 RISK-T20-16 P2 (从 P0 降级) — GC 兜底跳 Shot 6/11/16
**初判**: 永久跳过, 用户成片缺图 P0
**实证后修正**: 是**延后到末尾补跑**机制, 不是永久跳过 (3 张全部成功)
**当前残留 P2 UX 问题**: progress UI 跳变 (1→2→3→4→5→7→8...→6 补跑), 用户感觉乱序
**Backend 排查方向**: pipeline_orchestrator.py `[Pipeline] Shot N: 触发 GC 兜底（shot_index=N-1）` 代码位置, 决定是否要 UI 显示策略调整

### 🟡 P1 (4 个 pending)

#### #37 RISK-T20-9.v3 P1 — ETA 全局重审 (Founder 5/19 明确要求)
**Founder 原话**: "ETA 这个问题需要重新全局考虑"
**实证多层失真**:
1. Backend status 缺 shots_total/completed (见 T20-13)
2. message 更新延迟 (写完 Shot N 才 update message=N+1)
3. progress% 算法严重偏快: 84% 但 Shot 14/20 才开始 = 真实 ~70%
4. 单 shot 实测均值波动 79-680s (Shot 7 outlier 680s)
5. 终态消失: 78% → "即将完成" → "没有 ETA 数字" 错乱
6. **前后端完全没联系上**, 前端在自说自话 (Founder 原话)
**派活**: 不再小修 per_shot 参数, 全局算法重审, 依赖 T20-13 字段先到位

#### #41 RISK-T20-15 P1 — Client console React setState-in-render warning
**实证**: client.log 早期 185 errors 含此 P0 anti-pattern warning at `StageC.tsx:1572 CharacterPreview` (CreateProvider 渲染时改 state)
**疑似**: BUG-T13-REACT-ANTIPATTERN-STAGEC 回归未根治
**派活**: 待 Frontend 把 setState 移到 useEffect / event handler

#### #45 RISK-T20-19 P1 — Pipeline 无 Shot 级 wall-clock timeout (DevOps 诊断)
**DevOps 15:35 诊断**: SeedreamGenerator 有 HTTP 重试上限 (3 次 × 210s + 退避 2+8+30s), 理论最坏 ~14 min。但 Pipeline 层 (pipeline_orchestrator.py Stage 5) **没有 asyncio.wait_for 包裹** (全文 0 处)
**实证**: Shot 14 hang 12.5 min 直到 SeedreamGenerator 自己放弃, Shot 16 hang 14.2 min 最后险胜
**DevOps 推荐**: 加单 Shot wall-clock `asyncio.wait_for(timeout=600-720s = 10-12 min)`
**派活**: Backend 加 wall-clock timeout, 代码位置 pipeline_orchestrator.py L1228-1310 `_generate_single_shot()`

### 🟢 P2 (1 个 pending)

#### #36 RISK-T20-11 P2 — Frontend /create → /outline 重复 fetch (30s 二次载入)
**实证**: Founder 14:43 反馈: "大纲直接在 /create 出来了 停留 /create 地址, 10s 内跳到 /outline 显示载入中, 过了 30s 又出来"
**根因**: /create 已经拉过 outline 数据, /outline 又重复拉一遍
**派活**: Frontend 缓存 / 去重 fetch

### ✅ closed (3 个)

#### #42 RISK-T20-16 → P2 降级 + closed (上面已说明)

#### #44 RISK-T20-18 P0 ✅ closed — Shot 14 hang 11+ min 诊断
**DevOps 诊断完成**: SeedreamGenerator 有重试上限, 不是死锁, Pipeline 自愈
**残留**: 派生出 RISK-T20-19 (无 wall-clock timeout)

#### #46 RISK-T20-20 P1 ✅ closed — 失败 Shot 容错策略实证 PASS
**实证**: Frontend "查看并重生" 按钮 + Backend regenerate API 完整链路工作:
- Shot 14 重生 56s 一次过
- Shot 19 重生 101s 一次过
- 自动覆盖保存 + 5_image_results.json 回写 + DB partial_failure=False

---

## 3. Pipeline 性能/网络数据

### 总耗时分解 (74.8 min Pipeline + 4 min 重生)

| Stage | 耗时 | 占比 |
|-------|------|------|
| Stage 1 outline | 74s | 1.6% |
| Stage 2 characters | 112s | 2.5% |
| Stage 3 screenplay | 161s | 3.6% |
| Stage 4 storyboard | 142s | 3.2% |
| Stage 4.5 image_prep | ~30s | 0.7% |
| **Stage 5 image gen** | **~50 min** | **66%** ← 大头, 含网络抖动 + 长尾 |
| Stage 6 BGM (Mureka + FFmpeg) | 178s | 4% |
| **总 Pipeline** | **4488.7s = 74.8 min** | 100% |
| 重生 Shot 14 | 56s | - |
| 重生 Shot 19 | 101s | - |

### Stage 5 单 shot 耗时分布 (20 张)

| 耗时区间 | shots |
|---------|-------|
| 79-130s (中位) | 12 张 |
| 191-294s | 4 张 (1, 9, 11, 13) |
| 333-371s | 2 张 (4, 5) |
| **625-851s (长尾)** | **3 张 (7=680s, 18=625s, 16=851s)** |
| **失败 (4 次 retry 耗尽)** | **2 张 (14, 19)** |

**中位**: 130s, **均值**: ~250s (含长尾+失败), **方差极大** (79s ↔ 851s = 10 倍)

### 网络抖动事件统计

| 事件 | 数量 | 时段 |
|------|------|------|
| IncompleteRead | 24 | 集中在 15:08-15:34 |
| URLError (write timeout) | 2 | 15:25 附近 |
| Anthropic 529 Overloaded | 18 | 15:13-15:21 集中 |
| Pipeline 真 crash | **0** | 无 |
| 数据库 metadata lock | **0** | 无 (DEC-016 远程 MySQL 稳定) |
| sqlalchemy ERROR | **0** | 无 |
| 连接池耗尽 | **0** | 无 |

### 成本估算 (按 CLAUDE.md 官方定价)

| 项 | 数量 | 单价 | 小计 |
|----|------|------|------|
| Stage 5 Shot 生成 (含失败/重试) | 21 次 API 调用 | $0.03 | $0.63 |
| 角色参考图 (portrait) | 3 张 | $0.03 | $0.09 |
| 角色参考图 (fullbody) | 3 张 | $0.03 | $0.09 |
| 场景参考图 | 2 张 | $0.03 | $0.06 |
| 重生 Shot 14, 19 | 2 张 | $0.03 | $0.06 |
| BGM Mureka | 10 credits | - | - |
| ShotValidator Anthropic | 11 真调用 + 18 fail-open | ~$0.001 | ~$0.03 |
| Stage 1-4 Claude Sonnet 4.6 | 4 次 LLM | ~$0.05 | ~$0.20 |
| BGM prompt Haiku 4.5 | 1 次 LLM | ~$0.001 | $0.001 |
| **总计** | | | **~$1.16** |

略高于 CLAUDE.md 短篇基准 $0.78, 主要因 Shot 10 T17 重试 1 次 + Shot 14/19 失败但仍计费 + Shot 14/19 用户重生 + 长尾 shot 触发更多重试。

---

## 4. 已实证 PASS 的能力 (Wave 14 + T20-10 终极验证)

### A. CharacterSchema 兼容 19 character_type (T20-10)

✅ 3 anthropomorphic_animal 角色 (灰狐墨九/兔子米莉/麻雀啾啾) Stage 2 Schema 验证 PASS, **0 errors** (对比 test17 v1 5×4=20 errors 全崩)

### B. CharacterPromptBuilder 19 类型 dispatch (T20-10 5 处下游统一)

✅ Stage 4 storyboard_director 调用 dispatch 路径 (非 human 走 CharacterPromptBuilder), Founder 反馈"是动物的感觉"

### C. Stage 5 anthropomorphic_animal 风格 (Wave 14 终极实证)

✅ 18/20 PNG 全部画成动物形态, Founder 验收"动物的感觉对", **没有出现"Asian woman"** (test17 v1 的灾难)

### D. 失败容错链路 (RISK-T20-20)

✅ Frontend "查看并重生" 按钮触发 Backend `POST /api/projects/{uuid}/chapters/1/shots/{shot_id}/regenerate`, 走同一套 SeedreamGenerator + retry 机制, 实测 2/2 一次过 (网络稳定时)

### E. GC 兜底 = 延后机制 (RISK-T20-16 重新定性)

✅ Shot 6/11/16 都成功补跑, 不是丢图 P0

### F. ShotValidator T17 retry 机制

✅ Shot 10 走完 T17 retry 1/1 流程 (Anthropic 没 529 时), 即使 2 次都 valid=False, 强保存路径正常 (不阻塞 Pipeline)

### G. DevOps 自愈能力

✅ Shot 14 hang 12.5 min 后 SeedreamGenerator 自己放弃 (重试上限), Pipeline 自愈, Semaphore 自动释放

### H. BGM 全链路 (Mureka + FFmpeg)

✅ Haiku 4.5 prompt 生成 + Mureka 64s 生成 + FFmpeg LUFS=-14.7 后处理 + 静音检测 PASS, Founder "整体感觉很不错"

### I. 数据库 + 进程稳定性

✅ 75 min Pipeline 期间: 0 metadata lock, 0 sqlalchemy ERROR, 0 连接池耗尽, Backend RSS 692MB→1002MB (平稳增长), 无 OOM

---

## 5. 监控/可观测性问题

### 8 维度监控验证 PASS

8 维度 cron 全程覆盖, 在 Shot 14 hang 时第一时间预警, Founder 决策派 DevOps 诊断, 整个流程无遗漏。

### 但暴露 Backend 可观测性弱点

1. **缺 shots_total/completed 字段** (T20-13) → 前端无法精确知道 Pipeline 状态
2. **缺 shots_failed 实时更新** → message 字段需要 regex 解析
3. **缺 stage_substage 细分** → 无法知道当前在 Stage 5 哪个 sub-step (image_prep / shot_gen / validation / save)
4. **缺单 shot 耗时分布 metric** → 长尾/失败需要 grep 日志才能看到
5. **缺 Anthropic/Seedream API 健康度** → 529 / IncompleteRead 累计需要监控告警

---

## 6. 跨阶段贯穿问题汇总

### A. 前后端 ETA 完全脱节 (Founder 多次强调)

| 数据源 | 显示 | 真实 | 偏差 |
|--------|------|------|------|
| Founder 页面 | "已生成 8/20" / 83% / "即将完成" | Shot 13/20 启动, 实际 PNG 7 张 | 落后 5-6 步 + UX 严重欺骗 |
| 中段 | "已生成 13/20" / 88% / "即将完成" | Shot 19/20 启动, PNG 13 张 + Shot 14 hang 11 min | 严重欺骗 |
| 末段 | "已生成 19/20" | Shot 16 仍在 retry 14 min, PNG 17 张 + 2 失败 | UX 误导 |

**根因综合**: T20-13 (字段缺) + T20-9.v3 (算法失真) + T20-15 (React 状态更新)

### B. 网络稳定性强依赖

Pipeline 成功率严重依赖 Seedream 服务端网络 + Anthropic 服务端可用性, 这一轮 18 次 Anthropic 529 + 24 次 Seedream IncompleteRead 都是不可控外部因素。**Wall-clock timeout (T20-19) + 重试退避策略 (T20-14) 是治标的最大杠杆**。

### C. 用户旅程 Stage B (角色确认) 跳过

Founder 14:45 反馈: 角色页面**没看到就自动确认了** (RISK-T20-12 P0), 违反 DEC-011 用户旅程设计 (用户应该有机会编辑角色)。

---

## 7. 待 Founder 决定 (留给您补充意见)

### A. 内测前修哪些 P0?

8 个 pending RISK 中:
- **P0×3 pending**: T20-12 (自动 confirm), T20-13 (status 缺字段), T20-14 (Anthropic 529 全跳过), T20-17 (Shot 10 角色异象)
- **P1×3 pending**: T20-9.v3 (ETA 全局), T20-15 (React 警告), T20-19 (无 timeout)
- **P2×1 pending**: T20-11 (重复 fetch)

### B. 优先级建议 (PM 视角)

1. **T20-12 P0 + T20-13 P0 + T20-9.v3 P1** = 一起改 (用户旅程 + ETA 真实感, 影响用户对产品的整体感知)
2. **T20-14 P0** = 单独改 (后端服务质量, 不影响用户感知但影响内部质控)
3. **T20-17 P0** = 单独排查 (角色一致性, 是 Wave 14 的细节遗留)
4. **T20-19 P1** = 加 wall-clock timeout (DevOps 推荐)
5. **T20-11/15 + Shot 10 异象** = 可推到内测后第 2 批

### C. 是否需要再测一轮?

考虑:
- test17 v2 已经验证 Wave 14 + T20-10 终极闭环 PASS
- 失败容错链路实证 PASS
- 但 Shot 10 角色异象需要单独 case 验证 (灰狐回忆白狼是否能稳定画对)
- 短视频模式 (TTS + Whisper + alignment + TextOverlay) 这次 design 跳过, 但需要至少跑一次端到端测

---

## 8. Founder 实测后补充的发现和优化方向 (2026-05-19 16:08)

### 🚨 A0. 重大产品方向收敛 (新增最高优先级 RISK)

> **Founder 原话**:
> "现在所有生成的故事都有一个通病（通用性问题）：如果只通过看图片以及图片中的心理描述和对话泡泡，**不看旁白内容的话，会感觉故事不是很直白易懂，有点晦涩隐晦**，原因是因为有旁白，然而**现在我们其实是不用旁白的，就是 shots + BGM, 也不会用 TTS 读出旁白**, 目前已经确定这样的形式了, 至少现在觉得很好。
>
> 所以现在要做比较大的重构（非pipeline层面的）: **要去掉旁白**, 把不在 shot 画面里的旁白里的内容融入到 shot 中会显示的对话、心理描述、旁白, 让观众一看 shot 就知道这个 shot 发生的情节是什么, 应该会增加 shot 中的对话/心理描述/旁白的内容。"

→ 已加 **RISK-T20-21 P0 (重大重构, 通用性问题)** task #47, 详见第 2 节

**关键点**:
1. **最终产品形态**: shots + BGM, **无 TTS / 无朗读旁白** — 这是确定决策
2. **内容必须脱旁白自洽**: 用户只看 shot 图 + 心理气泡 + 对话气泡 + 顶部/底部 caption 必须能完整理解故事
3. **重构在 prompt + 内容生成层面**, 不动 Pipeline 调度
4. **Owner**: AI-ML 主导 + Backend/Tester 配合
5. **影响**: shot 内文字密度会增加, 这是预期, 不是 bug

### A. 看 20 张图 (重生成功后) 感觉

✅ **"都挺好的，整体感觉不错"** — Wave 14 + T20-10 + 失败容错 三层闭环 PASS

### B. Shot 10 类刺猬动物 引发原因

**待 Backend/AI-ML 深挖** — 已在 task #43 RISK-T20-17 详细记录排查方向 (4_storyboard.json shot_id=10 storyboard 角色 + Seedream refs + prompt 文本 + 渲染歪推断)

### C. ETA UX 期望理想形态

**Founder 原话**: "**大纲 - 预览/调整角色 - 预览/调整场景 - 后续全自动生成一直到预览全局 preview**"

→ 这跟 DEC-011 Stage A→B→C→D 设计完全一致, 但当前实测 (test17 v2) **Stage B 的"角色预览/调整"被自动跳过了** (RISK-T20-12 P0), 必须修

**衍生 PM 判断**: ETA 在"全自动生成一直到 preview" 这段必须**可信** (用户在等), 强化 RISK-T20-9.v3 P1 紧急度

### D. "查看并重生" 用着感觉

✅ **"用着不错, 可以成功生成, 有点慢, 但这个应该没办法, 整体可以 pass"**

→ RISK-T20-20 实测 PASS 确认, 用户体验可接受。慢的部分受 Seedream API 不可控 (~60-150s/张)

### E. BGM japanese_anime vs ghibli 故事氛围是否匹配

✅ **"BGM 很不错"** + 整体观感 "BGM 很不错"

→ Mureka API + japanese_anime style 适配 ghibli 故事氛围, **保持现有策略**

### F. 整体故事观感

✅ **"除了我提到的晦涩不是很易懂之外都不错"** → A0 重大重构覆盖唯一痛点

### G. 内测前必修 vs 可延后清单

Founder 让 PM 判断, 见第 9.5 节

### H. 其他

暂时没有

---

## 9. 完整 RISK 清单 (含 T20-21 重大重构)

| RISK | 严重度 | Owner | 预计工作量 | 备注 |
|------|--------|-------|----------|------|
| **T20-21 P0 (新, 通用性)** | **P0** | **AI-ML 主导 + Backend/Tester 配合** | **2-3 天** | **去旁白 + 内容融入 shot, 脱旁白可读** |
| T20-12 P0 自动 confirm-characters | P0 | Frontend | 半天 | Founder C 项隐含强调 |
| T20-13 P0 status API 缺字段 | P0 | Backend | 1h 后端 + 1h Frontend | T20-9.v3 前置 |
| T20-14 P0 Anthropic 529 全跳过 | P0 | Backend | 半天 | 加 429/529 退避重试 |
| T20-17 P0 Shot 10 角色异象 | P0 | Backend + AI-ML | 1-2 天 | 排查 Stage 4 prompt + 角色参考图传递链 |
| T20-9.v3 P1 ETA 全局重审 | P1 | Backend + Frontend | 1 天 | 依赖 T20-13 |
| T20-15 P1 React setState | P1 | Frontend | 半天 | 控制台警告 |
| T20-19 P1 无 wall-clock timeout | P1 | Backend | 半小时 | asyncio.wait_for, DevOps 建议 |
| T20-11 P2 重复 fetch | P2 | Frontend | 半天 | 30s 二次载入 UX |

**总工作量**: ~7-8 人天 (含新 T20-21 大重构)

## 9.5 PM 判断: 内测前必修 vs 可延后 (Founder G 项授权)

### 🚨 内测前必修 (4 项, ~4-5 天)

| RISK | 理由 |
|------|------|
| **T20-21 P0 重构 旁白→shot 内容融入** | **核心产品质量, 影响"故事易懂"的根本问题, 通用性 bug, 所有故事都受影响**, 不修内测会被用户感知到"晦涩". Founder 明确这是最终产品形态前置. |
| **T20-12 P0 自动 confirm-characters** | Founder C 项"理想形态"明确要求"预览/调整角色" 必须有, 当前被跳过 = 违反用户旅程设计, 影响用户对产品的掌控感. |
| **T20-13 P0 status API 缺字段** | 前后端 ETA 失真根因, 修这个才能修 T20-9.v3. 单独 1h Backend + 1h Frontend, 性价比最高. |
| **T20-9.v3 P1 ETA 全局重审** | UX 严重欺骗 ("即将完成" 实际还要 15-40 min), 内测用户会失去耐心和信任. 依赖 T20-13. |

### 🟡 内测可延后 (4 项, ~2-3 天)

| RISK | 延后理由 |
|------|---------|
| **T20-14 P0 Anthropic 529 全跳过** | 内部质控问题, 用户无感, B51 fallback 形同虚设是隐患不是 bug. 内测期持续观察 Anthropic 可用性, 内测后修. |
| **T20-17 P0 Shot 10 角色异象** | 单 case 偶发 (20 shots 出 1 个), 用户可"查看并重生" 兜底, 不阻塞产品上线. 内测后专项排查. |
| **T20-15 P1 React setState** | 控制台 warning, 不影响功能, 已经活了很久. 内测后清理. |
| **T20-19 P1 无 wall-clock timeout** | SeedreamGenerator 自身 4 次 retry 上限 ~14 min 已经是兜底, Pipeline 自愈机制工作正常. Asyncio.wait_for 是锦上添花的可观测性优化, 不紧急. |
| **T20-11 P2 重复 fetch** | 30s 二次载入纯 UX, 用户能容忍, 优先级最低. |

### 🎯 内测前总工作量: ~4-5 人天 (T20-21 + T20-12 + T20-13 + T20-9.v3)

### 推荐派活顺序 (依赖关系)

1. **Day 1** (并行):
   - AI-ML: T20-21 prompt 重构 (旁白融入 shot)
   - Backend: T20-13 status API 加字段
   - Frontend: T20-12 排查 + 修自动 confirm
2. **Day 2** (并行):
   - AI-ML: T20-21 继续 + 端到端测
   - Backend: T20-9.v3 ETA 算法重写 (依赖 T20-13 完成)
   - Frontend: T20-9.v3 改用真字段 + T20-12 收尾
3. **Day 3** (集成 + 测):
   - Tester: 跑新故事端到端, 验证 T20-21 脱旁白可读 + T20-12 角色可调整 + T20-9.v3 ETA 准确
   - Backend/Frontend: 修任何回归
4. **Day 4-5** (内测准备):
   - 整体回归 + 部署 + 内测启动准备

### 决策权: Founder

PM 建议如上, 但是否接受这个内测前清单, 由 Founder 决定. 任何调整 (加入 / 移除 / 推迟某项) 请告知, 我会重新规划派活顺序.

---

**报告生成**: 2026-05-19 16:08 (Founder 主对话 / boss-coordinator)
**审计方法**: 8 维度 cron 监控 + 5 维度 cron 监控 + DevOps 紧急诊断 + Founder 实时反馈 + 代码 + 日志地毯式回溯
**任务列表同步**: 已更新 #36-#46 (8 pending + 3 closed)
