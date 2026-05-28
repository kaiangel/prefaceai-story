# AI-ML Engineer 当前任务

> 更新时间: 2026-05-28 17:05 (test30 portrait 重生 #6 + #7 完成, PM 沙箱代补)
> 状态: 🟢 #6 CFP-3 保留数量 + #7 GROUP COMPOSITION 群体 token 强化全部代码层完成, PM 跑 pytest 22 PASS / 0 退化, 待 DevOps 部署

## 🟢 5/28 test30 portrait 重生批次 — Sonnet 4.6 high (沙箱限制 progress 由 PM 代补)

### 一句话

`storyboard_prompts.py:1678` 加 RULE CFP-3 (LLM 层防丢失"一群"等数量 token) + `reference_image_manager.py:L353` 加群体检测注入 GROUP COMPOSITION (Seedream 层强化群体 token 权重)。

### 改动文件 (2 个)
1. **`app/prompts/storyboard_prompts.py:1678+`** — `CHARACTER_FIELD_PRESERVATION_RULES` 内加 RULE CFP-3 约 35 行, 含完整规则说明 + 2 个 ✅/❌ 示例 (萤火群改颜色 / 三学生改书包) + 中英关键词列表
2. **`app/services/reference_image_manager.py:354-369`** — `_build_portrait_prompt` 内三 char_type 分支之后加 `_GROUP_KEYWORDS_ZH/EN` 检测 + `_has_group` 判断 + `_group_prefix` 注入到 `core_prompt` 最前面

### Pytest (PM 代跑)
- `pytest tests/ -k 'adjust_character or reference_image or storyboard_prompt'` → **22 passed, 2 skipped, 0 退化** ✅

### 越权 / 安全
- ✅ 未碰 Backend / Frontend / DevOps 负责文件
- ✅ 只改 `app/prompts/` + `app/services/reference_image_manager.py:_build_portrait_prompt`

### 待 DevOps 部署 (commit + rsync + VPS rebuild api)

---

## (历史 2026-05-27) #8 BGM 路径B 完成

---

## 🟢 #8 BGM 路径B [2026-05-27] — 文化识别增强 + character_dominant_type 降级 (Opus 4.7 xhigh)

### 一句话
test29《荷塘渡》(锦鲤 aquatic + 菖蒲 plant + 荷塘) 暴露 BGM 两处人类中心。路径B=让 BGM 主吃 universal 信号(mood[用户选]+setting_period+题材), 把 character_dominant_type & style_category 降软提示。**禁路径A**(19×95 堆专属规则)。只改 `story_music_extractor.py` 一个文件 (BGM prompt 仍 Haiku 生成, meta-prompt 未碰)。

### 改了什么 (全在 `app/services/story_music_extractor.py`)

**① setting_period 文化识别增强 (真漏点, 2 处)**
- **#1a 字段名 bug 修复**: `_derive_setting_period` 旧版读 location `description`+`location_type`, 但真实 outline 用 `description_zh`/`display_name`/`key_visual_elements` → 荷塘/锦鲤/莲 所在的场景文本**从未被扫到**。修: 读全 4 个字段 (description 保留作向后兼容) + 加扫 character.description (非人类物种线索)。
- **#1b 新增 `_detect_chinese_cultural()` + `_CHINESE_CULTURAL_KEYWORDS`**: 中式审美是**和时代轴正交**的信号 (荷塘渡 = 中式但不特定朝代)。旧 ancient_china_keywords 偏 wuxia/朝代 → 荷塘渡判 generic。新 helper 扫荷塘/锦鲤/莲/水墨/古琴/中秋… (跨时代中式意象), 命中则在 `_derive_style_category` 把中性视觉风格(western_realistic/generic)拉向 chinese_traditional。**universal**(任何中式题材受益), 非堆 type 规则。setting_period 本身仍诚实返回 generic (荷塘渡无朝代) → meta-prompt 不强加战鼓/古战场修饰, 正合温柔荷塘基调。

**② character_dominant_type 降级 (软提示 + 安全 fallback)**
- 新增 `_CHARACTER_TYPE_TO_BGM_BUCKET` 把 19 系统 type 就近映射到 meta-prompt 认识的 4 桶 (animal/aquatic/insect/anthropomorphic_animal→animal; robot/digital_virtual/vehicle_character→robot; fantasy/mythological/elemental/plant/object/concept…→fantasy; human/miniature→human)。
- **关键修**: 无人类时**不再默认 human** (旧版 bug: 鱼/草/物件全落 human → log 误导)。未知 type 字面非人类 → fantasy 兜底。平票 human>animal>fantasy>robot 稳定排序。
- **取舍说明**: meta-prompt 明确此维 "通常不影响 BGM"(仅 robot 轻度电子化) = 本就弱信号。所以**不精确分类 19 type**(那是路径A 无底洞), 只给诚实就近映射, 关键是消除"鱼→human"误导。BGM 听感真正由 mood+setting+style_category 主导。

**③ 顺带修 2 个 pre-finding (我触碰函数时暴露, 同类防御)**
- 移除 future_keywords 里单独的 "霓虹"/"neon" — 现代都市夜景普遍有霓虹, 单独命中把现代爱情/外卖误判 future (probe 案例②③实证)。赛博朋克仍由 赛博/cyber/全息 命中。
- `_derive_setting_period` 的 plot_points 循环加 `isinstance(p, dict)` 守卫 (与 T19-5/9 同类 dict/str 防御) — plot_points 偶被 LLM 输成 str 会 AttributeError 冲垮提取。

### dry-run 证据 (`scripts/bgm_signal_probe.py`, 7 组 type×style×mood)
| 案例 | style_preset | setting_period | cultural | **style_category** | char_dom | mood |
|---|---|---|---|---|---|---|
| ① 荷塘渡 锦鲤+菖蒲 | watercolor | generic | ✅True | **chinese_traditional**(修前 western_realistic) | **animal**(修前 human) | 感人 |
| ② 西式现代爱情 | oil_painting | generic(修前误判future) | False | western_realistic | human | 浪漫 |
| ③ 外卖小哥 | manhwa | modern_china(修前误判future) | False | western_realistic | human | 热血 |
| ④ 古风武侠 | ink_wash | ancient_china | False | ink_painting | human | 紧张 |
| ⑤ 机器人末日 | cyberpunk | future | False | sci_fi | robot | 悬疑 |
| ⑥ 奇幻动物 | ghibli | fantasy_world | False | japanese_anime | animal | 治愈 |
| ⑦ 中式灯笼(object) | watercolor | ancient_china | ✅True | chinese_traditional | **fantasy**(非human) | 温馨 |

- _fill_placeholders round-trip: 荷塘渡 user prompt 含 chinese_traditional×11, 0 data placeholder 泄露 → Haiku 走中式 cell (古琴/dizi/pentatonic) 而非西式 piano/strings。

### 人类不退化验证
- 年夜饭 human 故事 self-test: human 保持, style→chinese_traditional (灯笼命中, 中国新年用中式 BGM **正确改进**)
- probe 案例②③④⑤ 全 human/正确 category
- 391 PASS (bgm/music/extract/emotional_arc 全域) 0 FAIL 0 退化
- 空数据/malformed(str chars/locs/plot, None/int 混入) 全graceful 不崩

### Ben 协议 5+1 / 边界
- 0 schema / 0 Alembic / 0 API 契约 / [frontend-impact: no] / DEC-051 0 删 fallback / 图像 prompt 未碰 / db_retry.py 未碰 / meta-prompt 未碰
- 只改 1 文件 `story_music_extractor.py` (纯数据提取, 无 API/DB)

### 改的文件
- `app/services/story_music_extractor.py` (#1a 字段 + #1b 文化检测 + #2 19type 映射 + #3 neon/guard)
- `scripts/bgm_signal_probe.py` (新, dry-run harness, 复用 extract 管道)

### 待 @tester / Founder
- @tester: BGM 域回归 (上述 391 + 不退化) + 建议补正式 unit test (我未碰 tests/ 白名单, probe 可参考)
- Founder e2e/抽测听感真证: 荷塘渡是否真出中式 BGM; 现代/西式/武侠不退化 (听感真证留 e2e)

### 待 PM
- 建议记 DEC 补充: "#8 BGM 路径B — 文化符号(与时代轴解耦)拉 style_category + char_dom 19type 就近映射不默认 human"

---

## 🟢 test29 非人类消费层专项 [2026-05-26] — #5 + #6 + #7 (Opus 4.7 xhigh)

### 一句话
test29《荷塘渡》(金鲤 aquatic + 菖蒲 plant + 荷塘 concept) 炸出"数据层已通用、消费层全人类中心"假设链。本轮横扫 3 个消费层缺口: **prompt builder 字段错配(#5) / Seedream 角色融合(#7) / ShotValidator 非人类计数判 0(#6)**。

### #5 非人类 type 结构化外观字段错配 → golden 丢 (改 2 文件)
**根因**: Stage 2 把所有 type 属性写进 `physical`, 但消费层从 `character[type名]` 读。**两个独立层都中招**:
- **#5a 锚点层 (最影响成片, 改 `app/prompts/identity_anchor_prompts.py`)**: `_CHARACTER_TYPE_PRIMARY_COLOR_FIELDS` 对 aquatic/plant/insect/object 等 16 个非 human type **只列 `hair_color`** → 真鱼/真草无 hair_color → `primary_color=''` → CHARACTER ANCHORS 块**不渲染颜色** → golden 在到达 Seedream 的 shot prompt 里彻底丢失。**这是生产 shot 的主要漏点**(builder 那条只管参考图)。修: 每 type 列其真实结构化色字段(scale_color/leaf_color/exoskeleton_color/color_scheme/energy_color/skin_color/body_color...)在前, `hair_color` 作 tail fallback (mermaid/dryad 等半人形仍走 hair)。
- **#5b 参考图层 (改 `app/services/character_prompt_builder.py`)**: 18 个非人类 builder 从 `character.get('aquatic'/'plant'/...)` 读 → 空 → fallback "An aquatic creature"。加 `_type_attrs()` helper: `character[type] or physical` 字段级 fallback (向后兼容旧 sub-dict 布局 + 新 physical 布局)。
- ✅ 人类 path 0 改动 (未碰 `_build_human_description`/`_build_anthropomorphic_animal_description`)。实测 16 type primary_color 全resolve, 金鲤 "scale: golden" 进 prompt。

### #7 Seedream 融合非人类角色 (改 `app/services/identity_anchor_injector.py` + `shot_validator.py`)
- **prompt 侧 (主防线)**: `_render_character_anchors_block` 末尾, 当 ≥2 角色渲染 → 注入 `## MULTI-SUBJECT SEPARATION (MANDATORY — DO NOT MERGE)`: "N DISTINCT SEPARATE beings... MUST NOT fuse/merge/graft... 接触=两个独立身体相触, 绝非合并成一个生物"。2+ 非人类时追加 CRITICAL "different KINDS, no chimera" 行。通用(任何 type), 单角色 shot 不注入。
- **validator 侧 (诊断, 不洗白)**: anatomy 段加 "SUBJECT FUSION" 子检——两个该独立的角色被融成一体(草从鱼背长出)= GENERATION ERROR, **NOT 故意超现实**, 报 `has_visual_unnaturalness` 诊断。⚠️ 保持 log-only (不升 severe), 避免 #6 的重试浪费; 真预防靠 prompt 侧分离指令。

### #6 ShotValidator 非人类角色计数判 0 → 8/22 FAIL 重试浪费 (改 `shot_validator.py`)
- 根因: vision prompt L522 问 "how many **human** characters" + "Do NOT count animals/objects" → 鱼+草数成 0, 但 expected=2 → FAIL → 重试(+73% 成本/时间)。
- 修: 计数问题改 "distinct FEATURED characters... includes humans AND non-human: animals/plants/objects/creatures" + 显式 "golden fish + green reed = 2, not 0"。anatomy 段对非人形不套人类肢体计数(鱼有 fin 不是 hand)。
- 与 #7 联动: #7 修好图里真有 2 独立角色 → 计数自然过半 + 本 prompt 让模型把鱼/草算进 count → 双管齐下。

### 验证证据
- dry-run: 金鲤 shot prompt 含 "scale: golden" + MULTI-SUBJECT SEPARATION + 不丢 StyleEnforcer/marker/narrative 层
- 16 type primary_color 全 resolve (scale/leaf/exoskeleton/color_scheme...)
- builder 跨 type + 旧布局向后兼容 + human path 不退化
- 回归: 426 PASS (anchor/identity/cross-genre/validator/layer1/species) + shot_validator 58 PASS, 0 FAIL 0 退化
- 0 删 fallback (DEC-051) / 图像 prompt 全英文 / 单一模型 dispatch 未碰 / 未碰 db_retry.py

### 改的文件
- `app/prompts/identity_anchor_prompts.py` (#5a 优先色字段 map)
- `app/services/identity_anchor_injector.py` (#7 分离指令)
- `app/services/character_prompt_builder.py` (#5b builder physical fallback)
- `app/services/shot_validator.py` (#6 计数通用化 + #7 fusion 诊断)

### 待 @tester
- 回归: 上述 426+58 + 角色一致性回归 (3人场景 ≥95%)
- e2e 复测: 非人类多角色故事 (鱼+草/object 同框) — 验 golden 不丢 + 不融合 + 不再 8/22 FAIL 重试; 顺带 human 故事不退化

### 待 @backend (联动, 非本轮)
- #6 重试浪费的另一半: 若 e2e 仍偶发非人类 count mismatch, 可考虑 validator 计数对纯非人类多角色 shot 放宽容差 (与 T20-6 skip 同 pattern), 但建议先看 prompt 通用化 + #7 分离指令的 e2e 效果再定。

---

## 🟢 Wave 13 #5b 完成 [2026-05-25] — schema character_type 5 type fallback 核实 (Opus 4.7 default)

### 一句话结论
**任务问的核心 (5 type 的 physical 字段校验) 已被 Wave 8 通用 fallback 根治, 内测用户选这些 type 不会因 physical 崩 — PENDING "已根治" 对, memory "待修 Wave 4.5" 过时。** 但地毯式追调用栈意外挖出一个**旁路崩溃点**: `character_designer._validate_characters` 对 clothing 强制要求 top/bottom/footwear/style 全有 — 真物件/真鱼/真植物/真昆虫天然没衣服, 若 LLM 输出残缺 clothing → Stage 2 直接 raise 且无 retry/fallback 兜住 → pipeline 死。此点在 `app/services/character_designer.py` (非我白名单), 已派 @backend 修。

### 核实方法 (地毯式追完整 5 层调用栈, 不凭文档)
- 生成层: `character_designer.design()` L127 调 `_validate_characters` (Layer 1)
- 拼装层: `pipeline_orchestrator` L587 调 `validate_characters` → `CharacterSchema(**char)` (Layer 2, pipeline_schemas.py)
- 校验逻辑层: `CharacterSchema.validate_physical_by_type` (Wave 8 通用 fallback 架构 L307-374)
- 数据写入: 实测构造 5 type 真实数据跑两层校验
- 数据消费: 检查 output/ 历史 LLM 真实 clothing 输出

### ① physical 校验真实状态 (逐个, 实测证据)
Wave 8 `validate_physical_by_type` 三路:
- 路径 1 (精确规则, 仅 4 type): human / anthropomorphic_animal / animal / vehicle_character → 缺最小集才 raise
- 路径 3 (通用 fallback, 其余 15 type 含 aquatic/object/plant/insect): 含 humanoid 字段→PASS; **不含也只 logger.warning, 永不 raise**

| type | physical 含 humanoid? | physical 校验 | 会崩? |
|---|---|---|---|
| aquatic 水生 | 有/无均可 | 路径3 | ✅ 不崩 |
| object 物件 | 有/无均可 | 路径3 | ✅ 不崩 |
| plant 植物 | 有/无均可 | 路径3 | ✅ 不崩 |
| insect 昆虫 | 有/无均可 | 路径3 | ✅ 不崩 |
| anthropomorphic_animal | — | 路径1 | 仅缺 species 才崩 (已有 species 锁定) |

实测 (静音 warning 只看 raise): 5 type 真非 humanoid 数据 (会说话的钟/鱼/向日葵/蚂蚁) physical 全 PASS。
回归: `test_schema_generic_fallback_arch.py` 83 passed (含 5 type 有/无 humanoid 两种 case)。

### ② 旁路崩溃点 (意外发现, 真风险, 已派 @backend)
`character_designer._validate_characters` L618-621:
```python
clothing_required = ["top", "bottom", "footwear", "style"]
clothing_missing = [f for f in clothing_required if f not in clothing]
if clothing_missing: raise ValueError(...)  # 对所有 type 一刀切
```
实测: 真物件/鱼/植物/昆虫若 clothing 缺 top/bottom/footwear → **L1 RAISE**。
- 此校验在 `design()` L127 生产路径, **在 LLM fallback try/except 之外** → 不被 Claude→Gemini 链兜住
- orchestrator L580 调 `design()` **无 retry wrapper** → raise 直接冲垮整条 pipeline
- Stage 2 prompt (`_build_prompt` L404-412) 对 human/动物/超自然有 clothing 指引, **对 object/aquatic/plant/insect 零指引** → LLM 给残缺 clothing 概率高
- 为何 test28 没崩: test28 "灵魂"是 `supernatural` 人形 (78cb5ceb 实证), **非真 object** → 真 object/aquatic/plant/insect 从未跑过 pipeline, 此路径生产未测

### ③ 矛盾澄清
- memory `project_schema_humanoid_fallback_remaining` "aquatic/object/plant/insect 待修 Wave 4.5" → **过时** (Wave 8 通用 fallback 已根治 physical, 建议 PM 更新/归档)
- PENDING L26/#5b 引用的 "Wave 8 已根治" → **physical 维度正确**
- 但**两者都没覆盖 clothing 旁路崩溃点** — 这是核实新增发现

### ④ 我是否改了代码: 没有 (0 改动)
根因 (prompt 缺 clothing 指引) + 崩溃点 (`_validate_characters`) 均在 `character_designer.py` (`app/services/`, **非我白名单** `app/prompts/**`+`style_enforcer.py`)。按 stay-in-role, 派 @backend 修, 不越权。

### 给 @backend 的修复建议 (surgical, 不删 fallback DEC-051)
2 选 1 或都做:
- **A (推荐, 校验层放宽)**: `_validate_characters` L618-621 clothing 必填字段对非 human type 放宽 — 非穿衣 type (object/aquatic/plant/insect/animal/elemental 等) 只要 clothing 是 dict 即可, 或缺字段降级 warning 不 raise (与 anthropomorphic_animal physical 已用的 warning 降级同 pattern)
- **B (源头, prompt 补指引)**: `_build_prompt` 给 object/aquatic/plant/insect 加 clothing 说明 (无衣物时填 "n/a"/"none"/装饰性外观), 让 LLM 总输出合法 clothing
- ⚠️ 两者都属 Pipeline 域 (`character_designer.py`), 与 @backend 协商; 我可提供 prompt 文案

### 文件
- 0 代码改动
- 实测 harness: 内联脚本 (未落盘, 见 TEAM_CHAT 证据)
- 文档: ai-ml-progress 三件套 + TEAM_CHAT

---

## 🟢 Wave 12 P1 完成 [2026-05-24] — style 画风漂移系统评估 + 分层补强 (Opus 4.7 xhigh)

### 核心成果
1. **架构根因定位**: Seedream payload **无 negative_prompt** → forbidden 只能经 prefix 的 `DO NOT USE` 行 (取 `forbidden[:8]`) 影响 Seedream; mandatory 同理取 `[:5]`。shot 路径甚至不过 StyleEnforcer (用 Stage 4 LLM image_prompt 原文), forbidden/mandatory 真正生效靠参考图路径 + Layer 1 inject 的 top5/top8。**铁律: anti-anime 词必须挤进 forbidden[:8] / mandatory[:5]**。
2. **28 style 四维评估 + 实测校准** (强动漫先验角色 28岁帅哥, doubao-seedream 直生): 校准 PM 纸面初判 —
   - 🔴 cyberpunk (实证) + **pastel_dream (纸面🟡→实测🔴, full anime)**
   - 🟡 gothic (mild, 光面 CG idol)
   - 🟢 **下调** ink/watercolor/ukiyo_e/pixel (实测守住 — mandatory 已有介质锚点) + noir (B&W 强锁)
   - 根因模式: 漂移 ⟺ mandatory[:5] 只锁氛围不锁渲染介质 + forbidden[:8] 无 anti-anime
3. **分层补强 style_enforcer.py (仅 3 style, 逐个甄别)**:
   - cyberpunk: mandatory[:5] 加 photorealistic+cinematic / forbidden[:8] 加 anime/cartoon/manga/cel-shaded 等
   - pastel_dream: mandatory[:5] 加 soft painterly illustration+airbrushed (不加 photorealistic) / forbidden[:8] 加 cel-shaded/hard anime lineart/manga
   - gothic: mandatory dark romantic painting / forbidden[:8] 加 anime/cel-shaded/glossy idol render
4. **零破坏 by-design 动漫类** (cartoon/ghibli/manga/chibi/illustration/korean_webtoon/anime/slam_dunk 0 改动, verify 0 自禁介质)
5. **实测验证**: cyberpunk 强改善 (→真写实电影感, 与老周可同框) / pastel_dream 改善 (硬动漫→柔笔触插画) / gothic 轻横移
6. **回归**: 377 PASS 0 FAIL 0 退化, 28/28 prefix 正常 render, DEC-051 0 删 fallback

### 文件
- 改: `app/services/style_enforcer.py` (3 style forbidden/mandatory)
- 新: `scripts/style_drift_probe.py` (实测 harness, 复用 enforce_prompt 管道)
- 文档: `.team-brain/analysis/STYLE_ANTI_ANIME_FORBIDDEN_GAP_2026-05-24.md` 第七章

### 待 PM/Tester
- @PM: 5+1 维度审查 + self-commit
- @Tester: 重跑 test26 (老周+陈明同框) + pastel_dream 强动漫先验角色 e2e; watercolor 列 watch 抽检

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
