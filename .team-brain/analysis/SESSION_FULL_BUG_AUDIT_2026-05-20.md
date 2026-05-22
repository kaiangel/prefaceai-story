# 2026-05-20 完整 session Bug 全栈深度回溯

> **作者**: PM
> **生成时间**: 2026-05-20 19:15
> **范围**: 从 5/20 14:00 test19 重跑 + Wave 5 v3 实证 + test20 第一次 (daf30634) + test20 第二次 (c1b64961) **全部测试中暴露的 bug + 状态**
> **目的**: Founder 要求毫无遗漏全面具体清晰细致回溯

---

## 📋 总览 — 24 小时内发现 + 修复 + 待修的所有 bug

| # | RISK | 类型 | 真根因 | 状态 | 备注 |
|---|---|---|---|---|---|
| 1 | T20-43 supernatural schema | P0 | 镜中人 supernatural type 缺 being_type/base_form schema 严格 | ✅ Wave 1 hotfix | KEY_LEARNINGS #43 修了一半第 4 次 |
| 2 | T20-29 Schema extra='allow' | P0 | SceneSchema 丢 v3 字段 + validate 死代码 + cluster fallback 死 | ✅ Wave 5 + T20-29 完成 | 文档全栈更新 |
| 3 | T20-50 freshness check | P0 | `_portrait_fresh > _char_ts + 30` 把刚重生判陈旧 | ✅ Wave 1 完成 | KEY_LEARNINGS #45 修了一半第 5 次 |
| 4 | T20-50-fix-2 save_all_references | P0 (PM 误判) | size 差 ~500KB → 怀疑覆盖, 实际 PIL re-encode | 🟡 Round 3 多一层保护 | PM 误判, KEY_LEARNINGS #49 |
| 5 | T20-44 ETA 前后端联动 | P1 | Backend BGM 阶段重置 shots_completed + Frontend hardcoded "3 分钟" smoothing 4x 低估 | ✅ Wave 1 Backend + Wave 2 Frontend 全栈闭环 | STATUS_API_CONTRACT v1.2→v1.3 |
| 6 | T20-46 角色风格不一致 | P1 | CharacterDesigner LLM 描述具体性差异 → Seedream 自由发挥 | ✅ Wave 1 AI-ML STYLE_INFUSION + Wave 1 Backend wire | 47/47 + 11/11 PASS |
| 7 | T20-45 BGM 短曲 (36s) | P1 → P2 (PM 表象诊断错误) | PM 第一轮以为缺 duration 参数, 实际 Mureka API 无此参数, prompt 含"短促/收尾"词导致 | ✅ Wave 1 AI-ML BGM Haiku meta-prompt + Step 5a-2 linter | KEY_LEARNINGS #44 PM 表象诊断 |
| 8 | T20-47 Anthropic 529 fallback | P2 | Sonnet 全 529 → Haiku 降级 → 仍 fail → fail-open | ✅ Wave 2 完成 设计正确 | 但 T20-47-fix 真实 bug |
| 9 | **T20-47-fix SONNET_MODEL ID 写错** | **P0 (Wave 2 PM 漏抓)** | `"claude-sonnet-4-6-20251101"` 不存在 → Anthropic 404 → 100% fail-open | 🟡 **Wave 2 Round 3 修, 待 Backend 重启生效** | KEY_LEARNINGS #49 字符串存在 ≠ 语义正确 |
| 10 | T20-48 Shot anatomy hallucination | P2 | Shot 16 4 hands + Seedream 没硬约束 | ✅ Wave 2 AI-ML ANATOMY_FIDELITY_RULES + Backend retry + Round 2 wire | KEY_LEARNINGS #48 修了一半第 6 次 (round 1 漏 wire) |
| 11 | T20-50b adjust_character 审查 | P2 | 用户改 description 后 endpoint 是否真重生 portrait+fullbody | ✅ Wave 2 审查发现已正确实现 KEY_LEARNINGS #46 (16 单测) | 现有 endpoint 真完整, 无需改 |
| 12 | T20-49 outline validator 预防 | P3 | Stage 1 LLM 4 警告 (climax/beat tag/emotional_journey) | ✅ Wave 2 AI-ML OUTLINE_VALIDATION_RULES | 29/29 PASS |
| 13 | T20-51 BGM meta-prompt test_output 路径 | P3 | hardcoded `test_output/manualtest/...meta_mixed_v3_quote_picking.md` | ⏳ pending (不阻塞内测) | deployment 卫生 |
| 14 | T20-52 T20-47 测试 isolation | P3 | 综合 pytest 跑顺序污染 mock state, 单跑 19/19 PASS | ⏳ pending (不阻塞内测) | test infra 问题 |
| 15 | T20-53 SQLAlchemy + pymysql pool | P3 | "Packet sequence number wrong" 偶发 (全天 5 次) | ⏳ pending (不阻塞内测) | pool_pre_ping=True / aiomysql |

---

## 🎯 P0/P1 阻塞内测项 — 全部已修

```
✅ T20-43 supernatural schema      (Wave 1 hotfix)
✅ T20-50 freshness check          (Wave 1)
✅ T20-44 ETA (全栈)               (Wave 1 Backend + Wave 2 Frontend)
✅ T20-46 风格统一                  (Wave 1 AI-ML + Backend wire)
✅ T20-45 BGM 时长                  (Wave 1 AI-ML)
✅ T20-50-fix-2 多一层保护          (Wave 2 Round 3)
🟡 T20-47-fix SONNET_MODEL         (Wave 2 Round 3 修了, Backend 待重启)
```

