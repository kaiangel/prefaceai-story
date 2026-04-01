# Frontend 当前任务进度

> 更新时间: 2026-04-01
> 状态: TASK-UPLOADER-ENV-FIX 完成，等 PM Review

---

## 最新完成: TASK-UPLOADER-ENV-FIX (2026-04-01)

5 个 Uploader 组件的 API URL 统一为 `API_BASE` from `@/lib/api`：
- CustomStyleUploader.tsx — `/utils/analyze-style`
- CharacterUploader.tsx — `/utils/analyze-character`
- SceneUploader.tsx — `/utils/analyze-scene`
- DocumentUploader.tsx — `/utils/parse-document`（额外发现）
- StoryIdeaInput.tsx — `/utils/ocr`（额外发现）

`NEXT_PUBLIC_API_BASE_URL` 零残留。build 20 路由 0 错误。
