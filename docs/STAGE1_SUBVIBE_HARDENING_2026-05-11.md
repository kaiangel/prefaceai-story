# Stage 1 Sub-Vibe 反偏置硬化 (B47) — 2026-05-11

> 任务：B47 P1 — Stage 1 StoryOutlineGenerator LLM 加 sub-vibe 反偏置约束（仿 B40 BGM meta-prompt 模式）
> 真根因：test11 实测 5-11 15:25，用户选"幽默"→ DB 持久化 ✅ → backend log 强制注入 ✅ → 但 Stage 1 LLM 仍输出 `raw_outline.mood='治愈'` + `user_selected_mood=None` ❌
> Owner: @ai-ml
> 模型: Opus 4.7
> 文件: `app/services/story_outline_generator.py`（单文件）
> Status: ✅ 代码改动落地 / AST PASS / pytest test_architecture 7/7 PASS / 等 PM 重启 backend + Founder test12 真测验证

---

## 1. 真根因诊断（test11 5-11 15:25 实测）

### 链路三步：

| 步骤 | 实测结果 | 状态 |
|---|---|---|
| Stage A 前端用户选"幽默" | 写 DB `projects.user_selected_mood='幽默'` | ✅ |
| Backend log B33 强制注入 LLM 约束 | `[StoryOutlineGenerator] B33 user_selected_mood: 幽默 (强制注入 LLM 约束)` | ✅ |
| Stage 1 LLM 实际输出 | `raw_outline.mood='治愈'` + `raw_outline.user_selected_mood=None` | ❌ **断点** |

### 真正断点分析（4 层 prompt 工程缺陷）

**断点 1**: System prompt L203 写 `mood must be exactly one of: 感人/治愈/热血/悬疑/浪漫/温馨` — **只列 6 个选项，缺"幽默"和"紧张"**（前端 8 选项）。LLM 收到"幽默"用户约束 + system 限制 6 选项 → 只能在 6 个里找最近邻 → fallback 到"治愈"。

**断点 2**: 故事内容"孤独老人 + 凌晨3点 + 猫送外卖"含多个**内敛诱因关键词**（孤独 / 凌晨 / 独居），LLM 自动滑向"治愈" sub-vibe（默认"温暖抚慰"），完全忽视用户选"幽默"。这是 B40 BGM Haiku 已经识别并修复的**同型偏置**，但 B40 没修 Stage 1 LLM 这层。

**断点 3**: 旧 B33 mood_constraint 块（L164-178）只说"mood MUST be exactly: 幽默"但**没说为什么 LLM 会滑** + **没枚举 PREFER/AVOID 调性词** → LLM 没有"反偏置"的具体指令。

**断点 4**: `outline` JSON 没透传 `user_selected_mood` 字段（LLM 输出 schema 没要求），导致下游 confirmed_outline 也是 None，BGM Haiku 后续路由错桶。

**B19 写反的 bug（顺便发现）**: L610-617 `mood_map` 中 `"治愈": "warm"` ❌（应是 heartwarming），`"温馨": "heartwarming"` ❌（应是 warm）— 与 B33 的 `_mood_map`（L153-162）冲突。这是 B19 时未修干净的遗留，B47 一并修复。

---

## 2. B40 模式参考（BGM Haiku meta-prompt L100-145 + L516-540）

B40 (2026-05-09) 已修了 BGM Haiku 的 sub-vibe 漂移问题（test9 实测"热血→坚守式"误选）：

- **SYSTEM 段 "Sub-Vibe 默认锁定"**（meta_mixed_v3_quote_picking.md L100-145）：
  - 8 mood × 默认期望 sub-vibe / LLM 易误选 sub-vibe / 内敛诱因关键词 三列表
  - 工作流程 Step 0.5（取 user_selected_mood → 查表 → 扫内敛诱因 → 反偏置）
  - Escape Hatch + 6 个常见 sub-vibe slip 黑名单