---

## test20 e2e 实证 (新 project c1b64961, 5/20 18:37-19:07, ~30min)

### 4 大 e2e 真验证胜利

| 修复 | Founder 实测 |
|---|---|
| ✅ **T20-50 老刘绿色制服** | portrait 真信任不覆盖 |
| ✅ **T20-46 illustration 风格** | 3 角色统一 |
| ✅ **T20-48 ANATOMY** | 无 4 只手/6 根手指 |
| ✅ **3:4 画幅** | 20 shots 全 1664×2218 = 0.7502 (3:4) |

### 真完整时间轴

- 18:37 创建 project + 输入参数 (illustration, 3:4)
- 18:37:41 Stage 1 outline 启动
- 18:40:14 confirm-outline + start-generation
- 18:40:29 Stage 2 CharacterDesigner 启动 (style_preset=illustration 真传 T20-46 wire 验证)
- 18:42:00 Stage 2 完成 (Schema 通过, 镜中人 supernatural 真过 T20-43)
- 18:43-18:44 UX-1 3 角色 portrait 生成 (1664×2218 = 3:4 真生效)
- 18:46:21 AdjustCharacter "蓝→绿" (老刘)
- 18:47:13 portrait 重生 (R7-3 真接通)
- 18:47:17-18:48:16 B57 fullbody 同步重生
- 18:49:?? confirm-characters → Stage 3 启动
- 18:49:14 Stage 3 ScreenplayWriter 启动 (v3 prompt)
- 18:51:54 Stage 3 完成 (147.6s, 7 scenes, **全 C2 cluster + KPI 平均 0.923 ≥ 0.85**)
- 18:52:?? confirm-scenes → Stage 4 启动
- 18:55:24 Stage 4 完成 (20 shots)
- **18:55:30 Stage 5 image_preparation: "信任不重生" × 3 (T20-50 真生效)**
- 18:56:28 fullbody 重新生 (期望, in-memory 无 fullbody)
- 18:57:42-19:05:45 20 shots 生成 (1664×2218 = 3:4)
- 19:07:?? BGM 生成 (5 mood: creeping_dread → terror_escalating → ...)
- 19:07:?? Pipeline 100% completed

### Stage 5 实测的真 bug (Wave 2 PM 漏抓)

🚨 **T20-47-fix**: `SONNET_MODEL = "claude-sonnet-4-6-20251101"` Anthropic 404 NotFoundError → ShotValidator 100% fail-open (20 shots 都没经过 LLM 验证, 全靠 fail-open 放行)

---

## test20 第一次 (daf30634, 5/20 15:18-16:19) 全部 bug

1. ✅ T20-43 镜中人 supernatural schema fail → Wave 1 hotfix 修
2. ✅ T20-46 林深 anime/陈婶 realistic 风格不一 → Wave 1 AI-ML 修
3. ✅ T20-45 BGM 36s → Wave 1 AI-ML 修 (PM KEY_LEARNINGS #44 表象诊断)
4. ✅ T20-44 ETA 4x 低估 → Wave 1+2 全栈修
5. ✅ T20-48 Shot 16 4 只手 → Wave 2 AI-ML + Backend 修
6. ✅ T20-50 陈婶 portrait 被覆盖 → Wave 1 freshness check 删除
7. 🟡 T20-47 Anthropic 529 13/27 fail-open → Wave 2 Sonnet+Haiku fallback (实际 T20-47-fix model 错)

---

## Wave 1+2 PM 多次失误教训沉淀 (KEY_LEARNINGS #44-49)

- **#44** PM 第一轮 BGM 表象诊断错误 (Mureka 无 duration 参数, 必须查 API 文档)
- **#45** "修了一半"第 5 次 (B57 + freshness check 算法链路断)
- **#46** 用户操作 = 真相, Pipeline 不准二次裁判 (Founder T20-50 设计铁律)
- **#47** Agent 报告 "SKIP/PASS" 必须 PM 自跑 pytest 验证
- **#48** "修了一半"第 6 次 (Backend 双层防御只接兜底层)
- **#49** Wave 2 PM 审查两次漏抓 P0 (model name 字符串存在 ≠ API 接受 + save_all 防御一处 ≠ 全链路)

---

## 当前 Pipeline 服务态

```
Backend PID 79233 (5/20 18:42 重启, Wave 2 Round 3 修复代码还没生效, 等 Founder 决定重启)
Frontend PID 79256 (5/20 18:42 重启)
/health 200, Pipeline completed 100%
```

---

## 待 Founder 决策

### 立即做 (1 步)
- **重启 Backend** 让 T20-47-fix (SONNET_MODEL) + T20-50-fix-2 (save_all_references) Round 3 修复真生效

### 验证测试 (推荐)
1. 重启后跑 **test21 (scifi C6 AI 客服)** 跨题材验证: T20-47 SONNET_MODEL 真用 + ShotValidator 真验证 shot (不再 100% fail-open) + Wave 1+2 修复不退化
2. 跑 1 个 **fairytale (跨题材)** 验证 supernatural humanoid + 风格统一

### 内测就绪度

**核心 P0/P1 阻塞内测项全闭环 7 个** (T20-43/44/45/46/50/50-fix-2/47 wave 2 设计)。剩 1 个 **T20-47-fix 待重启**。剩 3 个 P3 不阻塞 (T20-51/52/53)。

**重启 + test21 验证通过后**: 可正式启动内测 ✅
