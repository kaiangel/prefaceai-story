# 全量生图模式缺少 image_generation progress_callback

> **记录时间**: 2026-04-09
> **发现者**: PM（Bug 3 修复审查时发现）
> **优先级**: P2（当前不阻塞，SKIP_IMAGE_GENERATION=true 下不影响）
> **触发条件**: 关闭 SKIP_IMAGE_GENERATION（启用真实 Gemini/NB2 生图）时必须处理

---

## 问题

`pipeline_orchestrator.py` 中 `progress_callback("image_generation", ...)` 的 3 次调用（L689-729）**全部在 `_run_stage5_skip_mode` 方法内**。

全量生图模式（`run()` 方法 L254+ 的代码路径）在 Stage 5 期间**没有**发送 `progress_callback("image_generation", ...)` 调用。最后一次 progress_callback 是 Stage 4 结束时的 `"storyboard"` at 55%（L234），之后直到 pipeline 完成或失败，没有任何 stage 更新。

## 影响

前端 `StageC.tsx` L80 依赖 `status.stage === "image_generation"` 来触发角色预览检查点。

- **SKIP 模式（当前）**: ✅ 正常触发 — `_run_stage5_skip_mode` 在 L690 发送 `"image_generation"`
- **全量模式（未来）**: ❌ 永远触发不了 — 没有发送 `"image_generation"` stage，只能等 `status.status === "completed"` 兜底

## 修复方案

当关闭 SKIP_IMAGE_GENERATION 时，需要在 `pipeline_orchestrator.py` 的全量 Stage 5 路径中补上 progress_callback 调用：

```python
# 在 5a 角色参考图生成完成后 (~L310 附近):
if progress_callback:
    await progress_callback("image_generation", 65, "角色参考图就绪...")

# 在 5a.5 场景参考图生成完成后 (~L350 附近):
if progress_callback:
    await progress_callback("image_generation", 75, "场景参考图就绪，正在准备 Shot 图...")

# 在 5b Shot 图全部生成完成后 (~L520 附近):
if progress_callback:
    await progress_callback("image_generation", 90, f"Shot 图就绪 ({len(image_results)} 张)...")
```

行号为估算，需根据实际代码位置调整。

## 关联

- **Bug 3 修复**: `StageC.tsx` L80 `"generating_images"` → `"image_generation"` (2026-04-09)
- **相关文件**: `app/services/pipeline_orchestrator.py`, `frontend/src/components/create/StageC.tsx`
- **负责人**: @Backend（补 progress_callback）
