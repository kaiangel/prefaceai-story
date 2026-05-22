# Stage 4 LLM 手部 Anatomy 约束强化（B45）

**任务**: B45 P2 — Stage 4 LLM prompt 加强手部 anatomy 约束
**日期**: 2026-05-11
**执行**: AI-ML agent
**触发**: Founder 像素级 review test10 Shot 08 — manila folder 姿势怪、手腕扭曲、手指抓握不自然

---

## 1. 实测案例 (test10 Shot 08)

### 故事
output ID `a17d42b6-8e85-446b-953d-d9ddbafffcad`，林开宇站在地铁站台等列车，文件夹夹在腋下。

### LLM 输出的 image_prompt（节选）
> "The manila folder is now clamped with **fierce pressure** under his left arm, his left elbow **pressed hard** against his ribcage — **knuckles white** against the folder's edge."

### 生成图问题
- 文件夹姿势怪（朝向不自然）
- 手腕扭曲
- 手指抓握不自然（指节位置/方向错乱）

### 表面看
prompt 描述非常详细（"knuckles white" 都写了），LLM 看起来"很对"。

---

## 2. 真根因分析（深挖）

### 三层根因

**层 1 — 抽象 vs 几何描写错位**

LLM 用文学性强烈的词汇（"fierce pressure / pressed hard / knuckles white"）表达**情绪紧张**，但这些词**不提供手指几何信息**。图像生成模型（Seedream / NB2 / SDXL / DALL-E 3 都一样）需要的是：
- 哪只手？
- 哪几个手指做什么？
- 掌心朝哪？
- 手腕角度如何？
- 接触点在哪？

**层 2 — 词形 vs 几何不匹配的高风险词汇**

"fierce pressure" / "pressed hard" / "knuckles white" / "fingers digging into" 这种词在自然语言里强烈，但图像模型把它们解读成"夸张姿态许可证"——结果渲染出扭曲手腕 + 扭曲指节。

**层 3 — 多重紧张姿态约束叠加**

Shot 08 prompt 同时要求：
- "clamped with fierce pressure"
- "elbow pressed hard against ribcage"
- "knuckles white"
- "feet planted squarely"
- "chin lifted"
- "shoulders pulled back"
- "barely perceptible tremor"

6 个紧张姿态约束让模型试图同时满足全部，但其中只有 3 个有几何信息（feet planted / chin lifted / shoulders back），手部那 3 个都是"情绪描写"无几何。

### 跨 shot 验证

test10 storyboard 19 个 shot 里其他持物描写也踩同一陷阱：

| Shot | 持物描写 | 风险点 |
|------|---------|--------|
| **08** | "clamped with fierce pressure / knuckles white against folder's edge" | **极高** |
| 05 | "fingers wrapped tightly around the pen barrel, knuckles whitening slightly" | 中 |
| 07 | "holds a manila folder clamped tightly under his left arm" | 中 |
| 09 | "fingers slightly curled but not reaching for anything" | 低（防御性描写） |
| 11 | "fingers slightly curled as if a command was half-formed and abandoned" | 低 |

LLM 默认偏好"紧张型"持物描写，全局问题，不是单 shot bug。

### 不是 Seedream 模型限制

Founder 之前怀疑"Seedream 限制"，但同模型在 docs/CC_KAI_STORY_SCRIPT.md 历史脚本里渲染过"defined fingers, slightly reaching" / "delicate fingers, palm slightly open" 这种 anatomy-grounded 描写**生成成功**。结论：模型有能力，是 prompt 没给够信息。

---

## 3. 方案对比

### Option A — 简化持物描写
让 LLM 只写 "holding a manila folder"，让 Seedream 自由发挥。
- ❌ 拒绝：丢失叙事张力，且自由发挥更危险（模型可能渲染扭曲）

### Option B — 加 anatomy-grounded 持物描写规则
要求 LLM 明确说明: 哪只手 + 哪几个手指 + 掌心方向 + 手腕角度 + 接触点。
- ✅ 采纳：直接修复几何信息缺失

