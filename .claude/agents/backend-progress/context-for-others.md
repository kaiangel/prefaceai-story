# Backend Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 Backend 的工作状态和可用资源
> **最后更新**: 2026-03-06 14:58

---

## 当前状态速览

```
状态: ✅ TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY 完成
当前任务: 等待 PM Code Review
阻塞: 无
```

---

## ✅ TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY 完成 (2026-03-06 14:56)

### 给 @PM 的信息（重要 — 请 Code Review）

**修改文件**: `app/services/image_generator.py` 第 845-853 行

**修改内容**:
```python
dialogue_embed = build_dialogue_scene_embed(
    text_overlay,
    characters=characters.get("characters", []),
    speaker_format='english',
    text_language='zh-CN'
)
```

**审查要点**:
1. 类型匹配: `characters` 参数从 dict wrapper (`{"characters": [...]}`) 提取为 list，匹配 `build_dialogue_scene_embed(characters: list)` 签名 ✅
2. `speaker_format='english'` — Founder 决策 ✅
3. `text_language='zh-CN'` — 强制简体中文 ✅
4. 死代码: 未发现需要清理的死代码路径 ✅
5. 向后兼容: `build_dialogue_scene_embed` 所有新参数均有默认值，不影响其他调用方 ✅

### 给 @AI-ML 的信息

- 你实现的 `_resolve_speaker_label()` + `build_dialogue_scene_embed()` 参数扩展 + `_TEXT_LANGUAGE_CONFIG` 现已在生产代码中正式启用
- 传参: `characters=list`, `speaker_format='english'`, `text_language='zh-CN'`

### 给 @DevOps 的信息

- 修改文件: `app/services/image_generator.py` (1 处修改)
- 下次 TASK-GIT-COMMIT 需包含

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

### 对话气泡渲染

| 配置 | 值 | 说明 |
|------|-----|------|
| speaker_format | `'english'` | Founder 决策，R2 验证 |
| text_language | `'zh-CN'` | 简体中文，修复繁体问题 |
| 对话嵌入方式 | `build_dialogue_scene_embed()` | 嵌入 [SCENE DESCRIPTION] |
