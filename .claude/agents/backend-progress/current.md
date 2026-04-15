# Backend Agent - 当前任务

> **最后更新**: 2026-04-15（PM 代更新）
> **状态**: ✅ Harness V2: Schema 扩展 (Stage 1→2 + 3→4) + 成本熔断 $10 + 已部署

---

## 刚完成

### ✅ TASK-PROMPT-B-PRIME — B' 为默认 Prompt 格式 (2026-04-14)

**改动文件**:
- `app/config.py` — 新增 `PROMPT_FORMAT: str = "b_prime"`
- `app/services/image_generator.py` — 新增 `_build_b_prime_prompt()` + `prompt_format` 参数

**实现**:
- 默认 B' 格式（盲测验证质量等价，省 46% token）
- A 格式保留：`PROMPT_FORMAT=legacy` 或 `prompt_format="legacy"` 切回
- B' 模式跳过 `StyleEnforcer.enforce_prompt()`（B' 自带风格块，避免重复）

### ✅ TASK-KI-FIX — 3 个 Shot 级 API 端点 (2026-04-14)

**改动文件**: `app/api/chapters.py`

| 端点 | 方法 | 路径 | 功能 |
|------|------|------|------|
| regenerate_shot | POST | `/{chapter_number}/shots/{shot_id}/regenerate` | 重新生成（SKIP 模式返回现有图片） |
| update_shot | PATCH | `/{chapter_number}/shots/{shot_id}` | 更新旁白/对话，写回 DB |
| delete_shot | DELETE | `/{chapter_number}/shots/{shot_id}` | 软删除（deleted: true） |

---

## 待处理队列

- 无。等 @frontend 接通 + PM Review。
