# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-05-22 20:30 (Wave 9.1 完成 — fullbody Layer 1 wire, 三路统一)

---

# 🟢 [2026-05-22 20:30] Wave 9.1: fullbody path 已 wire Layer 1 (TASK-T22-NEW-10 DEC-049-3)

**给 Backend / PM 注意**:

- `_build_reference_prompt()` (`reference_image_manager.py`) 现在会对彩色风格自动调用 `inject_identity_anchors()`
- 调用签名同 portrait: `inject_identity_anchors(image_prompt=..., characters_in_scene=[character], location=None, style_preset=style_name, props=None, time_continuity=None)`
- **lazy import** (函数内 import) 避免循环依赖
- **BW_STYLES 扩展位**: 同 portrait — `StyleEnforcer.BW_STYLES` 空 set + `_bw` 后缀触发 skip

**当前 Layer 1 wire 状态 (三路全统一)**:
| 路径 | 状态 |
|------|------|
| Shot path (`image_generator._apply_identity_anchors`) | ✅ Wave 7 Backend 已实施 |
| Portrait path (`reference_image_manager._build_portrait_prompt`) | ✅ Wave 9 AI-ML 已完成 |
| Fullbody path (`reference_image_manager._build_reference_prompt`) | ✅ Wave 9.1 AI-ML 本批完成 |

**DEC-049-3**: 已实施，无待修项。

---

# 🟢 [2026-05-22 19:30] Wave 9: portrait path 已 wire Layer 1 (TASK-T22-NEW-10)

**给 Backend / PM 注意**:

- `_build_portrait_prompt()` (`reference_image_manager.py`) 现在会对彩色风格自动调用 `inject_identity_anchors()`
- 调用签名: `inject_identity_anchors(image_prompt=..., characters_in_scene=[character], location=None, style_preset=style_name, props=None, time_continuity=None)`
- **lazy import** (函数内 import) 避免循环依赖，无需修改 `__init__.py`
- **BW_STYLES 扩展位**: `StyleEnforcer.BW_STYLES` 当前为空 set，只有 `_bw` 后缀触发 skip；未来加真黑白风格名进 set 即可

---

# 🟢 [2026-05-22 01:30] Layer 1 M2-M5 真实施完成 — Backend / Tester 真可开工

> 本 section 真**新增**, 描述本 session 真**已实施**的 prompt 改动 + helper 函数签名。
> M1 设计 spec 真保留在下方 (从 "[2026-05-22 00:30] Identity Anchor Framework v1.0" 开始)

## 真**已完成**清单 (本 session, ~3.5h)

### 1. `app/prompts/storyboard_prompts.py` L887-980 — `HAIR_COLOR_REQUIREMENT_RULE` 真重写为分工说明

旧文案 (Format examples / "replace [hair_color] with the actual value") 真**完全删除**, 替换为 `IDENTITY ANCHORS DELEGATION` 块:
- 明确告诉 LLM "anchors managed by backend post-process injection, NOT your responsibility"
- 列出 7 个 narrative variables (LLM 创意层) — pose / expression / camera_angle / camera_distance / emotion / interaction / scene_action
- 列出 4 类 DO-NOTs (character physical / style / location / props anchors 真**不能写**)
- 给出明确"通过 id 或 name_en 引用角色"的示例

### 2. 新建 `app/prompts/identity_anchor_prompts.py` (700+ 行)

**3 个模板常量** (供 Backend 渲染 anchor block):
- `IDENTITY_ANCHOR_MARKER = "[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED"` — idempotency 检测
- `IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE` — f-string template with 6 placeholders ({marker} + 5 anchor block)
- `NARRATIVE_VARIABLES_GUIDANCE` — 已 wire 到 storyboard_director Stage 4 prompt

**6 个 extract helper** (Backend + Tester 真消费):
- `extract_identity_anchors(character: dict) -> dict` — 跨 19 character_types dispatch, 返回 9 stable slots + type-specific extras
- `extract_style_anchors(style_preset: str) -> dict` — 从 `StyleEnforcer.STYLE_ENFORCEMENTS` 取 mandatory[:5] + forbidden[:8]
- `extract_location_anchors(location: dict | None) -> dict` — Stage 1 outline location 真支持多 field 名 (signature_visual / signature_visual_summary / visual_summary / description)
- `extract_props_anchors(props: list | None) -> list[dict]` — Stage 2/3 props, 真**跳过无 signature_visual** 的 props (无法 anchor)
- `extract_time_continuity_anchors(scene: dict | None) -> dict` — Stage 3 scene, 真支持 atmosphere sub-dict
- `extract_distinctive_tokens(text: str, n: int = 3) -> list[str]` — top-N 真去停用词去重, PromptValidator grep 用

### 3. `app/services/storyboard_director.py` — 真 wire NARRATIVE_VARIABLES_GUIDANCE 到 2 处

- L37-39: 真新加 `from app.prompts.identity_anchor_prompts import (NARRATIVE_VARIABLES_GUIDANCE,)`
- L1676-1680: `_build_scene_prompt()` 真在 `{HAIR_COLOR_REQUIREMENT_RULE}` 后真注入 `{NARRATIVE_VARIABLES_GUIDANCE}`
- L2007-2011: `_build_prompt()` (dead code 但同步) 真也注入

### 4. 新建 `tests/test_identity_anchor_extraction.py` (74 case, 74/74 PASS)

- 19 character_types × `extract_identity_anchors()` 全 PASS
- edge cases: 空 / 非 dict / 中文 name fallback / marks 限 2 / 长 mark 截断 / accessories 空 / clothing 缺失 / character_type 缺失默认 human / marks 为 dict / marks 为 str
- `extract_distinctive_tokens` — basic / n 参数 / empty / None / 纯中文 / 混合 / 全停用词 / 纯数字过滤 / 排序保留 / 去重
- 6 styles × `extract_style_anchors()` + 未知 preset + 空 preset
- `extract_location_anchors` — 含/无 signature_visual / None / 中文 name fallback / alt field 名
- `extract_props_anchors` — 含/无 signature / 空/None / 非 dict 跳过
- `extract_time_continuity_anchors` — 全字段 / atmosphere sub-dict / None / 空 dict / 部分字段
- 模板 sanity: marker 真起始 / Unicode boundary / 5 placeholders / NARRATIVE_VARIABLES_GUIDANCE 真含 7 narrative variables + 4 类 DO-NOTs / 5 block format / 空可选 block

### 5. 真回归测试 422 PASS / 0 fail

`tests/test_t20_17 + t20_21 + t20_26 + t20_27 + t20_28 + t20_43 + t20_48 + t20_49 + t21_digital_virtual + t21_new_2 + test_identity_anchor_extraction + wave6_full_regression + prompt_off_screen_handling` — 全 PASS, 0 退化。

---

## 真**Backend 接力开工依据** (~3h, 详细规格)

### A. `inject_identity_anchors()` 签名 (在 `app/services/image_generator.py`)