- **USER 段 "Step 0.5 PREFER/AVOID 矩阵"**（meta_mixed_v3_quote_picking.md L516-540）：
  - 8 mood × PREFER / AVOID 调性词表
  - 4 反例（含 test9 "30 年磨砺 → explosive surge" 真实教训）
  - 形状 > 内容 铁律

**复用模式**：B47 在 Stage 1 LLM prompt 注入同型反偏置块，但调性词改为 Stage 1 适用的"emotional_arc / plot_points / visual_tone"层级（而非 BGM 调性词），核心机制（8 mood 表 + PREFER/AVOID + 反例 + 形状>内容铁律）完全一致。

---

## 3. 改动清单（6 处 / 单文件）

| # | 位置 | 改动类型 | 内容 |
|---|---|---|---|
| 1 | L203-206 system_prompt | **修 bug + 加约束** | mood 8 选项全列 + 加 `user_selected_mood` 透传必填 + "禁止漂移"约束 |
| 2 | L317 JSON schema 注释 | **修 bug** | mood 字段注释从 6 选项改 8 选项 |
| 3 | L401 创作要点 #10 | **修 bug + 加约束** | mood 8 选项 + 显式说明用户约束块的覆盖优先级 |
| 4 | L150-281 mood_constraint 块 | **新增（核心）** | B47 升级：8 mood × PREFER/AVOID sub-vibe 表 + 4 反例 + 形状>内容铁律 + 输出前自检 |
| 5 | L297-345 generate() return 前 | **新增（兜底）** | 透传保险：强 enforce `mood / user_selected_mood / visual_tone.overall_mood` 三字段 + warning log |
| 6 | L704 _validate_outline mood_map | **修 bug** | B19 写反："治愈" warm→heartwarming / "温馨" heartwarming→warm |

### 改动 4 核心块（节选）

```markdown
## STORY MOOD CONSTRAINT (USER SELECTED — MANDATORY, HIGHEST PRIORITY)

═══════════════════════════════════════════════════════════════
用户在 Stage A 主动选择的情绪基调（不可被覆盖、不可被替换、不可漂移）：

  ╔══════════════════════════════════════════════════════════╗
  ║   user_selected_mood = "幽默"  (overall_mood = "comedic")  ║
  ╚══════════════════════════════════════════════════════════╝
═══════════════════════════════════════════════════════════════

### 必须输出的字段（如违反 → JSON 视为无效）

1. `mood` 字段 MUST be exactly: **"幽默"** （8 选项之一，禁止自造或替换为相似词）
2. `visual_tone.overall_mood` MUST be exactly: **"comedic"** （英文 8 桶之一）
3. `user_selected_mood` 字段（top-level）MUST be exactly: **"幽默"** （透传字段，复制用户原值）

### 🔑 形状 > 内容 铁律（Sub-Vibe Default Lock —— B47 反偏置核心）

⚠️ 用户选 mood 时**默认指"明亮/激昂/正面/主动" sub-vibe**，但 LLM 看故事内容
（孤独/独居/凌晨3点/已故/失败/中年/30年磨砺）会自动滑向"内敛/坚守/伤逝/黑色"sub-vibe。

**当用户选 mood 与故事内容内敛诱因冲突时：以用户选的 mood 形状为准，不要跟着内容滑。**

| user_selected_mood | PREFER sub-vibe（必须给的形状）| AVOID sub-vibe（绝不允许滑向）| 内敛诱因关键词 |
|---|---|---|---|
| **温馨** | warm/cozy/familial/家庭温情/朋友闲聊/情侣甜蜜 | mournful/longing for the lost/怀旧伤逝 | 已故/旧物/老照片 |
| **治愈** | restorative/温暖抚慰/重获力量/拥抱后释怀 | lonely/isolated/寂寞独处 | 独居/分手后/失业后/一个人/凌晨/孤独 |
| **紧张** | heartbeat-like/心跳加速/倒计时/危机感 | suffocating/窒息/breath held/hopeless | 无力反抗/被压制 |
| **幽默** | bouncy/段子反转/轻快搞笑/punchline/小恶作剧 | bitter laughter/黑色幽默/含泪的笑 | 失败/挫折/孤独/凌晨/独居 |
| **感人** | heartfelt/真情流露/泪点动人/释怀 | grief funeral/葬礼式哀伤 | 死亡/葬礼/生离死别 |
| **热血** | explosive/激昂高燃/突破爆发/巅峰对决 | enduring/坚守式/hold ground/not triumph | 中年/30年磨砺/长跨度 |
| **悬疑** | minor key/紧张未知/解谜推理/暗中观察 | shrieking/阴森恐怖/jumpscare | 鬼魂/超自然/失踪 |
| **浪漫** | butterflies/心动悸动/暧昧怦然/长情陪伴 | mournful goodbye/哀伤别离/永别 | 分手/错过/异地 |

### 4 个必须避免的 sub-vibe slip（test11 实测教训 + B40 BGM 经验）

❌ **反例 1**（test11 实测）：user_selected_mood="幽默" + idea="孤独老人凌晨3点训练AI客服 → 猫送外卖"
   → **不要**把 mood 滑成"治愈" / **必须** mood="幽默" + emotional_arc 写"comedic_chaos → mischief"

❌ **反例 2**（test9 BGM 经验）：user_selected_mood="热血" + idea 含"30 年磨砺/中年人坚持"
   → **不要**写"doesn't triumph but endures" / **必须** mood="热血" + "breakthrough/explosive surge"

❌ **反例 3**：user_selected_mood="温馨" + idea="已故妈妈的红烧肉"
   → **不要**把 mood 滑成"感人" / **必须** mood="温馨" + "warm familial cozy / 妈妈的味道还活着"

❌ **反例 4**：user_selected_mood="紧张" + idea="无力反抗的压迫"
   → **不要**写"suffocating breath held" / **必须** mood="紧张" + "heartbeat racing / deadline closing in"

### 输出前自检（生成 JSON 之前必须扫一遍）

1. ✅ mood = "幽默" 吗？（不是相似词）
2. ✅ user_selected_mood 顶层字段 = "幽默" 吗？（不是 null）
3. ✅ visual_tone.overall_mood = "comedic" 吗？
4. ✅ emotional_arc / plot_points 符合 PREFER 列调性吗？
5. ✅ idea 含内敛诱因时，有没有主动反偏置回到 PREFER 形状？
```

