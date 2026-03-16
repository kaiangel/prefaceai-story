# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: 2026-03-16 19:00

---

## 当前状态速览

```
状态: ✅ N13-FIX + TASK-IMG-SAFETY-RETRY Backend 完成
当前任务: 等 PM Code Review + Tester 验证
阻塞: 无
```

---

## ✅ N13-FIX + TASK-IMG-SAFETY-RETRY Backend 完成 (2026-03-16)

### 给 @PM 的信息

5 项修复完成，请审查:

**N13-FIX**: `pipeline_orchestrator.py` Stage 1 后自动补全缺失的 spouse_of 反向关系。遍历 `list()` 副本防止修改中列表问题。

**L1**: `image_generator.py` 2 处日志 `self.MAX_RETRIES` → `attempt + 1`（CONTENT_SAFETY 在 attempt=0 break 时显示真实尝试次数）

**L2+L3a**: `scene_reference_manager.py` `_generate_single_anchor()` 三级重试:
1. 原始 prompt → 失败
2. `_simplify_anchor_prompt()` 简化 → 重试（apply_simple_replacements + "No people" 前置）
3. `rewriter.rewrite_scene_ref()` LLM 改写 → 重试
- 仅 `error_type == 'content_safety'` 才触发，正常路径零影响

**L3b**: `reference_image_manager.py` `generate_character_reference()` 角色参考图改写重试:
- `error_type == 'content_safety'` → `rewriter.rewrite_char_ref()` → 重试 1 次

**PromptRewriter 新增**: `rewrite_scene_ref()` + `rewrite_char_ref()` 两个方法，分别使用 AI-ML 交付的专用改写模板

### 给 @AI-ML 的信息

- 已集成你交付的 5 项内容:
  1. CROWD/ANIMAL/FIRE_SMOKE/CHILD_CONTEXT/REVEALING_CLOTHING 新类别 → 通过 `apply_simple_replacements()` 用于 `_simplify_anchor_prompt()`
  2. SCENE_REF_REWRITE_PROMPT → `PromptRewriter.rewrite_scene_ref()` 调用
  3. CHAR_REF_REWRITE_PROMPT → `PromptRewriter.rewrite_char_ref()` 调用
  4. `build_scene_ref_rewrite_prompt()` + `build_char_ref_rewrite_prompt()` → import 到 prompt_rewriter.py

### 给 @Tester 的信息

- N13-FIX: R9 测试时 spouse_of 应自动双向，不再出现 N13 FAIL
- TASK-IMG-SAFETY-RETRY: 场景/角色参考图遇到 CONTENT_SAFETY 时会自动重试:
  - 场景参考图: 最多 3 次尝试（原始→简化→LLM改写）
  - 角色参考图: 最多 2 次尝试（原始→LLM改写）
  - 日志中搜索 `CONTENT_SAFETY → 简化` 或 `PromptRewriter` 可追溯重试链路
