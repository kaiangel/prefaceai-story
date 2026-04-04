# Backend Agent - 当前任务

> **最后更新**: 2026-04-03
> **状态**: ✅ TASK-CONFIRM-OUTLINE-WIRE Step 2 完成，等 PM Review

---

## 刚完成

### ✅ TASK-CONFIRM-OUTLINE-WIRE Step 2 (2026-04-03)

5 子项:
- 2a: `POST /projects/` 去掉 pipeline 触发（仅创建 Project）
- 2b: `confirm-outline` 合并 raw + 用户编辑 6 字段
- 2c: 新增 `POST /projects/{id}/start-generation`
- 2d: `_run_generation_in_background` + `run_story_generation_task` 透传 `confirmed_outline`
- 2e: `pipeline_orchestrator.run()` 有 confirmed_outline 时跳过 Stage 1

改动 3 文件: `projects.py` + `pipeline_orchestrator.py` + `job_manager.py`
验证: 3/3 syntax ✅

**PM Review 发现链路断裂修复**:
- `job_manager.py`: 有 `confirmed_outline` 时用 `Phase2PipelineOrchestrator.run()` 替代 `StoryGenerator`
- 完整链路打通: start-generation → job_manager → pipeline(skip Stage 1) ✅

---

### ✅ TASK-PLOTPOINT-REORDER-FIX Backend (2026-04-03)

- `projects.py`: confirm-outline plot_points 按 `original_index` 整体移动 dict + `.copy()` + 向后兼容
- syntax ✅

---

## 待处理队列

- 无。等 PM Review。
