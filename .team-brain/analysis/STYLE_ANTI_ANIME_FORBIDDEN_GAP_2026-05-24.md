# 风格防护缺陷分析: 非动漫画风 style 缺 anti-anime forbidden_keywords

**发现日期**: 2026-05-24 (test26 cyberpunk + ai_entity e2e 测试中)
**发现人**: PM (Founder 角色确认页观察 → PM 地毯式追根因)
**严重度**: 🔴 P1 (影响视觉统一性核心红线, 但有手动 prompt workaround 不阻塞内测)
**负责修复**: AI-ML (style_enforcer.py + 可能 storyboard_prompts.py)

---

## 一、实证现象 (test26)

**故事**: 《深夜小七》cyberpunk + ai_entity (出租车司机老周 / 乘客陈明 / 车载AI小七)

角色确认页 3 个角色画风**严重不统一**:

| 角色 | character_type | 实际画风 | 是否符合 cyberpunk 意图 |
|---|---|---|---|
| 老周 (char_001) | human | **写实照片级** (photorealistic, 银翼杀手式) | ✅ 符合 |
| 陈明 (char_002) | human | **日系动漫** (anime/二次元帅哥) | ❌ 漂移 |
| 小七 (char_003) | ai_entity | 赛博朋克场景 (车机屏幕+霓虹) | ✅ 符合 |

**老周(写实) 与 陈明(动漫) 是两种完全不同的画风**, 同一故事同框出现 = 视觉割裂。
若不修, 贯穿后续 18+ shots, 用户细看必然察觉 (违背单模型纪律要守的视觉统一性, 见 [[feedback_pipeline_single_model_only]])。

> Founder 初始直觉"老周不像赛博朋克"。PM 查 cyberpunk 定义后**修正**: 老周才是对的写实基调, **陈明的动漫风才是漂移**。

---

## 二、根因 (完整调用栈追踪)

### cyberpunk style 定义 (style_enforcer.py L283-295)

cyberpunk 的 `StyleEnforcement` 设计意图是**写实电影感**:
> style_description: "Syd Mead's chrome futures, **Ridley Scott's rain-soaked neon** (银翼杀手), Ghost in the Shell... augmented eyes reflecting data streams, leather and synthetic fabric layered for function..."

但它**只有 mandatory_keywords** (neon/futuristic city/dark atmosphere) + 写实文字描述,
**缺 forbidden_keywords 禁止 anime/cartoon/illustration**。

### 对比正确防护的 style (vintage_film L361)

```python
forbidden_keywords=[
    "digital clarity", "HDR", "neon", "cyberpunk", "anime", "cartoon",
    "3D render", "sharp digital", "modern clean", "vector", "pixel art",
    "illustration", "painting", "watercolor"
]
```
vintage_film 有完整 anti-anime forbidden → 画风锁死。

### 根因结论

**cyberpunk 缺 forbidden_keywords 的 anti-anime 条目** → Seedream 在 cyberpunk prompt 下画风不受约束 →
给老周出写实、给陈明出动漫, **两者都不算"违规"** → 画风自由分叉。

非生图模型的随机性问题, 是**我方 prompt 工程层 (StyleEnforcer) 防护不全** (符合 [[feedback_dont_blame_model_first]] — 先查可控的 prompt 层)。

---

## 三、地毯式扫描: 全 28 个 style_preset 的 forbidden_keywords 覆盖

PM 脚本扫描 `app/services/style_enforcer.py` 全部 StyleEnforcement 块:

| style | 有 forbidden | 禁 anime/动漫 | 判定 |
|---|---|---|---|
| realistic | ✅ | ✅ | OK |
| cartoon | ✅ | ❌ | by-design (本身卡通) |
| pixar_3d | ✅ | ✅ | OK |
| anime | ✅ | ✅ | OK (禁的是非动漫词) |
| ghibli | ✅ | ❌ | by-design (本身吉卜力) |
| illustration | ✅ | ❌ | by-design (本身插画) |
| watercolor | ✅ | ❌ | 🔴 缺陷 (水彩传统画) |
| children_book | ✅ | ❌ | 🟡 边缘 (本就偏插画) |
| manga | ✅ | ❌ | by-design (本身漫画) |
| slam_dunk | ✅ | ✅ | OK |
| korean_webtoon | ✅ | ❌ | by-design (本身韩漫) |
| oil_painting | ✅ | ✅ | OK |
| **cyberpunk** | ✅ | ❌ | 🔴 **缺陷 (实证, 写实电影感)** |
| **ink** | ✅ | ❌ | 🔴 **缺陷 (水墨传统画, test27 跑过)** |
| pixel | ✅ | ❌ | 🟡 缺陷 (像素艺术特定画风) |
| **ukiyo_e** | ✅ | ❌ | 🔴 缺陷 (浮世绘传统版画) |
| vintage_film | ✅ | ✅ | OK |
| pencil_sketch | ✅ | ✅ | OK |
| chibi | ✅ | ❌ | by-design (本身Q版) |
| dark_fantasy | ✅ | ✅ | OK |
| pop_art | ✅ | ✅ | OK |
| paper_cut | ✅ | ✅ | OK |
| steampunk | ✅ | ✅ | OK |
| art_nouveau | ✅ | ✅ | OK |
| noir | ✅ | ✅ | OK |
| comic_western | ✅ | ✅ | OK |
| pastel_dream | ✅ | ❌ | 🟡 缺陷 (粉彩梦) |
| gothic | ✅ | ✅ | OK |

### 缺陷清单 (按严重度)

**🔴 高 (明确非动漫画风, 必修)**:
- **cyberpunk** — 写实电影感 (test26 实证分叉)
- **ink** — 水墨传统中国画 (test27 用过, 动漫混入风险高)
- **watercolor** — 水彩传统画
- **ukiyo_e** — 浮世绘传统日本版画

**🟡 中 (特定画风, 建议修)**:
- **pixel** — 像素艺术 (混动漫会破坏像素质感)
- **pastel_dream** — 粉彩梦
- **children_book** — 边缘 (本就偏插画, 看设计意图)

**by-design 不动** (本身就是动漫/插画类):
cartoon / ghibli / manga / korean_webtoon / chibi / illustration

---

## 四、修复方案

### 短期 workaround (本次 test26) — 🔴 实测无效!

用户在角色"调整"框手动加画风关键词:
- 陈明: "改成写实电影感真人质感画风(photorealistic, cinematic), 去除动漫/二次元/插画风格, 保持30岁年轻壮年"
- 老周: 保持写实 + 增强赛博朋克霓虹氛围

**实测结果 (5/24 17:56 重生)**:
- 老周 ✅ adjust 加霓虹氛围**生效** (背景加蓝光, 写实基础上加元素 Seedream 容易做)
- 陈明 ❌ adjust 加 photorealistic/去动漫**无效** — 变年轻了但**画风仍是日系动漫**

**关键结论**: **手动 prompt workaround 救不了画风**。
根因精确化: **Seedream 对「年轻男性角色 + cyberpunk」有强动漫先验** (二次元帅哥=赛博朋克动漫经典题材)。
- 老周(五十岁风霜) 天然锚定写实
- 陈明(年轻帅哥) 天然锚定动漫
- adjust 框自然语言关键词**权重压不过这个先验**
→ **必须 style 层 negative prompt 强制禁 anime + 强制 photorealistic mandatory**, 用户层关键词无效。
→ 这也意味着内测用户即使想要写实也调不出来 = **P1 必修, 优先级上调**。

### 根治 (派 AI-ML)

给 🔴🟡 缺陷 style 补 forbidden_keywords 的 anti-anime 条目, 参考 vintage_film:
```python
# cyberpunk / ink / watercolor / ukiyo_e / pixel / pastel_dream 各自补:
forbidden_keywords=[
    ...现有词...,
    "anime", "cartoon", "manga", "2D illustration", "cel-shaded",
    "二次元", "chibi", "vector art"  # 按各 style 调整
]
```
⚠️ 注意: 每个 style 的 forbidden 要**贴合该画风**:
- cyberpunk/ink/watercolor/ukiyo_e → 禁 anime/cartoon/cel-shaded (要写实/传统)
- 但 ink 不能禁 "painting" (水墨本身是画) — 需 AI-ML 逐个甄别, 不可一刀切

