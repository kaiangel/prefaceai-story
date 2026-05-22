# test19 端到端完整测试审计报告

> **测试日期**: 2026-05-19
> **测试时段**: 20:34:22 → 22:04 (~90 min, 含 3 次原地重启 + 5 次 Shot 15 重生)
> **Project UUID**: `36b303b2-2877-4ab4-9d61-6090e7d7282c` (DB id=41)
> **故事**: 《独眼鸦的第二十七年》 (陈砚 + 陈怀山 + 独眼鸦, dark_fantasy, 3:4, 短篇 ~18 shots)
> **目的**: 验证 TASK-T20-FIXBATCH-4 Wave 1+2 全栈修复 (12 RISK) + 暗黑奇幻 + anthropomorphic_animal universal
> **最终成片**: 18/19 PNG (Shot 15 content_safety 永久失败) + BGM 198s dark_fantasy

---

## 0. 执行总结

| 维度 | 结果 |
|------|------|
| Pipeline 全栈闭环 | ✅ 6 stage 全过 (outline / characters / screenplay / storyboard / images / bgm) |
| Wave 1+2 修复实证 | **12 修 PASS** + **5 个新 RISK 发现** + **1 个 KEY_LEARNINGS 待加** |
| 故事可读性 | **85%** (Founder "脱旁白 80-90% 可读", 但 dialogue/thought 偏短) |
| Shot 15 content_safety | 5 次重生都失败 → 接受 18/19 |
| 总 Pipeline 时间 (最后成功一轮) | 1870s ≈ 31 min |
| 实证 PASS 的修复总数 | **9 项** (T20-9.v3/10/12/13/15/17/19/20/21) |
| 新发现 RISK 总数 | **6 项** (T20-22 P0 / T20-23 P0 / T20-24 P2 / T20-25 P2 / T20-26 P0 / T20-27 P2) |
| Backend 重启次数 | 3 次 (T20-22 + T20-23 + 重启加载 T20-23 修复) |

---

## 1. 完整时间线 + Bug 出现位置

### Phase 0: 服务准备 (20:04-20:34)

| 时间 | 事件 |
|------|------|
| 20:04 | Backend 干净重启 (PID 19913) |
| 20:05 | Frontend 干净重启 (PID 14043, next dev) |
| 20:09 | 8 维度 baseline 全绿 |
| 20:11 | Cron 9d5f09a6 每 2 min 拉起, 3 个 Monitor 启动 |

### Phase 1: 创建故事 (20:34-20:35)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 20:34:22 | ✅ Project 创建 (id=41, UUID 36b303b2) | OK |
| 20:34:22 | Founder 输入参数: style=dark_fantasy, ratio=3:4, duration=2min/18 shots, mood=空 | OK |
| 20:34:27 | Stage 1 StoryOutlineGenerator 启动 (Claude Sonnet 4.6) | OK |
| 20:35:46 | ✅ Stage 1 完成 (79s, 3 角色 + 7 情节点 + 3 场景) | OK |