### 改动 5 兜底逻辑（节选）

```python
# B47 (2026-05-11): 透传保险 + mood 兜底 enforce
if user_selected_mood:
    # 强 enforce 顶层 mood 字段（必须 == 用户选）
    old_mood = outline.get("mood")
    if old_mood != user_selected_mood:
        logger.warning(
            f"[StoryOutlineGenerator] B47 兜底纠正 mood: "
            f"LLM 输出 '{old_mood}' → 强制改为用户选 '{user_selected_mood}'"
        )
        outline["mood"] = user_selected_mood

    # 强 enforce 顶层 user_selected_mood 透传字段（LLM 常漏写为 null）
    if outline.get("user_selected_mood") != user_selected_mood:
        outline["user_selected_mood"] = user_selected_mood

    # 强 enforce visual_tone.overall_mood（与 mood 中英对应）
    _b47_mood_map = {
        "温馨": "warm", "治愈": "heartwarming", "紧张": "tense",
        "幽默": "comedic", "感人": "melancholic", "热血": "heroic",
        "悬疑": "mysterious", "浪漫": "romantic",
    }
    expected_overall = _b47_mood_map.get(user_selected_mood)
    if expected_overall:
        tone = outline.setdefault("visual_tone", {})
        if tone.get("overall_mood") != expected_overall:
            tone["overall_mood"] = expected_overall
```

---

## 4. 验证结果

### 静态验证

| 检查 | 结果 |
|---|---|
| AST parse | ✅ PASS |
| pytest tests/test_architecture.py | ✅ 7/7 PASS（不退化）|
| B47 关键词命中数（B47 + Sub-Vibe Default Lock + 反例[1234] + 形状>内容 + test11）| 16 处 |
| 文件行数变化 | 686 → 782 (+96 行，+14%) |
| 备份 | `app/services/story_outline_generator.py.bak-20260511-b47-pre` |

