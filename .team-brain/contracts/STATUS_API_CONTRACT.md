# Status API Contract

> **Wave 9 / DEC-030 落地 — Ben 方案 A "前后端纠验机制" 的核心契约文档**
> **版本**: v1.6 (2026-05-24 Wave 12 — §9.7 adjust 异步 job 端点新增, PM 代补 Backend gap) [frontend-impact: yes]
> **生效**: 2026-05-13 (v1.0) / 2026-05-19 (v1.1 + v1.2) / 2026-05-20 (v1.3) / 2026-05-21 (v1.4) / 2026-05-22 (v1.5)
> **基准代码**: Backend `app/api/chapters.py` L47-160 + `_compute_v3_eta` + `_derive_ui_phase` (8 状态机) / Frontend `frontend/src/lib/createUrl.ts` (Wave 8 #2 T22-NEW-5 Frontend 已同步 v1.5)

---

## 0. 设计原则（Why 这份契约存在）

### 0.1 single source of truth

`GET /api/projects/{project_id}/chapters/{chapter_number}/status` 是前后端共识的**唯一状态源**。

- **Backend** 计算 `ui_phase` + `hydrate_hints` + `*_confirmed/ready` flags
- **Frontend** 仅**派生** state（URL / subPhase / hydrate URL / ETA reset），**不本地猜测、不本地缓存**

### 0.2 Ben 方案 A 落地背景

test15 e2e 暴露 13 真 RISK 中 **7 个 (47%)** 属于"前后端契约断裂"模式（T15-2/3/7/8/12/13）。Ben 5/13 15:42 微信提出"前后端纠验机制"，3 项配套落地：

| 配套 | 实现 |
|---|---|
| Backend status authoritative | 本契约 + `chapters.py` 实现 |
| Frontend state 派生 | `createUrl.ts` + `CreateContent.tsx` + `StageC.tsx` 实现 |
| Pre-commit hook 强制 commit label | `scripts/pre-commit-frontend-impact.sh` 实现 |

### 0.3 改契约必读规则

> ⚠️ **Backend 改任何 Wave 9 字段（ui_phase / hydrate_hints / *_confirmed / *_ready） 必须先 PR 改本文档 → 再 PR 改代码**

Pre-commit hook 已强制：改 `app/api/chapters.py` / `pipeline_orchestrator.py` / `job_manager.py` / `app/schemas/project.py` 等契约文件时，commit message 必须含 `[frontend-impact: yes/no]` label。

---

## 1. 主 endpoint: GET /chapters/{n}/status

### 1.1 Request

```
GET /api/projects/{project_id}/chapters/{chapter_number}/status
Headers:
  Authorization: Bearer {user_uuid}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `project_id` | string (UUID) | ✅ | 项目 UUID |
| `chapter_number` | int | ✅ | 章节编号 (当前 ≥ 1) |

### 1.2 Response Schema

完整 13 字段（**7 旧 + 6 新 Wave 9**）：

```typescript
interface ChapterStatus {
  // ============================================
  // 旧字段 (Wave 7 + 之前)
  // ============================================
  status: "pending" | "queued" | "generating" | "processing" | "completed" | "failed" | string | null;
  stage: string | null;                          // job.current_stage: "story_generation" | "character_design" | "character_ready" | "screenplay" | "scenes_ready" | "storyboard" | "image_preparation" | "image_generation" | "bgm" | "completed"
  progress: number;                              // 0-100
  estimated_remaining_seconds: number | null;    // dynamic ETA (含 stage-aware 计算)
  message: string | null;                        // 人类可读的当前活动描述（如 "已生成 6/23 张图像..."）
  failed_shot_count: number;                     // 失败的 shot 数（mid-stage 实时累加，Wave 9 后）
  partial_failure: boolean;                      // failed_shot_count > 0 时为 true

  // ============================================
  // v1.1 新字段 (RISK-T20-13 — 2026-05-19 加, Frontend Wave 2 useETA 消费)
  // ============================================
  shots_total: number | null;                    // Stage 4 完成后总 shot 数（= actual_shot_count, 语义独立）
  shots_completed: number | null;
    // 已完成的 shot 数 (成功 + 失败合计)
    // - 早期 stage (outline/character_design/screenplay/storyboard/image_preparation): 0 或 null
    // - image_generation: 实时累加 (从 message regex "已生成 X/Y" 解析)
    // - **bgm / postprocess / finalize / completed (T20-44 新行为)**: 保留 shots_total 不重置
    //   即 shots_completed == shots_total, 表示所有 shot 已处理完 (不应当作"还在生图")
    // 详见 §1.4 跨阶段值表
  shots_failed: number | null;                   // 已失败的 shot 数 (= job.failed_shot_count, 复用避免重复)

  // ============================================
  // 新字段 (Wave 9 / DEC-030 — 本契约新增)
  // ============================================
  ui_phase: UiPhase;                             // frontend 应该看哪个 UI 阶段（v1.4 起 9 状态机，见 §2）
  hydrate_hints: HydrateHints | null;            // 当前阶段应 hydrate 哪个 endpoint（见 §3）
  characters_confirmed: boolean;                 // project.characters_confirmed 直读 — R4-1 闸门
  scenes_confirmed: boolean;                     // project.scenes_confirmed 直读 — R4-2 闸门
  storyboard_ready: boolean;                     // chapter.storyboard_json 非空 — Stage 4 完成
  outline_ready: boolean;                        // chapter.full_script || chapter.scenes_json 非空 — Stage 1+ 完成

  // ============================================
  // v1.4 新字段 (T21-NEW-7 DEC-047 — 2026-05-21 Founder 决方案 D)
  // ============================================
  scene_references_ready: boolean;               // chapter.scene_references_json 非空 — Stage 4.5 完成
  scene_references_confirmed: boolean;           // project.scene_references_confirmed 直读 — R4-3 闸门
}

type UiPhase =
  | "input"
  | "outline_review"
  | "char_review_pending"
  | "char_review"
  | "scene_review_pending"
  // "scene_review" REMOVED v1.5 (T22-NEW-5): R4-2 wait loop 移除，scene_review ui_phase 不再存在
  | "storyboard_running"
  | "scene_references_review"   // v1.4 新增 (T21-NEW-7 DEC-047): Stage 4.5 完成 R4-3 等用户确认场景参考图
  | "shot_generating"
  | "completed";

interface HydrateHints {
  endpoint: string;            // 含 {project_id} 占位符的 URL 模板
  display_field: string;       // frontend 应渲染 response 的哪个字段
  expected_data_shape: string; // 该字段的预期类型，frontend type guard 用
}
```

### 1.3 Response 完整示例（4 phase）

#### Example A: `ui_phase = "char_review"`

```json
{
  "status": "processing",
  "stage": "character_ready",
  "progress": 10,
  "estimated_remaining_seconds": 1379,
  "message": "等待确认角色设计...",
  "failed_shot_count": 0,
  "partial_failure": false,
  "ui_phase": "char_review",
  "hydrate_hints": {
    "endpoint": "/api/projects/{project_id}/chapters/1/characters",
    "display_field": "characters",
    "expected_data_shape": "list[Character]"
  },
  "characters_confirmed": false,
  "scenes_confirmed": false,
  "storyboard_ready": false,
  "outline_ready": true
}
```

#### Example B: `ui_phase = "scene_review"` (顺解 T15-3 核心场景)

```json
{
  "status": "processing",
  "stage": "scenes_ready",
  "progress": 35,
  "estimated_remaining_seconds": 1166,
  "message": "等待确认场景设计...",
  "failed_shot_count": 0,
  "partial_failure": false,
  "ui_phase": "scene_review",
  "hydrate_hints": {
    "endpoint": "/api/projects/{project_id}/chapters/1/story",
    "display_field": "scenes",
    "expected_data_shape": "list[Scene]"
  },
  "characters_confirmed": true,
  "scenes_confirmed": false,
  "storyboard_ready": false,
  "outline_ready": true
}
```

⚠️ **注意**: scene_review 阶段 hydrate `/story` 而非 `/storyboard`（4_storyboard.json 此时还没生成）。这是 **顺解 RISK-T15-3** 的关键。

#### Example C: `ui_phase = "shot_generating"`

```json
{
  "status": "processing",
  "stage": "image_generation",
  "progress": 75,
  "estimated_remaining_seconds": 350,
  "message": "已生成 6/23 张图像...",
  "failed_shot_count": 0,
  "partial_failure": false,
  "ui_phase": "shot_generating",
  "hydrate_hints": {
    "endpoint": "/api/projects/{project_id}/chapters/1/storyboard",
    "display_field": "shots",
    "expected_data_shape": "list[Shot]"
  },
  "characters_confirmed": true,
  "scenes_confirmed": true,
  "storyboard_ready": true,
  "outline_ready": true
}
```

#### Example D: `ui_phase = "completed"`

```json
{
  "status": "completed",
  "stage": "completed",
  "progress": 100,
  "estimated_remaining_seconds": 0,
  "message": "故事生成完成！",
  "failed_shot_count": 1,
  "partial_failure": true,
  "ui_phase": "completed",
  "hydrate_hints": {
    "endpoint": "/api/projects/{project_id}/chapters/1/storyboard",
    "display_field": "shots",
    "expected_data_shape": "list[Shot]"
  },
  "characters_confirmed": true,
  "scenes_confirmed": true,
  "storyboard_ready": true,
  "outline_ready": true
}
```

### 1.4 shots_completed 跨阶段值表 (T20-44 新行为, v1.3)

> **背景**: T20-44 (5/20) 修复 BGM/postprocess/finalize/completed 阶段 shots_completed 被重置为 0 的 bug。
> 修复后行为: 上述后期 stage 进入时保留 shots_total 值（不重置）。

| stage | shots_completed 期望值 | 说明 |
|---|---|---|
| `story_generation` | `null` 或 `0` | Stage 1 跑中，无 shot 信息 |
| `character_design` | `null` 或 `0` | Stage 2 跑中，无 shot 信息 |
| `screenplay` | `null` 或 `0` | Stage 3 跑中，无 shot 信息 |
| `storyboard` | `null` 或 `0` | Stage 4 跑中，shots_total 尚未确定 |
| `image_preparation` | `0` | shots_total 确定，生图尚未开始 |
| `image_generation` | `0..shots_total` | **实时累加** (regex "已生成 X/Y") |
| `bgm` | **`shots_total`** (T20-44) | 所有 shot 已处理完，BGM 阶段不重置 |
| `completed` | **`shots_total`** (T20-44) | Pipeline 完成，保留最终值 |

**Frontend useETA.ts 注意事项** (T20-44 配套):
- `bgm` 阶段 `shots_completed == shots_total` **不代表"还在生图"**
- ETA 计算此时应切换为 BGM baseline 算法 (`_V3_BGM_BASELINE_SECONDS=120`)，不再用 `(shots_total - shots_completed) * per_shot`
- Backend `_compute_v3_eta()` 已正确处理此逻辑（chapters.py）
- Frontend 直接读 backend `estimated_remaining_seconds` 即可，无需本地 ETA 计算

---

## 2. ui_phase 8 状态机详解

### 2.1 转换图 (v1.5 T22-NEW-5: scene_review 已移除, Stage 3→4 直连)

```
┌──────────┐
│  input   │  没 confirmed_outline + 没 raw_outline
└────┬─────┘
     │ user POST /create-project
     ▼
┌───────────────┐
│ outline_review│ raw_outline 有但还没 confirm; 或 confirmed_outline 有但 job 还没启动
└────┬──────────┘
     │ POST /confirm-outline + Pipeline 启动
     ▼
┌──────────────────────┐
│ char_review_pending  │  Stage 1/2 跑中 (story_generation / character_design)
└────┬─────────────────┘
     │ Stage 2 完成 (character_ready)
     ▼
┌──────────────┐
│ char_review  │  R4-1 等用户确认角色
└────┬─────────┘
     │ user POST /confirm-characters → project.characters_confirmed=True
     ▼
┌───────────────────────┐
│ scene_review_pending  │  Stage 3 (screenplay) 跑中
└────┬──────────────────┘
     │ Stage 3 完成 → 直接进 Stage 4 (T22-NEW-5: R4-2 砍掉)
     ▼
┌──────────────────────┐
│ storyboard_running   │  Stage 4 (storyboard) 跑中
└────┬─────────────────┘
     │ Stage 4 完成 → 自动进 Stage 4.5 (T21-NEW-7 v1.4)
     ▼
┌──────────────────────────┐
│ storyboard_running       │  Stage 4.5 (scene_image_preparation) 跑中
│ (复用 UI, stage 字段不同) │  真生成所有 interior+exterior anchor
└────┬─────────────────────┘
     │ Stage 4.5 完成 (scene_references_ready, R4-3)
     ▼
┌─────────────────────────────┐
│ scene_references_review     │  R4-3 等用户确认场景参考图 (视觉确认, 60s 倒计时)
└────┬────────────────────────┘  Founder 决方案 D, 镜像 characters 页面对偶设计
     │ user POST /confirm-scene-references → project.scene_references_confirmed=True
     ▼
┌──────────────────┐
│ shot_generating  │  Stage 5 (image_preparation fullbody+shots / image_generation / bgm)
└────┬─────────────┘
     │ Pipeline finalize
     ▼
┌─────────────┐
│  completed  │  全跑完
└─────────────┘
```

**T22-NEW-5 架构说明**:
- `scene_review` ui_phase 已从状态机移除 (Founder 5/22 13:37 决策)
- `scenes_confirmed` DB 列保留 (向后兼容 + 不做 Alembic migration)，运行时不再用作 Pipeline 闸门
- `confirm-scenes` endpoint 保留为 noop (向后兼容旧 frontend)，不更新 DB / 不阻塞 Pipeline
- scenes_ready stage → 直接 storyboard_running (不再停在 scene_review 等用户点确认)

### 2.2 每个 phase 详细

#### `input`

| 项 | 值 |
|---|---|
| **触发条件** | 没 job 或 job.status="pending" + 没 raw_outline + 没 confirmed_outline |
| **典型场景** | 用户刚创建 project，还没生成大纲 |
| **frontend URL** | `/create` |
| **hydrate_hints** | `null` (无内容数据可 hydrate) |
| **用户视觉** | StageA 输入界面（idea + style + 时长 + 情绪基调）|
| **验收点** | URL 是 /create + 显示 StageA 输入 form |

#### `outline_review`

| 项 | 值 |
|---|---|
| **触发条件** | (a) raw_outline 有但 confirmed_outline 还没有；或 (b) confirmed_outline 有但 job 还没启动 |
| **典型场景** | Stage 1 大纲生成完成（96s），用户在 StageB 看大纲调整角色/情节/结局 |
| **frontend URL** | `/create/{uuid}/outline` |
| **hydrate_hints** | `null`（前端用 project.raw_outline_json 已 hydrate）|
| **用户视觉** | StageB 大纲确认页面 |
| **验收点** | URL 是 /create/{uuid}/outline + 显示大纲 + 角色/情节/结局/情绪基调可调 |

#### `char_review_pending`

| 项 | 值 |
|---|---|
| **触发条件** | stage in (`story_generation`, `character_design`) |
| **典型场景** | Stage 1 / 2 LLM 跑中 (~3 min) |
| **frontend URL** | `/create/{uuid}/generating` |
| **hydrate_hints** | `null`（用户等内容生成）|
| **用户视觉** | 进度条 + "正在设计角色..." 消息 + ETA |
| **验收点** | URL 是 /generating + progress 涨 + 无"后台生成"按钮 |

#### `char_review`

| 项 | 值 |
|---|---|
| **触发条件** | stage == `character_ready` && project.characters_confirmed == false |
| **典型场景** | Stage 2 完成 + portraits 生成完，R4-1 等用户确认 |
| **frontend URL** | `/create/{uuid}/characters` |
| **hydrate_hints** | `{ endpoint: ".../characters", display_field: "characters", expected_data_shape: "list[Character]" }` |
| **用户视觉** | 角色卡（含 portrait + name + physical + clothing） + "确认并继续" 按钮 |
| **验收点** | URL 是 /characters + 角色卡列表 + 可编辑/调整发色等 |

#### `scene_review_pending`

| 项 | 值 |
|---|---|
| **触发条件** | stage == `screenplay`，或 stage == `character_ready` && project.characters_confirmed == true（瞬态过渡）|
| **典型场景** | Stage 3 ScreenplayWriter 跑中 (~3-4 min) |
| **frontend URL** | `/create/{uuid}/generating` |
| **hydrate_hints** | `null` |
| **用户视觉** | 进度条 + "正在编写分场剧本..." |
| **验收点** | URL 是 /generating + 无"后台生成"按钮 |

#### ~~`scene_review`~~ (v1.5 T22-NEW-5: REMOVED)

> **已废弃** (2026-05-22): Founder 决策 R4-2 场景文字确认环节砍掉。
> scenes_ready stage 现在直接 → storyboard_running，不再停在 scene_review 等用户确认。
> `scenes_confirmed` DB 列保留（向后兼容），`confirm-scenes` endpoint 保留为 noop。

#### `storyboard_running`

| 项 | 值 |
|---|---|
| **触发条件** | stage == `storyboard`，或 stage == `scenes_ready` && project.scenes_confirmed == true（瞬态过渡）|
| **典型场景** | Stage 4 StoryboardDirector 跑中 (~3 min) |
| **frontend URL** | `/create/{uuid}/generating` |
| **hydrate_hints** | `null` |
| **用户视觉** | 进度条 + "正在创建分镜..." |
| **验收点** | URL 是 /generating + 无"后台生成"按钮 |

#### `scene_references_review` (⭐ v1.4 T21-NEW-7 DEC-047 新增)

| 项 | 值 |
|---|---|
| **触发条件** | stage == `scene_references_ready` && project.scene_references_confirmed == false |
| **典型场景** | Stage 4.5 (scene_image_preparation) 完成, 所有 interior+exterior anchor 真生成完成, R4-3 等用户在 /scenes 页面真预览/编辑/重生场景参考图 (60s 倒计时) |
| **frontend URL** | `/create/{uuid}/scenes` (与 scene_review 复用, 但 hydrate 不同 endpoint) |
| **hydrate_hints** | `{ endpoint: ".../scene-references", display_field: "scene_references", expected_data_shape: "list[SceneReference]" }` |
| **用户视觉** | 场景参考图卡片列表 (每 location 显示 interior + exterior 2 张图) + 编辑文字描述按钮 + "重生" 按钮 + 60s 倒计时 + "确认场景继续" 按钮 (镜像 characters 页面对偶设计) |
| **验收点** | URL 是 /scenes + 显示场景参考图卡片 + 可编辑/重生 + 60s 倒计时 |
| **为什么有这个 phase** | Founder 5/21 决方案 D: "情节确认 ≠ 场景视觉确认", 情节在 scene_review (R4-2) 已确认, 此 phase 是真"场景视觉确认", 跟 characters 页面对称, 让用户审美统一 |

#### `shot_generating`

| 项 | 值 |
|---|---|
| **触发条件** | stage in (`image_preparation`, `image_generation`, `bgm`) — T21-NEW-7 v1.4 后 image_preparation 只剩 fullbody + shots 调度 (场景参考图已在 Stage 4.5 完成) |
| **典型场景** | Stage 5 fullbody+shots (~5 min) + Stage 6 BGM (~2 min) |
| **frontend URL** | `/create/{uuid}/generating` |
| **hydrate_hints** | `{ endpoint: ".../storyboard", display_field: "shots", expected_data_shape: "list[Shot]" }` |
| **用户视觉** | 进度条 + "已生成 N/M 张图像..." + **"后台生成，去做别的"按钮**显示（用户已过三个 checkpoint: R4-1 + R4-2 + R4-3）|
| **验收点** | URL 是 /generating + progress 涨 + 后台按钮显示 |

#### `completed`

| 项 | 值 |
|---|---|
| **触发条件** | job.current_stage == "completed" 或 job.status == "completed" |
| **典型场景** | Pipeline 全跑完，自动跳 /preview |
| **frontend URL** | `/create/{uuid}/preview`（**特例**: 如 URL 已是 `/delivery` 保持 `/delivery`，不跳回 /preview）|
| **hydrate_hints** | `{ endpoint: ".../storyboard", display_field: "shots", expected_data_shape: "list[Shot]" }` |
| **用户视觉** | 23 张完整成片 + BGM + 单 shot 重生/删除/编辑文字按钮 + 下载/打包 |
| **验收点** | URL 是 /preview + 显示 shots + 可重生失败 shot |

### 2.3 partial_failure 标识

`partial_failure = true` 时（如 22/23 张成功 + 1 张失败），ui_phase 仍是 `completed`，frontend 显示横幅 "22/23 张生成成功，1 张未生成" + 可点单 shot 重生（已 Wave 9 修 T15-12/13: 重生成功后 failed_shot_count 自动 -=1）。

---

## 3. hydrate_hints 设计详解

### 3.1 字段含义

```typescript
interface HydrateHints {
  endpoint: string;
  display_field: string;
  expected_data_shape: string;
}
```

| 字段 | 含义 | 示例 |
|---|---|---|
| `endpoint` | URL 模板（含 `{project_id}` 占位符，frontend 需 replace 后 fetch）| `/api/projects/{project_id}/chapters/1/story` |
| `display_field` | response JSON 的哪个字段含展示数据 | `scenes` |
| `expected_data_shape` | 该字段的预期 TypeScript 类型，frontend type guard 用 | `list[Scene]` |

### 3.2 完整映射表

| ui_phase | hydrate_hints |
|---|---|
| `input` / `outline_review` / `char_review_pending` / `scene_review_pending` / `storyboard_running` | `null` |
| `char_review` | `{ endpoint: ".../characters", display_field: "characters", expected_data_shape: "list[Character]" }` |
| ~~`scene_review`~~ | ~~`{ endpoint: ".../story", display_field: "scenes", ... }`~~ **v1.5 REMOVED** |
| `scene_references_review` (v1.4) | `{ endpoint: ".../scene-references", display_field: "scene_references", expected_data_shape: "list[SceneReference]" }` ⭐ T21-NEW-7 DEC-047 |
| `shot_generating` / `completed` | `{ endpoint: ".../storyboard", display_field: "shots", expected_data_shape: "list[Shot]" }` |

### 3.3 frontend 如何用

```typescript
// frontend pseudo-code
const status = await fetchStatus(projectId, chapterNumber);
if (status.hydrate_hints) {
  const url = status.hydrate_hints.endpoint.replace("{project_id}", projectId);
  const response = await fetch(url);
  const data = response.json();
  const displayData = data[status.hydrate_hints.display_field];
  // type guard with expected_data_shape
  render(displayData);
}
```

---

## 4. 配套 endpoint 契约

### 4.1 GET /chapters/{n}/story (⭐ Wave 9 顺解 T15-3 改造)

**关键变化（Wave 9）**: 旧逻辑当 `chapter.status == "generating_story"` 直接 404 → 新逻辑优先检查 `chapter.scenes_json` 非空。

| 阶段 | Response |
|---|---|
| 没 chapter / status="pending" | HTTP 404 "故事尚未开始生成" |
| Stage 3 跑中（scenes_json 空 + full_script 空）| HTTP 404 "故事正在生成中，请稍候" |
| **scenes_ready（scenes_json 有 + storyboard_json 空）** | **HTTP 200 + `{ scenes, characters }`** ⭐ Wave 9 改造 |
| completed（storyboard_json 有）| HTTP 200 + `{ scenes, shots, characters, title, summary, full_script }` |
| failed | HTTP 400 + error_message |

实现位置: `app/api/chapters.py` L395-430

### 4.2 GET /chapters/{n}/storyboard

| 阶段 | Response |
|---|---|
| `storyboard_ready=false` | HTTP 404 "分镜数据尚未生成" |
| `storyboard_ready=true` | HTTP 200 + `{ storyboard: { shots: [...], ... }, chapter_number, project_id }` |

实现位置: `app/api/chapters.py` L348-421

### 4.3 GET /chapters/{n}/characters

| 阶段 | Response |
|---|---|
| `characters_json` 空 | HTTP 404 |
| `characters_json` 有 | HTTP 200 + `{ characters: [{ id, name, physical, clothing, portrait_url, fullbody_url, ... }] }` |

### 4.4 GET /chapters/{n}/scene-references ⭐ T21-NEW-7 v1.4 DEC-047

| 阶段 | Response |
|---|---|
| `scene_references_json` 空 (Stage 4.5 未跑) | HTTP 200 + `{ scene_references: [], scene_references_ready: false, scene_references_confirmed: false, countdown_seconds: 60, ... }` |
| `scene_references_json` 有 | HTTP 200 + 完整 scene_references list |

**Response schema**:
```typescript
{
  scene_references: SceneReference[];
  scene_references_ready: boolean;        // chapter.scene_references_json 非空
  scene_references_confirmed: boolean;    // project.scene_references_confirmed
  countdown_seconds: number;              // 60 (镜像 characters 页面 60s 倒计时)
  chapter_number: number;
  project_id: string;
}

interface SceneReference {
  location_id: string;                    // 来自 outline.unique_locations[].location_id
  location_zh: string;                    // display_name (中文)
  interior_url: string | null;            // /static/.../scene_refs/xxx_interior_anchor.png?v={epoch}
  exterior_url: string | null;            // /static/.../scene_refs/xxx_exterior_anchor.png?v={epoch}
  interior_description: string;           // 原 outline interior_description (可被 user_edit 覆盖)
  exterior_description: string;
  description_zh: string;                 // 组合描述 (location_zh - interior/exterior_description)
  atmosphere: string;                     // 氛围 (如 "mechanical_eerie")
  time_of_day: string;                    // 时段 (如 "night")
  lighting_condition: string;             // 光照 (如 "neon_cold_blue")
  key_visual_elements: string[];          // 关键视觉元素列表
}
```

实现位置: `app/api/chapters.py:get_scene_references`

### 4.5 POST /chapters/{n}/scenes/{location_id}/regenerate-reference ⭐ T21-NEW-7 v1.4 DEC-047

重生单个场景参考图 (interior / exterior / both), 支持用户编辑描述触发重生.

**Request body**:
```typescript
{
  ref_type: "interior" | "exterior" | "both";   // 默认 "both"
  user_edit?: string;                            // 可选, 用户改的中文场景描述
}
```

**Response**:
```typescript
{
  success: true;
  location_id: string;
  interior_url: string | null;     // ref_type 涉及 interior 才有, 带 ?v={epoch} cache-buster
  exterior_url: string | null;     // ref_type 涉及 exterior 才有, 带 ?v={epoch}
  message: string;                  // "场景参考图已重新生成 (ref_type=both)"
}
```

**行为**:
- 重生 interior + exterior 时, exterior 用刚生成的 interior 作参考图 (DEC-014/DEC-009 一致性)
- 只重生 exterior 时, 用 disk 现有 interior 作参考
- 更新 chapter.scene_references_json 中对应 location 条目 (URL 带 cache-buster, 防 frontend cache)
- 镜像 AdjustCharacter / RegeneratePortrait 模式

实现位置: `app/api/chapters.py:regenerate_scene_reference`

### 4.6 POST /chapters/{n}/confirm-scene-references ⭐ T21-NEW-7 v1.4 DEC-047 (R4-3 闸门)

用户确认场景参考图 → Pipeline R4-3 wait loop 跳出, 解锁 Stage 5 fullbody+shots.

**Request body**: 空 (无 payload)

**Response**:
```typescript
{
  success: true;
  scene_references_confirmed: true;
  next_stage: "image_generation";
}
```

**行为**:
- 验证 chapter.scene_references_json 非空 (Stage 4.5 必须已完成, 否则 409)
- 设置 project.scene_references_confirmed = True
- Pipeline R4-3 wait loop (pipeline_orchestrator.py, 轮询 2s 一次) 检测到 True 跳出循环, 进 Stage 5
- 与 R4-1 (/confirm-characters), R4-2 (/confirm-scenes) 对称模式

实现位置: `app/api/chapters.py:confirm_scene_references`

---

## 5. Backend 改契约规则（强约束）

### 5.1 规则 1: 加/改字段必须先 PR 文档

任何 `ChapterStatus` schema 字段变更（加/删/改类型）必须：

1. 先 PR 改本契约文档 (`STATUS_API_CONTRACT.md`)
2. 通知 Frontend agent（@frontend 在 TEAM_CHAT 标记 或 Founder 触发 Frontend agent task）
3. 再 PR 改代码 (`app/api/chapters.py` + `app/schemas/chapter.py`)
4. commit message 含 `[frontend-impact: yes]` label

### 5.2 规则 2: 改 ui_phase 状态机必须升级版本号

改 `_derive_ui_phase` 逻辑（如加新 phase / 改触发条件）必须：

1. 升级本文档 v1.0 → v1.1
2. 同步更新 §2 转换图 + §2.2 详细
3. Frontend `UI_PHASE_TO_URL` 必须同步加映射，否则 fallback 到 `generating`
4. 写新单测 in `tests/test_status_authoritative.py`

### 5.3 规则 3: pre-commit hook 强制

`scripts/pre-commit-frontend-impact.sh` 监控 6 个契约文件：
- `app/api/projects.py`
- `app/api/chapters.py`
- `app/services/pipeline_orchestrator.py`
- `app/services/job_manager.py`
- `app/models/project.py`
- `app/schemas/project.py`

改其中任一文件 commit 时必须含 `[frontend-impact: yes/no]` label 否则 hook block。安装：`bash scripts/install_pre_commit_hook.sh`

### 5.4 规则 4: 旧字段保留向后兼容

不可删除现有的 7 个旧字段（status/stage/progress/message/estimated_remaining_seconds/failed_shot_count/partial_failure），frontend 老代码可能仍依赖。新字段加 default value 保 backward compat。

---

## 6. Frontend 派生规则

### 6.1 URL 派生

```typescript
// frontend/src/lib/createUrl.ts L151
const UI_PHASE_TO_URL: Record<UiPhase, UrlStage> = {
  "input": "outline",                  // 或 "create"
  "outline_review": "outline",
  "char_review_pending": "generating",
  "char_review": "characters",
  "scene_review_pending": "generating",
  // "scene_review": "scenes" — v1.5 REMOVED (T22-NEW-5): Frontend Wave 8 已从 createUrl.ts 删除
  "storyboard_running": "generating",
  "shot_generating": "generating",
  "completed": "preview",
};

// reconcileBackendVsUrl 优先用 ui_phase
if (input.uiPhase) {
  // 特例: completed + URL=delivery → keep delivery
  if (input.uiPhase === "completed" && input.urlStage === "delivery") {
    return "delivery";
  }
  return UI_PHASE_TO_URL[input.uiPhase] ?? "generating";
}
// fallback 到 legacy heuristic（向后兼容）
```

### 6.2 subPhase 派生

```typescript
// CreateContent.tsx Watcher 5s tick
const phaseToSubPhase: Record<UiPhase, GenerationSubPhase> = {
  "char_review_pending": "text-gen",
  "char_review": "char-preview",
  "scene_review_pending": "text-gen",
  // "scene_review": "scene-preview" — v1.5 REMOVED (T22-NEW-5)
  "storyboard_running": "shot-gen",   // 或 "text-gen" 看产品决策
  "shot_generating": "shot-gen",
  "completed": "completed",
};
```

⚠️ **顺解 T15-8**: subPhase 必须从 `status.ui_phase` 派生，不依赖 user click handlers。这样 PM 直接 `curl POST /confirm-scenes` 解 R4-2 时 frontend 也能正确切换。

### 6.3 hydrate URL 派生

```typescript
const hydrateEndpoint = status?.hydrate_hints?.endpoint;
if (hydrateEndpoint) {
  const url = hydrateEndpoint.replace("{project_id}", projectId);
  const data = await fetch(url).then(r => r.json());
  const displayData = data[status.hydrate_hints.display_field];
  // ...render
}
```

### 6.4 ETA monotonicity guard 监听 stage 切换重置

```typescript
// StageC.tsx L187
const lastStageRef = useRef<string | null>(null);

useEffect(() => {
  const currentStage = status?.stage;
  if (lastStageRef.current && currentStage && lastStageRef.current !== currentStage) {
    // Wave 9 / DEC-030: backend stage 切换时重置 ETA guard
    // 允许新 stage 的 ETA 自然跳变（不再被旧 stage 的 lastEta 压缩）
    lastEtaSecondsRef.current = null;
  }
  lastStageRef.current = currentStage ?? null;
}, [status?.stage]);
```

⚠️ **顺解 T15-7**: 之前 UX-7 guard 永远不允许 ETA 上调 → 阶段切换时 ETA 被压到 ≤0 不显示。Wave 9 修复让 ETA 在新 stage 自然显示。

### 6.5 failed_shot_count 直读

```typescript
// 不本地缓存，每次 render 从 status 直读
const showPartialFailureBanner = status?.partial_failure && status?.failed_shot_count > 0;
```

⚠️ **顺解 T15-12**: regenerate 成功后 backend 自动 -=1（已 Wave 9 修复），frontend 直读 status 保持同步。

---

## 7. 实现位置（代码 reference）

### 7.1 Backend

| 文件 | 实现内容 | 行号 |
|---|---|---|
| `app/schemas/chapter.py` | `HydrateHints` class + `ChapterStatus` 6 新字段定义 | L8 / L47-52 |
| `app/api/chapters.py` | `_derive_ui_phase()` 8 状态机 | L47-113 |
| `app/api/chapters.py` | `_build_hydrate_hints()` 4 endpoint 映射 | L116-156 |
| `app/api/chapters.py` | status endpoint 两个 return 路径填新字段 | L265-279 / L337-356 |
| `app/api/chapters.py` | GET /story 顺解 T15-3 (scenes_review 阶段返 scenes) | L395-430 |
| `app/services/job_manager.py` | `increment_failed_shot_count(job_id)` async helper | L139-189 |
| `app/services/pipeline_orchestrator.py` | `pipeline.run(job_id=...)` 参数 + Stage 5 fail path 调 increment | L317 / L1278-1287 / L1365-1372 |

### 7.2 Frontend

| 文件 | 实现内容 | 行号 |
|---|---|---|
| `frontend/src/lib/createUrl.ts` | `UI_PHASE_TO_URL` 8 映射 + `reconcileBackendVsUrl` 加 uiPhase 参数 | L151 / L183-227 |
| `frontend/src/app/create/CreateContent.tsx` | `HydrateHints` interface + Watcher subPhase 派生 | L474 / L1167-1370 |
| `frontend/src/components/create/StageC.tsx` | `lastStageRef` + ETA reset useEffect | L187 / L236-247 |

### 7.3 测试

| 文件 | 覆盖 |
|---|---|
| `tests/test_status_authoritative.py` | 44 单测：ui_phase 派生 (18) / hydrate_hints (9) / GET /story (5) / mid-stage failed_count (4) / schema (8) |
| `tests/test_shot_regenerate_persistence.py` | 9 单测：regenerate 后 failed_count -=1 + 5_image_results.json 回写 + ApiCost project_id |

### 7.4 DevOps

| 文件 | 作用 |
|---|---|
| `scripts/pre-commit-frontend-impact.sh` | git pre-commit hook 监控契约文件 |
| `scripts/install_pre_commit_hook.sh` | 一键安装 hook symlink |
| `docs/CONTRACT_HOOK.md` | hook 使用文档 |

---

## 8. 历史 / 版本

### v1.5 (2026-05-22) T22-NEW-5 — scene_review ui_phase 移除, R4-2 wait loop 移除 [frontend-impact: yes]

- **决策**: Founder 5/22 13:37 反馈 "/scenes 文字层场景确认页用户无修改意愿，可以跳过"。14:50 升级为内测前必修。
- **架构改动**:
  - **Pipeline**: `pipeline_orchestrator.py` R4-2 wait loop 完整移除。Stage 3 完成后直接进 Stage 4 (storyboard)，无需等用户点"确认场景"。
  - **ui_phase 状态机**: 9 → 8 个状态。`scene_review` 移除，`scenes_ready` stage 直接映射 `storyboard_running`。
  - **`_derive_ui_phase`**: 移除 `scenes_ready → scene_review` 分支，改为 `scenes_ready → storyboard_running`（直接）。
  - **`_build_hydrate_hints`**: 移除 `scene_review` hydrate 分支。
  - **`confirm-scenes` endpoint**: 在 `chapters.py` 添加 noop endpoint（`/{chapter_number}/confirm-scenes`），直接返 200 + deprecation warning，不更新 DB。向后兼容旧 frontend 调用。
- **保留 (向后兼容)**:
  - `scenes_confirmed` DB 列保留（不做 Alembic migration），运行时不再用作 Pipeline 闸门
  - `scenes_confirmed` 字段仍在 status response 中返回（backward compat，前端仍可读）
  - R4-1 (character_review) + R4-3 (scene_references_review) wait loop 完整保留
- **Frontend 行动 (Wave 8 #2 T22-NEW-5 已完成)**:
  - `frontend/src/types/create.ts`: 删 `"scene-preview"` GenerationSubPhase
  - `frontend/src/lib/createUrl.ts`: 删 `scene_review: "scenes"` mapping
  - `frontend/src/app/create/CreateContent.tsx`: 删 `scene_review` → `"scene-preview"` mapping + `isSceneReview` force-route block
  - `frontend/src/components/create/StageC.tsx`: 删 `handleConfirmScenes` + `scene-preview` render block
  - `frontend/src/components/create/StageB.tsx`: 更新 D.14 progressStage 三元
- **转换图**: outline_review → character_design → char_review → scene_review_pending → **storyboard_running** → scene_references_review → shot_generating → completed (跳过 scene_review)
- **测试**: `tests/test_t22_new_5_r4_2_removed.py` (新建, 含 Stage 3→4 直连 + _derive_ui_phase 不返 scene_review + confirm-scenes noop + status response 验证)
- **部署**: Frontend (Wave 8 #2) + Backend (本任务) 必须**同时部署**，否则状态机不一致

### v1.4 (2026-05-21) T21-NEW-7 DEC-047 — Stage 4.5 scene_image_preparation 引入 + R4-3 闸门

- **决策**: Founder 5/21 18:25 决方案 D — 场景视觉确认作为用户旅程独立停留点 (与"情节确认" R4-2 区分), 跟 characters 页面对偶设计.
- **架构改动**:
  - Pipeline 新增 **Stage 4.5 `scene_image_preparation`** (在 Stage 4 完成 + Stage 5 之前):
    - 真生成所有 interior + exterior anchor (`SceneReferenceManager.generate_anchor_images`)
    - 写 `chapter.scene_references_json` (新字段)
    - 进入 **R4-3 wait loop** 等用户确认 (轮询 `project.scene_references_confirmed`, 超时 1800s)
  - **Stage 5 image_preparation 简化**: 不再生成场景参考图 (Stage 4.5 已做), 只剩 fullbody + shots 调度. ETA baseline 420s → 270s.
  - Pipeline Stage 5 5a.5 改 "复用 Stage 4.5 scene_ref_manager", 保留兜底路径 (Stage 4.5 异常时重生).
- **新 ui_phase**: `scene_references_review` (Stage 4.5 后 R4-3 等待状态)
- **新字段** (ChapterStatus schema):
  - `scene_references_ready: bool` — chapter.scene_references_json 非空 → True (Stage 4.5 完成)
  - `scene_references_confirmed: bool` — project.scene_references_confirmed 直读 (R4-3 闸门)
- **新 endpoint** (3):
  - `GET /chapters/{n}/scene-references` (§4.4)
  - `POST /chapters/{n}/scenes/{location_id}/regenerate-reference` (§4.5)
  - `POST /chapters/{n}/confirm-scene-references` (§4.6)
- **DB 改动** (Alembic 006_add_scene_references_t21_new7):
  - `projects.scene_references_confirmed` (Boolean, default=False)
  - `project_chapters.scene_references_json` (LONGTEXT, nullable=True)
  - Backfill: 已完成 Stage 5+ 老项目 scene_references_confirmed=True (防卡 R4-3)
- **start_generation 重置**: project.scene_references_confirmed = False (与 R4-1/R4-2 一致)
- **Pipeline progress bounds**: storyboard (35-60), scene_image_preparation (60-63), scene_references_ready (63-63), image_preparation (63-70), image_generation (70-92)
- **Frontend 行动** (Wave II Frontend agent):
  - 消费 ui_phase=`scene_references_review` 在 /scenes 页面真预览场景参考图卡片
  - 编辑文字描述 + "重生" 按钮 (调 POST regenerate-reference, ref_type 选 interior/exterior/both)
  - 60s 倒计时 (镜像 characters 页面 60s 倒计时)
  - "确认场景继续" 按钮 (调 POST confirm-scene-references)
  - createUrl.ts `UI_PHASE_TO_URL` 加 `scene_references_review: "scenes"` 映射
- **DEC-014 / DEC-009 保留**: interior/exterior 一致性逻辑真保留 (regenerate exterior 时用 interior 作参考)
- **向后兼容**: 老 frontend 不消费新字段 → 仍走 legacy heuristic, 行为不破坏. R4-3 wait loop 超时 1800s 自动继续, 防卡死.
- **测试**: tests/test_t21_new_3_to_7_backend.py 51 PASS (含 T21-NEW-3/4/5/6/7 全覆盖)
- **DEC**: DECISIONS.md DEC-047 (新增)
- **Backend 改动文件**:
  - app/models/project.py (+ scene_references_confirmed)
  - app/models/chapter.py (+ scene_references_json)
  - app/schemas/chapter.py (+ 2 字段)
  - app/services/pipeline_orchestrator.py (Stage 4.5 + R4-3 + Stage 5 简化 + STAGE_DURATIONS)
  - app/services/scene_reference_manager.py (sub_progress_callback 参数)
  - app/services/job_manager.py (_ETA_STAGE_BASELINES + _ETA_STAGE_PROGRESS_BOUNDS 9 stage)
  - app/api/chapters.py (3 新 endpoint + _derive_ui_phase + _build_hydrate_hints + status return)
  - app/api/projects.py (start_generation 重置)
  - alembic/versions/006_add_scene_references_t21_new7.py (新 migration)

### v1.3 (2026-05-20) T20-44 BGM 阶段不重置 shots_completed (schema 不变)

- **决策**: T20-44 (2026-05-20) 修复 `app/api/chapters.py` shots_completed 在 BGM/postprocess/finalize/completed 阶段被重置为 0 的 bug。
- **新增常量**: `_POST_IMAGE_GEN_STAGES = {"bgm", "postprocess", "finalize", "completed"}` — 这些阶段进入时 shots_completed 保留 shots_total 值而非重置。
- **schema 不变**: 字段名 / 字段类型 / 字段数量无任何变动。仅 shots_completed 在后期 stage 的行为描述更新。
- **更新内容**:
  - §1.2 `shots_completed` 字段注释：明确 8 个 stage × 期望值的行为说明
  - §1.4 新增跨阶段值表（8 行 × 期望值 + Frontend useETA.ts 注意事项）
- **Frontend 行动**: useETA.ts 在 bgm stage 检测到 `shots_completed == shots_total` 时，不应判断为"还在生图"，直接读 backend `estimated_remaining_seconds` 即可。
- **测试**: tests/test_t20_44_bgm_no_reset.py 21 PASS（Backend 5/20 17:19 完成）
- **向后兼容**: 旧字段全保留，早期 stage 行为不变，修复只影响 bgm/postprocess/finalize/completed 四个 stage。

### v1.2 (2026-05-19 18:30) RISK-T20-9.v3 estimated_remaining_seconds 算法升级 (schema 不变)

- **决策**: Founder 5/19 16:08 反馈 test17 v2 实测 4 项核心问题:
  1. progress=84% 但 Shot 14/20 才开始 — ETA 严重失真 (legacy 基于 progress 反推, 不信真实 shots_completed)
  2. 前后端 ETA 脱节, "前端在自说自话"
  3. progress >= 95% 显"即将完成"无具体 ETA — 终态 UX 灾难
  4. Stage 5 + Stage 6 BGM (~3min) + 后处理 (~30s) 必须算入剩余时间
- **算法升级** (chapters.py 新 `_compute_v3_eta` 接管 image_generation+ 阶段 ETA):
  - image_generation: `(shots_total - shots_completed) * 80 / max_concurrent + 120 (bgm) + 30 (postprocess)`
  - bgm: bgm baseline 按 (progress - 92) / 8 折扣 + postprocess
  - completed: 0
  - 早期 stage (shots_total=None) → 走原 legacy chain (向后兼容)
  - **v3 真实数据完全接管, 不被 legacy_eta 上限约束** (Founder 反馈核心修复)
  - 终态保底: progress >= 95% 仍返 >= 5s 具体数值, 不显"即将完成"
- **schema 不变**: `estimated_remaining_seconds: int | None` — 字段定义和类型不动, 只算法升级.
  Frontend useETA.ts 行动: 优先用 backend 这个字段 (现在更准), 不需要前端 fallback 算法.
- **Wave 1 已加字段 (T20-13) shots_total/completed/failed**: v3 算法直接消费, frontend 不需重复 regex 解析 message.
- **Backend 实现**:
  - chapters.py 新 `_compute_v3_eta()` helper (L134-230) + status endpoint v3 接管层 (L478-498)
  - 常量: `_V3_PER_SHOT_SECONDS=80` / `_V3_BGM_BASELINE_SECONDS=120` / `_V3_POSTPROCESS_BASELINE_SECONDS=30` / `_V3_TERMINAL_PHASE_MIN_ETA=5`
- **测试**: tests/test_t20_9_v3_eta.py 32 PASS + 102 regression PASS (status_authoritative + T20-13 + T20-9 + d2_eta_parallel)
- **向后兼容**: 旧字段全保留, 早期 stage 行为不变, 算法升级只在 image_generation/bgm/completed/image_preparation 阶段生效.

### v1.1 (2026-05-19) RISK-T20-13 加 3 shots_* 字段

- **决策**: test17 v2 实测 (5/19) Founder 反馈"前后端 ETA 完全脱节, 前端在自说自话". 根因: Backend status API 缺 shots_total/completed/failed 字段, Frontend 只能 regex parse `message` "已生成 X/Y" 算 ETA.
- **新字段**: `shots_total` / `shots_completed` / `shots_failed` (3 字段, 见 §1.2)
- **Frontend Wave 2 useETA 行动** (T20-9.v3 P1 配套):
  1. 删除 message regex "已生成 X/Y" 解析 — 直接读 `shots_completed`
  2. ETA 算法 `(shots_total - shots_completed) * 80 / max_concurrent` 更精
  3. `shots_in_flight = shots_total - shots_completed` 可派生
- **Backend 实现**: chapters.py +63 行 (5 层兜底: regex → progress 反推 → stage 派生, universal 适配任意 shot count) + schemas/chapter.py +12 行 (字段定义 + 注释)
- **测试**: tests/test_t20_13_shots_count_fields.py 34 PASS + 293 regression PASS
- **向后兼容**: 旧字段 (status / stage / progress / message / failed_shot_count / partial_failure / estimated_remaining_seconds / Wave 9 6 字段) 全部保留

### v1.0 (2026-05-13) Wave 9 Phase 2 落地

- **决策**: DEC-030 / Ben 方案 A（5/13 15:42 Ben 微信提出）
- **顺解 RISK**: T15-3 (GET /story scenes_review 永久治本) / T15-7 (ETA reset on stage change) / T15-8 (subPhase backend-authoritative) / T15-9 (mid-stage failed_count 实时)
- **agent 战果**: Backend Opus xhigh ~55 min + Frontend Opus xhigh ~50 min + DevOps Sonnet ~5 min
- **单测**: 60+ PASS (44 backend status + 9 regenerate + 7 architecture)
- **e2e 实证**: PM 5/13 21:08 curl `/status` 6 新字段全返 ✅ + GET /story 真返 11 scenes ✅

### 未来 (v1.x+)

可能的扩展：
- Stage 5 sub-stage 状态机（image_preparation 内细分 character_fullbody / scene_anchor / shot_context）
- 加 `next_action_expected: string` 字段（"用户应该点确认角色" / "等待 30s 自动跳"）
- ETA 加置信区间字段（low / high range）
- partial_failure 加详细 shot 列表（哪些 shot_id 失败）

---

## 9. FAQ

### Q1: 为什么 ui_phase 8 状态机不是直接用 backend `stage`？

A: `stage` 是 Pipeline 内部技术状态（character_design / screenplay / image_generation 等），含义偏 backend 实现细节。`ui_phase` 是面向用户体验的语义状态，加了：
- "*_pending" 区分 backend "跑中" 等待
- "char_review" / "scene_review" 等待用户确认
- "completed" 终态
- 也独立于 `stage` 字段的具体技术命名（backend 改 stage 名称不影响 frontend）

### Q2: 为什么 hydrate_hints.endpoint 含 `{project_id}` 占位符不直接 hardcode？

A: 后端不知道 project_id（来自 URL），但需要返一个可复用的 template。Frontend 拿到后 `.replace("{project_id}", projectId)` 即可。也方便未来加多 chapter 支持。

### Q3: scene_review 阶段为什么 hydrate `/story` 不是 `/storyboard`？

A: scene_review 时 chapter.storyboard_json **还为空**（Stage 4 未跑），但 chapter.scenes_json **已写入**（Stage 3 完成）。用户应该看 11 screenplay scenes 而非 23 storyboard shots（storyboard 是分镜层，用户旅程 Stage B 不暴露给用户 — 详见 CLAUDE.md "Phase 2-4 系统自动 不打断用户" 设计原则）。Wave 9 backend `GET /story` 优先检查 scenes_json 非空 → 返 scenes（永久治本 T15-3）。

### Q4: PM 直接 curl POST /confirm-scenes 时 frontend subPhase 为什么仍能切到 shot-gen？

A: Wave 9 之前 frontend subPhase 仅 user click handler 触发（handleConfirmScenes 内 dispatch）。PM 绕过 handler 直接 API call → subPhase stale (T15-8)。

Wave 9 修复：frontend Watcher 5s tick 监听 `status.ui_phase`，自动 dispatch SET_GENERATION_SUB_PHASE。所以即使 PM 直接 curl 解 R4-2，~5s 后 status.ui_phase 变 storyboard_running / shot_generating，frontend subPhase 跟着派生。

### Q5: 旧 frontend 没用 ui_phase 怎么办？

A: backward compat 第一原则。`reconcileBackendVsUrl` signature 加 `uiPhase?: string | null` 为 optional。如老 frontend 没传 uiPhase，走 legacy heuristic 路径（reconcile 旧逻辑），行为完全不变。新 frontend 传 uiPhase → 走优先路径（更精确）。

### Q6: 改契约文档要 PR review 谁？

A: 项目当前规模：
- Founder + Ben (合伙人) 任一 approve 即可 PR merge
- Frontend agent 在 spawn 时强制读契约文档
- Backend agent commit 改契约文件时 pre-commit hook 强制 `[frontend-impact: yes/no]` label

### Q7: Wave 8.x RISK-T14-10 参考图并行化会改 status response 吗？

A: 不会。参考图并行化是 Stage 5 image_preparation 内部优化（asyncio.gather 跨角色/location 并行），不改 stage / ui_phase / hydrate_hints。属于 backend 内部实现优化，frontend 透明。

---

## 9.7 adjust 异步 job 端点 (Wave 12, 2026-05-24, [frontend-impact: yes])

> Backend P2-1 把角色 adjust 从同步阻塞 90s 改为异步 job + 轮询 (test26 实证: 同步阻塞导致前端转圈+超时重试)。
> 新增 status API, 按 DEC-030 0.3 规则入本契约 (PM 代补 — Backend agent 完成时漏更, 契约取自 Backend 完成通知)。

### 9.7.1 POST adjust (发起, 异步)

```
POST /api/projects/{project_id}/characters/{char_id}/adjust
Body: { "adjustment": "<用户调整描述>" }
```
**成功 → 202 Accepted** (不再同步等 90s):
```json
{ "success": true, "job_id": "<uuid>", "status": "pending", "char_id": "char_002", "message": "..." }
```
快速校验失败仍同步返回: 404 (项目/角色不存在) / 400 (大纲未确认等) / 500 (API key)。

### 9.7.2 GET adjust job 轮询

```
GET /api/projects/{project_id}/characters/adjust-jobs/{job_id}
```
**Response**:
```json
{
  "job_id": "<uuid>", "char_id": "char_002", "kind": "adjust",
  "status": "pending|processing|completed|failed",
  "progress": 0-100,            // 节点: 5→15→30→40→70→100
  "stage_message": "<人类可读进度>",
  "result": {                   // status=completed 时非 null, 字段与旧同步返回体一致
    "success": true, "character": {...}, "char_id": "char_002",
    "portrait_url": "...", "fullbody_url": "...", "message": "..."
  } | null,
  "error": "<失败原因>" | null   // status=failed 时非 null
}
```
- job **404** = 不存在 / 过期 (in-memory TTL 1h) / 越权
- **Frontend 派生规则** (DEC-030 backend authoritative): POST 拿 job_id → 轮询 GET 直到 status ∈ {completed, failed} → completed 读 result.portrait_url/fullbody_url 刷新角色卡 → failed 读 error 提示。**不本地猜测 90s 完成时间**, 按 progress + status 派生 loading UI。

### 9.7.3 实现注意
- in-memory job 注册表 (`app/services/adjust_job_manager.py`, asyncio.Lock + TTL), **0 DB schema / 0 Alembic** (短命 UI 操作, 角色数据变更仍由原逻辑 DB 持久化)
- 单 uvicorn worker 假设 (与现有 asyncio.create_task 一致)
- fallback 全保留 (DEC-051): LLMFallbackChain + B57 fullbody 重生 + RISK-T17-9 portrait_ref

### 9.7.4 regenerate-portrait 异步 (Wave 13 #6, 2026-05-25, [frontend-impact: yes])

> Backend #6 把 regenerate-portrait (reroll, 留空调整框) 也改异步, 复用 adjust job 模式。
> ⚠️ 前端 reroll 调用必须配合改轮询 (Wave 13 #6前端, 否则拿到 202+job_id 而非旧 200+结果 → reroll 断)。

```
POST /api/projects/{project_id}/characters/{char_id}/regenerate-portrait
  → 202 { success:true, job_id, status:"pending", char_id, message }
  → 同步错误: 404(项目/角色不存在) / 400(未生成大纲)
GET  /api/projects/{project_id}/characters/adjust-jobs/{job_id}  (复用 §9.7.2 adjust 轮询端点)
  → 200 { job_id, char_id, kind:"regenerate_portrait", status, progress, stage_message,
          result:{success,char_id,portrait_url,fullbody_url,message}|null, error|null }
  - kind 字段区分 adjust vs regenerate_portrait (前端复用同一轮询逻辑)
  - portrait_url/fullbody_url 带 ?v={epoch} cache-buster; fullbody 失败时 null(非阻塞)
```
**前端派生规则** (DEC-030): reroll POST 拿 job_id → 轮询 GET adjust-jobs → completed 读 result.portrait_url 刷新 → 与 adjust 同 pattern, 仅 kind 不同。

### 9.7.5 实现注意

- **决策**: `.team-brain/decisions/DECISIONS.md` DEC-030 (Wave 9 方案 A 完整决策)
- **审查报告**: `.team-brain/analysis/TEST15_DEEP_AUDIT_2026-05-13.md` (test15 5 维度根因 + Ben 建议价值)
- **经验**: `.team-brain/knowledge/KEY_LEARNINGS.md` (Wave 9 收尾 3 条经验 + test15 6 条核心经验)
- **DevOps hook**: `docs/CONTRACT_HOOK.md`
- **Memory**: `~/.claude/projects/.../memory/feedback_frontend_backend_contract_verification.md`

---

**契约文档维护人**: PM (序话Story Agent Team Lead)
**最后更新**: 2026-05-24 22:50 (v1.6 §9.7 adjust 异步 job)
**Founder 批准**: 2026-05-13 20:25（DEC-030 采纳 Ben 方案 A）
