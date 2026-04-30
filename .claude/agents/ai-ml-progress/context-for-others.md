# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-04-24 19:45

---

## ✅ TASK-SEEDREAM-INTEGRATION Prompt 层 — Seedream 2D 风格硬约束 (2026-04-24)

**@backend 必读** — 接入 `seedream_generator.py` 时用这个新方法替代 `enforce_prompt()`:

```python
from app.services.style_enforcer import StyleEnforcer
from app.config import settings

# 替代旧的: StyleEnforcer.enforce_prompt(shot_prompt, style_config.style_preset)
# 新的:
enforced_prompt = StyleEnforcer.enforce_prompt_for_provider(
    original_prompt=shot_prompt,
    style_name=style_config.style_preset,
    provider=settings.IMAGE_GEN_PROVIDER,  # "seedream" or "nb2"
)
```

- `provider="nb2"` → 完全等价于旧的 `enforce_prompt()`，零变化
- `provider="seedream"` → 在 prompt 最开头注入 2D 锁定块（1169 字符），禁止 3D/Pixar/CGI，强制 2D watercolor 画风

**风险提示给 @backend**:
- 锁定块有 Unicode 特殊字符 `▌`，如 Seedream API 不接受请在 `seedream_generator.py` 调用时用 `StyleEnforcer.build_seedream_2d_boost_prefix()` 检查并替换
- 2D 锁定块新增约 1169 字符到 prompt 开头，请确认 Seedream token 限制不会截断

---

## ✅ Wave 1 Step B — 95 风格 music_hint 字段 (2026-04-21)

- `app/services/style_enforcer.py` + `app/models/style_config.py` 都加了 music_hint
- **Backend 使用**: `from app.models.style_config import get_music_hint; hint = get_music_hint(style_name)`
- 未知 style 返回 fallback hint，永远不会抛异常
- 这个 hint 将作为 Haiku 的 user prompt 一部分（music_generation_service.py 会用）

## ✅ v3.2 精修 (2026-04-21，取代 v3.1)

- `meta_mixed_v3_quote_picking.md` 精修（15.2KB，回到 v3 大小）
- 回退 v3.1 的 ASCII 图 + 输出纯净规则大段（Haiku 分心原因）
- 保留 few-shot 示例的纯净（无 markdown 围栏）
- 新加 2 行轻量长度建议（"建议"措辞而非"必须"）
- **与 @backend clean_haiku_output() 配合**：污染清理在代码层，meta-prompt 专注创作

## ✅ TASK-HAIKU-QUOTE-EXTRACTION Step 1 — v3 quote picking (2026-04-21)

- 产出: `meta_prompts/meta_{en,mixed}_v3_quote_picking.md`
- 占位符变化: `{{narration_quotes}}` → `{{full_narration}}`（其他 13 个不变）
- 输出格式: Haiku 需先输出 `<quotes>...</quotes>` 块（独立金句审查）+ BGM prompt
- @backend 脚本 Step 2 需支持 `--quote-mode haiku-pick` 模式读 v3 文件 + 6 故事循环

## ✅ TASK-MUSIC-LANG-AB-V2 Step 1 — meta-prompt v2 升级 (2026-04-20)

- 产出: `meta_prompts/meta_{en,cn,mixed}_v2.md` (9-10KB 每个)
- v1 → v2 变更：新增 cross_sensory 4 条元原则 + 3 精选示例 + ≤400 字符硬约束
- 14 个占位符与 v1 完全一致（脚本只需加参数切换文件名）
- 核心预期：通过硬约束修复 v1 mixed 版 855 字符失控问题

## ✅ TASK-MUSIC-LANG-AB Step 1 — 3 个语言变体 meta-prompt (2026-04-18)

- `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/` 下 3 个文件
- meta_en / meta_cn / meta_mixed，14 个数据占位符一致
- 给 @backend 的 Haiku API 调用用（同一套 story input dict 可 format 三个模板）

## ✅ TASK-MUSIC-EXTRACT — 音乐 Prompt 输入格式定义 (2026-04-17)

**文件**: `.claude/skills/music-prompt/templates/story_input_format.md`

定义了从 Pipeline JSON 中提取音乐 prompt 所需信息的格式。核心字段：
- **必须**: emotional_arc, visual_tone, plot_points, sound_design_hint, narration_tone, narration_pace, narration 金句, atmosphere.mood
- **可选**: temperature_feel, lighting_condition, action_beats emotional_note
- **不提取**: beat_id, duration_hint, location_id, characters_in_scene, dialogue_beats, action 细节

@Backend 用此规范写 `scripts/extract_story_for_music.py`。

## ✅ TASK-MUSIC-TRANSITION — 转折测试 Prompt (2026-04-17)

**文件**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/transition_test_prompt.md`

用年夜饭故事测试 Mureka 是否响应显式分段转折描述：
- Section A (祥和) → wood block hit → Section B (窒息) → firework + silence → Section C (像素钢琴) → Section D (微暖淡出)
- 合并版 856 字符
- PM 已调 API 生成 bgm_transition_test.mp3，等 Founder 试听

---

## ✅ TASK-MUSIC-PROMPT + REWRITE — 6 个故事 BGM Prompt (2026-04-16~17)

6 个测试故事音乐 prompt 全部交付，其中 #3/#4/#6 经 Founder 试听后重写。

**Prompt 文件**: 6 个 `music_prompt.md`（各故事目录下）
**Skill 位置**: `.claude/skills/music-prompt/`

---

## TASK-STAGED-V2-AIML (2026-04-14) — Shot 画面调整 Haiku Prompt

新文件 `app/prompts/shot_adjustment_prompt.py`:
- `SHOT_ADJUSTMENT_SYSTEM_PROMPT`: Haiku 4.5 系统提示词，9 条规则
- @Backend 已集成到 regenerate 端点

## Prompt Format A/B 分析 (2026-04-14)

- 结论：B' 质量等价 A，省 46% token → 已切为默认格式


---

## 🆕 TASK-T5-FIXBATCH BGM-1 完成 (2026-04-27 PM 代更)

**对其他 agent**:
- **@backend**: 用 `from app.services.style_music_hints import get_raw_hint` 给 outline LLM 注入 music_hint。BGM-1 后端部分配合：Stage 1 后 `outline["music_hint"] = get_raw_hint(visual_style_preset)`，下游 story_music_extractor 透传给 Haiku.
- **@tester**: T6 测试时验证 outline.music_hint 字段非空，BGM 听感与故事情绪契合
- **@frontend**: 无影响

**未碰**: style_config.py / style_enforcer.py / music_generation_service.py / meta_mixed_v3_quote_picking.md (Wave 4 + v3.2 已稳)


---

## 2026-04-29 17:33 给同事的关键信息（PM 代更）

**O-1 outline 一致性 prompt** 已加到 `story_outline_generator.py` _build_prompt() L415-427。后续 outline LLM 会主动自检数字/角色名/时间地点物件一致性。如果遇到 plot 间矛盾，可优先怀疑 prompt 规则没生效（grep "故事内部一致性规则"确认）。

JSON 解析 fallback 三路径都加了 logger.warning，监控 R4 启动时可统计 fallback 触发率。
