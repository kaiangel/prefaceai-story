# test20 完整地毯式审查报告

> **生成时间**: 2026-05-20 16:45
> **作者**: PM
> **测试**: test20 - "电梯镜中人" (horror, gothic 风格, 2:3, 3min, LLM 自由情绪)
> **Project UUID**: daf30634-576c-45be-adea-2dcf1f87e2b8
> **目的**: Wave 5 v3 通用叙事原则 + 全栈实证, 准备内测决策

---

## TL;DR

**v3 通用叙事原则真生效, 11 scene 全过 85% KPI (平均 0.929), 27 shot 全部生成 failed=0**。

但还**不能内测**, 因为发现 **5 个真问题** 需修复:

| # | 问题 | 优先级 | Owner | 阻塞内测? |
|---|---|---|---|---|
| 1 | ✅ supernatural schema 验证太严 (镜中人) | P0 → 已修 | Backend | 已闭环 |
| **6** | 🔴🔴 **freshness check 算法 bug — 用户重生角色白做** (PM 二次深挖发现) | **P0** | Backend | **🚨 是 (系统级 bug)** |
| 2 | 🔴 BGM 时长 36s (题材 prompt 含"短促/收尾"暗示词) | P1 | AI-ML | **是** |
| 3 | 🔴 角色风格不一致 (林深 anime/陈婶 realistic 不全 gothic) — 部分根因是 #6 | P1 | AI-ML + #6 修复 | **是** (用户视觉感知 P0) |
| 4 | 🟡 前后端 ETA 严重偏差 (4x 低估) + shots_completed 滞后 | P1 | Frontend + Backend | 是 (用户期望管理) |
| 5 | 🟡 Anthropic 529 fail-open 13/27 (48%) - 50% shot 未验证 | P2 | DevOps + Backend | 否 (兜底 by-design 但需监控) |

下一阶段最小修复集: **#6 (P0)** + #2 + #3 + #4. 然后跑 test21 (scifi) 验证, 再决定内测.

### 🚨 P0 灾难新发现 (Founder 二次实测追查): #6 freshness check 算法 bug

