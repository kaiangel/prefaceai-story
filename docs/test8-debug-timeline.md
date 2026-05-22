# test8《行李箱里的她》Debug Timeline

> **目的**: 每步真实状态记录（backend log + frontend UI 表现 + 时间戳），为后续 frontend 修复提供实证依据
> **触发原因**: 5-08 11 task 修复完成后，5-09 test8 实测发现 D.21 在 character preview / scenes 子页面**完全没生效**（与 5-02 同等 bug 重现）
> **Founder 严肃指示**: "这次一定要把每一步都记下来（在确认 debug 相关代码逻辑日志足够的情况下），以便后续更有质量和效率的修复"

## 项目实证

- **project UUID**: `21ebb0d8-2eb0-483d-a4a5-fd8c93ec49ba`
- **project_id**: 23
- **idea**: 楼下独居老人每天清晨拖着黑色超大行李箱绕小区一圈... (test8.md 一行 idea)
- **style**: oil_painting (油画风)
- **aspect_ratio**: 3:4
- **chapter_duration_minutes**: 3 (短篇)
- **mood**: melancholic (LLM 输出) → user 改为 **悬疑** (确认时 user_selected_mood)
- **结局选择**: 老人独自完成捐赠后，从夹层取出亡妻照片 — 悲而不伤开放留白

## 时间线（真实数据）

### 阶段 1: 项目创建 + Stage 1 outline 生成

| 时间 | Backend log | Frontend UI 实际 | Bug |
|------|------------|----------------|-----|
| 10:26:37 | `[CreateProject] ✅ 项目创建成功: id=23` | 创建项目按钮点击 | - |
| 10:26:39 | `[StoryOutlineGenerator] 生成故事大纲...` style=oil_painting | "正在创作你的故事" 1% 进度 | - |
| 10:28:17 | `✅ 大纲生成成功 (via claude)` title=行李箱里的她 (98s LLM) | 切到 outline 编辑页（Image #94 看到）| 切换有 spinner 1-2 min（正常 hydrate）|
| 10:31:03 | `[ConfirmOutline] OBS-4: user_selected_mood='悬疑'` (用户改的) | 用户改了情绪基调 + 结局 + 点确认 | - |
| 10:31:17 | `[ConfirmOutline] ✅ 大纲已确认` | spinner 加载 | UX-2 一致性检查 warning（非阻塞）|

### 阶段 2: Pipeline 启动 + Stage 2 角色设计 + UX-1 portrait