### Option C — 黑名单某些"过度紧张"形容词
禁用 "fierce pressure / knuckles white / vice grip" 这种暗示形变的词。
- ✅ 采纳：避免高风险词汇暗示模型变形

### Option D — 让 ShotValidator (Haiku) 兜底
- ⚠️ 单独不足：ShotValidator B17 Phase 2 只判 SEVERE（3 hands / 6 fingers / floating limb），"手腕扭曲 + 抓握不自然"会被判 mild → 不触发 retry。
- 协同：B45 在源头修，ShotValidator 兜其他维度。

### 最终选择：Option B + Option C 组合

---

## 4. 实施细节

### 新增文件：无

### 修改文件：2 个

#### 1) `app/prompts/storyboard_prompts.py`（白名单内 ✅）

新增常量 `HAND_PROP_ANATOMY_RULES`（5349 字符）位于 NARRATION_TO_VISUAL_EXTRACTION_RULES 之后、COMIC_MODE_NARRATIVE_RULES 之前。

**5 条核心规则**:

| Rule | 内容 | 解决的问题 |
|------|------|----------|
| 1. REQUIRED ANATOMY ANCHORS | 持物描写必须包含 5 个锚点中至少 3 个：哪只手 / 哪几指做工 / 掌心朝向 / 手腕角度 / 接触点 | 几何信息缺失 |
| 2. HIGH-RISK VOCABULARY | 黑名单"fierce pressure / pressed hard / knuckles white / vice grip / fingers digging / crushing grip / trembling fingers (without specifying which)"，改用面部/姿态表达紧张 + 手保持几何中性 | 词形 vs 几何错位 |
| 3. ONE HAND PER OBJECT | 默认单手持物，双手持物必须叙事驱动 | 避免双手过度约束 |
| 4. FINGERS-OUT-OF-FRAME ESCAPE | 几何描写难写时可让手出框（cropped at elbow / obscured by angle） | Escape Hatch 防止"硬写但写不好" |
| 5. SELF-CHECK | 输出前扫所有持物动词（hold/grip/clutch/clamp/clasp/clench/grasp/pinch/press/pick up/set down/hand/pass），检查 Rule 1+2+多角色限肢 | 主动检查闭环 |

**好/坏对比示例**（嵌在规则里）:

❌ BAD:
> "the manila folder is clamped with fierce pressure under his left arm, knuckles white against the folder's edge"

✅ GOOD:
> "the manila folder is tucked under his left arm — his left forearm crosses over his ribcage at a relaxed angle, palm flat against the folder's side, fingers naturally curled around its bottom edge, thumb resting visible on top. The folder rests parallel to his torso, not crushed."

#### 2) `app/services/storyboard_director.py`（任务派发授权 ⚠️ 严守边界）

只改 2 处：
- L25-29: import 块加 HAND_PROP_ANATOMY_RULES（带 B45 注释）
- L875: 第一个 prompt 路径（_build_scene_prompt）注入 `{HAND_PROP_ANATOMY_RULES}`
- L1186: 第二个 prompt 路径（单场景路径）注入 `{HAND_PROP_ANATOMY_RULES}`

**严守边界（不改）**:
- ✅ character_id 映射逻辑（build_identity_line_phase2）：未触碰
- ✅ IMAGE 编号链：未触碰
- ✅ reference_images 14 张限制：未触碰
- ✅ StyleEnforcer 风格强制层：未触碰
- ✅ 业务逻辑代码：未触碰
- ✅ 其他 11 条 IMAGE PROMPT QUALITY RULES：未修改

### Diff 摘要

```diff
# app/prompts/storyboard_prompts.py

+ # ====================
+ # Stage 4 Prompt增强：手 + 道具 anatomy 几何描写规则 (B45, 2026-05-11)
+ # ====================
+
+ HAND_PROP_ANATOMY_RULES = """
+ ... [5349 字符，5 条规则 + 好坏对比] ...
+ """
```

