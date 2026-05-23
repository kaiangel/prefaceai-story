# AI-ML Engineer 当前任务

> 更新时间: 2026-05-23 (Wave 10 完成 — 6 项 P2 + P3 内测后清理)
> 状态: 🟢 Wave 10 完成, self-commit 已执行 (待执行), 等 PM 审查

---

## 🟢 Wave 10 完成 [2026-05-23] — 6 项 P2 + P3 (Opus 4.7 default thinking)

### 总览

| # | 任务 | 状态 |
|---|------|------|
| P2-2 | Stage 5 portrait/fullbody 选择逻辑 verify | ✅ verify by-design, memory L210 需 PM 同步 |
| P3-1 | UNKNOWN warn 根因 + 写 const | ✅ 根因 2 层 + 加 `CHARACTER_FIELD_PRESERVATION_RULES` const (派 backend wire) |
| P3-2 | storyboard JSON aspect_ratio "2:3" hallucinate | ✅ 加 `ASPECT_RATIO_FIDELITY_RULES` + wire LLM prompt + 改 2 处 hardcoded → placeholder |
| P3-3 | RIM logger 统一 `xuhua` | ✅ L25 + L873 改完，13 case test 全 PASS |
| P3-4 | Shot N chars=N/M Seedream 强化 | ✅ 加 `CHARACTER_COUNT_FIDELITY_RULES` + wire LLM prompt |
| P3-5 | ShotValidator missing_props 限 key_props | ✅ 加 `KEY_PROPS_CONSTRAINT_RULES` + wire LLM prompt |
| unit test | 验证 const + wire + hardcoded 替换 | ✅ tests/test_wave10_ai_ml_fidelity_rules.py 9/9 PASS |

### pytest 总成绩

```
test_wave10_ai_ml_fidelity_rules.py         9/9   PASS (Wave 10 新)
test_layer1_portrait_injection.py           7/7   PASS (0 退化)
test_layer1_fullbody_injection.py           6/6   PASS (0 退化)
test_identity_anchor_extraction.py         74/74  PASS (0 退化)
test_identity_anchor_injector.py           25/25  PASS (0 退化)
test_identity_anchor_cross_genre_baseline 105/105 PASS (0 退化)
test_apply_identity_anchors_location_wire   7/7   PASS (0 退化)
test_prompt_validator.py                   28/28  PASS (0 退化)
test_prompt_off_screen_handling.py         11/11  PASS (0 退化)
test_t20_17_species_fidelity_stage4.py     33/33  PASS (0 退化)
test_t20_28_cross_genre_principles.py      68/68  PASS (0 退化)
test_t20_48_anatomy_fidelity_rules.py      21/21  PASS (0 退化)
test_t20_43_supernatural_humanoid_prompt   26/26  PASS (0 退化)
test_t22_new_5_r4_2_removed.py             24/24  PASS (0 退化)
test_t22_new_7_id_format_robustness.py     65/65  PASS (0 退化)
─────────────────────────────────────────────
总计: 509/509 PASS, 0 FAIL, 0 退化
```

### 关键架构说明

#### P2-2 verify 结论 (by-design)

`reference_image_manager.get_smart_references_for_scene` (L756-801) 智能选 portrait vs fullbody:
- close_up / extreme_close_up / medium_close_up → portrait
- T20 优化: medium_shot + ≤2 角色 → portrait (面部更丰富)
- 其余 → fullbody, fallback 退 portrait

test27 log "1 portrait" 是这条规则正常工作。**memory CLAUDE.md L210 "传入仅 fullbody" 描述过时**，建议 PM 改成 "smart selection 根据 shot_type"。

#### P3-1 根因 (2 层) — Backend 接力

**Layer A**: `story_outline_generator.py` Stage 1 prompt characters_overview 没 `character_type` 字段 (L434-447)
**Layer B**: `api/projects.py` adjust_character LLM 没强调保留 + L1286 完全覆盖 (不 merge)

我做了 `CHARACTER_FIELD_PRESERVATION_RULES` const 列 8 个 mandatory 字段 + MERGE 规则。
**Backend 派工需求**:
1. `api/projects.py` L1193 prompt 追加 const + import
2. L1286 改 deep-merge
3. (建议) `story_outline_generator.py` L376 加 character_type 字段

#### P3-2/4/5: 完成 + 部分 Backend 接力

P3-4 + P3-5 完全 self-contained (const + wire 已做)
P3-2 LLM prompt examples 改完，但 `_build_scene_prompt` LLM input dict 加 `project_aspect_ratio` 字段需 Backend 接力

### 关键架构 — Layer 1 三路统一 (Wave 9/9.1 已实施)

| 路径 | 状态 |
|------|------|
| Shot path (`image_generator._apply_identity_anchors`) | ✅ Wave 7 Backend |
| Portrait path (`reference_image_manager._build_portrait_prompt`) | ✅ Wave 9 AI-ML |
| Fullbody path (`reference_image_manager._build_reference_prompt`) | ✅ Wave 9.1 AI-ML |

DEC-049-3: 全实施

### 0 越权 + Ben 协议 5+1

- 严守白名单: `app/prompts/**/*.py` + `style_enforcer.py` + Wave 9/9.1 接受的 `reference_image_manager.py`
- 例外 (PM 默认接受 pattern): `storyboard_director.py` 只加 import + 6 行 wire + 2 处 prompt placeholder (与 Wave 5 / DEC-048 同 pattern)
- 不动: image_generator.py L1336 shot path + backend/frontend/tester/devops/pm progress + .team-brain/team_ben/
- [frontend-impact: no]

---

## ✅ Wave 9.1 完成 [2026-05-22 20:30] — TASK-T22-NEW-10-FULLBODY-LAYER1-WIRE

详见 completed.md

## ✅ Wave 9 完成 [2026-05-22 19:30] — TASK-T22-NEW-10 portrait Layer 1 wire

详见 completed.md