### 端到端验证（待 PM 重启后做）

**期望行为**（test12 同 idea + user_selected_mood="幽默"）：
1. ✅ Backend log: `B33 user_selected_mood: 幽默 (强制注入 LLM 约束)`
2. ✅ `raw_outline.mood = "幽默"`（不是"治愈"）
3. ✅ `raw_outline.user_selected_mood = "幽默"`（不是 None）
4. ✅ `raw_outline.visual_tone.overall_mood = "comedic"`
5. ✅ emotional_arc 不再含 "lonely/isolated/yearning" 等 AVOID 词，含 "comedic_chaos/mischief/playful" 等 PREFER 词

**兜底兜住的边缘情况**：
- LLM 输出 `mood = "治愈"` 时 → warning log + 强制改为"幽默"
- LLM 输出 `user_selected_mood = null` 时 → 静默补字段 = "幽默"
- LLM 输出 `visual_tone.overall_mood = "heartwarming"` 时 → warning log + 强制改为"comedic"

---

## 5. 给同事影响

### @backend
- 零代码改动 / 下次 Stage 1 LLM 调用自动加载新 prompt
- 生产环境无需特殊处理 / Sonnet 4.6 / Gemini 3.1 任一都会消费新约束
- B47 兜底逻辑在 generate() return 前，不影响 `_validate_outline` 现有 valid_moods 校验
- B19 mood_map 写反的 bug 顺便修了 — 历史数据如果有 overall_mood='warm' 但 mood='治愈'的不一致 row，下次 LLM fallback 会归正

### @tester
- 下次跑 test12+ 真故事重点验证：
  - 同 idea ("孤独老人凌晨3点训练AI客服 → 猫送外卖") + 用户选"幽默"
  - 期望 raw_outline.mood = "幽默"（不是 test11 的"治愈"）
  - 期望 raw_outline.user_selected_mood = "幽默"（不是 null）
  - 期望 confirmed_outline 跟着对，下游 BGM Haiku 路由到 Comedic 桶（不是 Heartwarming）

### @frontend
- 无影响（前端继续传 user_selected_mood，不需要 schema 变化）

### @pm
- 等 PM 重启 backend 让新 prompt 生效（meta-prompt 是 Python f-string 常量，每次模块加载即注入，但实践上 backend 启动后 Python 文件改动需要 kill+restart 让 import 刷新）
- ai-ml-progress 三件套需 PM 代写（agent 权限受限 — 仅可 read 不可 write progress 目录）

---

## 6. 风险点 + Mitigation

### 风险 1: Prompt 过长，LLM context 压力
**风险**: 旧 B33 块约 30 行 → 新块约 130 行（+100 行 / ~3500 字符），可能稀释其他约束（如 plot_points 一致性、family_relationships transitivity）
**Mitigation**:
- 8 mood 表压缩成单表 / 4 反例每个 2 行 / 自检清单 5 条 / Escape Hatch 1 行
- 关键短语用 `**` 加粗 + `═` 框 + `╔═╗` 方块强化注意力
- 兜底逻辑（改动 5）作为最后一道防线，即使 prompt 失效也保 mood 字段对
**预期**: Sonnet 4.6 / Gemini 3.1 都能处理 16K input，新增 3.5K 不会丢失其他约束。test12 验证。

### 风险 2: LLM 仍然不输出 user_selected_mood 顶层字段
**风险**: LLM 可能因 schema 不强（旧 JSON 示例 L302 没列此字段）而忽略
**Mitigation**:
- system prompt L203 改 `MANDATORY: outline JSON MUST include top-level field user_selected_mood (passthrough)`
- 兜底逻辑（改动 5）静默补字段
**预期**: 即使 LLM 漏写，兜底逻辑保字段一定存在。warning log 可监控漏写率。