```diff
# app/services/storyboard_director.py

- from app.prompts.storyboard_prompts import NARRATION_TO_VISUAL_EXTRACTION_RULES, COMIC_MODE_NARRATIVE_RULES
+ from app.prompts.storyboard_prompts import (
+     NARRATION_TO_VISUAL_EXTRACTION_RULES,
+     COMIC_MODE_NARRATIVE_RULES,
+     HAND_PROP_ANATOMY_RULES,  # B45 2026-05-11: 手+道具 anatomy 几何规则
+ )

# 注入点 1 (L875, _build_scene_prompt):
  {COMIC_MODE_NARRATIVE_RULES}
+
+ {HAND_PROP_ANATOMY_RULES}

  ## IMAGE PROMPT QUALITY REQUIREMENTS (MANDATORY)

# 注入点 2 (L1186, 单场景路径):
  {COMIC_MODE_NARRATIVE_RULES}
+
+ {HAND_PROP_ANATOMY_RULES}

  {SCENE_PROP_CONTINUITY_RULES}
```

---

## 5. 验证

### 静态验证

| 检查 | 结果 |
|------|------|
| AST PASS (两个文件) | ✅ |
| import HAND_PROP_ANATOMY_RULES 可正常导入 | ✅ 5349 字符 |
| 规则内容完整（5 子节）| ✅ REQUIRED ANATOMY ANCHORS / HIGH-RISK VOCABULARY / FINGERS-OUT-OF-FRAME / SELF-CHECK 全在 |
| 注入点数 = 2（不多不少）| ✅ |
| pytest test_architecture | ✅ 7/7 PASS |

### 运行验证（已确认 prompt 工程层 OK，下次 LLM 跑 storyboard 自动生效）

下次 Stage 4 调用（Claude Sonnet 4.6 / Gemini Pro 备用）时会自动加载新 prompt，预期看到 LLM:
- 不再写 "fierce pressure / knuckles white" 这类词
- 改写"his left forearm crosses... palm flat... fingers naturally curled around the edge..."
- 持物动词出现时主动列出 anatomy 锚点

未做端到端 Seedream 跑图验证（PM 任务说可选，避免成本/时间投入）— 真实效果需要 Founder 下次 test 真跑后观察。

---

## 6. 风险点与回滚

### 主要风险

1. **LLM 输出长度增加**: 加 5 条规则后 prompt 可能更长。但 anatomy 描写本来就需要这些细节，预期增加 ≤ 100 字符/shot。
2. **LLM 可能"过度遵守"**: 不持物的 shot 也加无意义的 hand 描述。Mitigation：Rule 4 ESCAPE HATCH 明确"手出框也行"。
3. **风格化场景的误伤**: 水墨/卡通风格本来手就抽象。Mitigation：规则只在描写持物时生效，不强制所有 shot 描写手。
4. **ShotValidator B17 Phase 2 协同**: B45 在源头预防，ShotValidator B17 兜底 SEVERE 边界，互补无冲突。

### 回滚方案

如果新规则导致 LLM 输出异常：

```bash
cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
git diff HEAD~1 -- app/prompts/storyboard_prompts.py app/services/storyboard_director.py
# 确认改动只是 B45
git checkout HEAD~1 -- app/prompts/storyboard_prompts.py app/services/storyboard_director.py
# 或精确回滚: 删除 HAND_PROP_ANATOMY_RULES 常量 + 删除 import + 删除 2 个注入点
```

---

## 7. ShotValidator 协同分析（B30 PEND 顺手提及）

### 现状
ShotValidator B17 Phase 2（2026-05-08 完成）已具备 anatomy 检测能力：
- L75-81 检测 `hands_count` / `finger_anomaly` / `extra_limbs_floating`
- L88 SEVERE = "3+ hands, third arm, two faces, floating limb, 6+ fingers"
- L89 mild = "hand at unusual angle, finger partially hidden" → **仅日志，不触发 retry**

### 对 B45 场景的覆盖

test10 Shot 08 的"手腕扭曲 + 文件夹姿势怪 + 手指抓握不自然"在 Haiku 4.5 眼里**很可能判 mild**（不是 3 hands 也不是 6 fingers，是"姿态不自然"）→ valid=True → 不重生。