```python
from app.prompts.identity_anchor_prompts import (
    extract_identity_anchors,
    extract_style_anchors,
    extract_location_anchors,
    extract_props_anchors,
    extract_time_continuity_anchors,
    IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE,
    IDENTITY_ANCHOR_MARKER,
)

def inject_identity_anchors(
    image_prompt: str,
    characters_in_scene: list[dict],   # 完整 character schema, 含 physical / clothing
    location: dict | None = None,       # Stage 1 outline location entry
    style_preset: str = "realistic",
    props: list[dict] | None = None,    # Stage 2/3 props list
    time_continuity: dict | None = None,  # Stage 3 scene
) -> str:
    """5-block identity anchor prepended to image_prompt. Idempotent + edge-safe."""

    # Step 1: Idempotency — return unchanged if anchor already injected
    if IDENTITY_ANCHOR_MARKER in image_prompt:
        return image_prompt

    # Step 2: Extract 5-dimensional anchors via helpers
    char_anchors = [extract_identity_anchors(c) for c in characters_in_scene]
    style_anchor = extract_style_anchors(style_preset)
    loc_anchor = extract_location_anchors(location) if location else None
    props_anchor_list = extract_props_anchors(props) if props else []
    time_anchor = extract_time_continuity_anchors(time_continuity) if time_continuity else None

    # Step 3: Render 5 anchor blocks (your responsibility)
    character_anchors_block = _render_character_anchors_block(char_anchors)  # may be "" if no chars
    style_anchor_block = _render_style_anchor_block(style_anchor)
    location_anchor_block = _render_location_anchor_block(loc_anchor) if loc_anchor and loc_anchor["location_id"] else ""
    props_anchor_block = _render_props_anchor_block(props_anchor_list) if props_anchor_list else ""
    time_continuity_anchor_block = _render_time_anchor_block(time_anchor) if time_anchor and time_anchor["scene_id"] else ""

    # Step 4: Format template + prepend
    anchor_block = IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE.format(
        marker=IDENTITY_ANCHOR_MARKER,
        character_anchors_block=character_anchors_block,
        style_anchor_block=style_anchor_block,
        location_anchor_block=location_anchor_block,
        props_anchor_block=props_anchor_block,
        time_continuity_anchor_block=time_continuity_anchor_block,
    )
    return anchor_block + image_prompt
```

### B. `extract_identity_anchors()` 真返回 dict (Backend 渲染 anchor block 用)

```python
{
    "character_id": str,             # 如 "char_001"
    "name_en": str,                  # 英文名 (中文自动 fallback 到 id)
    "character_type": str,           # 19 types 之一 (默认 "human")
    "identity_anchor": {
        # === 9 个 stable slots — 总是存在 ===
        "hair_color": str,           # 可能 "" (动物 → fur_color)
        "hair_style": str,
        "face_shape": str,
        "skin_tone": str,
        "eye_color": str,
        "eye_shape": str,
        "distinctive_marks_short": list[str],  # 限 2 项, 每项 80 字符
        "clothing_core": {"top": str, "signature_accessory": str},
        # === 主色字段 (跨 type dispatch) ===
        "primary_color": str,         # humanoid → hair_color; animal → fur/feather/scale
        "primary_color_field": str,   # "hair_color" / "fur_color" / "feather_color" / "scale_color" / "skin_color" / "chitin_color" / "plumage_color" / "coat_color"
        # === 类型特异 extras (仅在 schema 存在时填充) ===
        # 可能字段: species / breed / fur_color / feather_color / plumage_color / coat_color
        # / scale_color / skin_color / chitin_color / creature_type / origin_culture / base_form
        # / being_type / undead_type / original_form / robot_type / material / digital_type
        # / object_type / base_object / plant_type / wing_type / body_type / primary_type
        # / body_plan / element_type / material_form / concept_type / giant_type / height_category
        # / base_type / vehicle_type
    }
}
```

### C. 推荐 character anchor block 渲染格式 (与 docs/CHARACTER_IDENTITY_FRAMEWORK.md 协同)

```
## CHARACTER ANCHORS (each visible character)

char_001 (Coral, mythological):
- hair: deep sea-green with teal highlights — long flowing past the waist
- face: oval, fair with luminous aquamarine sheen
- eyes: vivid ocean blue almond
- signature: iridescent scale-shimmer along collarbones; sweeping coral-pink to golden-amber fish tail
- core outfit: soft blush-pink shell-fragment bodice, small pearl-tipped pins in hair

char_002 (Milly, anthropomorphic_animal rabbit):
- species: rabbit
- fur: clean warm ivory white
- face: (no humanoid fallback in schema)
- signature: single pale freckle on tip of left ear
- core outfit: cream knitted vest over white long-sleeve shirt, small woven straw basket
```

### D. `PromptValidator` 接力依据 (M1 spec D.1-D.4 已写好, 用 extract_distinctive_tokens)

```python
from app.prompts.identity_anchor_prompts import extract_distinctive_tokens

def validate_prompt_vs_schema(image_prompt: str, characters_in_scene: list[dict]) -> ValidationResult:
    missing = []
    for char in characters_in_scene:
        anchors = extract_identity_anchors(char)
        ia = anchors["identity_anchor"]
        # hair_color (or primary_color for non-humanoid) — 100% MUST
        hair_text = ia["hair_color"] or ia["primary_color"]
        if hair_text:
            tokens = extract_distinctive_tokens(hair_text, n=3)
            if tokens and not any(tok.lower() in image_prompt.lower() for tok in tokens):
                missing.append({"char_id": anchors["character_id"], "field": ia["primary_color_field"] or "hair_color", "expected": hair_text, "tokens": tokens})
        # skin_tone — 100% MUST (humanoid only)
        if ia["skin_tone"]:
            tokens = extract_distinctive_tokens(ia["skin_tone"], n=3)
            if tokens and not any(tok.lower() in image_prompt.lower() for tok in tokens):
                missing.append({"char_id": anchors["character_id"], "field": "skin_tone", "expected": ia["skin_tone"], "tokens": tokens})
        # distinctive_marks + clothing_core (90% SHOULD, warning level)
        # ...
    return ValidationResult(passed=not missing, missing_anchors=missing, severity="critical" if missing else "info")
```

---

## 真**Tester 接力开工依据** (~1h, baseline 矩阵 95 case)

```python
# 在 tests/test_identity_anchor_cross_genre_baseline.py
from app.prompts.identity_anchor_prompts import (
    extract_identity_anchors,
    extract_distinctive_tokens,
)
# inject_identity_anchors 来自 Backend 接力交付 (app/services/image_generator.py)

@pytest.mark.parametrize("char_type", ALL_19_TYPES)
@pytest.mark.parametrize("style_preset", ["realistic", "anime", "children_book", "cyberpunk", "ink"])
async def test_baseline_case(char_type, style_preset):
    # 1. Mock Stage 1-4 LLM 输出 (固定 fixture)
    characters = mock_characters(character_type=char_type, count=3)
    storyboard = mock_storyboard(characters=characters, num_shots=18)

    # 2. 真跑 inject_identity_anchors() 在 18 shot 上
    for shot in storyboard["shots"]:
        chars_in_shot = [c for c in characters if c["id"] in shot["characters_in_scene"]]
        injected = inject_identity_anchors(
            image_prompt=shot["image_prompt"],
            characters_in_scene=chars_in_shot,
            style_preset=style_preset,
            location=...,
        )

        # 3. grep 验证 — shot prompt 真**100% 含** character schema 关键字
        for char in chars_in_shot:
            anchors = extract_identity_anchors(char)
            ia = anchors["identity_anchor"]
            for field in ("primary_color", "skin_tone"):
                value = ia.get(field, "")
                if not value:
                    continue
                tokens = extract_distinctive_tokens(value, n=3)
                assert any(tok.lower() in injected.lower() for tok in tokens), \
                    f"{char_type}/{style_preset} char {char['id']} field {field}={value!r} tokens {tokens} not in prompt: {injected[:300]}"
```

**注意**: 不调真生图 API (零成本), 只跑 prompt-level grep 验证。

---

## 真**0 阻塞**其他角色

- ✅ Backend 第3批职责 (image_generator wire + PromptValidator) — 函数签名稳定, Backend 真接力即可
- ✅ Tester 第3批职责 (baseline 95 case) — extract helper API 真稳定, Tester 真按 mock fixture 跑
- ✅ Frontend — 0 改动需要 (Layer 1 真纯 prompt + backend post-process)
- ✅ DevOps — 0 改动需要 (不涉及 Alembic / VPS)
- ✅ PM — 真审查 + 协调 + 派 Backend / Tester

---

# 历史 — Identity Anchor Framework v1.0 设计 spec (M1 完整规格)

> 本部分真为 M1 设计文档, 保留供 PM / Backend / Tester 参考完整 spec。
> 真**已实施**的部分在本文件顶部"Layer 1 M2-M5 真实施完成" section。

---

# 🟢 [2026-05-22 00:30] Identity Anchor Framework v1.0 — 完整设计规格 (DEC-048 Layer 1)

