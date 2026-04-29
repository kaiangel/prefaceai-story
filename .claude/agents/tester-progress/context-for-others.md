# Tester Agent - 给其他Agent的上下文

> **最后更新**: 2026-04-29 [Tester]

---

## 当前状态

Wave 3.6 R7-3 独立复测完成 — PASS。R7-3 修复确认有效，可进入 Wave 4 DevOps 部署。

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