### 结论

**B45 在源头预防 > ShotValidator 在末端兜底**。

如果要让 ShotValidator 更严（B30 升级方向），可考虑：
- 新增 `wrist_twisted_unnaturally` SEVERE 类型
- 新增 `hand_holding_object_anatomically_wrong` SEVERE 类型
- 风险：误伤艺术风格化（水墨/油画的手本来抽象）— 已有 L94 排除清单，但新类型需要更细致的判断标准

**建议**：B45 先观察实际效果，B30 升级 ShotValidator anatomy 严格度暂缓，等 B45 跑过 2-3 个故事后再评估是否需要补刀。

---

## 8. 给同事的影响

### @backend
- **零代码改动**。新 prompt 模板会被下次 Stage 4 LLM 调用自动加载（生产环境无需重启，meta-prompt 是字符串常量，每次启动加载）。
- Stage 4 LLM 调用方式（StoryboardDirector）不变。
- 注意：Sonnet 4.6 / Gemini Pro 任一都会消费新规则，不需要切模型。

### @tester
- 下次跑 test11+ 真故事时，重点验证：
  - LLM 输出 image_prompt 不再含 "fierce pressure / knuckles white / vice grip" 等高风险词
  - 持物 shot 的 image_prompt 包含明确的"左/右手 + 手指 + 掌心方向"描写
  - Seedream 生成图手部/持物 anatomy 改善（vs test10 baseline）
- 如条件允许，建议跑 1 个含 3+ 持物 shot 的故事做 A/B 对照（旧 prompt vs 新 prompt）

### @frontend
- 无影响。

### @resonance
- 用户感知：手部/持物画面更自然 → 减少"AI 画的"违和感 → 提升内容可信度

---

## 9. 文件清单

### 修改文件
| 文件 | 类型 | 改动量 |
|------|------|--------|
| `app/prompts/storyboard_prompts.py` | 新增常量 | +112 行 |
| `app/services/storyboard_director.py` | import + 2 注入点 | +6 行 (净增) |

### 新增文档
| 文件 | 用途 |
|------|------|
| `docs/ANATOMY_PROMPT_HARDENING_2026-05-11.md` | 本文档（调研 + 方案 + 实施 + 验证） |

### 未修改（任务边界严守）
- ✅ `app/services/image_generator.py`
- ✅ `app/services/reference_image_manager.py`
- ✅ `app/services/scene_reference_manager.py`
- ✅ `app/services/style_enforcer.py`
- ✅ `app/services/shot_validator.py`（B17 Phase 2 留作 anatomy 末端兜底）
- ✅ `app/services/seedream_generator.py`
- ✅ `app/services/pipeline_orchestrator.py`
- ✅ `tests/*`
- ✅ 其他 agent progress 文件

---

## 10. 关键 commit message 草稿（DevOps 提交时用）

```
feat(prompt): B45 — Stage 4 LLM hand-prop anatomy hardening rules

- Add HAND_PROP_ANATOMY_RULES constant (5349 chars) in app/prompts/storyboard_prompts.py
  with 5 rules: REQUIRED ANATOMY ANCHORS / HIGH-RISK VOCABULARY blacklist /
  ONE HAND PER OBJECT / FINGERS-OUT-OF-FRAME ESCAPE / SELF-CHECK
- Inject HAND_PROP_ANATOMY_RULES at 2 prompt-build points in storyboard_director.py
- Root cause: test10 Shot 08 — LLM literary "fierce pressure / knuckles white"
  language gave Seedream no finger geometry, resulting in twisted wrist + warped grip.
- Fix: require explicit hand/finger/palm/wrist/contact-point anchors + blacklist
  high-risk emotional-tension vocabulary that doesn't carry geometry.
- pytest test_architecture 7/7 PASS, no behavior changes to reference_images / IMAGE
  numbering / character_id mapping / StyleEnforcer.

Refs: B45 PENDING
```

---

**End of doc.**