> 这是本 session 的核心交付物, 直接给 @backend / @tester / @pm 作为 Layer 1 实施依据。
> Founder 5/21 22:55 决策: 不走 hotfix patch, 选 Layer 1 长期架构治本。
> 设计范围: 跨 19 character_types × 80+ styles × 任意题材通用框架。
> 全文 ~420 行, 包含 A-G 7 个子任务的完整规格。

---

## 0. TL;DR (给协作 agent 30 秒读懂)

**Problem**: Stage 4 LLM 生成 image_prompt 时把 character schema 当软建议自由发挥。test22 实测: 20/20 shot 中 0 个用对 Coral 的 sea-green hair, Shot 9-14 真写"dark hair"。这不是 prompt bug, 是 LLM 创意性与一致性的根本张力。

**Solution**: 把"identity anchor 维护"从 LLM 职责剥离, 交给 Backend post-process 强注入。LLM 只管 narrative variables (创意层), anchor 由代码绕过 LLM 决策强行 prepend 到 image_prompt 起始位置。覆盖 5 维度 anchor:

1. **character anchor** — hair/face/skin/eye/marks/clothing_core (每 shot 出现的每个角色)
2. **style anchor** — mandatory + forbidden keywords (从 StyleEnforcer 提取)
3. **location anchor** — signature_visual + atmosphere + time_of_day (按 location_id)
4. **props anchor** — signature props 的视觉描述 (按 prop_id)
5. **time_continuity anchor** — lighting + time_of_day (按 scene_id)

**新增 validator**: `PromptValidator.validate_prompt_vs_schema()` — grep prompt 包含 character schema 关键字, 不通过 auto-correct (re-inject anchor)。这是 ShotValidator (image vs prompt) 的对偶, 实现完整的 cross-stage validation 链。

**AI-ML 工时**: ~2h (移除建议性 hint + 写新模板 + extract helper + 单测)。依赖 Backend ~3h + Tester ~1h, 总 ETA ~6h。

---

## A. 根本性 Problem 深度分析 (max thinking)

### A.1 LLM 训练机制角度: 为什么"建议性 hint"永远会被自由发挥?

`storyboard_prompts.py` L887-930 (`HAIR_COLOR_REQUIREMENT_RULE`) 写了:

> "For EVERY image_prompt where a character is visible, you MUST explicitly mention that character's hair color using the EXACT value from the character data's physical_summary field."

但 test22 实测 20/20 shot, **0 个用对 Coral 的 sea-green hair**。Shot 10/13 真写"dark hair"。为什么?

**根因 1: RLHF 训练把"narrative quality"奖励信号训成主导**。
- LLM (Sonnet 4.6 / Gemini Pro / GPT-4) 在 instruction tuning 阶段被反复用 "creative writing", "vivid description", "engaging narrative" 等任务训练。
- 写"dark hair drifting underwater"比"sea-green hair drifting underwater"在 RLHF 评分上更"诗意" — sea-green 是 schema 词, 不符合多数训练样本的"美学惯例"。
- LLM 在多重指令冲突时, 真**优先满足 RLHF reward signal**, 而不是用户最新的指令。MUST/EXACT 这类强词在大量训练样本里也被"礼貌地无视"过。

**根因 2: instruction tuning 教会 LLM "intent over literal"**。
- LLM 被训练成"理解用户的更高意图"而不是"严格机械执行"。
- 当 schema 说 hair="deep sea-green with teal highlights, like sunlit seaweed" 时, LLM 真**自动总结"underwater mermaid hair"语义**, 输出"flowing dark hair"是它认为的"更自然的表达"。
- 它真不是在违抗指令, 它是在"用更好的方式实现你的意图"。

**根因 3: 创意性 vs 一致性是 LLM 训练目标的根本张力**。
- 创意性: temperature > 0, sampling diversity, "vivid storytelling"
- 一致性: deterministic output, exact token reproduction, "schema compliance"
- 这两个目标在数学上是矛盾的 (互信息正交)。RLHF 优化创意性时一定牺牲一致性, 反之亦然。
- **任何 prompt 工程都无法根治这个张力** — 因为它根植于训练目标。

**根因 4: 当前 Pipeline 让 LLM 同时管创意 + 一致, 注定失败**。
- Stage 4 LLM 收到的指令是 "be creative AND maintain schema fidelity" — 这是 dual mandate
- LLM 真**永远偏向 creative**, 因为 creative 是它的 native strength
- 解决方案不是写更强的指令 (无效), 是 **separation of concerns**: LLM 只管 creative, Backend 管 fidelity

**关键洞察**: 同问题不止序话Story。Midjourney 用户输入 "/imagine girl with blue hair" 模型也常常忽略 blue 输出 black hair。这是 LLM-generated visual content 整个行业的通用问题。我们的方案 (Identity Anchor 强注入) 真能成为序话Story 的**架构级竞争优势** — 用户能感受到"角色真的是同一个人"。

### A.2 跨 19 character_types × 80+ styles: 哪些"应该 anchor", 哪些"应该 variable"?

判断边界的核心问题: **观众认出角色/场景/风格的关键特征是什么?**

| 特征类型 | 应该 anchor? | 理由 |
|---------|-------------|------|
| hair_color | 🟢 是 | 远景剪影也能辨识, 跨 shot 必须一致 |
| hair_style | 🟢 是 | 长发 vs 短发差异巨大, 跨 shot 必须一致 |
| face_shape | 🟢 是 | 脸型决定五官底层结构 |
| skin_tone | 🟢 是 | 跨 shot 漂移 = 不同人 |
| eye_color | 🟢 是 | 近景特写关键 |
| distinctive_marks | 🟢 是 | 疤痕/纹身/标志性特征, 角色"身份证" |
| clothing_core | 🟢 是 | 主装 (top + signature 配饰), 跨 shot 必须一致 |
| pose | 🔴 否 | 每 shot 不同, 服务于动作叙事 |
| expression | 🔴 否 | 每 shot 不同, 服务于情绪叙事 |
| camera_angle | 🔴 否 | 每 shot 不同, 服务于构图 |
| emotion | 🔴 否 | 每 shot 不同, 服务于剧情 |
| interaction | 🔴 否 | 每 shot 不同, 服务于场景动作 |
| eye_shape | 🟡 边界 | 真锚定 — 但表情会变 eye 开合度 |
| eyebrows | 🟡 边界 | 真锚定形状 — 但表情会变 eyebrow 角度 |

**边界规则**: anchor = "脱离当前 shot 也成立的稳定身份特征"。variable = "为当前 shot 叙事服务的瞬时状态"。

### A.3 docs/CHARACTER_IDENTITY_FRAMEWORK.md v1.0 历史 — 为什么早写好但未实施?

文档 2026-02-26 由 AI-ML 写, DEC-012 决策 1 (Founder 提出)。**漏了什么落地机制?**

1. **Stage 2 输出未引入 `identity_anchors` 字段** — Founder 当时建议但 CharacterDesigner prompt 未改, 仍输出扁平 physical + clothing
2. **未设计 backend post-process 注入机制** — 文档只说"prompt 中强调"但没说"绕过 LLM"
3. **未引入 PromptValidator** — 只有 ShotValidator (image vs prompt) 这种事后兜底, 没有 prompt 生成阶段的实时校验
4. **没跨 5 维度 anchor** — 只想 character, 没想 style/location/props/time_continuity 同样问题

**Layer 1 v1.0 设计补全这 4 个缺失机制**, 完成 Founder 早期愿景。

---

## B. Identity Anchor Framework v1.0 完整规格 (max thinking)

### B.1 Identity Anchors (锁定不变) — 精确字段定义 + JSON 模板

#### B.1.1 Character Anchor

