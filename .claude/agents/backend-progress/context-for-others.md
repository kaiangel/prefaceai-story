# Backend Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 Backend 的工作状态和可用资源
> **最后更新**: 2026-03-04 18:07

---

## 当前状态速览

```
状态: ✅ TASK-SHOT-QUALITY-BUGFIX Backend 全部修复完成 (Bug#1, #2, #4, #5)
当前任务: 无（等待 PM review + TASK-GIT-COMMIT-3）
阻塞: 无
```

---

## ✅ TASK-SHOT-QUALITY-BUGFIX Backend 部分 (2026-03-04 18:07)

### 给 @PM 的信息

**4 项 Bug 修复全部完成，3 个文件修改，全部语法/import 检查通过。请 review。**

| # | Bug | 级别 | 文件 | 修复方式 |
|---|-----|------|------|----------|
| 1 | 场景标签中文→□ | **P1** | `scene_reference_manager.py` | 标签改用英文 `location_id` + CJK 字体兜底 |
| 2 | Prompt 指令泄漏 | **P2** | `image_generator.py` | 移除 "70-80% opacity"/"1-2px"/"~15px" 技术英文 |
| 4 | Validator 字段名 | **P3** | `storyboard_service.py` | `camera.camera_angle` → `camera.angle` |
| 5 | dialogue handler dict crash | **P2** | `image_generator.py` | L81-82 添加 `isinstance(txt, dict)` 类型检查 |

### 给 @AI-ML 的信息

- **Bug #3 (神秘路人)** 是 @AI-ML 的任务，Backend 侧无需改动
- Backend 的 Bug #2 修复已精简 `build_native_text_prompt()` 中所有带数值的技术英文，降低 NB2 文字泄漏风险

### 给 @Tester 的信息

- Backend 4 项 Bugfix 完成 (Bug #1/#2/#4/#5)，等 PM review 后进入 TASK-GIT-COMMIT-3
- Bug #4 修复后 Validator 的假阳性警告应大幅减少

### 给 @DevOps 的信息

- TASK-GIT-COMMIT-3 需等全部 Bugfix (Backend + AI-ML) 完成后执行
- Backend 修改文件: scene_reference_manager.py, image_generator.py, storyboard_service.py (共 3 文件 4 项修复)

---

## 已完成可用的服务

### Phase 2.0 五阶段服务

| 阶段 | 服务 | 主力模型 | 备用模型 |
|------|------|---------|---------|
| Stage 1 | StoryOutlineGenerator | **Claude Sonnet 4.6** | Gemini 3 Pro |
| Stage 2 | CharacterDesigner | **Claude Sonnet 4.6** | Gemini 3 Pro |
| Stage 3 | ScreenplayWriter | **Claude Sonnet 4.6** | Gemini 3 Pro |
| Stage 4 | StoryboardDirector | **Claude Sonnet 4.6** | Gemini 3 Pro |
| Stage 5 | ImageGenerator | **Nano Banana 2** (gemini-3.1-flash-image-preview) | *(Pro 作 fallback)* |

### 文字渲染双通道

| 通道 | 方式 | 开关 | 状态 |
|------|------|------|------|
| **原生渲染（默认）** | NB2 在 prompt 中渲染中文 | `use_native_text=True` | ✅ 激活 |
| **后处理渲染（备用）** | TextOverlayService 叠加 | `use_native_text=False` | ✅ 保留 |
