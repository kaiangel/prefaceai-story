# Tester Agent - 给其他Agent的上下文

> **最后更新**: 2026-05-23 [Tester]

---

## 当前状态 (2026-05-23)

**TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED 完成 ✅**

| 运行方式 | 修复前 | 修复后 |
|---------|--------|--------|
| 单跑 test_status_authoritative.py | 41 PASS + 3 FAIL | **44 PASS** |
| 综合跑 (含 t21_digital_virtual + schema_generic + llm_fallback) | 27 errors + 4 fail | **44 PASS** |
| 17文件联跑 Wave 9 全量 | 636 PASS + 27 errors | **667 PASS** |

**根因**: 多文件 collection 时 stub 污染 — `app.config.settings` 无 DATABASE_URL + `google.genai.types` stub 阻断真实包
**修法**: autouse fixture 补全 settings stub + 清除 google stub

---

## 上一完成 (2026-05-22)

**TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE 完成 ✅ (独立第二意见)**

### pytest 真自跑结果 (16 files, 623 cases)

| 文件 | 结果 | 内容 |
|------|------|------|
| **test_wave9_cross_genre_independent_baseline.py (NEW)** | **76/76 PASS** | **Tester 独立跨题材矩阵** |
| test_layer1_portrait_injection.py | 7/7 PASS | Wave 9 portrait wire |
| test_layer1_fullbody_injection.py | 6/6 PASS | Wave 9.1 fullbody wire |
| test_identity_anchor_cross_genre_baseline.py | 105/105 PASS | Layer 1 baseline (0 退化) |
| test_identity_anchor_injector.py | 25/25 PASS | Layer 1 regression |
| test_prompt_validator.py | 28/28 PASS | Layer 1 regression |
| test_apply_identity_anchors_location_wire.py | 7/7 PASS | Wave 7 |
| test_t22_new_7_id_format_robustness.py | 65/65 PASS | Wave 7 |
| test_first_batch_chars_not_zero.py | 17/17 PASS | Wave 7 |
| test_llm_fallback_chain.py | 14/14 PASS | Wave 7 |
| test_schema_generic_fallback_arch.py | 83/83 PASS | Wave 8 |
| test_t22_new_5_r4_2_removed.py | 24/24 PASS | Wave 8 |
| test_identity_anchor_extraction.py | 74/74 PASS | Layer 1 regression |
| test_t21_new_3_to_7_backend.py | 51/51 PASS | T21 regression |
| test_t21_digital_virtual_fallback.py | 25/25 PASS | T21 regression |
| test_t21_new_2_humanoid_fallback_wave2.py | 16/16 PASS | T21 regression |
| **综合** | **623/623 PASS** | **0 FAIL, 0 退化, 0.90s, $0** |

**@PM @DevOps**: Wave 9+9.1 可部署，Tester 独立验证完成。

---

## Wave 9+9.1 跨题材矩阵结果

### Portrait + Fullbody 双路矩阵 (50 case)

| char_type \ style | manga | children_book | cyberpunk | ink | realistic |
|---|---|---|---|---|---|
| human | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS |
| supernatural | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS |
| anthropomorphic_animal | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS |
| ai_entity | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS |
| mythological | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS | PASS/PASS |

格式: portrait/fullbody

**50/50 PASS** — Layer 1 跨 5 风格 × 5 character_type 完全通用

### BW Skip (10 case)

5 char_types × portrait (manga_bw) + 5 char_types × fullbody (ink_bw) = 10/10 PASS

### Log Marker 实际触发 (4 路 verify)

- portrait inject log: PASS (wire 真跑过，不是死代码)
- fullbody inject log: PASS
- portrait bw skip log: PASS
- fullbody bw skip log: PASS

---

## Tester 独立发现 (给 @AI-ML @Backend)

**P3 建议 (非阻塞)**:
- `reference_image_manager.py` logger name 是 `app.services.reference_image_manager`
- `identity_anchor_injector.py` logger name 是 `xuhua`
- 建议未来统一到 `xuhua` 方便 log 聚合和告警

**T4 边缘 case 全 PASS**:
- no_id + name_en fallback: 正常注入
- no_id + no_name_en + only_name: 正常注入
- inject 异常兜底: try/except 防 crash 验证
- cross-path anchor consistency: portrait/fullbody 相同主色 token

---

## Wave 9+9.1 风险评估