### 验证要求 (Tester)

- 修后重跑 test26 (cyberpunk) + test27 (ink), 确认 3+ 角色画风统一
- 跨 character_type 验证 (human + ai_entity 等不分叉)

---

## 五、优先级 + 时间线

- **优先级**: P1 (视觉统一性是核心红线, 但有手动 workaround 不阻塞内测)
- **本次 test26**: 手动 prompt 救 (Founder 操作中)
- **根治时机**: 内测启动**前**修完 (派 AI-ML, Tester 复测) — 内测用户不会手动调 prompt, 必须系统锁死画风
- **负责**: AI-ML (style_enforcer.py forbidden_keywords) + Tester (test26/27 复测)

---

## 六、关联

- [[feedback_pipeline_single_model_only]] — 视觉统一性纪律 (18 图 1 张异类用户必察觉)
- [[feedback_dont_blame_model_first]] — 先查可控 prompt 层再归咎模型
- test27 (ink) 当时未报画风分叉, 但 ink 同样缺防护 = 潜在隐患, 需复测确认
- DEC-051 红线: 此修复是**补防护**, 不是删 fallback, 与简化红线无冲突

---

## 七、AI-ML 实测校准 + 修复落地 (2026-05-24 Wave 12, Opus 4.7 xhigh)

### 7.1 架构关键发现 (修复前必须搞清的"防护到底走哪条路")

地毯式追完整调用栈, 发现 **Seedream 根本不收 negative_prompt**:
- `seedream_generator._build_payload()` (L361-384) 的 payload 只有 `prompt` 正向字段, **无 negative_prompt 字段** → `build_style_negative_prompt()` (用全部 forbidden) 对 Seedream **完全无效**。
- Seedream **shot 路径** dispatch (`image_generator` L1086/L1726) 调 `generate_shot_image_seedream(shot=...)` **不传 full_prompt** → shot 用的是 Stage 4 LLM 写好的 `image_prompt` 原文, **shot 路径根本不过 StyleEnforcer.enforce_prompt**。
- forbidden/mandatory 真正能影响 Seedream 的**唯一通道**是 prefix 的 `MUST INCLUDE` / `DO NOT USE` 行, 而它们只取 **`mandatory_keywords[:5]` / `forbidden_keywords[:8]`** (`build_mandatory_prefix` L611-612 + `extract_style_anchors` L465-466 同切片)。
- 这条 prefix 走 3 条 Seedream 真实路径: ① 参考图 portrait/fullbody (`RIM` L381/L621 `enforce_prompt`) ② 参考图 Layer 1 inject ③ shot Layer 1 inject (`_render_style_anchor_block` 用 top5/top8)。

**铁律结论**: anti-anime 词 + 渲染介质锚点**必须挤进 forbidden 前 8 / mandatory 前 5**, 否则 Seedream 看不到。这是本次所有改动的设计约束。

### 7.2 实测校准 (强动漫先验角色 = 28岁帅哥, 复刻陈明; doubao-seedream 单模型直生)

probe 脚本: `scripts/style_drift_probe.py` (复用 `StyleEnforcer.enforce_prompt` + `_call_seedream_sync`, 与参考图路径同管道)。图: `test_output/manualtest/style_drift_probe/`。