```json
{
  "character_id": "char_001",
  "name_en": "Coral",
  "character_type": "mythological",
  "identity_anchor": {
    "hair_color": "deep sea-green with teal highlights, like sunlit seaweed",
    "hair_style": "long flowing past the waist, loose and undulating, with small pearl-tipped pins near the temples",
    "face_shape": "oval",
    "skin_tone": "fair with a soft luminous aquamarine sheen — subtly iridescent",
    "eye_color": "vivid ocean blue, faintly luminescent",
    "eye_shape": "almond",
    "distinctive_marks_short": [
      "fine iridescent scale-shimmer along the collarbones",
      "lower body is a sweeping fish tail of overlapping scales in gradient coral-pink to golden-amber"
    ],
    "clothing_core": {
      "top": "soft blush-pink top woven from interlocking pale pink and cream shell fragments, fitted bodice",
      "signature_accessory": "small pearl-tipped pins in hair"
    }
  }
}
```

**提取规则** (`extract_identity_anchors(character: dict) -> dict`):
1. 必含字段: `hair_color` / `hair_style` / `face_shape` / `skin_tone` / `eye_color` / `eye_shape` (空字符串占位, 不能 None)
2. 可选字段: `distinctive_marks_short` (从 `physical.distinctive_marks` 截取前 2 条, 每条 ≤ 80 chars)
3. clothing_core: `top` (从 `clothing.top`) + `signature_accessory` (从 `clothing.accessories[0]`, 若无则空)
4. 19 character_types 通用 — 对 anthropomorphic_animal 这类 type, hair_color 字段可能是 `fur_color` / `feather_color`, extract helper 自动 dispatch
5. 中文字段自动用 `_strip_chinese_bilingual_segments()` 清洗

#### B.1.2 Style Anchor

```json
{
  "style_preset": "children_book",
  "style_anchor": {
    "mandatory_keywords_top5": [
      "children's book illustration",
      "soft watercolor textures",
      "hand-drawn line work",
      "warm pastel palette",
      "storybook aesthetic"
    ],
    "forbidden_keywords_top8": [
      "photorealistic",
      "3D render",
      "CGI",
      "Pixar",
      "Disney 3D",
      "realistic rendering",
      "scary",
      "violent"
    ],
    "style_signature_line": "soft pastel watercolor illustration with hand-drawn line work and storybook warmth"
  }
}
```

**提取规则**: 从 `StyleEnforcer.STYLE_ENFORCEMENTS[style_preset]` 取 `mandatory_keywords[:5]` + `forbidden_keywords[:8]` + 拼装 signature line。

#### B.1.3 Location Anchor

```json
{
  "location_id": "loc_001",
  "location_anchor": {
    "name_en": "underwater_palace",
    "signature_visual": "bioluminescent coral pillars, schools of small silver fish, kelp forests swaying in current",
    "atmosphere": "soft blue-green ambient light filtering down from the surface, dust motes glowing in shafts",
    "time_of_day": "perpetual underwater twilight",
    "interior_or_exterior": "interior"
  }
}
```

**提取规则**: 从 Stage 1 `1_outline.json` 的 `unique_locations[]` 取 `signature_visual_summary` (Stage 1 prompt 已有此字段) + 从 Stage 3 `3_screenplay.json` 取 `atmosphere`。如果 location 无 signature_visual, fallback "see scene reference image (loc_001 interior/exterior anchor)"。

#### B.1.4 Props Anchor

```json
{
  "prop_id": "prop_001",
  "prop_anchor": {
    "name_en": "shell_harmonica",
    "signature_visual": "small palm-sized harmonica carved from a single pink-and-cream spiral shell, faint inner glow of pearl"
  }
}
```

**提取规则**: 从 Stage 2 `2_characters.json` 的 `character_specific_directions.signature_props[]` 或 Stage 3 `scene.key_props[]` 提取。Phase 2.0 schema 已支持但 LLM 输出不稳定 — Layer 1 实施时需同步加强 Stage 2/3 prompt 让 LLM 必输出 signature_visual 字段 (1 句话视觉描述)。

#### B.1.5 Time Continuity Anchor

```json
{
  "scene_id": 5,
  "time_continuity_anchor": {
    "time_of_day": "golden morning sunrise",
    "lighting": "warm amber light from the rising sun, long shadows toward the west, golden ripples on water surface",
    "weather": "clear sky, light sea breeze",
    "continuity_from_previous_scene": "shot 9 was night at underwater palace, shot 10 is now morning at fishing village dock — explicit time jump"
  }
}
```

**提取规则**: 从 Stage 3 `scene.time_of_day` + `scene.lighting` + `scene.weather` 直接读。`continuity_from_previous_scene` 由 Stage 4 输出后, Backend 计算前后场景对比生成。

### B.2 Narrative Variables (LLM 创意层) — 字段定义

| 字段 | 字段类型 | LLM 创意范围 | 示例 (test22 Shot 10 Coral) |
|------|---------|-------------|------------------------------|
| pose | string | 全身姿态 | "chin lifted, both hands raised to chest" |
| expression | string | 面部表情 | "eyes wide and direct, gaze locked unflinchingly" |
| camera_angle | enum | birds_eye/high/eye/low/dutch | "low_angle" |
| camera_distance | enum | ECU/CU/MCU/MS/MWS/WS/EWS | "medium_shot" |
| emotion | string | 情绪状态 | "determination, defiance" |
| interaction | string | 与其他角色/环境互动 | "facing the Sea Witch beyond, hands wrap around shell harmonica pendant" |
| scene_action | string | 场景动作描述 | "stands at the underwater palace center" |
| dialogue | string (中文 OK) | 对白内容 (Stage 3 提供) | "我不怕你。" |

**关键边界**: pose/expression/emotion 真允许 LLM 自由创意 (服务叙事), 但 hair/face/skin/marks/clothing_core 真**绝对不能让 LLM 写** (Backend 强注入)。

### B.3 跨 19 character_types 统一 framework + anchor 字段 mapping

| character_type | character anchor 必含字段 | 备注 |
|----------------|--------------------------|------|
| human | hair_color / hair_style / face_shape / skin_tone / eye_color / eye_shape / distinctive_marks_short / clothing_core | 标准模板 |
| anthropomorphic_animal | species + fur_color (or feather_color / plumage_color / coat_color / scale_color) + 半人形 hair_color (T21-NEW-2 fallback) / skin_tone / face_shape / clothing_core | species 优先, 然后 fur/feather/scale |
| animal | species + fur_color (or feather_color / plumage_color / scale_color / skin_color / chitin_color) | 纯动物, 不需 humanoid 字段 |
| supernatural | being_type + 人外貌 hair_color / skin_tone / face_shape / eye_color (T20-43 fallback) | 镜中人/鬼魂呈人形 |
| undead | undead_type + original_form + 人外貌 hair_color / skin_tone / face_shape / eye_color | 僵尸/复活者呈人形 |
| mythological | creature_type + origin_culture + 人外貌 hair_color / skin_tone / face_shape / eye_color | 美人鱼/狐仙呈人形 |
| fantasy_creature | creature_type + base_form + 人外貌 hair_color / skin_tone / face_shape / eye_color | 精灵/兽人呈人形 |
| digital_virtual | digital_type + base_form + 人外貌 hair_color / skin_tone / face_shape / eye_color | AI 客服/数字分身呈人形 |
| robot | robot_type + material + 人外貌 hair_color / skin_tone / face_shape (拟人型) | 拟人型机器人 |
| hybrid | primary_type + 人外貌 hair_color / skin_tone / face_shape | 半人半兽 |
| alien | body_plan + 人外貌 hair_color / skin_tone / face_shape | 人形外星人 |
| elemental | element_type + material_form + 人外貌 hair_color / skin_tone / face_shape | 偶尔呈人形 |
| concept_personified | concept_type + 人外貌 hair_color / skin_tone / face_shape | 拟人化概念 |
| giant | giant_type + height_category + 人外貌 hair_color / skin_tone / face_shape | 巨人 |
| miniature | base_type + 人外貌 hair_color / skin_tone / face_shape | 小人 |
| aquatic | species + body_type + 人外貌 hair_color / skin_tone / face_shape | 美人鱼/鱼人 |
| object | object_type + base_object + 人外貌 hair_color / skin_tone / face_shape (拟人化) | 钟先生/Olaf |
| plant | plant_type + species + 人外貌 hair_color / skin_tone / face_shape | 树精/花仙 |
| insect | species + wing_type + 人外貌 hair_color / skin_tone / face_shape | 蝴蝶仙子 |
| vehicle_character | vehicle_type | Transformers 罕见, 暂不要求 humanoid 字段 |

