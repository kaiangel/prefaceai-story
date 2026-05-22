# Wave 11 派活计划 + 内测后必修 RISK 清单

**最后更新**: 2026-05-14 21:05 PM (Wave 11.x + RISK-NEW-1/2 真彻底闭环后)
**Founder 决策 (5/14 16:30)**: Wave 11 P0 到 P2 都做，P3 内测后做但**不能遗漏**

---

## 🎉 Wave 11 + Pre-内测 audit + RISK-NEW-1/2 真彻底全闭环 (2026-05-14 23:30)

| Wave / 段 | RISK | 完成时刻 | 状态 |
|---|---|---|---|
| Wave 11.1 | T18-F + T17-9 + T18-H | 17:30 | ✅ |
| Wave 11.2 | T18-G + T18-E + StageC 配套 | 19:30 | ✅ |
| Wave 11.3 | T17-5 4 步 (job_manager + chapters 集成 + useETA + StageC 集成) | 20:30 | ✅ |
| Wave 11.4 | T18-A + T18-B + T18-D | 22:30 | ✅ (含 SeedreamMetrics 死代码补漏) |
| Wave 11.4 timeout | SEEDREAM_TIMEOUT_SEC 180→210 | 22:35 | ✅ |
| Pre-内测 audit | 找 3 新 RISK (PM 漏检) | 23:00 | ✅ |
| RISK-NEW-2 | IMAGE_GENERATION_TIMEOUT 配置统一 | 23:30 | ✅ |
| RISK-NEW-1 | actual_elapsed_sec 11 消费点 + sanity check | 23:30 | ✅ |

**12 RISK 内测前全闭环, 内测就绪度 A**, 等 Founder 明天 e2e 实证

---

---

## 🎯 Wave 11 (内测前必修, P0 + P1 + P2)

### Wave 11.1 — P0 角色一致性 + P1 ShotValidator ✅ **完成 (2026-05-14 17:30)**

| ID | 任务 | 文件 (实际) | 派给 | 状态 |
|---|---|---|---|---|
| #10 | 🔴 RISK-T18-F: regenerate_shot 传 portrait + fullbody | `app/api/chapters.py` L1878-1890 (实际不在 projects.py) | Backend #1 Sonnet 4.6 | ✅ |
| #3 | 🔴 RISK-T17-9: adjust_character R7-3 传 portrait_ref | `app/api/projects.py` L1288-1309 | Backend #1 (顺序) | ✅ |
| #12 | 🟡 RISK-T18-H: ShotValidator 5MB+ 图片直接跳过 | `app/services/shot_validator.py` L37-89/L304/L461-474 | Backend #2 Sonnet 4.6 xhigh (并行) | ✅ |

**验证**: 103+9 单测 + 82 regression PASS + 0 越权 + Backend 重启 PID 70144 含改动 + PM 5 维度审查通过

**验收**:
- ✅ 跑 `pytest tests/test_character_consistency_regression.py` 0 fail (CLAUDE.md 高风险铁律)
- ✅ 跑新增 ShotValidator 单测
- ✅ Backend 重启
- ✅ Founder 手动测 (shot 重生 + character adjust + 5MB+ shot 验证)

### Wave 11.2 — P1 数据契约 (估时 1.5h)

| ID | 任务 | 文件 | 派给 | 估时 |
|---|---|---|---|---|
| #11 | 🟡 RISK-T18-G: /chapters/{id}/story|storyboard 404 风暴 41 次 | `app/api/chapters.py` 加 endpoint or 改 by-design 404 → 200+empty | Backend Sonnet xhigh | 1h |
| #1 | 🟡 RISK-T18-E: /preview API 接口空数据 | `app/api/projects.py` 或 `chapters.py` | 同 Backend (等 Wave 11.1 projects.py 改完) | 0.5h |
| #11 配套 | Frontend StageC 调用 endpoint 修复 | `frontend/src/components/create/StageC.tsx` | Frontend Sonnet xhigh 并行 | 0.5h |