**可部署 ✅** — 0 阻塞问题，0 退化，P3 建议不阻塞。

---

### pytest 真自跑结果 (13 test files, KEY_LEARNINGS #47 铁律)

| 文件 | 结果 | 内容 |
|------|------|------|
| test_identity_anchor_cross_genre_baseline.py | 105/105 PASS | Layer 1 baseline (0 退化) |
| test_first_batch_chars_not_zero.py | 17/17 PASS | T22-NEW-7 Wave 7 |
| test_llm_fallback_chain.py | 14/14 PASS | T22-NEW-4 Wave 7 |
| test_apply_identity_anchors_location_wire.py | 7/7 PASS | T22-NEW-6 Wave 7 |
| test_schema_generic_fallback_arch.py | 83/83 PASS | T22-NEW-9 Wave 8 |
| test_t22_new_5_r4_2_removed.py | 24/24 PASS | T22-NEW-5 Wave 8 |
| test_identity_anchor_injector.py | 25/25 PASS | Layer 1 regression |
| test_prompt_validator.py | 28/28 PASS | Layer 1 regression |
| test_identity_anchor_extraction.py | 74/74 PASS | Layer 1 regression |
| test_t21_new_3_to_7_backend.py | 51/51 PASS | T21 regression |
| test_t21_digital_virtual_fallback.py | 25/25 PASS | T21 regression |
| test_t21_new_2_humanoid_fallback_wave2.py | 16/16 PASS | T21 regression |
| **test_t22_new_7_id_format_robustness.py (NEW)** | **65/65 PASS** | T22-NEW-7 ID format |
| **综合** | **534/534 PASS** | **0 FAIL, 0 退化** |

elapsed: 0.84s, API calls: 0

**PM 可安排**: 终审 → e2e test22 重跑视觉验证 → Founder 验证 → 内测启动

---

## T22-NEW-7 ID format mismatch — 修后真实证