### 风险 3: 修 B19 mood_map 影响历史数据
**风险**: 历史 outline 可能依赖旧的（错误的）mood_map 映射（"治愈"→warm）
**Mitigation**:
- 此 mood_map 只在 `_validate_outline` 的 fallback 分支（current_mood 不在 valid_moods 时）触发
- 即历史数据如果 LLM 已正确输出英文 overall_mood，不走 fallback，不受影响
- 只有 LLM 输出非标 mood 时才走 fallback，此时修正后的映射是正确的
**预期**: 实际历史数据影响 0%（fallback 是边缘路径）

### 风险 4: 反例 1 (test11) 太具体，LLM 可能模仿"孤独老人"故事内容
**风险**: 反例 1 提到"孤独老人凌晨3点训练AI客服 → 猫送外卖"，LLM 可能误把它当作示例去生成类似 idea 的故事
**Mitigation**:
- 反例 1 在"必须避免的 slip"段，上下文明确是"反偏置教训"不是"生成示例"
- 4 个反例各覆盖不同 mood（幽默/热血/温馨/紧张），分散注意力
**预期**: LLM 模仿风险 < 5%。可通过 test12 用全新 idea 验证。

---

## 7. 回滚方案

如发现 B47 改动导致 outline 质量退化（如其他字段一致性下降）：

```bash
cp /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/app/services/story_outline_generator.py.bak-20260511-b47-pre \
   /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story/app/services/story_outline_generator.py

# PM 重启 backend
```

**回滚条件**:
- LLM 输出其他必填字段（plot_points / family_relationships / unique_locations）出现退化 ≥ 20%
- LLM 输出长度暴涨超过 max_tokens 16384（被截断导致 JSON 不完整）

**回滚后**:
- B33 旧版仍能强制 mood 字段（虽然无 PREFER/AVOID 表）
- 兜底逻辑（改动 5）独立于 prompt，可考虑保留兜底但回滚 prompt 块

---

## 8. 待做（B47 闭环后）

| # | 项 | Owner | 时机 |
|---|---|---|---|
| 1 | PM 重启 backend 让新 prompt 生效 | @pm | 即时 |
| 2 | Founder test12 真测验证（同 idea + mood="幽默"）| @founder + @tester | 等 PM 重启后 |
| 3 | 如 test12 仍滑 mood → 加强 prompt 或加 Pydantic schema 校验 | @ai-ml | 等验证结果 |
| 4 | 监控 warning log 中 "B47 兜底纠正 mood" 触发率 | @backend | 1 周后 |
| 5 | 如触发率 > 30% → prompt 仍有缺陷 / 如触发率 < 5% → prompt 有效，兜底冗余可保留 | @ai-ml | 1 周后 |

---

## 9. Commit Message 草稿

```
feat(stage1): B47 加 sub-vibe 反偏置约束 + user_selected_mood 透传保险

真根因 (test11 5-11 15:25 实测):
- 用户选"幽默" → DB ✅ + backend log ✅ + LLM 输出 mood="治愈" ❌
- 故事含"孤独/凌晨/独居"内敛诱因 → LLM 滑向"治愈"sub-vibe
- raw_outline.user_selected_mood=None（LLM 漏写透传字段）

改动 (app/services/story_outline_generator.py, 单文件 / 6 处):
1. system_prompt: mood 6 选项 → 8 选项 + user_selected_mood 必填
2. JSON schema 注释: mood 字段 6 → 8 选项
3. 创作要点 #10: 8 选项 + 用户约束块覆盖优先级
4. mood_constraint 块: 加 8 mood × PREFER/AVOID 表 + 4 反例 + 形状>内容铁律 + 输出前自检
5. generate() return 前兜底: 强 enforce mood/user_selected_mood/overall_mood 三字段
6. _validate_outline mood_map: 修 B19 写反的 bug (治愈→heartwarming, 温馨→warm)

验证:
- AST PASS / pytest test_architecture 7/7 PASS / 不退化
- B47 关键词命中 16 处 / 686→782 行 (+96)
- 备份: story_outline_generator.py.bak-20260511-b47-pre

待: PM 重启 backend + Founder test12 真测验证

Refs: B47 PEND / B40 BGM Haiku Sub-Vibe Default Lock (2026-05-09)
```
