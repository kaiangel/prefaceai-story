# Backend Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 Backend 的工作状态和可用资源
> **最后更新**: 2026-03-10 14:15

---

## 当前状态速览

```
状态: ✅ PRO_MODEL 命名清理完成
当前任务: 等待 PM 快速确认 → Step 9 E2E R4
阻塞: 无
```

---

## ✅ PRO_MODEL → NB2_MODEL 命名清理完成 (2026-03-10 14:15)

### 给 @PM 的信息

PRO_MODEL 命名混乱修复已完成，请快速确认后进入 Step 9。

**修改范围**:
- `image_generator.py`: 类常量 `PRO_MODEL` → `NB2_MODEL` + 7 处引用 + 误导性注释清理
- `tests/test_nb2_switch.py`: 4 处 `ig.PRO_MODEL` → `ig.NB2_MODEL`
- 不改功能逻辑，`use_pro_model` 参数名保留

### 给 @Tester 的信息

- `image_generator.py` 类常量从 `PRO_MODEL` 改为 `NB2_MODEL`，值不变 (`gemini-3.1-flash-image-preview`)
- 功能零改动，E2E R4 测试不受影响
- `test_nb2_switch.py` 已同步更新

### 给 @AI-ML 的信息

- `image_generator.py` 变量/注释变更，无功能逻辑改动
- `build_dialogue_scene_embed()` 等你之前修改的代码不受影响

---

## 已完成可用的服务

### Phase 2.0 五阶段服务（全部对齐 DEC-012）

| 阶段 | 服务 | 主力模型 | 备用模型 |
|------|------|---------|---------|
| Stage 1 | StoryOutlineGenerator | **Claude Sonnet 4.6** | Gemini 3 Flash |
| Stage 2 | CharacterDesigner | **Claude Sonnet 4.6** | Gemini 3 Flash |
| Stage 3 | ScreenplayWriter | **Claude Sonnet 4.6** | Gemini 3 Flash |
| Stage 4 | StoryboardDirector | **Claude Sonnet 4.6** | Gemini 3 Flash |
| Stage 5 | ImageGenerator | **Nano Banana 2** (gemini-3.1-flash-image-preview) | *(Pro 作 fallback)* |

### 文字渲染双通道（T12 修复后）

| 通道 | 方式 | 开关 | 状态 |
|------|------|------|------|
| **原生渲染（默认）** | NB2 渲染所有文字，TextOverlay 完全不调用 | `use_native_text=True` | ✅ DEC-012 架构 |
| **后处理渲染（备用）** | TextOverlayService 叠加 | `use_native_text=False` | ✅ 保留 |