| style | PM 纸面 | **AI-ML 实测** | 实测证据 |
|---|---|---|---|
| cyberpunk | 🔴 | 🔴 **确认** | 二次元帅哥 (光面 CG/动漫眼) |
| pastel_dream | 🟡 | 🔴 **上调** | full anime 美少年 (大紫眼 cel-shaded) |
| gothic | 🟡 | 🟡 确认(轻) | 光面 CG idol 照 (非动漫但偏离绘画基调) |
| ink | 🔴 | 🟢 **下调** | 真水墨笔触 — mandatory 已锁 ink-wash 介质 |
| watercolor | 🔴 | 🟢 **下调** | 真水彩 — forbidden[:8] 已含 photorealistic/3D |
| ukiyo_e | 🔴 | 🟢 **下调** | 真浮世绘木版画 — 介质+8词防护已足 |
| pixel | 🟡 | 🟢 **下调** | 真 16-bit 像素 — 像素网格介质天然抗动漫 |
| noir | 🟡 | ✅ 守住 | B&W 摄影 noir — "high contrast B&W" 强锁介质 |

**根因模式 (实测提炼)**: 漂移 ⟺ **mandatory[:5] 只锁氛围/色调/场景, 不锁渲染介质** 且 forbidden[:8] 无 anti-anime。
ink/watercolor/ukiyo_e/pixel/noir 都在 mandatory 里有**强介质锚点** (ink-wash / watercolor / woodblock / pixel / B&W) → 守住。
cyberpunk/pastel_dream/gothic 只锁氛围 → 年轻角色被先验拉去动漫/光面 CG。

**对 PM 纸面初判的校准**: PM 把 4 个传统画风 (ink/watercolor/ukiyo_e) 列 🔴 是合理的纸面担忧, 但**实测它们已被现有 mandatory 介质锚点守住** (这是"先查可控层"的胜利 — 防护其实够)。真正的 🔴 是 **pastel_dream (纸面 🟡, 实测 full anime)**, 比 ink 三件套更急。

### 7.3 修复落地 (style_enforcer.py, 仅 3 style, 逐个甄别)

- **cyberpunk** (must): mandatory 前 5 加 `photorealistic` + `cinematic film still` (对齐 style_desc 的 Blade Runner 真人电影基调); forbidden 前 8 加 `anime/cartoon/manga/cel-shaded/2D illustration/stylized digital painting/glossy idol render/chibi`, 场景排除词 (pastoral/rural…) 保留在后。**实测后老周写实↔陈明同框已统一**。
- **pastel_dream**: mandatory 前 5 加 `soft painterly illustration` + `airbrushed soft shading` (柔光插画介质, **不加 photorealistic** — 与其本质冲突且已在 forbidden); forbidden 前 8 加 `cel-shaded/hard anime lineart/manga/sharp ink outlines/glossy idol render`。**实测从硬动漫 → 柔笔触插画** (方向对, pastel_dream 本就该是插画非写实)。
- **gothic** (轻): mandatory `dark romantic aesthetic`→`dark romantic painting` (绘画介质); forbidden 前 8 加 `anime/cel-shaded/manga/glossy idol render`。实测从光面 idol 照 → 偏绘画/插画感 (轻微横移, 本就是 mild drift)。

**未动 (实测守住, 遵守 surgical-change + 不一刀切)**: ink / watercolor / ukiyo_e / pixel / noir。
**零破坏 by-design 动漫/插画类**: cartoon / ghibli / manga / chibi / illustration / korean_webtoon / anime / slam_dunk — 0 改动, 0 自禁介质 (verify 通过)。

### 7.4 回归 + 验收
- pytest: `test_identity_anchor_extraction/injector` + `test_layer1_portrait/fullbody` + `test_t20_46_character_style_infusion` + `test_wave9_cross_genre_baseline` + `test_prompt_validator` + `test_wave10_ai_ml_fidelity_rules` + `test_identity_anchor_cross_genre_baseline` = **377 PASS, 0 FAIL, 0 退化**。
- 28/28 style prefix 仍正常 render。
- DEC-051 红线: 纯补 forbidden/mandatory 防护, **0 删 fallback**。
- **Tester 复测建议**: 重跑 test26 (cyberpunk 老周+陈明 同框统一) + 新增 pastel_dream 强动漫先验角色 e2e。watercolor 列"watch"项 (实测守住但最贴近临界, 后续抽检)。
