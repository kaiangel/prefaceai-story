# confirm-outline 数据传递全链路审计

> 2026-04-07 PM 深度审查
> 来源: Founder 要求全维度验证 StageB 数据是否完整传入下一 stage

---

## 审查结论

6 个 UI 维度中 **4 个正确传递，2 个有 bug**。

### ✅ 正常传递（4/6）

| 维度 | 前端发送 | 后端合并 | Pipeline 读取 |
|------|---------|---------|-------------|
| 故事标题 (title + title_en) | ✅ | ✅ L301-304 覆盖 raw | ✅ Stage 2+ 读 title |
| 角色设定 (name/nameEn/description/personality) | ✅ 4 字段/角色 | ✅ L309-315 逐角色覆盖 characters_overview | ✅ Stage 2 读 characters_overview |
| 情节走向 (plot_points 含拖拽重排) | ✅ {description, original_index} | ✅ L317-333 按 original_index 整体移动 dict | ✅ Stage 3 逐 plot_point 生成场景 |
| 情绪基调 (mood) | ✅ | ✅ L340-343 写入 visual_tone.overall_mood | ✅ Stage 4 读 visual_tone |

### ❌ 有 Bug（2/6）

#### Bug 1: 故事简介 summary→logline 写错位（🟡 中）

**代码位置**: `app/api/projects.py` L305-306

**问题**: 
```python
if user.get("summary"):
    raw["logline"] = user["summary"]   # ← 写到了 logline，没写到 summary
```

Stage 1 输出有两个不同字段：
- `logline`: 一句话梗概（50 字以内）
- `summary`: 故事简介（100-200 字）

前端 StageB 展示和编辑的是 `summary`，但后端把用户编辑值写到了 `logline`。

**影响**:
- Stage 2 CharacterDesigner 读 `logline` — 歪打正着拿到了用户编辑值 ✅
- `confirmed_outline_json` 里 `summary` 字段仍是 LLM 原始值 — 用户修改丢失 ❌
- 后续读 `summary` 的功能（Dashboard 展示、续写上下文等）会拿到旧值

**修复**: L306 改为同时写两个字段。

---

#### Bug 2: 结局选择不影响故事生成（🔴 高）

**代码位置**: `app/api/projects.py` L336-337

**问题**: 
用户在 StageB 选了结局 B（三选一），前端发了 `selected_ending: "结局B描述"`，后端存到了 `raw["selected_ending"]`。但 Stage 3 `screenplay_writer.py` **只按 `plot_points` 逐场生成**，不读 `selected_ending`。`plot_points` 最后一条仍是 LLM 原始结局。

**影响**: UI 上用户可以选结局，但**实际不影响最终故事** — 核心产品承诺"用户选结局→故事按选的结局走"不生效。

**全链路影响分析**:

| Stage | 读 plot_points? | 受方案 C 影响? |
|-------|----------------|---------------|
| Stage 2 角色设计 | ❌ (读 characters_overview) | 无影响 |
| Stage 3 剧本 | ✅ 直接读 | ✅ 预期影响（最后一场按用户结局生成）|
| Stage 4 分镜 | ❌ (读 Stage 3 输出) | 间接传递 |
| Stage 5a 角色参考图 | ❌ (来自 Stage 2) | 无影响 |
| Stage 5a.5 场景参考图 | ❌ (来自 unique_locations) | 无影响 |
| Stage 5b Shot 图 | ❌ (读 Stage 4 输出) | 间接传递 |

**当前修复方案（方案 C）**: 用用户选的结局 description 替换 `plot_points` 最后一条的 `description`，保留 `beat`/`estimated_duration_seconds` 等元数据。Stage 3 的 LLM 根据"方向性结局 + 前序场景上下文"展开最后一场剧本。

**方案 C 的局限**: `ending_options` 是一句话概括（15-30 字），而 `plot_points` 最后一条原始 description 是 30-80 字的完整场景描述。替换后 Stage 3 拿到的信息量减少，但有 `previous_scenes` 上下文 + `beat="resolution"` 类型标识，LLM 可以展开。

---

## 未来优化方向（最理想方案）

**当前方案 C 是务实选择，后续应迭代为：**

在 Stage 1 prompt 里让 LLM 对每个 `ending_option` 都生成一个对应的**完整 plot_point 级别的场景描述**（30-80 字，含角色动作、环境、情感），存在 `ending_options` 数组里。结构改为：

```json
{
  "ending_options": [
    {
      "id": "ending_1",
      "description": "一句话概括（给用户看）",
      "full_plot_point": {
        "beat": "resolution",
        "description": "完整的场景描述（30-80字，和 plot_points 同等信息量）",
        "estimated_duration_seconds": 30
      }
    }
  ]
}
```

用户选结局后，直接用对应 ending 的 `full_plot_point` **整体替换** `plot_points` 最后一条。这样 Stage 3 拿到的信息量完全不减少。

**改动范围**: Stage 1 prompt 改结构 + confirm-outline 合并逻辑改为取 `full_plot_point` + 前端 ending 数据结构适配。

**优先级**: P2（当前方案 C 已能工作，优化在信息量充足性上）。