**Universal 规则**: extract_identity_anchors() 函数对每个 character_type 走 dispatch 表, 提取对应字段; 提取后统一打成 5-7 行的 anchor block 字符串 (给 backend post-process 使用)。

---

## C. Backend post-process 强注入接口设计 (max thinking, 与 Backend 协作)

### C.1 函数签名

```python
def inject_identity_anchors(
    image_prompt: str,
    characters_in_scene: list[dict],   # 完整 character schema list (含 physical, clothing)
    location: dict | None = None,       # location anchor dict (B.1.3 格式), 可为 None
    style_preset: str = "realistic",
    props: list[dict] | None = None,    # props anchor list (B.1.4 格式), 可为 None
    time_continuity: dict | None = None,  # time continuity anchor (B.1.5 格式), 可为 None
) -> str:
    """
    Backend post-process 强注入 5 维度 identity anchor 到 image_prompt 起始位置。

    设计原则:
    1. 绕过 LLM 决策 — anchor 真后注入, LLM 真看不到
    2. 注入位置 — image_prompt 真起始 (LLM 注意力衰减原理: 开头权重最高)
    3. Idempotent — 重跑 N 次结果一致 (检查 marker "[IDENTITY ANCHORS]" 真已存在则跳过)
    4. Edge case 兜底 — characters_in_scene=[] (纯环境镜头) 跳过 character anchor, 但 style/location/time 仍注入
    5. 跨 19 character_types 通用 — dispatch extract_identity_anchors() 自动适配

    Returns:
        image_prompt 真带 anchor block prepended
    """
```

### C.2 模板格式 (5 个 block, 注入到 prompt 起始位置)

```
═══════════════════════════════════════════════════════════
[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED, DO NOT VARY]
═══════════════════════════════════════════════════════════

## CHARACTER ANCHORS (each visible character)

char_001 (Coral, mythological mermaid):
- hair: deep sea-green long flowing past the waist with small pearl-tipped pins
- face: oval, fair skin with luminous aquamarine sheen
- eyes: vivid ocean blue almond
- signature: iridescent scale-shimmer along collarbones, sweeping coral-pink to golden-amber fish tail
- core outfit: soft blush-pink shell-fragment bodice with pearl droplets

char_003 (Sea Witch, mythological):
- hair: silver-white spiraling tendrils intertwined with sea-stones
- face: diamond, soft lavender-pale skin
- eyes: deep abyssal indigo with silver iris-edge ring
- signature: dark violet vein-lines at temples, dark indigo-black fingertip staining
- core outfit: voluminous deep sea-moss green robe of woven kelp

## STYLE ANCHOR

children_book watercolor — MUST INCLUDE: children's book illustration, soft watercolor
textures, hand-drawn line work, warm pastel palette, storybook aesthetic.
DO NOT USE: photorealistic, 3D render, CGI, Pixar, Disney 3D, realistic rendering.

## LOCATION ANCHOR

loc_001 underwater_palace (interior):
- signature visual: bioluminescent coral pillars, schools of small silver fish, swaying kelp
- atmosphere: soft blue-green ambient light filtering from surface

## PROPS ANCHOR

prop_001 shell_harmonica: small palm-sized harmonica carved from pink-and-cream spiral
shell with faint pearl glow.

## TIME CONTINUITY ANCHOR

scene 5: golden morning sunrise, warm amber light, long west-pointing shadows.
Time jump from scene 4 (underwater night) — explicit transition acknowledged.

═══════════════════════════════════════════════════════════
[NARRATIVE SCENE — LLM creative layer below]
═══════════════════════════════════════════════════════════

{原 LLM 生成的 image_prompt 内容 — 允许 pose/expression/camera/emotion/interaction 自由创意}
```

### C.3 注入时机与调用链路

```
Stage 4 LLM 输出 image_prompt (含 narrative variables, 可能漏 anchor)
    ↓
Stage 5 image_generator.generate_shot_image_phase2_safe() 调用前
    ↓
inject_identity_anchors(
    image_prompt=shot["image_prompt"],
    characters_in_scene=[c for c in characters if c["id"] in shot["characters_in_scene"]],
    location=location_dict,   # 从 Stage 1 outline.unique_locations 查 location_id
    style_preset=project.style,
    props=[p for p in scene["key_props"] if p["id"] in shot["props_in_scene"]],  # 可选
    time_continuity={
        "time_of_day": scene["time_of_day"],
        "lighting": scene["lighting"],
        ...
    }
) → 返回 image_prompt with anchors prepended
    ↓
SeedreamGenerator / NB2 真生图调用
```

**关键**: 这一步在 image_generator 内部, 不改 Stage 4 LLM, 也不改 image generator 的 Seedream/NB2 dispatch。新加一个"前处理" hook 即可。

### C.4 Edge case 处理

1. **0 角色 shot** (`characters_in_scene=[]`): 跳过 CHARACTER ANCHORS block, 但 STYLE / LOCATION / TIME ANCHOR 仍注入
2. **0 props shot** (`props=[]` or None): 跳过 PROPS ANCHOR block
3. **0 location info** (location 不存在或无 signature_visual): 跳过 LOCATION ANCHOR block
4. **already injected** (image_prompt 含 marker "[IDENTITY ANCHORS]"): 跳过 (idempotent), log warning
5. **多角色 shot (3-6 角色)**: CHARACTER ANCHORS 真每个角色独立一段 (不合并), 保证身份分离
6. **anthropomorphic_animal**: 模板适配 species 优先, fur/feather 次之, humanoid 字段 (T21-NEW-2 fallback) 最后

---

## D. PromptValidator 接口设计 (max thinking)

### D.1 函数签名

```python
class PromptValidator:
    """
    在生图前对 image_prompt 真校验 schema 关键字, 不通过 auto-correct (re-inject anchor)。
    与 ShotValidator (image vs prompt 事后校验) 对偶, 实现完整的 cross-stage validation 链。
    """

    def validate_prompt_vs_schema(
        self,
        image_prompt: str,
        characters_in_scene: list[dict],
    ) -> ValidationResult:
        """
        校验 image_prompt 真包含 characters_in_scene 真每个角色的 schema 关键字。

        校验维度 (按字段重要性):
        - hair_color (字面值或同义词集) — 100% MUST 含
        - skin_tone (字面值或同义词集) — 100% MUST 含
        - distinctive_marks (≥ 1 个关键字) — 90% SHOULD 含 (远景可放宽)
        - clothing_core.top (≥ 1 个关键字) — 90% SHOULD 含

        Returns:
            ValidationResult(
                passed: bool,
                missing_anchors: list[dict],  # 每个 dict 含 character_id, field, expected, actual
                severity: str,  # 'critical' | 'warning' | 'info'
            )
        """

    def auto_correct(
        self,
        image_prompt: str,
        validation_result: ValidationResult,
        characters_in_scene: list[dict],
    ) -> str:
        """
        基于 validation_result 真自动 re-inject 缺失 anchor。

        算法:
        1. 如果 image_prompt 已含 [IDENTITY ANCHORS] block (inject_identity_anchors 已跑过) → 仅 log warning, 不重注 (idempotent)
        2. 如果未注入过 → 调用 inject_identity_anchors() 真完整注入
        3. log 缺失字段详情供 PM 审查 (KEY_LEARNINGS #47/#48 防御)
        """
```

### D.2 grep 规则: shot prompt 真**必须含** 关键字判定

**hair_color 关键字判定**:
- schema 值 `"deep sea-green with teal highlights, like sunlit seaweed"`
- 关键字提取: `["sea-green", "teal", "seaweed"]` (取前 3 个 distinctive token, 去停用词)
- 校验通过条件: prompt 中含**任一**关键字 (lower case, substring match)
- 失败示例: prompt 真写 "dark hair" / "flowing hair" 真**不含**任一 keyword → fail