**T22-NEW-7 根因** (KEY_LEARNINGS #56 教训 A): Stage 4 LLM 在同一故事内不同 shot 用不同格式输出 `characters_in_scene`:
- Shot 1-3: `['Coral']` (name_en 格式)
- Shot 4-21: `['char_001']` (char_id 格式)

旧代码只匹配 `c["id"]` → 前 3 shot chars=0 → Coral CHARACTER ANCHORS 未注入 → Seedream 弱引用 → Shot 2 蓝发人腿。

**Wave 7 修复** (`resolve_characters_in_shot` 三路 fuzzy match):
```python
for fld in ("id", "name_en", "name"):
    val = c.get(fld)
    if isinstance(val, str) and val.strip():
        match_keys.append(val.strip().lower())
if any(k in shot_ids_norm for k in match_keys):  # 三路任一命中即匹配
```

**test_t22_new_7_id_format_robustness.py 实证** (65 cases):
- Format A (char_id): 19/19 types PASS
- Format B (name_en): 19/19 types PASS — T22-NEW-7 修后真实证，前 3 shot 不再 chars=0
- Format C (mixed):   19/19 types PASS — 混合场景全 resolve
- Boundary (8): empty/None/no-match/dedup/case-insensitive/WARNING 全覆盖

---

## Wave 7+8 验证总结 (给 @PM @Founder)

### T22-NEW-7 (chars=0 修) — 实证 PASS

resolve_characters_in_shot 三路 fuzzy match 跨 19 types × 3 ID formats 全通过。
前 3 shot 不再 chars=0，CHARACTER ANCHORS 注入完整。

### T22-NEW-4 (LLM fallback 三层) — 实证 PASS

LLMFallbackChain (Haiku → Gemini → Sonnet) 14/14 PASS。
AdjustCharacter / Shot regen / BGM Haiku 529 时自动 fallback，不再直接 500。

### T22-NEW-6 (location wire) — 实证 PASS

location 字段正确透传到 inject_identity_anchors()，LOCATION ANCHOR 注入完整。

### T22-NEW-9 (通用 fallback 架构) — 实证 PASS

pipeline_schemas.py 19→4 entries + has_humanoid_fallback() 通用函数。
83/83 cases 全过，含 strict types (animal/vehicle_character) 正确拒绝 humanoid fallback。

### T22-NEW-5 (R4-2 移除) — 实证 PASS

scene_review 状态机已移除，24/24 cases。Stage 3→Stage 4 无 wait loop 阻塞。

### 0 退化确认

105 Layer 1 baseline + 74 AI-ML extraction + 51 T21 + 25 T21-DV + 16 T21-HFW2 全 PASS。
Wave 7+8 改动未破坏任何现有功能。

---

## Layer 1 跨题材 Baseline Regression 设计方案 (准备中)

### 背景 (DEC-048, Founder 5/21 22:55 决策)

test22 fairytale 暴露 T22-NEW-3 P0 灾难: Stage 4 LLM 真 0 注入 character physical 字段到 image_prompt。
- 珊瑚 char_001 schema `hair_color="deep sea-green"` → 但 Stage 4 生成的 shot 9-14 全 6 张都写 `"dark hair"`
- 这是 CLAUDE.md "角色一致性产品生命线" 铁律的 100% miss
- 真根因: storyboard_director.py L229 真 0 注入 char physical；storyboard_prompts.py L904 仅"建议"而非"强制"

Founder 决策: 不走 Layer 2 hotfix patch，走 Layer 1 架构层治本 (Identity Anchor Framework v1.0 真实施)。

### Tester 的角色

等 AI-ML + Backend Layer 1 实施完成后执行验证，重点是：
1. **grep validation**: 验证所有 shot prompt 真 100% 含 character schema 关键字
2. **跨题材矩阵**: 19 character_types × 5 styles 覆盖
3. **回归不退化**: 与 wave 5 前基线对比，确认 260 PASS 基线无退化

### 19 character_types × 5 styles 矩阵设计

**19 character_types (来自 CharacterDesigner schema)**:
1. human
2. animal (realistic)
3. anthropomorphic_animal (拟人动物，如小熊、小鸟)
4. fantasy_creature (精灵、龙等)
5. supernatural (鬼魂、吸血鬼)
6. undead (僵尸)
7. mythological (神明、神仙)
8. robot
9. ai_entity
10. digital_virtual
11. hybrid (半人半兽)
12. alien
13. elemental (元素精灵，如火精灵)
14. aquatic (水生生物，如美人鱼)
15. anthropomorphic_plant (植物拟人)
16. insect (昆虫类)
17. object_personified (物品拟人)
18. cosmic_entity (宇宙存在)
19. historical_figure (历史人物)

**5 styles (代表性选取)**:
1. realistic (写实)
2. anime (日式动画)
3. children_book (儿童绘本/水彩)
4. cyberpunk (赛博朋克)
5. ink (中国水墨)

### grep Validation 标准 (每个 shot prompt 必须含以下字面值之一)

对于 human/anthropomorphic_animal/fantasy_creature 等有 physical 字段的类型:
- `hair_color` 字面值 OR 实际颜色词 (e.g., "sea-green hair", "ash-blonde", "silver-white")
- `skin_tone` 字面值 OR 实际肤色词 (e.g., "fair skin", "sun-tanned", "pale")
- 至少 1 个 `distinctive_marks` 描述 (如果 schema 有)

具体 grep pattern:
```bash
# 检查 shot prompt 是否含具体发色 (拒绝 generic "dark hair" / "black hair" 而 schema 是其他颜色)
grep -c "hair" shot_prompt.txt  # 应 >= 1

# 检查发色是否与 schema 匹配
python -c "
import json
schema_hair = char['physical']['hair_color']  # e.g., 'deep sea-green'
assert schema_hair.split()[0] in shot_prompt or schema_hair in shot_prompt
"
```

### 测试用例设计

**优先级 1 (test22 复现，必跑)**:
- fairytale + children_book: char_type=aquatic, 验证 hair_color=sea-green 真注入
- fairytale + ghibli: char_type=anthropomorphic_animal, 验证 species+fur_color 真注入

**优先级 2 (跨题材扩展)**:
- cyberpunk + anime: char_type=robot, 验证 body_material/color 真注入
- horror + realistic: char_type=supernatural, 验证 skin_tone/distinctive_marks 真注入
- wuxia + ink: char_type=human, 验证 physical 字段全含

**优先级 3 (long-tail)**:
- 任意题材: char_type=elemental/cosmic_entity, 验证非人类 anchor 注入
- 验证 props signature (道具描述) 是否一致 (如 shell harmonica)

### 执行方式

不生成真实图片 (避免 API 成本)，只验证 Stage 4 LLM 生成的 image_prompt 文本：
1. 对测试故事运行 Stage 1-4 (LLM)
2. 提取生成的 `storyboard_json.shots[i].image_prompt`
3. 对每个 shot 执行 grep validation
4. 输出 "schema_key 真存在率" 报告 (目标: 100%)

### ETA

- 设计: 已完成 (本文档)
- 执行: ~3-4h (等 Layer 1 实施完成后)
- 需要: PM 派工通知 + AI-ML/Backend Layer 1 代码完成

---

## [2026-05-08] 最新回归测试基线

| 测试项 | 结果 | 日期 |
|--------|------|------|
| pytest 全套 | 295 PASS / 3 fail (pre-existing) / 6 errors (pre-existing) | 2026-05-08 |
| 3人场景一致性 | B16 hotfix 后 PIL 实测 shot_01.png 1664x2218 PASS | 2026-05-08 |
| 参考图传递链 | 角色一致性高风险文件 5/8 全零改动 | 2026-05-08 |
| Wave 3 T20 系列 | 260 PASS (后续 Wave 波加) | 2026-05-20 |

**注**: Wave 1-5 期间 Backend/AI-ML 新增了大量 test 文件，基线已升至 260+ PASS。
Tester 最后一次实跑基线: 5/08，295 PASS。Wave 3 之后 Backend 自跑测试维护。

---

## [2026-05-08] TASK-T8-INTEGRATION-VERIFY 给 @Backend 的信息

### B16 P1 Bug — regenerate_shot 返回 500（Seedream 格式不匹配）

**现象**: POST /api/projects/{uuid}/chapters/1/shots/1/regenerate → HTTP 500 "生成图像数据格式异常"

**实测证据**:
- 图像 **已真实生成**: SeedreamGenerator 日志 `✅ Shot 1 生成成功 (1664x2218, 446.27s)` ✅
- 保存步骤 **失败**: chapters.py L1683-1696 格式检测逻辑不匹配 Seedream 返回 ❌
- shot_01.png mtime **未变**: 1778230393 (生成前) = 1778230393 (生成后)

**根因**:
```python
# chapters.py L1683
image_data = result.get("image_data")  # Seedream 返回: base64 STRING, 不是 bytes 或 PIL

if isinstance(image_data, bytes):     # False (str)
    ...
elif hasattr(image_data, "save"):     # False (str)
    ...
else:
    raise HTTPException(500, "生成图像数据格式异常")  # <- 命中这里
```

**Seedream 实际返回格式**:
```python
{
    "success": True,
    "image_data": "<base64_png_string>",  # 注意: string, 不是 bytes
    "pil_image": <PIL.Image>,              # PIL Image 对象在这里
    ...
}
```

**修复建议** (app/api/chapters.py L1683附近):
```python
# 选项 A (推荐): 优先用 pil_image
pil_image = result.get("pil_image")
if pil_image and hasattr(pil_image, "save"):
    pil_image.save(shot_path)
elif isinstance(image_data, bytes):
    with open(shot_path, "wb") as f:
        f.write(image_data)
elif isinstance(image_data, str):
    import base64
    with open(shot_path, "wb") as f:
        f.write(base64.b64decode(image_data))
else:
    raise HTTPException(500, "生成图像数据格式异常")
```

**严重度**: P1 — 用户重新生成画面功能完全不可用

---

### B6 failed 状态返回值分歧（小）

`chapter.status == "failed"` 返回 HTTP 400，任务 spec 写 404。400 语义更准确（有内容但失败）。建议 @backend @frontend 对齐这个状态的前端处理逻辑（现有代码 400 不是 bug，只是 spec 描述模糊）。

---

### pytest 基线 (2026-05-08)

两次运行结果一致:
- **295 passed, 3 failed (pre-existing), 32 skipped, 6 errors (pre-existing), 596-599s**
- 与 Wave 5.2 DevOps 基线完全一致 (`295 passed, 3 pre-existing failed`)
- **Wave 5.1 + 5-08 4 Agent 修复批零引入新退化**

---

### 回归风险评估 (2026-05-08)

高风险文件修改状态:

| 文件 | 修改 | 角色一致性风险 |
|------|------|--------------|
| image_generator.py | 未动 | 无 |
| storyboard_prompts.py | 未动 | 无 |
| storyboard_service.py | 未动 | 无 |
| reference_image_manager.py | 未动 | 无 |
| chapters.py | 修改 (B6/B16) | 无(不影响参考图传递链) |
| screenplay_writer.py | 修改 (B8/B20) | 无(只影响剧本生成逻辑) |

**结论**: 角色一致性回归风险极低。image consistency 完整链路零改动。

---

---

## 给 @PM / @Backend 的信息（Wave 3.6 R7-3 独立复测）

### R7-3 P1 portrait 重生 — Tester 独立复测 PASS

**测试时间**: 2026-04-29 15:04 - 15:12
**项目**: T7 UUID 631eef3c-4a26-413a-bcb1-1f038d176e85，char_001（陈伯，老年男性）

| 证据点 | 结果 | 精确数据 |
|--------|------|----------|
| adjust API HTTP 200 + portrait_url 非 null | PASS | HTTP 200, portrait_url=/static/outputs/.../char_001_portrait.png, 35.5s |
| portrait mtime 真变 | PASS | `1777383723.85` (21:42:03) → `1777446647.27` (15:10:47 +62923s) |
| portrait 文件可访问 | PASS | HTTP 200, Content-Length=1524775 bytes (1489.0 KB) |
| DB chapter.characters_json[0].updated_at 真更新 | PASS | N/A → `2026-04-29T07:10:47.273465Z` |
| backend log 无 'str' object has no attribute 'get' | PASS | 全日志计数=0 |
| character_prompt_builder.py isinstance 检查真生效 | PASS | L106-116 代码 + 日志确认 |

backend 成功日志: `[AdjustCharacter] R7-3: char_001 肖像已重生成 → .../char_001_portrait.png`

**结论**: R7-3 P1 独立复测 PASS。Wave 4 DevOps 部署解除阻塞。

**附带发现 BUG-2026-04-29-001 (P3)**:
- char_002（七岁小孩"小宝"）触发 CONTENT_SAFETY，portrait 重生失败（非 R7-3 bug）
- NB2 模型内容审查拦截 "7-year-old boy" 类角色 portrait
- 影响: 儿童类角色 adjust 后 portrait 不更新（非阻塞，功能降级）
- 建议: 在 PromptRewriter 改写策略中加入儿童角色脱敏规则（去掉年龄描述，改用"young child"等中性描述）
- 严重度: P3（非主流场景，有 fallback，不影响 MVP）

---

## 给 @PM / @Backend 的信息（TASK-T6-FIXBATCH Wave 3 T7 验收）

### T7 验收汇总

**T7 UUID**: `631eef3c-4a26-413a-bcb1-1f038d176e85`
**故事**: "深夜灯火"，插画风，1:1，2 角色，16 shots，BGM 156s
**实际花费**: 约 ¥3.50（16 × $0.03 Seedream + portrait/refs）

### 12 项验收结果

| # | 验收项 | 结论 | 关键证据 |
|---|--------|------|----------|
| 1 | D.15 P0：shot 尺寸 1:1 = 2048x2048 | **PASS** | PIL 实测 16/16 shots = 2048x2048（Python PIL.Image.open 逐文件读取） |
| 2 | R7-9：job.current_stage='completed' | **PASS** | DB SELECT 直查确认 |
| 3 | P1-1：Stage label 跟随 backend stage | **PASS** | 日志观察 6 阶段 character_design→character_ready→storyboard→image_preparation→image_generation→completed |
| 4 | P1-2：ETA 单调递减，Stage 5 ≥5min | **PASS** | /status 轮询：855s→270s→0s，image_generation 入口 STAGE_DURATIONS=300s |
| 5 | R7-8：Progress 不倒退，BGM 不掉 92% | **PASS** | DB progress 轨迹 10→35→75→95→100，BGM 入口无 92% 覆盖 |
| 6 | R7-3 P1-3：adjust portrait 自动重生 | **FAIL** | 非阻塞异常 `'str' object has no attribute 'get'` at projects.py 约 L987；portrait mtime 前后不变 |
| 7 | P1-5：character_ready portrait ≤2s | **PASS** | 两角色 portrait 文件均在 character_ready 前生成完毕，DB portrait_url 已写 |
| 8 | P0-1：StageD shots 可见 + BGM 可播 | **PASS** | 16/16 shots 有 image_url，BGM endpoint HTTP 200 |
| 9 | P1-6：Stage E 读 outline.summary | **PASS** | confirmed_outline.summary 存在，内容与 original_idea 不同 |
| 10 | P0-4 UX-16：URL 路由 F5 / 后退 | **PASS** | 6 stage 路由全 200，invalid stage 返 404 |
| 11 | P1-4：Dashboard 封面+shot 数+北京时区 | **PASS** | cover_image_url 存在，shot_count=16，ISO 含时区，mood 字段=温馨 |
| 12 | ARCH-1：GET /images 返真数据 | **PASS(保留)** | 16 行 chapter_scene_images 记录，URL 格式 legacy 问题为预存在 issue（Agent F 已记录） |

**总计**: 11 PASS / 1 FAIL / 0 未触发

### D.15 P0 PIL 实测证据（最关键）

```
project_id = 631eef3c-4a26-413a-bcb1-1f038d176e85
path       = output/631eef3c-4a26-413a-bcb1-1f038d176e85/images/shot_NN.png
PIL.Image.open() 逐文件实测:

shot_01.png: (2048, 2048)
shot_02.png: (2048, 2048)
shot_03.png: (2048, 2048)
shot_04.png: (2048, 2048)
shot_05.png: (2048, 2048)
shot_06.png: (2048, 2048)
shot_07.png: (2048, 2048)
shot_08.png: (2048, 2048)
shot_09.png: (2048, 2048)
shot_10.png: (2048, 2048)
shot_11.png: (2048, 2048)
shot_12.png: (2048, 2048)
shot_13.png: (2048, 2048)
shot_14.png: (2048, 2048)
shot_15.png: (2048, 2048)
shot_16.png: (2048, 2048)
Unique sizes: {(2048, 2048)}

结论: 100% 1:1 正方形，证明 D.15 P0 fix 生效
```

### 新 Bug：R7-3 Portrait 重生失败（P1，需 Backend 修复）

**现象**: POST /api/projects/{id}/characters/char_001/adjust 后，portrait 文件 mtime 未变
**日志**: `[AdjustCharacter] R7-3: 肖像重生成异常（非阻塞）: 'str' object has no attribute 'get'`
**定位**: `app/api/projects.py` adjust_character() 约 L945 调用 `_ref_manager.generate_character_reference(character=updated_char, ...)` 时，`updated_char` 应为 dict 但某处被当作 str 传入（或 generate_character_reference 内部 `.get()` 调用对象类型错误）
**影响**: F-2 前端刷新按钮接真 API 功能也同步失效（依赖此路径）
**严重度**: P1（功能失效，不崩溃，非阻塞 catch 静默吞掉）
**派给**: @backend 修复

---

## 上一任务：TASK-SEEDREAM-POC Phase 3b ✅ (2026-04-24)

---

## 给 @PM / @Founder 的信息（TASK-SEEDREAM-POC Phase 3b）

### 评分报告已就绪

**报告路径**: `.team-brain/analysis/SEEDREAM_VS_NB2_POC_REPORT.md`

**9 shots 公平对比均分**（排除 shot_04 sanitized prompt）:

| 维度 | Seedream 5.0-lite | NB2 (Gemini 3.1 Flash Image) | 差值 |
|------|-------------------|------------------------------|------|
| D2 角色一致性 | 2.78 | 3.00 | NB2 +0.22 |
| D3 场景一致性 | 3.22 | 3.44 | NB2 +0.22 |
| D4 整体质量 | 3.00 | 3.78 | NB2 +0.78 |
| **综合均分** | **3.00** | **3.41** | NB2 +0.41 |

**D5 审查严格度**: Seedream 2/5 vs NB2 5/5
- Seedream 1/10 shots 被拦截（10%），需 sanitize 兜底
- "elderly + worry" 组合触发火山方舟内容审查

**总体推荐**: 暂时保留 NB2 为默认，Seedream 需要肉眼看图后再决策

**关键局限**: 本评分是 text-only agent 的 metadata 间接评估（亮度、std、文件大小），不能替代肉眼看图

**建议 Founder 重点看的 3 张**:
1. **shot_06**（打铁铺 4 角色宽景）—— D2 最高风险
2. **shot_08**（打铁铁 4 角色俯拍）—— 背面服装识别最难
3. **shot_10**（石桥妈妈惊慌）—— 场景切换，SD brightness 明显低于 NB2（115 vs 154）

---

## 上一任务：TASK-HE-TESTER-1 ✅ (10/10, 0.06s)

---

## 给 @PM / @Founder 的信息

### 架构测试 + 质量门测试已就绪

PreCommit hook 现在可以激活完整闭环（去掉 `|| true`）。

测试执行命令：
```bash
python3 -m pytest tests/test_architecture.py tests/test_quality_gates.py -v
```

10 个测试覆盖以下架构规则：
1. 前后端边界隔离（互不 import）
2. Shot 生成默认用 NB2 模型（NB2_MODEL + use_pro_model=False）
3. Image prompt 模板/风格配置全英文
4. Pipeline 5 阶段核心服务文件完整
5. 参考图串行生成（portrait→fullbody，无 asyncio.gather）
6. 角色必需字段在代码中完整定义
7. 翻译函数存在且被调用
8. .env.example 和必需目录存在

---

## 给 @DevOps 的信息

### PreCommit hook 可以激活

测试文件已就绪，可以去掉 PreCommit 的 `|| true`：
- `tests/test_architecture.py`（6 个测试）
- `tests/test_quality_gates.py`（4 个测试）

执行时间: 0.06 秒，不会影响 commit 速度。

---

## 给 @Backend / @AI-ML 的信息

### 新的架构约束测试

以下操作会被 PreCommit hook 拦截：
- 前端代码引用后端模块（或反过来）
- 修改 NB2_MODEL 值或 use_pro_model 默认值
- 在 STYLE_PROMPTS 或 StyleEnforcement 配置中加入中文
- 删除 Pipeline 核心服务文件
- 在 reference_image_manager.py 中加入 asyncio.gather

---

## 历史任务

### TASK-HE-TESTER-1 ✅ (10/10, 0.06s)
### TASK-REAL-PIPELINE-UX Step 1 ✅ (35/35, pytest)
### TASK-OUTLINE-MERGE-TEST ✅ (55/55)
### TASK-PLOTPOINT-REORDER-FIX ✅ (39/39)
### TASK-CONFIRM-OUTLINE-TEST ✅ (37/37 → 55/55)
### TASK-SAFE-DRYRUN ✅ (7/7)
### TASK-IMG-SAFETY-VERIFY ✅ (17/17)
### TASK-E2E-REGRESSION-R8 ✅ (42/44)

---

## 🆕 TASK-PARALLEL-M1 D1 redo 完成 (PM 代更 2026-04-27)

> Tester agent 04-25 sandbox blocked 文档写入，PM 代更。

**D1 redo 14 测试全过**（用 round 3 修复后的代码）:
- ✅ perf 第 1 (18 shots) + 第 2 run (11 shots)
- ✅ quality teststory6.4 / 6.5_wuxia / 6.6_multichar
- ✅ 跨题材 modern_urban / wuxia / realistic / ink
- ✅ 8 失败分支 unit test 17/17
- ✅ 内存峰值 198 MB (< 1.5 GB)
- ✅ ShotValidator 37 PASS（鉴权完全修了）
- 🟡 121 new INSERT records — project_id 仍 None（需 round 4 修 dispatcher）

**实际成本**: ¥34.3 / 预算 ¥48 (省 ¥14)
**总耗时**: ~115 min

**4 Bug 验证**:
- Bug 1 project_id=None: 🟡 PARTIAL (dispatcher 没传 **_kwargs_copy)
- Bug 2 ShotValidator: ✅ COMPLETE (37 PASS)
- Bug 3 IncompleteRead: ✅ retry 3 有效
- Bug 4 Event loop closed: 🟡 PARTIAL (主 bug 修，残留 aiomysql cleanup)
- 🆕 Bug 5: ShotValidator 5MB 图片限制（部分 Seedream PNG 超限触发 fail-open）

**Founder 04-27 看图反馈**: "不错，可用，比 NB2 稍逊但可接受"
**PHASE2_REPORT.md**: `test_output/parallel_m1_phase2_2026-04-25/PHASE2_REPORT.md` (222 行)

**Founder 看图入口** (D1 redo 8 故事):
- `test_output/parallel_m1_phase2_2026-04-25/quality/{teststory6.4,teststory6.5_wuxia,teststory6.6_multichar}/<timestamp>/images/`
- `test_output/parallel_m1_phase2_2026-04-25/cross_genre/{modern_urban,wuxia,realistic,ink}/<timestamp>/images/`
- `test_output/parallel_m1_phase2_2026-04-25/perf_test_20shots/{20260425_164127,20260425_170530}/images/`