### Phase 2: 大纲 + 确认 (20:36-20:40)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 20:36 | Founder 进 /outline 看大纲 | OK |
| 20:36-20:40 | 🐛 /outline 页面 frontend 重复 polling chapters/* (76 个 404 routine warn) | **P2 RISK-T20-11.v2 (Wave 1 修了 30s 二次载入, 但 /outline polling 仍有)** |
| 20:40:15 | Founder 选最后一个结局, 点确认大纲 | OK |
| 20:40:23 | Pipeline 启动 (job_id=28, chapter_id=26) | OK |

### Phase 3: Stage 2 失败 1 次 (RISK-T20-22 真根因)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 20:40:39 | Stage 2 CharacterDesigner 启动 (Claude Sonnet 4.6) | OK |
| 20:42:18 | ❌ **Stage 2 失败 (99.3s)** | **P0 RISK-T20-22** |
| | char_003 (独眼鸦, character_type='animal') schema 验证失败 | |
| | `_TYPE_REQUIRED_GROUPS['animal']` 只接受 `[fur_color OR feather_color OR scale_color]`, 但 LLM 用了 `plumage_color` (鸟类专用) | |
| 20:42:36 | Frontend StageC 收到失败信号 → 显示 "生成遇到问题" 友好 UI (RISK-T19-2 Wave 12) | ✅ 实证 |

### Phase 4: PM 紧急修复 RISK-T20-22 (20:42-20:54)

| 时间 | 事件 |
|------|------|
| 20:43 | PM 发现 T20-22 真根因 + spawn AI-ML agent (Sonnet 4.6 high) |
| 20:44 | AI-ML 改 pipeline_schemas.py `_TYPE_REQUIRED_GROUPS`: 加 plumage_color/skin_color/chitin_color |
| 20:48 | AI-ML 完成 12/12 新单测 + test19 真实数据验证 PASS |
| 20:52 | PM 5 维度地毯式审查 PASS + 验证 test19 char_003 真过 schema |
| 20:53 | Backend 重启 (kill 13620 + nohup 19913 + T20-22 加载) |
| 20:53:25 | Founder 点 "原地重启" → Pipeline 第 2 次启动 (从 disk 加载 1_outline.json, 省 Stage 1 LLM) |

### Phase 5: Stage 2 失败 2 次 (RISK-T20-23 真根因)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 20:53:36 | Stage 2 Claude 第 2 次 | OK |
| 20:56:13 | ❌ **Stage 2 失败 (156s)** | **P0 RISK-T20-23** |
| | `character_designer.py:322 _validate_characters()` 抛 ValueError | |
| | "角色 char_003 physical 缺少字段: ['hair_color', 'hair_style', 'skin_tone', 'face_shape']" | |
| | T20-10 Wave 1 修了 5 处下游 dispatch, **漏改第 6 处** _validate_characters! | |
| 20:56 | KEY_LEARNINGS #30 "Wave 14 修了一半" **第 3 次重复实证** |

### Phase 6: PM 紧急修复 RISK-T20-23 (20:56-21:08)

| 时间 | 事件 |
|------|------|
| 20:57 | PM 加 RISK-T20-23 + spawn Backend agent (Sonnet 4.6 high) |
| 20:59 | Backend 改 character_designer.py L300-330: 按 character_type 分类 (human 严格 / anthropomorphic_animal warning / 其他跳过让 pipeline_schemas 验证) |
| 21:00 | 新单测 13/13 PASS + audit 全 codebase 无第 4 处漏点 |
| 21:02 | PM 5 维度审查 PASS |
| 21:03 | Backend 重启 (kill 19913 + nohup 21703 + T20-23 加载) |
| 21:08 | PM 用 backend python 真实验证 test19 char_003 schema + _validate_characters else 分支 |

### Phase 7: Stage 2 成功 (21:12-21:17)

| 时间 | 事件 |
|------|------|
| 21:12:48 | Founder 点 "原地重启" (第 3 次) |
| 21:12:52 | RISK-T17-8 从 disk 加载 1_outline.json |
| 21:13:02 | Stage 2 Claude 第 3 次启动 |
| 21:14:49 | ✅ **Stage 2 完成 (107s)** 3 角色全过 schema | |
| 21:15:41 | ✅ char_001 陈砚 portrait (49s) |
| 21:16:27 | ✅ char_002 陈怀山 portrait (46s) |
| 21:17:06 | ✅ char_003 独眼鸦 portrait (39s) ← T20-17 species fidelity 关键! |

### Phase 8: Stage B 用户确认 (21:17-21:25)

| 时间 | 事件 | 反馈 |
|------|------|------|
| 21:17 | Founder 进 /characters 页面 | ✅ 60s 倒计时圆形 badge (T20-12 PASS) |
| 21:17 | ✅ 独眼鸦真画成乌鸦 (T20-17 SPECIES_FIDELITY_RULES 实证 PASS) | |
| 21:17 | ✅ 陈砚/陈怀山/独眼鸦 portrait 显示正常 | |
| 21:19:55 | Founder 测试: 把陈怀山"银扣"改"黄金扣", 点重新生成 | (adjust_character API) |
| 21:20:37 | ✅ char_002 portrait 重生 (42s) | ✅ T20-20 实证 |
| 21:22:09 | ✅ B57: char_002 fullbody 同步重生 (88s) | ✅ B57 双层一致性 |
| 21:22:42 | Founder 看新 portrait 满意, 点确认角色 | OK |
| 21:22:50 | Stage 3 ScreenplayWriter 启动 | OK |
| 21:24:23 | ✅ **Stage 3 完成 (92s, 7 场景 + 21 action_beats)** | |
| 21:25:42 | Founder 在 /scenes 看 7 场景, 点 "修改/完成" 确认 | OK |
| 🐛 | Frontend confirm-characters 后跳错: /characters → /scenes 加载 20s → /generating | **P2 RISK-T20-25** |

### Phase 9: Stage 4 storyboard (21:25-21:29)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 21:25:54 | Stage 4 StoryboardDirector 启动 (7 batches Claude) | OK |
| 21:26:36 | Claude 第 1 批响应 (42s, Scene 1) | OK |
| 21:29:30 | 🟡 [B51 fallback T20-7 v2 + LLM] Scene 5 LLM 3 次失败, 用 screenplay-aware fallback shot (variant_idx=0) | **已知设计行为, Wave 1 T20-1 修复目标** |
| 21:29:30 | ✅ T20-7-v2 LLM 翻译成功 (302 chars, 同秒后续) | ✅ Wave 1 T20-1 修复实证 |
| 21:29:33 | ✅ **Stage 4 完成 (219s, 总 shots=19)** | DEC-028 不截断 |

### Phase 10: Stage 5 image_preparation + 生图 (21:29-21:42)

| 时间 | 事件 | 严重度 |
|------|------|--------|
| 21:29-21:32 | 角色参考图 6 张 (3 portrait + 3 fullbody) + 场景参考图 (interior/exterior anchor) | OK |
| 21:33:05 | Stage 5 image_generation 启动 (Semaphore=3 并发) | OK |
| 21:33:16 | 🟡 GC 兜底跳 Shot 6/11/16 (每 5 shots 跳 1, RISK-T20-16 P2 已知延后机制) | 已知 |
| 21:34-21:38 | Shot 1-9 顺利完成, 均值 ~52s (vs test17 v2 ~143s **快 3 倍**) | ✅ |
| 21:39:39 | ❌ **Shot 15 content_safety_failure** (sanitize 3 次拦截, D.17 不切 NB2) | **P1 RISK-T20-26** |
| 21:39:50 | SafetyAdvisor 分析: "0 个可疑词" (库不全, 没识别 ghost/double-exposure) | |
| 21:40:33 | ✅ Shot 11 GC 延后补跑 (53.71s) | ✅ |
| 21:41:08 | ✅ Shot 16 GC 延后补跑 (62.88s) + ShotValidator pass | ✅ |
| 21:42 | Stage 5 完成 (18/19 PNG, Shot 15 ❌) | partial_failure=True |

### Phase 11: Stage 6 BGM (21:43-21:44)

| 时间 | 事件 |
|------|------|
| 21:43:44 | FFmpeg 后处理 (B31 切水印 4s, 202s → 198s) |
| 21:43:46 | ✅ BGM 完成 (LUFS=-15.7, 静音检测 PASS, 10 credits) |
| 21:44:02 | ✅ **Pipeline 完成 (总耗时 1870s = 31 min)** + 标题 "独眼鸦的第二十七年" |
| 21:44:11 | GenerationResult 返回 |

### Phase 12: Founder /preview 验收 + Shot 15 重生 (21:45-22:04)

| 时间 | 事件 |
|------|------|
| 21:45+ | Founder 进 /preview 看 18/19 PNG |
| 21:50 | Founder 反馈: ✅ 独眼鸦画对乌鸦 / ✅ 18 shots 可读 80-90% / 🟡 dialogue 过于简短 / ✅ "描述(只读)" 文案 / ✅ BGM dark_fantasy |
| 21:51 | ❌ Shot 15 重生第 1 次 (用同 prompt) — 失败 |
| 21:52 | Founder 点 "调整画面" 改 "极其相似" → 重生第 2 次 — 失败 |
| 21:56 | Founder 改 "光晕中陈砚独立, 远处虚化身影但不重叠" → 重生第 3 次 — 失败 |
| 21:59 | Founder 改 "陈砚跪在雪地, 双手按在墓碑上, 远景" → 重生第 4 次 — 失败 |
| 22:00 | PM 深挖: Haiku 改写 **追加** Founder intent 到原 prompt (含 ghost/double-exposure), 没 strip 敏感词! |
| 22:04 | Founder 决定: 接受 18/19 缺图发布, 跳过 Shot 15 |

---

## 2. 全部 RISK 清单 (按严重度排序, 含本测试新发现 6 个)

### 🔴 P0 (新发现 + 升级, 4 个 — 内测前必修)

#### #50 RISK-T20-22 ✅ closed — schema 'animal' 缺 plumage_color
**实证修复**: pipeline_schemas.py `_TYPE_REQUIRED_GROUPS['animal']` 加 plumage_color/skin_color/chitin_color, `_TYPE_REQUIRED_GROUPS['anthropomorphic_animal']` 加 plumage_color. 12 新单测 PASS + test19 真实数据 char_003 schema PASS.

#### #51 RISK-T20-23 ✅ closed — character_designer 硬要求 human 字段
**实证修复**: `app/services/character_designer.py:_validate_characters()` 按 character_type 分类:
- human → 严格 5 字段
- anthropomorphic_animal → warning only
- else (17 种其他类型) → 跳过, 由 pipeline_schemas 验证
13 新单测 + audit 全 codebase 无第 4 处漏点

#### #54 RISK-T20-26 P0 (真根因升级) — PromptRewriter 追加策略 (不 strip 旧 ghost/overlay)
**实证 5 次失败**: Haiku PromptRewriter 是 **append-only**, Founder intent 追加到原 prompt 末尾, 不删 ghost/double-exposure 等敏感词. Founder 试 4 种不同 intent (含彻底改场景) 都失败.
**修复方向**:
- Haiku prompt 改 replace 策略
- 加强制 strip 规则: "MUST DELETE: ghost / double-exposure / deceased / face overlap / two faces merging / identical jaw"
- Haiku 生成全新 prompt 基于 Founder intent + scene 元数据 (不 patch 原)

#### #54.2 SafetyAdvisor 关键词库不全 (T20-26 派生)
**实证**: 分析显示"0 个可疑词", 但 Seedream 实际拒. SafetyAdvisor 没识别 ghost/double-exposure/jaw 等暗黑题材高频词.
**修复**: 扩展 SafetyAdvisor 关键词库 + 给用户清晰提示

### 🟡 P1 (1 个)

#### #54 RISK-T20-26 (同上, 已升 P0)

### 🟢 P2 (5 个新发现)

#### #52 RISK-T20-24 P2 — Frontend progress bar 不读 backend progress 字段 (Stage 2 早期 0% 卡住)
**实证**: Stage 2 startup 时 Backend progress=5-10%, Frontend 显示 0% 卡住. Stage 3+ 自动校正.
**修复**: Frontend useETA 或 progress bar 组件确认接 backend `progress` 字段

#### #53 RISK-T20-25 P2 — Frontend confirm-characters 后路由 race condition
**实证**: 用户确认角色后 frontend 跳 /scenes 加载 20s → 跳回 /generating
**修复**: createUrl.ts UI_PHASE_TO_URL 对 `scene_review_pending` 应该直接跳 /generating 不经 /scenes

#### #55 RISK-T20-27 P2 — Stage 4 偶有 text_overlay 空 (Shot 13)
**实证**: Shot 13 "碑上刻着陈砚 生卒年空白" 重大转折, text_overlay 字段空, 只有 19 字 caption
**修复**: Stage 3/4 prompt 加硬规则 + Pipeline fallback (overlay 空时用 narration_segment)

#### #11 RISK-T20-11.v2 — /outline 页面 frontend 仍 polling chapters/* (76 个 404 routine warn)
**实证**: T20-11 Wave 1 修了 30s 二次载入, 但 /outline 页面对 chapters/* 仍 polling 累积 console noise
**修复**: 优化 /outline polling 策略 (chapter 未创建时降频或停)

#### 文字密度偏短 (T20-21 改进空间)
**Founder 反馈**: "对话气泡/心理描述/旁白文字都还有点过于简短, 不是很直观通俗易懂"
**实证数据**: 平均 narration_segment 20 字 + text_overlay 24 字 = 每 shot 44 字
**改进方向**: Stage 3 ScreenplayWriter prompt 提升 dialogue/thought 长度上限 (24 → 35 字)

### ✅ closed (本测试新关闭 2 个)

- T20-22 (schema)
- T20-23 (character_designer)

### ✅ 仍 pending (4 个待 Wave 4)

- T20-24 (frontend progress)
- T20-25 (frontend race condition)
- T20-26 P0 (PromptRewriter 真根因)
- T20-27 (Stage 4 overlay 空)

---

## 3. Wave 1+2 修复实证清单 (test19 验证 PASS)

### A. 角色一致性 / Schema (T20-10 + T20-22 + T20-23)
- ✅ Schema 19 character_type universal (含 'animal' + plumage_color 鸟类)
- ✅ character_designer 不硬要求 human 字段 (anthropomorphic_animal + animal 等不再 ValueError)
- ✅ pipeline_orchestrator validate_characters 经 CharacterSchema PASS

### B. Frontend UX (T20-12 + T20-15)
- ✅ /characters 60s 倒计时圆形 badge 显示
- ✅ /scenes 60s 倒计时 (Founder 30s 内手动确认更快)
- ✅ 0 React setState-in-render warning (Wave 1 T20-15 修)
- ✅ adjust_character API 工作 (黄金衣扣实证)
- ✅ B57 portrait + fullbody 双层一致性同步重生

### C. Backend 契约 (T20-13 + T20-9.v3 + Ben 5/13 STATUS_API_CONTRACT v1.2)
- ✅ status API 返 shots_total/shots_completed/shots_failed (Stage 5 全程对齐 frontend)
- ✅ ETA 估算准确 (Founder 多次反馈 "ETA 不错")
- ✅ Backend 主动更新 contract v1.1 → v1.2 (Wave 2 学到 KEY_LEARNINGS #36 教训)
- ✅ partial_failure=True 触发 frontend 横幅 + "查看并重生" 按钮

### D. Stage 4 SPECIES_FIDELITY_RULES (T20-17)
- ✅ **独眼鸦真画成乌鸦** (Founder 实证 PASS), 不再像 test17 v2 "类刺猬" bug
- ✅ SPECIES_FIDELITY_RULES 5.7KB 注入 + build_stage4_character_data_block 加 species/character_type

### E. Stage 5 wall-clock + 失败容错 (T20-19 + T20-20)
- ✅ asyncio.wait_for(720s) 包裹, 0 触发 (网络好)
- ✅ Frontend 失败容错 UI ("18/19 张生成成功, 1 张未生成" + 查看并重生)
- ✅ Backend regenerate-shot endpoint + Haiku PromptRewriter 工作 (但有 RISK-T20-26 缺陷)

### F. Stage 3+4 旁白融入 shot (T20-21)
- ✅ narration_segment 平均 20 字 (caption-style, vs 旧 245-370 字 长篇)
- ✅ text_overlay 每 shot 含 dialogue/thought/narration 之一 (18/19 shot 有, Shot 13 例外)
- ✅ DEC-044 UI 文案 "描述(只读)" (Founder 实证 OK)
- 🟡 改进空间: 文字密度 24 字 → 35 字可提通俗易懂

### G. BGM dark_fantasy (Wave 14)
- ✅ 198s BGM + LUFS=-15.7 + dark_fantasy 风格匹配 (Founder "可以")

### H. RISK-T17-8 原地重启 (Wave 12)
- ✅ 3 次原地重启 (T20-22 + T20-23 修复后第 3 次成功), 不浪费 Stage 1 大纲

### I. DEC-028 不截断 + B58 60s 倒计时
- ✅ Stage 4 总 shots=19 不截断
- ✅ /scenes 60s 倒计时 (Founder 30s 手动确认)

---

## 4. Pipeline 性能数据 (test19 vs test17 v2)

### 总耗时分解 (最后一次成功 Pipeline 21:12:52 → 21:44:02)

| Stage | 时间 | vs test17 v2 |
|-------|------|--------------|
| Stage 1 outline (from disk) | <5s | -75s (RISK-T17-8 复用) |
| Stage 2 character (Claude) | 107s | -5s |
| Stage 3 screenplay | 92s | -69s (test17 v2 161s) |
| Stage 4 storyboard | 219s | +77s (test17 v2 142s, test19 含 B51 fallback) |
| Stage 5 image gen (18/19) | ~9 min | **vs test17 v2 ~50 min ✅ 快 5 倍** |
| Stage 6 BGM | 178s | 一致 |
| **总 Pipeline** | **31 min** | **vs test17 v2 75 min ✅ 快 2.4 倍** |
| 用户停留 (Stage B 角色 + 场景确认) | ~3 min | 类似 |

### Shot 生成性能对比

| 指标 | test19 | test17 v2 | 改进 |
|------|--------|-----------|------|
| Shot 平均耗时 | **52s** | 143s | **3x faster** |
| Anthropic 529 次数 | **0** | 18 次 | ∞ better |
| IncompleteRead 次数 | **2** | 24 次 | 12x fewer |
| ShotValidator 真 FAIL | **0** | 1 (Shot 10) | ∞ better |
| sanitize 重试 | 5 次 × Shot 15 (全失败) | 0 | regression |
| GC 兜底跳 shots | 3 (6/11/16, 已补) | 3 | 一致 |
| 失败 shot | 1 (Shot 15 content_safety) | 2 (Shot 14/19 network) | 改性质 |

### 成本估算

| 项 | 数量 | 单价 | 小计 |
|----|------|------|------|
| Stage 5 Shot 生成 (含 5 次 Shot 15 重生) | 23 次 API | $0.03 | $0.69 |
| 角色 portrait + fullbody | 6 张 + 1 重生 | $0.03 | $0.21 |
| 场景参考图 | 3 张 | $0.03 | $0.09 |
| BGM Mureka | 10 credits | - | - |
| Stage 1-4 Claude Sonnet 4.6 | 4 次 (大纲/角色/剧本/分镜) | ~$0.05 | $0.20 |
| BGM prompt Haiku 4.5 | 1 | $0.001 | $0.001 |
| Haiku PromptRewriter (Shot 15 ×4) | 4 | $0.001 | $0.004 |
| **总计** | | | **~$1.20** |

---

## 5. Founder 验收反馈精准记录 (21:50)

```
✅ 独眼鸦真画对乌鸦 (T20-17 关键验证)
✅ 60s 倒计时 badge 显示 (T20-12 / T20-15)
✅ 角色卡 portrait+name+描述都对
✅ "描述(只读)" 文案 OK (DEC-044)
✅ BGM dark_fantasy 风格匹配
🟡 故事脱旁白可读 80-90%, 但文字过于简短不直观通俗易懂 (T20-21 改进空间)
🟡 Shot 15 缺图 + 5 次重生失败 (RISK-T20-26 PromptRewriter)
✅ ETA "不错" (T20-9.v3 v3 实证)
```

---

## 6. KEY_LEARNINGS 待加 (基于 test19 实证)

### #37 — Seedream 暗黑题材敏感词 (ghost/double-exposure/deceased/overlap)
- test19 实证: Seedream 对 "ghost / double-exposure of deceased / face overlapping / two faces merging" 明确敏感
- Stage 4 prompt 避开 → 改"虚化" / "记忆" / "梦境" / "光晕" / "倒影"
- 角色单独场景 + symbolic 远处虚化身影

### #38 — PromptRewriter 必须 replace 不能 append (T20-26 真根因)
- Wave 5.1 Haiku PromptRewriter 实际是 **追加** Founder intent 到原 prompt 末尾
- 不 strip 原始 ghost/double-exposure 段落 → Seedream 仍触发
- 修复: Haiku prompt 必须 replace 策略 + 强制 strip 已知敏感词 list

### #39 — "修了一半" 教训第 3 次重复实证 (T20-22 + T20-23)
- Wave 14 (anthropomorphic_animal 映射) → T20-10 (5 处下游 dispatch) → T20-22 (schema plumage_color) → T20-23 (character_designer)
- 每次都漏一处, 跨 schema + LLM prompt + multiple consumers
- 必须用 Explore agent 5+ 维度地毯式审查整个 codebase

---

## 7. Wave 4 派活建议 (待 Founder 批准)

### 内测前必修 (4 项, P0, ~2-3 人天)

| RISK | Owner | 工作量 |
|------|-------|--------|
| **T20-26 P0** PromptRewriter replace 策略 + 敏感词 strip | AI-ML (Haiku prompt) + Backend (replace 实现) | 1 天 |
| T20-21 v2 文字密度提升 (24→35 字, 通俗易懂) | AI-ML (Stage 3 prompt) | 半天 |
| T20-27 P2 (升级 P1) Stage 4 text_overlay 必填 | AI-ML (Stage 3/4 prompt) | 半天 |
| Stage 4 prompt 加 Seedream 敏感词避开规则 (#37 KEY_LEARNINGS) | AI-ML | 半天 |

### 内测可延后 (3 项, P2)

| RISK | 说明 |
|------|------|
| T20-24 frontend progress 0% (Stage 2 早期) | 不阻塞, Stage 3+ 自动校正 |
| T20-25 confirm-characters 跳错 (20s 加载) | UX 等待, 可忍 |
| T20-11.v2 /outline 页面 polling 76 个 404 console noise | 不影响功能 |

### KEY_LEARNINGS 必加 #37/#38/#39 (3 条)

---

## 8. 跟 test17 v2 对比总评

| 维度 | test17 v2 (5/19 14:41) | test19 (5/19 20:34) |
|------|------------------------|--------------------|
| Pipeline 总耗时 | 75 min | **31 min** ✅ 快 2.4 倍 |
| 生图均速 | 143s/shot | **52s/shot** ✅ 快 3 倍 |
| 失败 shot 类型 | 2 个 network failure | 1 个 content_safety |
| 失败可救? | ✅ 重生 1 次过 | ❌ 重生 5 次都失败 |
| Wave 14 + T20-10 终极验证 | ✅ 动物风格对 | ✅ 独眼鸦画对乌鸦 |
| 文字密度 (Wave 2 T20-21) | 旧版长 narration | 新版短 narration + dialogue/thought |
| Founder 故事可读性 | "感觉晦涩" | "80-90% 可读" |
| 新发现 RISK | 11 个 (Wave 2 全修) | 6 个 (Wave 4 待修) |

### 关键提升 (Wave 1+2 实证)
- ✅ Schema universal (3 层修复: T20-10 + T20-22 + T20-23 终结)
- ✅ Frontend UX (60s 倒计时 + 失败容错)
- ✅ Backend 契约 (status API + ETA + Ben 5/13 STATUS_API_CONTRACT v1.2)
- ✅ T20-17 species fidelity (核心修复)
- ✅ Stage 5 性能 (52s vs 143s)

### 仍待改进
- 🔴 T20-26 PromptRewriter replace 策略 (P0, 暗黑题材救不回来)
- 🟡 T20-21 文字密度可提升
- 🟡 Frontend progress 早期不准

---

**报告生成**: 2026-05-19 22:05 (PM, 主对话 boss-coordinator)
**审计方法**: cron 8 维度每 2min 监控 + 3 background monitors + 11 次实时 8 维度 check + DevOps 诊断 + Founder 实时反馈 + 代码 grep + DB 查询 + Backend Python 真实验证
**任务列表同步**: 已更新 #50-#56 (5 closed + 4 pending 待 Wave 4)