| 时间 | Backend log | Frontend UI 实际 | Bug |
|------|------------|----------------|-----|
| 10:31:20 | `[StartGeneration] ✅ Pipeline 启动` | spinner | - |
| 10:31:22 | `[Pipeline] ========== Pipeline 开始` | spinner | - |
| 10:31:25 | `[Pipeline] ARCH-4: → db_project_id=23` | 切到进度条页 | - |
| 10:31:27 | BGM-1 music_hint 注入 (oil_painting): classical chamber gravity | - | - |
| 10:31:27 | Schema 验证 Stage 1→2: 3 角色 / 11 plot / 5 场景 | - | - |
| 10:31:29 | `[CharacterDesigner] 开始设计 3 个角色` | 进度 1% "正在启动创作引擎" (Image #97) | ✅ stale-copy 修复生效 |
| 10:32:32 | `[CharacterDesigner] ✅ 角色设计完成` (63s LLM) | - | - |
| 10:32:51 | UX-1: 陈晓 portrait | - | - |
| 10:33:41 | UX-1: 林守仁 portrait | - | - |
| 10:33:57 | UX-1: 王师傅 portrait + UX-14 portrait_url 写入 | - | - |
| 10:34:01 | `[Pipeline] R4-1: 开始等待用户确认角色 (超时 1800s)` | 切到 character preview 页 | 🔴 **B26 P1**: 页面**完全空白**仅"确认角色继续"按钮 + 30s 倒计时（Image #99）|
|  |  | Founder 实测: 没看到任何 portrait | - |

**B26 调查待 (frontend logging 不够)**:
- 不知道 frontend GET portrait 是否触发（grep backend log 看到 char_001_portrait HTTP 请求 = 0）
- 不知道 D.21 fallback chain 哪层 hit
- 不知道 buildStaticPortraitUrl 是否真调用

### 阶段 3: Character 确认 + Stage 3 ScreenplayWriter

| 时间 | Backend log | Frontend UI 实际 | Bug |
|------|------------|----------------|-----|
| 10:34:53 | `[ConfirmCharacters] ✅ 角色已确认` (30s 倒计时自动跳，被迫) | URL 切到 `/scenes`（Image #100 显示）| 🔴 **B27 P1**: URL `/scenes` 但 backend 还在 Stage 3 — 应显示进度条，实际 spinner |
| 10:34:57 | `[Pipeline] R4-1: ✅ 用户已确认角色 (等待 30s)` | spinner | - |
| 10:34:57 | `[ScreenplayWriter] 开始生成分场剧本` | - | - |
| ~10:36 | (Founder 报告 30s timeout 触发, URL 改 /outline 显示"加载项目失败")| **B28 P1**: GET /projects 30s timeout 触发（Image #101）| - |
| 10:39:12 | `[ScreenplayWriter] ✅ 剧本生成完成 (总耗时 254.8s)` 11 场景 23 beats | spinner / 加载失败页 | ✅ B8 SCENE-FAIL-FIX 实证生效（0 Scene 失败 vs test7 3/16 失败）|
| 10:39:12 | Schema 验证 Stage 3→4: 11 场景 23 action_beats | - | - |

### 阶段 4: Stage 4 StoryboardDirector

| 时间 | Backend log | Frontend UI 实际 | Bug |
|------|------------|----------------|-----|
| 10:39:?? | `[StoryboardDirector] 开始` | - | - |
| 待续 | 生成 Scene 1-11 shots | - | - |

### 阶段 5: Stage 5b 18 shot 真生 (油画风 × 3:4 × Seedream)

待续

### 阶段 6: Stage 6 BGM (Mureka — 应该出 Mysterious 桶)

待续

---

## 已确认的 Bug 清单（test8 实测）

### 🔴 P1 阻断/影响体验

**B26 D.21 character preview portrait fallback 没生效**:
- 现象: portrait 文件真生成 + 文件存在 + 但 character preview 页空白 + 没 GET portrait 请求
- 5-02 已经发现过同类问题，5-08 D.21 修复声称已修，5-09 test8 实测**完全没生效**
- frontend 缺 logging 无法精确定位（buildStaticPortraitUrl 是否触发？fallback chain 哪层 hit？）

**B27 `/scenes` 路由 spinner 而非进度条**:
- character 30s 跳过后 frontend 切到 `/scenes` 但 backend 在 Stage 3
- 应显示"剧本编写中"进度，实际 spinner
- 推测 D.23 引入新路由但页面渲染条件不全覆盖 stage state

**B28 backend Stage 3 期间 GET /projects 30s timeout 触发**:
- D.21 timeout 30s 不够（Stage 3 LLM 阻塞期）
- frontend 显示"加载项目失败，请刷新重试"（D.21 fallback 页正常工作）
- 但用户体验差（pipeline 还在跑就被告知失败）

### ✅ test8 实证生效

- ✅ B19 mood enum: LLM 输出 `melancholic` 标准化 enum（不再自由复合词）
- ✅ B11 调性优先匹配: user 选悬疑覆盖 LLM melancholic（user_selected_mood='悬疑' 真传到 confirm-outline）
- ✅ B6 chapter/story 404: pre-confirm 阶段返 404 不再返 400
- ✅ B8 SCENE-FAIL-FIX: Stage 3 0 失败（vs test7 3/16 失败）— inner quote 修复真生效
- ✅ B18 plot completeness: schema 验证通过 11 plot 全部含 beat
- ✅ stale-copy 副文案: 进度条页"正在启动创作引擎"合理（不再"喝杯可可"过期）
- ✅ B16 generate-outline 幂等: `[GenerateOutline] 幂等: ... 直接返已存数据（不调 LLM）` 真触发

### ⚠️ 待续观察

- B11 BGM Mysterious 桶（要等 Stage 6 Mureka 出来）
- B17 ShotValidator anatomy（要看 18 shot 是否有多肢自动 sanitize）
- B16 重新生成单 shot（要 pipeline 完成后试）
- D.23 自动跳 preview（要 Stage 6 完成后看）
- D.24 cache bust（要重新生成时看 ?v= 参数）
- D.25 BGM 文案（要在预览页看）

---

## Frontend Logging 缺口（必须补）

为了下次 bug 能精确定位，frontend 需补:

1. **D.21 fallback chain 每层 console.log**:
   ```
   [D.21] portrait_url from API: <value>
   [D.21] fallback to buildStaticPortraitUrl(charId): <url>
   [D.21] fallback to outline data: <found/not_found>
   [D.21] final portrait src: <value>
   ```

2. **subPhase 切换日志**:
   ```
   [StageC] subPhase changed: text-gen → char-preview at <ts>
   [StageC] /scenes route entered, currentStage=<>, generationSubPhase=<>
   ```

3. **CreateContent hydrate timeout 触发**:
   ```
   [hydrate] project fetch attempt at <ts>
   [hydrate] timeout after Xms — fallback notFound: false
   [hydrate] state dispatch: <action>
   ```

4. **路由跳转触发**:
   ```
   [Router] subPhase=<>, current URL=<>, decided new URL=<>
   ```

派 Frontend 加这些 logging（不是修 bug，是加可观测性）。下一次复测时这些 log 会让根因定位 5x 更快。

---

## 当前 Backend Pipeline 状态（实时）

最后更新: 11:00 (Stage 5 完成)

### 阶段 4: Stage 4 StoryboardDirector ✅

| 时间 | Backend log | 备注 |
|------|------------|-----|
| 10:39:?? | StoryboardDirector 启动 | - |
| 10:46:14 | ✅ 分镜生成完成 (总耗时 417.5s = 7 min) 11 个 Scene 全成功 | 比 test7 快 30%（test7 用 10 min 16 Scene）|
| 10:46:14 | O-2 cap 23→18 真生效 | LLM 生 23 shots → 截到 18 |

### 阶段 5: Stage 5 真生 18 shot ✅

| 时间 | Backend log | 备注 |
|------|------------|-----|
| 10:46-10:50 | Stage 5a fullbody（复用 portrait）+ 5a.5 scene_anchor 5 张 | ~4 min |
| 10:50:?? | Stage 5b 启动并行生 18 shot | - |
| 10:50:?? | shot_01 生成（mtime 10:50） | - |
| 10:51:?? | shot_02-04 生成 | - |
| 10:52:?? | shot_05/07 生成 | - |
| 10:57:51 | Shot 6 生成成功 (57.77s, sanitize_attempts=0) | - |
| 10:58:32 | Shot 12 生成成功 (369.34s 慢)  | 可能 sanitize 重试 |
| 10:58:45 | Shot 11 生成成功 (58.08s) | - |
| 10:58:49 | Shot 16 生成成功 (50.91s) | - |
| 10:59:59 | Shot 11 保存 | 注意有重生 |
| ~11:00 | ✅ Stage 5 完成: 18/18 图像生成成功 | 0 次 CONTENT_SAFETY 触发 |

**实证**:
- 18 张全 1664×2218 (3:4 ratio) ✅ D.15 + D.18 真生效
- 文件大小 2-4.6MB（油画风厚涂吃带宽）
- 0 次 sanitize_attempts（B17 anatomy 检测可能没触发，要看实际质量）

### 阶段 6: Stage 6 BGM Mureka — 关键 Mysterious 桶验证

待续 — 此处验证 B11 6 桶通用化 Mysterious 桶

---

## Frontend 加固 Logging 完成（11:00 前）

Frontend agent 完成 logging 加固:
- `StageC.tsx` + `CreateContent.tsx` 加 10+ 条 console.log
- 前缀: `[D.21]` / `[StageC]` / `[hydrate]` / `[Router]`
- 覆盖: portrait fallback chain 4 层 + subPhase 切换 + hydrate 各阶段 + 路由决策
- npm build 0 errors

新 frontend PID 46431（11:00 重启含 logging）

下次 Founder 复测 B26/B27 可在 Console 过滤 `[D.21]` 看精确 portrait fallback 触发哪层 — 之前完全黑箱，现在可见。

---

## 服务实证（最新）

- backend PID **35835**（5-08 20:30 重启含 11 task + B16 hotfix）
- frontend PID **46431**（5-09 10:59 重启含 logging 加固）
- caffeinate 15793
- Monitor v8 task bjizt964d