**skin_tone 关键字判定**:
- schema 值 `"fair with a soft luminous aquamarine sheen"`
- 关键字: `["aquamarine", "iridescent", "fair", "luminous"]` (取 distinctive token)
- 校验同上

**distinctive_marks 判定 (放宽)**:
- schema 值 `["iridescent scale-shimmer along collarbones", "sweeping fish tail of overlapping scales"]`
- 关键字: 每条 marks 取 1-2 distinctive token, 例如 `["scale-shimmer", "fish tail", "scales"]`
- 校验通过条件: prompt 含**任一** marks 的**任一**关键字 → pass
- (远景 wide shot 真可能 distinctive_marks 不可见, 标 'warning' 不 'critical')

**clothing_core 判定 (放宽)**:
- schema 值 `"soft blush-pink shell-fragment bodice"`
- 关键字: `["shell-fragment", "blush-pink", "bodice"]`
- 校验同 marks (warning level)

### D.3 auto-correct 算法 (idempotent)

```python
def auto_correct(image_prompt, validation_result, characters_in_scene):
    # Step 1: 检查是否已有 anchor marker
    ANCHOR_MARKER = "[IDENTITY ANCHORS — MUST APPEAR EXACTLY AS DESCRIBED"
    if ANCHOR_MARKER in image_prompt:
        # 已注入过, 不重注 (idempotent)
        logger.warning(
            f"PromptValidator: image_prompt 已含 IDENTITY ANCHORS block 但仍校验失败, "
            f"missing: {validation_result.missing_anchors}. "
            f"Possible LLM ignored anchor block — manual review needed."
        )
        return image_prompt

    # Step 2: 未注入过 → 调 inject_identity_anchors 完整注入
    return inject_identity_anchors(
        image_prompt=image_prompt,
        characters_in_scene=characters_in_scene,
        # ... 其他参数从 context 传入
    )
```

### D.4 多角色 shot 兼容性

3-6 角色场景, validator 真**逐角色逐字段**校验, 不合并判定。例如 Shot 10 (Coral + Sea Witch):
- char_001 Coral: hair=sea-green ❌, skin=aquamarine ❌, marks=scale-shimmer ❌, clothing=shell-fragment ❌ → 全 fail
- char_003 Sea Witch: hair=silver-white ✅ (prompt 含 "silver"), skin=lavender ❌, marks=violet-vein ❌ → 部分 fail

ValidationResult 真返回 8 个 missing_anchors entries (4 fields × 2 chars 真各算)。auto-correct 注入完整 5-维度 anchor block 一次性补齐。

---

## E. 跨题材 baseline 矩阵设计 (max thinking, 与 Tester 协作)

### E.1 95 测试 case 完整列表 (19 character_types × 随机 5 styles)

**Tester 真任务**: 写一个 `tests/test_identity_anchor_cross_genre_baseline.py`, 真覆盖 19 character_types × 5 random styles = 95 case。每 case mock 一个 story (3 角色 / 18 shots, 不调真生图 API)。

| character_type | 5 random styles (建议) | mock story 题材 |
|----------------|------------------------|----------------|
| human | realistic, anime, cartoon, ghibli, ink | 都市情感 / 古装武侠 / 校园 / 职场 |
| anthropomorphic_animal | children_book, ghibli, watercolor, cartoon, anime | 小动物冒险 / 童话 |
| animal | realistic, watercolor, ink, children_book, ghibli | 动物纪录片 |
| supernatural | gothic, anime, ink, watercolor, realistic | 镜中人 / 鬼魂 |
| undead | gothic, anime, cyberpunk, realistic, ink | 僵尸 / 复活者 |
| mythological | watercolor, ghibli, anime, ink, children_book | 美人鱼 / 狐仙 / 哪吒 |
| fantasy_creature | ghibli, anime, watercolor, cartoon, ink | 精灵 / 兽人 |
| digital_virtual | cyberpunk, anime, cartoon, realistic, illustration | AI 客服 / 数字分身 |
| robot | cyberpunk, anime, cartoon, illustration, realistic | 机器人 |
| hybrid | anime, fantasy, watercolor, cartoon, ink | 半人半兽 |
| alien | cyberpunk, anime, sci-fi, cartoon, realistic | 外星人 |
| elemental | watercolor, ghibli, anime, ink, children_book | 火/水精灵 |
| concept_personified | watercolor, ink, anime, gothic, ghibli | 时间/死神拟人 |
| giant | ghibli, watercolor, anime, cartoon, children_book | 巨人传说 |
| miniature | children_book, watercolor, ghibli, cartoon, anime | 小人国 |
| aquatic | watercolor, ghibli, anime, children_book, ink | 美人鱼 / 鱼人 |
| object | cartoon, children_book, ghibli, anime, watercolor | 钟先生 / Olaf |
| plant | ghibli, watercolor, anime, children_book, ink | 树精 / 花仙 |
| insect | watercolor, ghibli, children_book, anime, cartoon | 蝴蝶仙子 |

(vehicle_character 暂跳过 Transformers 罕见, Layer 1 后续扩展)

### E.2 每 case 真验证内容

```python
async def test_baseline_case_<char_type>_<style>():
    # 1. Mock Stage 1-4 LLM 输出 (固定 mock 数据, 不调真 LLM)
    outline = mock_outline(character_type=char_type, style=style)
    characters = mock_characters(character_type=char_type, count=3)  # 3 角色
    screenplay = mock_screenplay(characters=characters, num_scenes=5)
    storyboard = mock_storyboard(screenplay=screenplay, characters=characters, num_shots=18)

    # 2. 真跑 inject_identity_anchors() 在 18 shot 上
    for shot in storyboard["shots"]:
        chars_in_shot = [c for c in characters if c["id"] in shot["characters_in_scene"]]
        injected_prompt = inject_identity_anchors(
            image_prompt=shot["image_prompt"],
            characters_in_scene=chars_in_shot,
            style_preset=style,
            ...
        )

        # 3. 真 grep 校验 100% 含 character schema 关键字
        for char in chars_in_shot:
            anchors = extract_identity_anchors(char)
            hair_keywords = extract_distinctive_tokens(anchors["hair_color"])
            assert any(kw.lower() in injected_prompt.lower() for kw in hair_keywords), \
                f"Char {char['id']} hair_color {anchors['hair_color']!r} keywords {hair_keywords} not in prompt: {injected_prompt[:200]}"

    # 4. 真 validate 跨 95 case 通过率 = 100%
```

**CI 防退化**: 这个 baseline 测试加入 pre-commit hook (与 Ben STATUS_API_CONTRACT 协议同款), 每次 PR 跑 95 case, 任一 fail PR 不能 merge。

### E.3 真**不调真生图 API** 设计

- 95 case 真 mock Stage 1-4 LLM (用预存 fixture)
- 不调 SeedreamGenerator / NB2 (零成本)
- 只校验 prompt-level 真含 schema 关键字
- 真生图质量验证留给 Founder 手动 e2e (test19/20/21/22 跨题材)

---

## F. AI-ML 工时估 + 真 Milestone

### F.1 Milestone 分解

| Milestone | 工时 | 交付物 |
|-----------|------|--------|
| M1 设计 | ✅ ~2h (已完成) | Identity Anchor Framework v1.0 规格文档 (本文档) |
| M2 prompt 调整 | ~1h | `storyboard_prompts.py` HAIR_COLOR_REQUIREMENT_RULE 改为"职责分工说明" |
| M3 helper 函数 | ~1h | `app/prompts/identity_anchor_prompts.py` 新建 + `extract_identity_anchors()` |
| M4 单元测试 | ~1h | `tests/test_identity_anchor_extraction.py` 19 type × extract PASS |
| M5 协作支持 | ~1h | 与 Backend 对齐接口签名, 与 Tester 对齐 baseline 矩阵 |
| **AI-ML 小计** | **~6h (含设计)** | 实施侧 ~4h |