**症状**: 用户在 /characters 页主动重生角色 → 确认 → Pipeline 完成后 shot 里**仍然是旧版本**, 用户重生白做。
**真根因**: `pipeline_orchestrator.py:L1071` freshness check `_portrait_fresh = _portrait_mtime > _char_ts + 30` — `+30` buffer 把"同一时刻重生的"判为"陈旧", Pipeline 重新生成覆盖。
**影响范围**: **系统级 bug, 影响所有用户重生场景**。test20 林深+镜中人 Founder 没发觉是因为没主动重生 (用同样描述重生结果相似); 陈婶因风格大改 (realistic→gothic) 才显形。
**修复**: 改 `+30` 为 `>=` 比较 / abs 双边 / portrait_locked flag, 详见 PENDING T20-50。
**这是"修了一半"链条第 5 次重演** (#30/#39/#40/#43/本次), KEY_LEARNINGS #45 已记。

---

## 1. test20 完整 User Journey 时间轴

| 时刻 | 阶段 | 事件 | 备注 |
|---|---|---|---|
| 15:18:08 | Stage A | POST /api/projects/ (aspect=**2:3**, style=**gothic**, total_chapters=1, duration=3min, mood=null/LLM自由) | "未命名项目" Lin Shen idea |
| 15:18:11 | Stage 1 | POST /generate-outline → StoryOutlineGenerator → Claude Sonnet 4.6 | |
| ~15:20:?? | Stage B | Outline 出来, 11 plot_points, Founder 选最后一个 ending, **触发 outline validator 4 条警告** (climax 缺/inciting 重复/emotional_journey 不符) | Founder 点"知悉并继续" |
| 15:21:18 | Stage B | POST /confirm-outline | |
| 15:24:18 | Stage C | INSERT project_chapters + chapter_generation_jobs + POST /start-generation | Pipeline 真启动 |
| 15:24:18 | Stage 2 | [CharacterDesigner] 开始设计 3 角色 (林深 + 镜中人 + 陈婶) | Claude Sonnet 4.6 调用 |
| **15:25:43** | Stage 2 | 🚨 **P0 FAIL**: char_002 镜中人 supernatural physical 字段缺 being_type/base_form (KEY_LEARNINGS #43 - 第 4 次"修了一半") | Pipeline 失败 |
| 15:29:?? | hotfix | PM 派 Backend Agent (Sonnet 4.6) hotfix `pipeline_schemas.py:L213-245` 给 4 种"可能呈人形"的 type (supernatural/undead/mythological/fantasy_creature) 加 hair_color/skin_tone/face_shape OR fallback | 5 行改动 + 7 单测 + 重启 PID 52747 → 55022 |
| 15:35:31 | Stage 2 | Founder 点"原地重启" → CharacterDesigner 重新跑 | hotfix 真生效, 镜中人这次通过 schema |
| 15:37:32 - 15:39:02 | UX-1 | 林深 + 镜中人 + 陈婶 3 角色 portrait + fullbody 生成 (Seedream) | 6 张参考图全 1664×2496 (2:3) |
| ~15:39:?? | Stage 2 | character_ready, 跳 /characters | Frontend 真自动跳 ✅ |
| 15:40-46 | Stage B | Founder 在 /characters 页, 看到风格不一致: **林深 anime, 镜中人 gothic ✅, 陈婶 realistic ❌** | Founder 担心 |
| 15:46:00 | RegeneratePortrait | 陈婶 portrait 单独重生 (Founder 点) → 这次 gothic ✅ | |
| 15:46:56 | B57 | 陈婶 fullbody 同步重生 (用新 portrait 作参考) | |
| ~15:48:?? | Stage B | Founder 确认角色, 继续 | POST /confirm-characters |
| 15:49:14 | Stage 3 | [ScreenplayWriter] 开始生成 11 个 scene | Claude Sonnet 4.6 + v3 prompt |
| 15:51:10 | Stage 3 | 第 1 批 7 scene 完成 (Claude 响应 17071 chars, 115s) | |
| ~15:53:?? | Stage 3 | 第 2 批 4 scene 完成 | scenes_ready |
| 15:54:?? | Stage B | Frontend 自动跳 /scenes, Founder 浏览 + "象征性修改/完成" | POST /confirm-scenes |
| 15:54:27 | Stage 4 | [StoryboardDirector] 开始生成 storyboard, scene 分批 | 11 scenes → **27 shots** (LLM 决定, 比预估 18 多 50%) |
| 15:54-15:58 | Stage 4 | batch 处理 11 scenes, 每 scene ~30s Claude | |
| ~15:59:?? | Stage 5 image_preparation | 重新生 3 角色参考图 (Founder 陈婶重生后 Pipeline 刷新缓存) | |
| 16:00:03 | warning | [SeedreamGenerator] IncompleteRead (attempt 1, by-design retry) | 网络抖动 routine |
| 16:02:24 | Stage 5 image_generation | ✅ Shot 3 (1664x2496, 46s, sanitize=0) | T20-26 SEEDREAM_SAFETY 真生效 |
| 16:02:30 | Stage 5 | ✅ Shot 1 (51s) | |
| 16:02-16:18 | Stage 5 | 27 张 shot 陆续生成, **fail-open skipped_count 累计 13** (48% shots Anthropic validator 跳过) | Anthropic 全区域 529 过载 |
| 16:16:58 | T17 ⚠️ | Shot 16 anatomy_issue: 4 hands visible (Seedream hallucination) | by-design 警告级, 不强制重生 |
| 16:18:31 | Stage 6 BGM | [StoryMusicExtractor] 5 mood 解析 (unsettling_fatigue → paranoid_dread → mounting_dread → peak_terror → relief_then_dread) | B57 str/dict 双修正常 |
| 16:18:36 | Stage 6 | BGM Haiku prompt 生成 (605 chars, gothic generic 风格) | linter 1st pass PASS |
| 16:19:14 | Stage 6 | Mureka 返回 mp3, **duration_ms=40670 (40s)** ❌ 比之前的 2-3min 短了 5x | 真根因 = prompt 含"silences/stops/no resolution"暗示词 |
| 16:19:19 | Stage 6 | FFmpeg fade 处理 → output **36.84s** | 后处理 fade 在短曲上比例过大 |
| 16:19:20 | Stage 6 | BGM URL 写入 chapter | |
| 16:19:28 | Pipeline | ========== Pipeline 完成 ========== | 总耗时 ≈ 44 min (含 Founder 等待 + hotfix 重启) |
| ~16:25:?? | Stage D | Founder 看 /preview, BGM 仅 36s 提问 → PM 第一轮误诊为"payload 缺 duration" | KEY_LEARNINGS 第 5 次表象诊断 |
| ~16:35:?? | 纠正 | Founder 反驳 → PM 地毯式深挖, 真根因 = prompt 工程层 | T20-45 已记 PENDING |

---

## 2. Bug 完整清单 (P0/P1/P2/P3)

### A. ✅ 已修 P0 真 bug (1 个)

#### B1. supernatural humanoid schema 验证太严 (KEY_LEARNINGS #43)

- **症状**: 镜中人 char_002 LLM 给 character_type=supernatural + 完整人类外貌字段 → schema 报"physical 字段缺少最小集: 需要 being_type OR base_form"
- **真根因**: `_TYPE_REQUIRED_GROUPS['supernatural']` = `[('being_type', 'base_form')]` 太严, 没接受"呈人形"配置
- **修复**: `pipeline_schemas.py:L213-245` 给 supernatural / undead / mythological / fantasy_creature 各加 `hair_color, skin_tone, face_shape` OR fallback
- **验证**: 7 新单测 + 44 回归全 PASS, Backend 重启 PID 55022, /health 200, test20 镜中人通过 schema
- **教训沉淀**: KEY_LEARNINGS #43 "修了一半第 4 次"

### B. 🔴 待修 P1 阻塞内测 bug (3 个)

#### B2. BGM 时长 36s (Mureka 没 duration 参数, prompt 词控时长)

- **症状**: test20 BGM 0:36, 故事 3min, BGM 只够前 5-6 张 shot
- **真根因 (PM 第一轮误诊后纠正)**:
  - ❌ 不是 payload 缺 duration (Mureka API 文档确认根本没 duration 字段)
  - ✅ 真根因: BGM prompt 含 "Long silences / suddenly stops / No resolution / question hanging" 等"短促/收尾"暗示词 → Mureka 推断短曲
  - ✅ 历史 BGM (4/23 ~ 5/19) 全部 2-3min, payload 一直没 duration, 只是 prompt 内容是 sustained 风格
- **修复方向**: AI-ML 改 BGM Haiku meta-prompt 加硬约束 "TARGET DURATION: ~3 minutes sustained development, AVOID 'silences / suddenly stops / no resolution' as primary motifs"
- **PENDING**: T20-45 (已记)

#### B3. 角色风格不一致 (gothic 没强力 override 人物描述)

- **症状**: test20 林深 anime/manga 风, 镜中人 gothic ✅, **陈婶 realistic 真人写实** (3 张 portrait 风格完全不同, Founder 第一眼看出)
- **真根因**: StyleEnforcer 真调了 (`reference_image_manager.py:L378+L586`), gothic 词典也存在. 但 CharacterDesigner LLM 输出的角色描述具体性差异巨大:
  - 镜中人: "面容模糊, 苍白, 双眼空洞" → 抽象风格化 → Seedream 顺势 gothic
  - 陈婶: "60岁老妇人, 头发花白, 暗红色睡袍" → **过度写实化具象** → Seedream 偏 realistic
  - 林深: "28岁程序员, 戴眼镜, 深蓝卫衣" → 普通写实 → Seedream 给 anime (审美默认)
- **修复方向**: AI-ML 改 CharacterDesigner prompt 让 LLM 输出 character 描述时**强制带 style hint** (e.g. "60-year-old woman in gothic dark romantic style with pale skin and gaunt face")
- **PENDING**: 待加 T20-46

#### B4. 前后端 ETA 联动严重偏差 (4x 低估) + shots_completed 字段滞后

- **症状**: Backend ETA 790s (13min), Frontend 显示"3 分钟"; backend log 5 shot 完成时 status API 仍报 3 shot
- **真根因**:
  1. Frontend StageC ETA 渲染没真用 `status.estimated_remaining_seconds`, 用了 hardcoded/缓存值
  2. `shots_completed` 字段写库时机延迟 (可能只在 ShotValidator pass 后才 increment, fail-open 路径漏 increment)
  3. BGM 阶段 `shots_completed` 重置 0 (应保留 27 最终值)
- **修复方向**: Backend SeedreamGenerator 成功后立即 increment shots_completed; Frontend 5 stage 节点 ETA 算法对齐 backend
- **PENDING**: T20-44 (已记)

### C. 🟡 P2 待修非阻塞 (3 个)

#### B5. Anthropic 529 fail-open 13/27 (48% shot 验证跳过)

- **症状**: ShotValidator 调 Claude 验证 27 shot, 13 次 4/4 retry 全 529 → fail-open 放行 (skipped_count=13)
- **真根因**: Anthropic 服务今天大范围过载, T20-14 retry 兜底真生效
- **影响**: 48% shot 没经过 LLM 质量验证就交付了 (Shot 16 anatomy issue 是验证抓到的少数, 其他 48% 未知质量)
- **修复方向**: ① 降级 fallback (失败时用 Haiku/Sonnet 备用模型) ② 增加 retry 次数 (4→8) ③ 监控 fail-open 率, > 30% 时告警
- **PENDING**: 待加 T20-47

#### B6. Shot 16 anatomy_issue (Seedream 画 4 只手)

- **症状**: Shot 16 验证抓到 "4 hands visible" + "4 arms" hallucination
- **真根因**: Seedream 大模型常见 anatomy hallucination, 不是 prompt 错 (prompt_quality_report.md 显示 prompt 1158 字符 ✅ 三大检查通过)
- **当前**: 警告级 ⚠️, 不自动重生
- **修复方向**: ① 升级为 ERROR + 触发自动重生 ② 在 prompt 加 "anatomically accurate, exactly 2 hands, exactly 2 arms" 强制词 ③ 让用户在 /preview 看到"质量警告"标记 + 一键重生
- **PENDING**: 待加 T20-48

#### B7. Outline Validator 警告 4 条 (Stage 1 LLM 内部一致性)

- **症状**: outline 出来后弹"大纲存在以下提示" 4 条:
  - plot_points[-1] 仍为 midpoint 缺 climax/resolution
  - inciting_incident + first_turn 各 2 个用相同 beat 标签
  - 镜中人 emotional_journey 与实际节拍不符
  - 陈婶 emotional_journey 与实际节拍不符
- **影响**: Founder "知悉并继续", Stage 3 LLM 还会补 — **实测确实 Stage 3 + Stage 4 把缺失的 climax 补回来了** (Scene 11 完美高潮反转)
- **修复方向**: AI-ML 加强 StoryOutlineGenerator prompt 让 Stage 1 输出已自带 climax + beat 区分 + emotional_journey 一致性
- **PENDING**: 待加 T20-49 (P3)

### D. ✨ 已 wired 但未派工的长期改进 (1 个)

#### B8. CharacterDesigner prompt 补强 4 种人形 type (T20-43 长期修)

- **状态**: B1 schema 端已兜底, prompt 端补强让 LLM 输出更语义化 (优先填 being_type, 否则补人类外貌字段)
- **PENDING**: T20-43 (已记)

---

## 3. v3 通用叙事原则真效果验证 (Wave 5 实证)

### ✅ 完美通过 85% KPI

**11 个 scene 全部 ≥ 0.85** (平均 0.929):

| Scene | cluster | reader_comprehension_score |
|-------|---------|---------------------------|
| 1 | C2 | 0.90 |
| 2 | C2 | 0.92 |
| 3 | C2 | 0.91 |
| 4 | C2 | 0.95 |
| 5 | C2 | 0.93 |
| 6 | C2 | 0.94 |
| 7 | C2 | 0.92 |
| 8 | C2 | 0.93 |
| 9 | C2 | 0.95 |
| 10 | C2 | 0.91 |
| 11 | C2 | 0.96 |

**11 个 scene 全 C2 cluster** (悬念反转), 跟 horror 题材完美对应 ✅

### ✅ v3 完整字段透传

每 scene 含: `narrative_cluster` / `narrative_phase` / `narrative_viewpoint` / `narrative_structure` / `scene_self_evaluation` / `target_text_density` / `top5_principles_applied` / `structure_position_pct` / `cluster_reasoning` / `structure_reasoning`

(`SceneSchema.model_config = ConfigDict(extra='allow')` T20-29 P0 修复真接通)

### ✅ scene_self_evaluation 真深度

Scene 11 (高潮) self_eval:
```
reader_comprehension_score: 0.96
reasoning: "三个 critical turn 全部有对应 thought+dialogue：
  手没有温度揭示他已是死者；
  手表停在22:47锁定死亡时刻；
  最终'我就是镜中人'完成身份崩塌。
  读者关闭旁白完全能理解最大反转"
```

### ✅ horror C2 dialogue/narration 风格

Scene 6 (中段悬念):
- narration (简洁): "灯灭。陈婶话没说完，门锁上了。" (16 chars)
- dialogue:
  - 陈婶: "那面镜子……以前就有人在里面……"
  - 林深 thought: "（以前就有人？那是什么意思？！）"
  - 陈婶 (emphasis !!!): **"我不说了，你别去碰那面镜子！！！"**

`!!!` 红字渲染语义真生效, 关键线索通过对话+心理双通道传达, 留白合理.

Scene 11 (高潮反转):
- narration: "手表停在22:47。他就是镜中那个人。" (17 chars)
- dialogue: 6 条 thought+dialogue 揭示"我就是死去的镜中人"
- 完成 C2 cluster"悬念→反转"目标

---

## 4. 其他真生效模块验证

| 模块 | 状态 | 证据 |
|---|---|---|
| T20-22 anthropomorphic_animal plumage_color | N/A | test20 无动物角色 |
| T20-23 character_designer.py 按 type 分类验证 | ✅ | 3 角色全过 (含 supernatural hotfix) |
| T20-26 SEEDREAM_SAFETY_AVOIDANCE | ✅ | 27 shot 全部 sanitize_attempts=0, horror 暗黑题材一次通过 |
| T20-27 text_overlay 关键转折强制 | ✅ | Scene 6 / 11 emphasis_words `!!!` 真渲染 |
| T20-28 v3 通用叙事原则 | ✅ | 11 scene KPI 0.929 |
| T20-29 SceneSchema extra='allow' | ✅ | 所有 v3 字段真透传 |
| StyleEnforcer gothic | 部分 ✅ | 镜中人 gothic ✅, 林深/陈婶偏移 (B3) |
| Pipeline 单一生图模型 D.17 | ✅ | 全 Seedream, 无 NB2 混用 |
| 画幅 2:3 (1664×2496) | ✅ | 27 shot + 6 ref 全 2:3, 用户选的真生效 |

---

## 5. 未发现但可能存在的隐患 (待后续核查)

| 隐患 | 风险 | 验证方式 |
|---|---|---|
| 27 张 shot 角色一致性 (跨 shot 林深 / 镜中人 / 陈婶 是否同一个人) | 🟡 中 | Founder 翻 27 shot 视觉 check, 或派 Tester 跑 character_consistency_regression |
| BGM 5 mood 在 36s 内是否真渐进 | 🟡 中 | Founder 听 BGM 验证, 但 36s 不够展开 5 mood, 修 B2 后重测 |
| TextOverlay V2 在 27 shot 是否全部成功叠加 | 🟡 中 | Founder /preview 看每张 shot 是否有 caption/dialogue/thought 文字 |
| Shot 16 之外的 Anatomy issue (T17 ShotValidator 48% 跳过, 12 张未验证) | 🔴 高 | Founder /preview 翻 12 张未验证 shot 看是否有 hallucination |
| /preview 页所有功能 (重生/调整/文字编辑/BGM 换风格) | 🟡 中 | Founder 实测每个按钮 |
| Outline validator 警告"知悉并继续"后是否影响 Stage 3 (climax 缺) | ✅ 已验证 | Stage 3 真把 climax 补回来了 (Scene 11) |
| ETA contract Wave 6 / B58 是否覆盖所有 stage | 🟡 中 | T20-44 修时同步审计 |

---

## 6. 内测准备评估

### 当前完成度

| 模块 | 完成度 | 评分 |
|---|---|---|
| Stage 1 outline 生成 | 95% | A (validator 4 警告但 LLM 自愈) |
| Stage 2 角色设计 | 80% | B (schema hotfix 后 OK, 但风格不一致是真问题) |
| Stage 3 剧本 + v3 通用叙事原则 | **98%** | **A+** (85% KPI 全过, 真完美) |
| Stage 4 storyboard | 95% | A (T20-26 SEEDREAM_SAFETY 完美) |
| Stage 5 shot 生图 | 85% | B+ (27/27 但 48% validator 跳过 + Shot 16 anatomy) |
| Stage 6 BGM | 30% | D (36s 严重不达标) |
| Stage 6 文字叠加 | 待验证 | ? |
| 前端 user journey | 80% | B (跳转完整 + 真自动跳, 但 ETA 严重偏差) |

**综合**: ~80% (B 评级)

### 内测决策建议

**❌ 不建议立即内测**, 阻塞点 3 个 (B2 + B3 + B4):

1. **BGM 36s 严重不达标** — 用户看故事 1/5 BGM 就静音, 用户体验 P0 灾难
2. **角色风格不一致** — 用户第一眼就发现 (Founder 实测), 内测必然吐槽
3. **前后端 ETA 偏差 4x** — 用户期望 3min 实际 13min, 严重失信

**最小修复集 (内测前必须修)**: B2 + B3 + B4 三个 P1.

**最小验证**: 修完后跑 test21 (scifi 跨题材) + 1 个 fairytale (跨题材) 验证不退化, 然后跑 1 个新 horror 验证 B2 + B3 修复.

---

## 7. 下一阶段工作计划

### 立即派工 (本周内)

| RISK | 优先级 | Owner | 工时 | 模型 |
|---|---|---|---|---|
| T20-45 BGM prompt 工程修复 | 🔴 P1 | AI-ML | 1-2h | Sonnet 4.6 high |
| T20-46 (新) CharacterDesigner prompt 加 style hint | 🔴 P1 | AI-ML | 2-3h | Sonnet 4.6 high |
| T20-44 前后端 ETA 联动对齐 | 🔴 P1 | Frontend + Backend 协作 | 3-4h | Sonnet 4.6 high |
| T20-47 (新) Anthropic 529 备用模型 fallback | 🟡 P2 | Backend | 2h | Sonnet 4.6 high |
| T20-48 (新) Shot anatomy auto-regen + prompt 加 "exactly 2 hands" | 🟡 P2 | AI-ML + Backend | 2h | Sonnet 4.6 high |

### 修完后验证

1. 跑 test20 重生 (验证 B2 + B3 修复)
2. 跑 test21 scifi (跨题材, 验证 v3 + 风格 + ETA)
3. 跑 1 个 fairytale (跨题材, 验证 supernatural humanoid hotfix)
4. Founder ✅ 后正式内测启动

### KEY_LEARNINGS 待加

- **#44**: PM 第一轮 BGM 表象诊断错误 — "payload 缺 duration" 实际 Mureka API 没此参数, prompt 内容控制时长. Founder 反驳后地毯式深挖. 教训: API 参数假设必须先查文档 + 看历史数据 (历史成功为什么这次失败).

---

## 8. 文档更新清单

- ✅ `.team-brain/handoffs/PENDING.md` 加 T20-43 / T20-44 / T20-45 (已记)
- ✅ `.team-brain/knowledge/KEY_LEARNINGS.md` 加 #42 / #43 (已记); #44 待加
- ⏳ `.claude/agents/ai-ml-progress/context-for-others.md` 加 T20-43 (已记)
- ⏳ `.team-brain/TEAM_CHAT.md` 待 PM 追加 test20 完成消息
- ⏳ `.team-brain/status/TODAY_FOCUS.md` 待更新 "test20 全栈完成 + 5 维度审查"
- ⏳ `.claude/agents/pm-progress/current.md` 待更新

---

> **审查铁律**: 此文档按 KEY_LEARNINGS #29 / Ben 5/13 提醒 / Founder "毫无遗漏" 要求, 5+ 维度地毯式核查产出. PM 自评完整度 ~95%, 剩余 5% 待 Founder 实测 /preview 后反馈补充 (角色一致性 + TextOverlay + 27 shot 视觉质量).