**验收**:
- ✅ backend log 0 个 [ClientLog].*HTTP_ERROR.*404 (story|storyboard)
- ✅ /api/projects/{id}/preview 返回完整数据 (project_id + bgm_url + chapters[] 完整)
- ✅ npm run build 0 errors

### Wave 11.3 — P1 ETA 全面深挖 (Founder 明确要求, 估时 2h)

| ID | 任务 | 文件 | 派给 | 估时 |
|---|---|---|---|---|
| #2 | 🟡 RISK-T17-5: ETA 算法 + status response 字段 | `app/services/job_manager.py` + `app/api/chapters.py` | Backend Sonnet xhigh | 1.5h |
| #2 配套 | Frontend ETA hook + stage 切换 reset | `frontend/src/.../useETA.ts` (假设) | Frontend Sonnet xhigh 并行 | 1h |

**验收**:
- ✅ Backend status response `eta_remaining_sec` 大部分时间返实际值 (非 None)
- ✅ Frontend ETA 显示稳定 (不再忽 8 min 忽 9 min 忽空)
- ✅ Stage 切换时 ETA 自动 reset
- ✅ pytest ETA 算法单测 PASS

### Wave 11.4 — P2 性能 + 监控 (估时 3-4h)

| ID | 任务 | 文件 | 派给 | 估时 |
|---|---|---|---|---|
| #4 | 🟢 RISK-T18-A: progress per-shot 增量 | `app/services/pipeline_orchestrator.py` image_generation 阶段 | Backend Sonnet xhigh | 1h |
| #5 | 🟢 RISK-T18-B: Seedream 长尾 150-180s 调研报告 | (调研为主) | Backend Sonnet xhigh | 1.5h |
| #6 | 🟢 RISK-T18-D: Seedream 失败率监控 + 4 次 retry 阈值评估 | (统计 + dashboard) | Backend Sonnet xhigh | 1h |

**验收**:
- ✅ progress 不再 75%→84%→88%→95% 跳变, 改成 75%→76%→77%→...→95% 平滑增量
- ✅ Seedream 长尾调研文档 `.team-brain/analysis/SEEDREAM_LONGTAIL_RESEARCH.md` 完成
- ✅ 失败率统计跨 test16/17/18 + 4 次 retry 阈值是否要调整结论

---

## 🔵 内测后必修 RISK 清单（不要遗漏！）

> ⚠️ **Founder 明确要求 (5/14 16:35)**: 内测后做的 RISK 必须明确记下，**不能任何遗漏**。
> 这些 RISK 不阻塞内测启动，但内测期间或内测后必须完成。

### POST-BETA-1 (P3): RISK-T17-7 后台按钮已存在 — 复盘 PENDING

**Task ID**: #7
**任务**: 从 PENDING.md 删除 RISK-T17-7 条目（前端早实现, PM 漏检）。
**派给**: PM 自做
**估时**: 5 min
**优先级**: P3 (清理类)
**触发**: 内测启动后任意时间, PM 安排
**验收**: PENDING.md 不再有 T17-7 条目 + 复盘类似漏检模式

### POST-BETA-2 (P3): RISK-T17-1 markdown JSON 解析全调用点排查

**Task ID**: #8
**任务**: Wave 10 已修 ConfirmScenes 接收 markdown fence (UX-2)，但 LLM 输出还有其他 endpoint 可能受影响 (R7-3 character adjust, ConfirmStoryboard 等)。
**派给**: Backend Sonnet xhigh
**文件**: 全项目 grep
**修复方向**:
1. grep `_strip_markdown_json_fence` 调用点
2. 找 LLM JSON 解析的所有路径
3. 确保统一处理
**估时**: 1h
**优先级**: P3 (预防性, 还没真发生 bug)
**触发**: 内测启动后或下个迭代
**验收**: 全调用点统一处理 + 加单测

### POST-BETA-3 (P3): RISK-T18-I Seedream IncompleteRead 24 次网络抖动监控