### F.2 真依赖关系

```
M1 设计 (已完成)
    ↓
M2 prompt 调整  ←→  Backend 实施 inject_identity_anchors() (~3h)
M3 helper 函数  ←→  Backend 接入 image_generator.py (~1h)
    ↓
M4 单元测试    ←→  Tester 实施 baseline 矩阵 (~1h)
    ↓
M5 协作支持 (持续)
```

**关键依赖**: M2/M3 真要先与 Backend 确认接口签名 (extract_identity_anchors 返回 dict 格式必须双方一致), 否则两边并行干完会对不上。建议 PM 派工时让 AI-ML M2 先做 (~30 min), Backend 等 M2 ready 后再开工。

### F.3 风险识别

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| Backend 注入 anchor block 后 LLM image_prompt 太长 (Seedream context limit) | 🟡 中 | prompt 截断, 部分 narrative 丢 | AI-ML M2 同步加 "concise narrative" 约束 + Backend 实施时控 anchor block ≤ 800 chars |
| 多角色 shot (5-6 chars) anchor block 太长 | 🟡 中 | 同上 | 限制 distinctive_marks 真截前 2 条 (extract helper) + 单角色 anchor block ≤ 200 chars |
| LLM 反复忽略 anchor block (即使 prepended) | 🟢 低 | PromptValidator auto-correct 兜底 | 验证 generation 5 次后, fail 率应 < 5% |
| anthropomorphic_animal anchor dispatch 错 (species vs humanoid fields) | 🟡 中 | 狼人画成狼 (T20-17 复现) | extract_identity_anchors 严格按 character_type dispatch 表 + 单测覆盖 |
| 跨题材 baseline 95 case 太多, CI 跑得慢 | 🟢 低 | PR merge 慢 | mock fixture 跑 ~30s 真接受 |
| `[IDENTITY ANCHORS]` 字符串在 prompt 中作为字面值出现 (LLM 模仿) | 🟢 低 | LLM 输出畸形 | 用 `═══════` Unicode boundary 作 marker, LLM 真不会模仿 |

---

## G. 协作 protocol (与其他 agent 真分工)

### G.1 AI-ML 真职责 (本人, ~4h 剩余实施)

1. **prompt 调整** (`app/prompts/storyboard_prompts.py`):
   - 修改 `HAIR_COLOR_REQUIREMENT_RULE` (L887-930) — 移除"建议性 hint" + Format examples 段
   - 替换为新文案: "Identity anchors (hair/face/skin/marks/clothing_core) are managed by backend post-process injection. LLM only writes narrative variables (pose/expression/camera/emotion). Do not duplicate anchor content in image_prompt — backend will prepend authoritative anchor block automatically."
   - 同步在 `_build_scene_prompt()` 添加新约束块 `NARRATIVE_VARIABLES_GUIDANCE` 说明 LLM 创意层范围

2. **新建 prompt 模板文件** (`app/prompts/identity_anchor_prompts.py`):
   - `IDENTITY_ANCHOR_INSTRUCTION_BLOCK_TEMPLATE` — Backend post-process 使用的模板字符串 (含 ═══ marker)
   - `NARRATIVE_VARIABLES_GUIDANCE` — 给 LLM 的创意层指引 (Stage 4 prompt 使用)

3. **新增 helper 函数** (`app/prompts/identity_anchor_prompts.py` 或 `app/services/character_prompt_builder.py`):
   - `extract_identity_anchors(character: dict) -> dict` — 5 字段标准化 (B.1 格式)
   - `extract_style_anchors(style_preset: str) -> dict` — 从 StyleEnforcer 提取
   - `extract_location_anchors(location: dict) -> dict` — 从 Stage 1 outline 提取
   - `extract_distinctive_tokens(text: str, n: int = 3) -> list[str]` — 提取 top-N distinctive tokens (用于 PromptValidator)

4. **单元测试** (`tests/test_identity_anchor_extraction.py`):
   - 19 character_types × extract_identity_anchors() 全 PASS
   - extract_distinctive_tokens 边界 case (空字符串, 中文, 长 sentence)
   - mock characters_in_scene → 调 inject_identity_anchors → grep prompt 含 anchor block marker

### G.2 Backend 真职责 (~3h)

1. **实现** `inject_identity_anchors()` (C.1 签名, C.2 模板, C.3 调用链路)
2. **实现** `PromptValidator.validate_prompt_vs_schema()` + `auto_correct()` (D.1-D.4 规格)
3. **接入** `image_generator.generate_shot_image_phase2_safe()` — 在调 Seedream/NB2 dispatch 前调 inject + validate
4. **单元测试** — inject 真 idempotent, validator 真覆盖 4 字段 × 多角色

**关键文件**: `app/services/image_generator.py` (~3 个调度点 L620/L837/L1430)

### G.3 Tester 真职责 (~1h)

1. **实现** baseline 测试 `tests/test_identity_anchor_cross_genre_baseline.py` (E.1-E.3 规格)
2. **覆盖** 19 character_types × 5 random styles = 95 case
3. **CI 接入** — pre-commit hook (与 Ben STATUS_API_CONTRACT 同款)
4. **fixture 准备** — `tests/fixtures/identity_anchor_baseline/*.json` 19 个 character schema 模板

### G.4 PM 真职责

- 派工 + 协调 + 审查
- KEY_LEARNINGS #29/#47/#48 防御性 (agent 报告必须 PM 自跑 pytest 验证)
- AI-ML M2 完成后通知 Backend 开工 (依赖管理)
- Layer 1 实施后通知 Founder e2e 重跑 test22 (Coral hair 真 sea-green) + 跨题材 test19/20/21

### G.5 0 阻塞 Frontend / DevOps

- Layer 1 真**纯 prompt 工程 + backend 内部逻辑**, 0 API contract 变更, 0 前端影响
- Ben STATUS_API_CONTRACT v1.4 不需要升级
- DevOps 部署只需 push backend 改动到 VPS, 不需要 Alembic migration

---

# 历史记录 (按时间倒序)

## ✅ [2026-05-20 19:00] T20-48 + T20-43 + T20-49 完成 — prompt 层三任务

### 给 @backend

#### T20-48 Wire 点 — storyboard_director.py 注入 ANATOMY_FIDELITY_RULES (~5 min, 优先)

```python
# 顶部 import (在已有 SEEDREAM_SAFETY_AVOIDANCE_RULES 后加):
from app.prompts.storyboard_prompts import (
    ...,
    SEEDREAM_SAFETY_AVOIDANCE_RULES,
    ANATOMY_FIDELITY_RULES,      # ← T20-48 新增
    DEC046_V3_STAGE4_RULES,
    build_stage4_character_data_block,
)

# _build_scene_prompt() 和 _build_prompt(): 在 {SEEDREAM_SAFETY_AVOIDANCE_RULES} 后追加:
{SEEDREAM_SAFETY_AVOIDANCE_RULES}

{ANATOMY_FIDELITY_RULES}          # ← 新增, 紧跟 SEEDREAM_SAFETY

{DEC046_V3_STAGE4_RULES}          # ← 已有 v3
```

#### T20-43 / T20-49 — 无需额外 wire (inline in `_build_prompt()`)

### 给 @tester

T20-48/43/49 验证: 跑 test20 (gothic 镜中人), Shot 16 不再出现 anatomy_issue 或 4 hands; char_002 镜中人 physical 应同时含 being_type + hair_color; outline validator 0 警告。

---

## ✅ [2026-05-20 17:30] T20-46 + T20-45 完成 — P1 内测 blocker 修复

### 给 @backend

#### T20-46 Wire 点 — pipeline_orchestrator.py 传 style_preset 给 CharacterDesigner (~5 min)

```python
# 找到 Stage 2 调用处 (~L561), 改为:
characters = await self.character_designer.design(
    outline,
    style_preset=style_preset,  # T20-46: 触发 STYLE_INFUSION_RULES
)
```

详细规范见 `forclaudeweb/t20_46_backend_wire_spec.md`

#### T20-45 已完成 — 无需 Backend wire

