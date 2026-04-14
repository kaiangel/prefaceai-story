# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: 2026-04-14 21:30（PM 代更新）

---

## ✅ TASK-STAGED-V2 — Haiku 集成到 regenerate 端点 (2026-04-14)

- regenerate 端点 API 契约更新：
  - Body (可选): `{ "adjustment_intent": "让她笑" }`
  - 返回新增: `prompt_modified: bool`, `modified_prompt_preview: str | null`
- 有 intent: Haiku 4.5 改 image_prompt → 写回 DB → 生图（或 SKIP 返回现有图片）
- 无 intent: 原 prompt re-roll
- Haiku 修改持久化：写回 storyboard_json
- 错误处理：Haiku 失败 fallback 到原始 prompt，不阻塞

---

## ✅ TASK-PROMPT-B-PRIME — B' 默认格式 (2026-04-14)

- `image_generator.py` 的 `generate_shot_image_phase2()` 新增 `prompt_format` 参数
- 默认 `"b_prime"`（省 46% token，盲测验证质量等价）
- `"legacy"` 切回 A 格式（全部旧代码保留）
- 环境变量 `PROMPT_FORMAT=b_prime|legacy` 可全局切换
- B' 模式跳过 `StyleEnforcer.enforce_prompt()`（B' 自带风格块）

## ✅ TASK-KI-FIX — 3 个 Shot 级 API 端点 (2026-04-14)

**@Frontend 需要的 API 契约**:

### POST `/{chapter_number}/shots/{shot_id}/regenerate`

请求: 无 body
响应:
```json
{
  "status": "completed",
  "shot_id": 1,
  "imageUrl": "/images/shot_01.png",
  "skipped": true,
  "message": "..."
}
```

### PATCH `/{chapter_number}/shots/{shot_id}`

请求:
```json
{
  "narration_segment": "新的旁白文字",   // optional
  "chinese_text": "新的对话文字"         // optional
}
```
响应:
```json
{
  "status": "updated",
  "shot_id": 1,
  "updated_fields": ["narration_segment"],
  "shot": { ... 完整 shot 数据 ... }
}
```

### DELETE `/{chapter_number}/shots/{shot_id}`

请求: 无 body
响应:
```json
{
  "status": "deleted",
  "shot_id": 1,
  "message": "Shot 1 已标记为删除"
}
```

**通用**: 所有端点需 Authorization header（Bearer token），路由前缀 `/api/projects/{project_id}/chapters/`

---

## 之前的工作

### ✅ R6 Backend (2026-04-13)

- R6-5: max_wait 300→1800（30 分钟）
- R6-6: 有自定义风格时日志显示 `Style: custom (display_name)`
- R6-1b: mood 更新顶层字段
- R6-2b: 删除 selected_ending 替换 plot_point 逻辑

### ✅ TASK-HE-BACKEND-1 — Pipeline Schema 验证 (2026-04-14)

- `app/services/pipeline_schemas.py` — Pydantic 验证 characters + shots
- Stage 2→3 + Stage 4→5 验证调用已嵌入 pipeline_orchestrator.py
- image_prompt 中文比例检测 validator（>15% 拒绝）