**Task ID**: #13
**数据**: test18 24 次 IncompleteRead, attempt 1-3 全部重试成功, 0 张 shot 因此失败
**任务**:
1. 监控 Seedream API 稳定性趋势 (建立 dashboard)
2. 评估 24 次告警阈值化 (如 >10 次/Pipeline 升级 P1)
3. 跨 test16/17/18 比较 IncompleteRead 频率, 找规律
4. 考虑联系 Doubao 官方了解服务稳定性 SLA
**派给**: Backend / DevOps
**估时**: 2-3h (监控 + 调研)
**优先级**: P3 (不影响成功率, 服务质量信号)
**触发**: 内测启动后, 服务稳定性需要建立基线
**验收**: dashboard 上线 + 历史数据可视化

### POST-BETA-4 (P3): RISK-T18-J Sync Anthropic 调用阻塞 event loop

**Task ID**: #14
**任务**: character_designer / screenplay_writer / storyboard_director 改用 AsyncAnthropic + await。
**派给**: Backend Opus xhigh (架构改造, 复杂)
**文件**:
- `app/services/character_designer.py`
- `app/services/screenplay_writer.py`
- `app/services/storyboard_director.py`
- 其他 Anthropic 调用点全 audit
**修复**:
1. 看是否用 anthropic.Anthropic() 而非 anthropic.AsyncAnthropic()
2. 改用 AsyncAnthropic + await
3. 单测 + 多用户压测
**影响**: 多用户并发支持
**估时**: 4-6h (架构改造 + 单测 + 压测)
**优先级**: P3 (内测 1-10 人不需要)
**触发**: 内测后扩大用户量前
**验收**:
- 多用户并发跑 Pipeline 不互相阻塞
- 跨多个 user 同时跑 Stage 4 不卡顿
- pytest async LLM 调用 PASS

---

## 📊 内测前 + 内测后总览

```
═══════════════════════════════════════════════════
内测前 (Wave 11, ~10h, 全 PM 跟进)
═══════════════════════════════════════════════════
Wave 11.1 (P0 + P1, 2h):  T18-F + T17-9 + T18-H
Wave 11.2 (P1, 1.5h):     T18-G + T18-E + StageC 配套
Wave 11.3 (P1, 2h):       T17-5 ETA Backend + Frontend
Wave 11.4 (P2, 3-4h):     T18-A + T18-B + T18-D
─────────────────────────────────────────────
内测前总耗时: ~10h, 修 8 RISK (修订后清单)

═══════════════════════════════════════════════════
内测后 (Wave 12, ~7-10h)
═══════════════════════════════════════════════════
POST-BETA-1 (P3): T17-7 PENDING 清理 (5 min)
POST-BETA-2 (P3): T17-1 markdown JSON 排查 (1h)
POST-BETA-3 (P3): T18-I IncompleteRead 监控 (2-3h)
POST-BETA-4 (P3): T18-J Sync LLM → Async (4-6h)
─────────────────────────────────────────────
内测后总耗时: ~7-10h, 修 4 RISK
```

---

## 🛡️ 防遗漏机制

为确保内测后 4 RISK 不遗漏:

1. **Task list 长期保留** (#7, #8, #13, #14 不删除直到内测后修完)
2. **本文档** `.team-brain/analysis/WAVE11_PLAN_AND_POST_BETA_RISKS.md` 永久保留
3. **PENDING.md** 加 "POST_BETA_RISKS" 段 (PM 内测启动前更新)
4. **TODAY_FOCUS.md** 内测启动当天提示 PM 排 Wave 12 计划
5. **每月复盘** 检查 task list 是否仍含 P3 RISK 待办

---

## 📚 关联文档

- 完整 audit 报告: `.team-brain/analysis/TEST16-18_DEEP_AUDIT_2026-05-14.md` (11 段)
- PM 当前: `.claude/agents/pm-progress/current.md`
- PM 上下文: `.claude/agents/pm-progress/context-for-others.md`
- 今日焦点: `.team-brain/status/TODAY_FOCUS.md`
- PENDING: `.team-brain/handoffs/PENDING.md`
- DECISIONS: `.team-brain/decisions/DECISIONS.md` (Wave 10.1 hotfix DEC-031 待加)
- KEY_LEARNINGS: `.team-brain/knowledge/KEY_LEARNINGS.md` (Wave 10/10.1 已记)