`music_generation_service.py` 已自行注入 Step 5a-2 duration linter, Pipeline 自动生效。

### 给 @tester

T20-46 验证: 跑 test20 (gothic, 镜中怒者) 看三个角色 portrait 画风是否统一。
T20-45 验证: test20 BGM prompt 应包含 "sustained" / "building" 等框架词, 不含 "suddenly stops" 等短片信号词。
检查路径: `output/<uuid>/bgm_prompt_chapter0.txt`

---

## ✅ [2026-05-20 10:15] Wave 5 完成 — T20-28 v3 通用叙事原则重构

### 给 @backend (2 核心 wire + 1 可选)

#### Wire 1 — Stage 3 screenplay_writer.py 注入 v3

```python
from app.prompts.screenplay_prompts import (
    DEC044_SCREENPLAY_RULES, DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
    DEC046_V3_NARRATIVE_PRINCIPLES, DEC046_V3_OUTPUT_EXAMPLE,
)
# _build_batch_prompt() 在 {DEC044_SCREENPLAY_RULES} 后追加 {DEC046_V3_NARRATIVE_PRINCIPLES}
# 输出 example 同
```

#### Wire 2 — Stage 4 storyboard_director.py 注入 v3

```python
from app.prompts.storyboard_prompts import (
    ..., SEEDREAM_SAFETY_AVOIDANCE_RULES, DEC046_V3_STAGE4_RULES,
)
# 在 {SEEDREAM_SAFETY_AVOIDANCE_RULES} 后追加 {DEC046_V3_STAGE4_RULES}
```

#### Wire 3 (P1 可选) — TextOverlayServiceV2 emphasis_words 支持

`!!!` 已支持; emphasis_words 数组 P1 待 Backend wire。

### 给 @tester (Wave 5 e2e 验证)

跑 5-6 跨题材测试样本 (C1/C2/C7 优先), 验证 Stage 3 真输出 v3 字段 + 85% KPI ≥ 0.85 自评。

### 给 @frontend

✅ 0 改动需要 — Wave 5 全部是 Prompt 层 + validator 修复。

---

## 🟡 待 AI-ML 长期修 (Founder 5/20 15:35 要求记录)

### TASK-T20-43-PROMPT-SUPPLEMENT — 已在 5/20 19:00 完成 (见上方)

---

## Prompt 核心约束 (历次累积)

### v4 新约束 (2026-05-22 — Identity Anchor Framework v1.0)

1. **Identity Anchor (5 维度) 由 Backend post-process 强注入** — LLM 真不写, 真不能改
2. **LLM 只管 narrative variables** — pose/expression/camera/emotion/interaction/scene_action
3. **PromptValidator 新增 cross-stage validation** — prompt vs schema (生图前) + ShotValidator image vs prompt (生图后) 形成完整链
4. **跨 19 character_types × 80+ styles 通用** — extract_identity_anchors dispatch 表自动适配
5. **anchor block 注入位置: image_prompt 真起始** (LLM 注意力衰减原理)
6. **idempotent** — 重跑 N 次结果一致

### v3 约束 (2026-05-20, 仍生效)

1. **Stage 3 必须输出 v3 字段**: `narrative_cluster` / `narrative_viewpoint` / `narrative_phase` / `scene_self_evaluation` 等
2. **极简对话 1-3 字 OK 修订**: 撤销旧 D2 反例 (在 C1/C7/C4 cluster 中是正确做法)
3. **emphasis 使用规范**: 1 故事整体 1-3 处 `!!!` 即可
4. **85% KPI 自评机制**: LLM 输出后自评, <0.85 自动补救
5. **Cluster-aware 不一刀切**: 8 cluster 各有 TOP 5 不同的关键原则

### v2 约束 (2026-05-19, 仍生效)
- `dialogue/thought line ≤ 35 字` (T20-21 v2)
- 反文言通俗易懂 (15 词替换表)
- text_overlay 必须非空 (RULE 0)
- 关键转折 shot 必含 text_overlay (T20-27 RULE 0.B + D8)

### v1 约束 (2026-05-19, 仍生效, DEC-044)
- `narration ≤ 120 CJK chars 总长 + ≤ 25 chars per sentence`
- text_type=none 仅纯环境镜头允许 (characters_in_scene=[])
- 每 scene ≥1 thought + ≥1 plot-essential dialogue/thought

### Wave 4 约束 (仍生效)
- T20-17 SPECIES_FIDELITY_RULES (Stage 4 物种保真)
- T20-26 SEEDREAM_SAFETY_AVOIDANCE_RULES (Stage 4 暗黑词避开)
- T20-22 schema 'animal'/'anthropomorphic_animal' 接受 plumage_color/skin_color/chitin_color
- T20-23 character_designer 按 character_type 分叉

---

## Prompt 优化追踪表 (历次)

| 版本 | 日期 | 焦点 | 状态 |
|------|------|------|------|
| v0 (TTS-era) | <2026-05-18 | 长 prose narration 配合 TTS 朗读 | 已废弃 |
| v1 (DEC-044) | 2026-05-19 Wave 1 | 去 TTS, narration ≤25 caption + dialogue 主导 | ✅ |
| v2 (DEC-045 T20-21) | 2026-05-19 Wave 4 | dialogue 25→35 + 反文言通俗 | ✅ |
| v2.1 (T20-27) | 2026-05-19 Wave 4 | 强制 text_overlay + 关键转折 | ✅ |
| v2.2 (T20-26 Stage 4) | 2026-05-19 Wave 4 | Seedream 暗黑词避开 | ✅ |
| v2.3 (T20-17) | 2026-05-19 Wave 2 | Stage 4 物种保真 | ✅ |
| v3 (DEC-046 T20-28) | 2026-05-20 Wave 5 | 15 原则 + 8 cluster + 85% KPI 通用叙事重构 | ✅ |
| **v4 (DEC-048 T22-NEW-3)** | **2026-05-22 Layer 1** | **Identity Anchor Framework v1.0 — separation of concerns (LLM 创意 + Backend 一致)** | 🟢 **设计完成, 等 PM 派实施** |

---

## 关键文件位置

```
app/prompts/
├── screenplay_prompts.py        ← Stage 3 prompts (DEC-044 v1+v2 + DEC-046 v3)
├── storyboard_prompts.py         ← Stage 4 prompts (DEC-046 v3 + Layer 1 v4 待调整)
├── identity_anchor_prompts.py    ← 🟢 待新建 (Layer 1, AI-ML M3)
├── shot_adjustment_prompt.py     ← Founder /preview 调整画面 (TWO-MODE Haiku)
└── prompt_safety_rewrite.py      ← Pipeline 自动救场 (Sonnet)

app/services/
├── screenplay_writer.py          ← Stage 3 集成点 (v3 已 wire)
├── storyboard_director.py        ← Stage 4 集成点 (v3 已 wire, v4 待 backend wire)
├── image_generator.py            ← 🟢 Layer 1 backend 实施 inject + validator 接入点
├── character_prompt_builder.py   ← extract_identity_anchors helper 候选位置
└── text_overlay_service.py       ← !!! 已支持; emphasis_words P1 待 Backend wire

tests/
├── test_identity_anchor_extraction.py        ← 🟢 待新建 (Layer 1, AI-ML M4)
├── test_identity_anchor_cross_genre_baseline.py  ← 🟢 待新建 (Layer 1, Tester)
├── test_t20_28_cross_genre_principles.py     ← v3 新单测 68 PASS
├── test_t20_21_narration_to_shot_content.py  ← DEC-044 v1+v2 60 PASS
├── test_t20_27_text_overlay_required.py      ← T20-27 33 PASS
├── test_t20_17_species_fidelity_stage4.py    ← T20-17 33 PASS
├── test_t20_26_seedream_safety_avoidance.py  ← T20-26 23 PASS
├── test_t20_22_animal_plumage_color.py       ← T20-22 12 PASS
└── test_text_overlay_v2.py                   ← !!! 红字渲染 (Wave 4 已存在)
```
