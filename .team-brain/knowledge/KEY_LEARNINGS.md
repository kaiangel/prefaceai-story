# 关键经验与教训

> 从开发过程中积累的重要认知
> 避免重复踩坑

---

## 2026-05-15 test19 Wave 14 第 21-23 条新教训 (深度审查 + 多次修一半综合)

### 第 21 条: 单测 PASS + 代码改对 ≠ 真根因修对 (Wave 11.4 IMAGE_TOO_LARGE 错 target 实证)

**事件 (Wave 14 RISK-T19-7)**: Wave 11.4 改 _compress_for_claude target 5MB→4.5MB binary. 单测 9/9 PASS. PM 审查通过. test19 实测 Shot 21 5.7MB 还超! 真根因: Anthropic API 限制是 **base64 < 5MB** (不是 binary), base64 编码膨胀 ~33% → 4.5MB binary × 1.33 ≈ 6MB base64, 仍超! Wave 14 改 3.5MB binary (3.5 × 1.33 ≈ 4.65MB safe) 才真修.

**根因模式**:
- agent 单测覆盖了 "binary < 4.5MB" 但没考虑 base64 编码层膨胀
- PM 5 维度审查信单测 PASS, 没真追到 Anthropic API limit 实际是 binary 还是 base64
- API 文档不读, 凭印象设 target

**教训**:
- 涉及外部 API 限制 (5MB / token limit 等) 必须 RTFM (Read The Fucking Manual)
- 编码层膨胀 (base64 ~33%, JSON 字符串引号转义等) 必须计入 budget
- 单测覆盖应包括"模拟真实 API 限制"而非"代码内部边界"

### 第 22 条: B51 fallback 中文来源 6 处全找 (Wave 12+13 修 2/6 的彻底总结)

**事件**:
- Wave 12 修 atmosphere (1/6)
- Wave 13 修 scene_heading (2/6)
- test19 第三次跑 B51 fallback 仍触发 → Wave 14 Backend #1 深挖发现 LLM 主路径 6 中文来源:
  1. characters_json `name` (灰狐/米莉等中文)
  2. characters_json `clothing_summary` (中英双语)
  3. scene_heading
  4. atmosphere
  5. action_beats `action` (全中文, LLM 需理解)
  6. narration / dialogue_beats (全中文, TTS 用)

**根因模式**:
- 每次只修当时实证触发的字段
- 没系统性 grep LLM input 的全部字段
- Wave 12/13 PM 审查信 agent paste "已覆盖" 但实际只覆盖了 prompt 主路径不是 fallback

**教训**:
- 修 LLM 输入相关 bug 必须 grep LLM input 完整字段清单 + 标注每个字段语言/类型/防御策略
- 不能依赖"已 fallback 修复"的局部 paste, 必须 traverse 全调用链
- 类似 Wave 14 audit 时 Backend #2 发现 emotional_arc 同模式 — 主动 grep 同类风险扩散范围

### 第 23 条: 5 维度地毯式审查 + Explore agent very-thorough 双审 是发现真根因的金钥匙

**事件 (Wave 14 audit 5/15 17:30)**:
- Founder 反馈 "Shot 8 是女孩" → PM 初次诊断 "LLM image_prompt 写错了"
- PM 深挖发现 米莉 character_type=anthropomorphic_animal
- Explore agent very-thorough 进一步发现 **character_types.py 枚举不存在 ANTHROPOMORPHIC_ANIMAL** → CHARACTER_TYPE_DECLARATIONS 没映射 → CharacterPromptBuilder 不处理 → fallback 到 description 字符串 → LLM 自由解释

**根因模式**:
- 单次 PM 审查容易停在 "image_prompt 写错了" 表面
- Explore agent very-thorough 深挖代码可以追到 "字段不映射" 真根因
- 5 维度审查 (代码 + 调用链路 + 日志 + 单测 + 实际数据) 缺一不可

**教训**:
- 任何 Founder 反馈的产品级问题 (用户体验异常) 必须 PM + Explore agent 双审
- 不能停在第一层诊断, 真根因往往在 3-5 层下游
- 类似 Wave 14 多次实证 PM 单审会漏 (#24 #25 #26 都是 Explore agent 提示的真根因)
- 强烈建议: 内测前关键 RISK 必跑双审

---

## 2026-05-15 test19 Wave 12 + Wave 13 第 20 条新教训（修了一半教训）

### 第 20 条: agent paste "已覆盖路径" 必须 grep 完整代码验证, 不能只信 (RISK-T19-1 实证)

**事件 (test19 5/15 16:15)**: Wave 12 Backend #1 修 RISK-T19-1 atmosphere 中文化, agent paste 给 PM:
> "唯一直接拼接点是 L680-684 (fallback 路径)，已覆盖。"

PM 5 维度审查时验证了 atmosphere 部分, 单测 22/22 PASS, 标 task #18 completed. 

但 test19 第二次重启 Pipeline 又 failed at 同样 Schema 验证位置 (Shot 14 中文). PM 深度诊断: 真根因不只 atmosphere, **scene_heading 也是 image_prompt 中文来源**:
```python
fallback_image_prompt = (
    f"Establishing shot of {scene_heading}. "  ← scene_heading="EXT. 白桦树下" 含中文! Wave 12 漏修!
    f"{'Atmosphere: ' + atmosphere_str + '. ' if atmosphere_str else ''}"  ← Wave 12 修了 ✅
    ...
)
```

Wave 12 修了 1/2 中文来源, scene_heading 是另一条独立未修. 派 Wave 13 RISK-T19-4 补.

**根因模式**:
- agent paste "覆盖了 X 路径" 时 PM 直接信
- 但 fallback_image_prompt 拼装是**多个变量** (scene_heading + atmosphere_str), agent 只看了 atmosphere 没看 scene_heading
- PM 5 维度审查也只验证了 atmosphere 单测, 没 grep fallback_image_prompt 完整拼装代码

**教训**:
- agent paste "已覆盖 X" 必须 PM grep 完整代码验证
- fallback / 拼装类代码必须 Read 完整段, 看所有变量来源 (一行 f-string 可能含 5 个变量, 每个都要查)
- "单测 PASS" 只证明 agent 测的边界 PASS, 不代表所有拼装路径覆盖
- 类似教训: 第 14-19 条 (Schema 演化 / 死代码 / 死字段 / 配置统一 / 8 维度审查 / PM audit "已实现"判断 / agent paste "已覆盖") 都是同样模式 — **PM 不能信任 agent 的范围声明, 必须代码层验证完整链路**

**Wave 13 验证补救**:
- Backend agent 主动 paste: "B51 fallback_image_prompt 拼装来源全排查完毕：scene_heading（Wave 13 封） + atmosphere_str（Wave 12 封） + 固定英文字面量 + narration_segment（TTS 用，不进 image_prompt） + chars_in_scene（英文 ID）— B51 fallback 路径中文来源已全部封堵, 无遗漏" ← 这是正确的 paste 风格 (列出全变量来源)

**关联**: Wave 12 + Wave 13 PM audit + KEY_LEARNINGS 第 14-19 条 (相同模式)

---

## 2026-05-15 test19 第 19 条新教训（PM audit 误判修正）

### 第 19 条: PM audit "已实现" 判断必须实测验证, 不能基于历史快照推断 (RISK-T17-7 实证)

**事件 (test19 5/15 15:09)**: Founder e2e 测试在 `stage=storyboard` 阶段反馈 "仍然没看到'后台生成 去做别的'的前端UI"。PM grep frontend StageC.tsx L1087 注释明确 `"后台生成" button shown ONLY during shot-gen phase` (RISK-T15-1 fix 老限制), 跟 PM 5/14 audit 时判断 "PM 想象但前端早实现" **完全相反**。

**根因模式**:
- PM 5/14 16:00 audit 看 PENDING 列表, 看到 "RISK-T17-7 后台按钮"
- PM 想到 test18 时 Founder 看到过按钮 → 假设 "前端一直有这个按钮"
- PM 直接列入 POST_BETA "复盘删条目"
- **没追代码** 验证按钮 **何时显示 + 显示条件**
- → test19 实测发现 PM 误判 (按钮只在 image_generation 显示, 其他长 stage 都不显示)

**教训**:
- PM audit "已实现" 判断必须 **grep 代码 + 看条件分支**, 不能仅基于 "用户曾看到过" 推断
- "用户看到过" ≠ "所有 stage 都看到" — 条件渲染的 UI 元素必须验证显示条件
- 任何 PENDING 标 "复盘删" 的 RISK 都需要 **代码层证据** (grep 函数定义 + 调用点 + 显示条件)
- 类似教训: 第 14-18 条 (Schema 演化 / 死代码 / 死字段 / 配置统一 / 8 维度审查) 都是同样模式

**实证 + 修复**:
- task #7 升级 PM 5/14 P3 → P2 (内测前必修)
- 修复方案: Frontend StageC.tsx L1087 扩展按钮显示条件到 ['storyboard, image_preparation, image_generation, bgm'] 全部耗时 stage
- Wave 12 派给 Frontend Sonnet xhigh, 30 min

**关联**: PENDING.md "RISK-T17-7 升级 P2" 段 (5/15 15:10 PM 写)

---

## 2026-05-14 Wave 11.x 5 条新教训（Wave 11.1+11.2+11.3+11.4+RISK-NEW-1/2 修复后总结）

### 第 14 条: Schema 演化暴露下游隐藏 bug (Wave 10.1 + Wave 11.x 验证)

**事件 (Wave 10.1)**: Wave 10 T16-4 B58 merge 修复正确, 完美保留 atmosphere 字段 (从空 str 变成 dict). 但意外暴露 storyboard_director.py L635 假设 atmosphere 是 str 的隐藏 bug → test17 Stage 4 TypeError → Pipeline 失败。

**根因模式**:
- 上游修复"完美保留字段" + 下游"写死类型" = 暴露之前因为字段缺失被掩盖的 bug
- 这是 schema 演化 (字段从 missing/empty 变成 dict/对象) 的常见副作用

**教训**:
- Schema 修复 (e.g., merge 而非 replace, 完整保留字段) 后, **必须 grep 全项目下游消费点, 检查是否假设旧 schema (空 str / null) 类型**
- 防御式编程: helper 函数容错 dict / str / None / Any 4 种类型 (e.g., _atmosphere_to_str)
- LLM 输出字段类型不可假设, 永远 isinstance 检查

**实证**: Wave 10.1 hotfix _atmosphere_to_str() 救场, test18 Stage 4 0 TypeError

### 第 15 条: 死代码警钟 (Wave 1.1 教训重演 — Wave 11.4 SeedreamMetrics)

**事件 (Wave 11.4)**: Backend #6 完成 RISK-T18-D, 新建 seedream_metrics.py (200 行) + 30 单测 PASS + 完整 SeedreamMetrics class API. 但 grep 全项目: **0 个调用点** (除自己 tests/)。Backend agent paste "等 PM 决策集成" — PM 差点放过, 标 task completed。

**根因模式**:
- 单测 PASS ≠ 功能真接通
- 函数定义 ≠ 函数被使用
- agent 报告 "完成" 时可能只完成了"代码 + 单测", 没接到调用链路

**教训**:
- PM 5 维度审查必须 **grep 全项目调用点** (Wave 1.1 教训第二次重演)
- 任何 "新建 class / helper / monitoring 工具" 类任务, agent 必须告知 "调用点在哪", 没接通的话明确说"待集成"
- task list 标 completed 前必查: grep 调用点 >= 1 (除 tests/)

**实证**: PM Wave 11.4 23:00 audit 抓出 → reverse #6 → 派 mini agent 接通 6 调用点 → 真活字段

### 第 16 条: 死字段警钟 (Wave 11.3 actual_elapsed_sec)

**事件 (Wave 11.3 → Wave 11 收尾)**: Backend #2 ETA 算法完成后, paste 给 PM "actual_elapsed_sec snippet" 说"前端可用做 countdown 修正". PM 派 Backend #3 落实 chapters.py 加字段, 但 frontend useETA hook + StageC 没消费 → 死字段, 浪费一次往返。

**根因模式**:
- Backend 加字段时主动想"frontend 怎么用"
- Frontend 改 hook 时被动等待 backend 字段, 不主动检查 status response 全字段
- 跨 backend / frontend 字段消费需要 PM 主动验证

**教训**:
- 前后端契约改动 (backend 加字段 / frontend 加 hook) 必须 **paired** — backend agent paste 字段 + 同时派 frontend agent 消费
- PM 5 维度审查加 "**字段消费验证**": grep 字段名在 frontend 是否真消费
- 未消费的新字段 = 死字段, 等于没加 (浪费维护性 + 容易被误以为有用)

**实证**: PM Pre-内测 audit (23:00 Explore agent) 抓出 → 派 Frontend mini agent 11 消费点真接通 (sanity check >= 30 min "正在收尾, 请稍候...")

### 第 17 条: 配置统一管理 (Wave 11.4 + RISK-NEW-2 timeout)

**事件**: Wave 11.4 Backend #6 调研 Seedream 长尾后建议 SEEDREAM_TIMEOUT_SEC 180s → 210s. PM 派 Backend mini 改 seedream_generator.py L103 hardcode 210s. Pre-内测 audit 发现 config.py L33 还是 IMAGE_GENERATION_TIMEOUT=120 (旧 NB2 时代值), 两处不一致维护性隐患。

**根因模式**:
- Wave 11.4 timeout 改 hardcode 没用 settings — 临时方案 (1 行改快)
- config.py 旧值没清理 (旧 NB2 时代 120s)
- 多个 timeout 来源, 改一处漏一处

**教训**:
- **Magic number 应统一在 config.py / settings**, 各 service 从 settings 读
- 改 hardcode 是临时方案, 不是 long-term — PM 需追踪后续清理
- 历史值 (旧 NB2 时代 120s) 需主动清理, 别留维护性陷阱

**实证**: RISK-NEW-2 修复后 grep "IMAGE_GENERATION_TIMEOUT" 全项目 → 1 个定义点 (config.py L33) + seedream_generator.py 真从 settings 读

### 第 18 条: PM 地毯式审查必须做"调用链路 + 死代码 + 死字段"3 项 (Wave 11.x 综合)

**事件**: Wave 11.x 多 agent 工作中, PM 多次几乎放过隐藏问题:
1. Wave 11.4 SeedreamMetrics 死代码 (PM grep 后才抓出)
2. Wave 11.3 actual_elapsed_sec 死字段 (Pre-内测 audit Explore agent 抓出)
3. Wave 11.4 timeout 配置不一致 (Pre-内测 audit Explore agent 抓出)

**根因模式**:
- agent 完成 task 后报告 "完整修复 + 单测 PASS", PM 容易信
- PM 5 维度审查停在表面 (代码 Read + pytest), 没追"调用链路 + 死代码 + 死字段"

**教训**:
- PM 审查必查 8 维度 (代码改动 + **调用链路** + py_compile + pytest + 0 越权 + 服务重启 + progress 三件套 + **死代码 / 死字段检查**)
- 审查发现死代码 / 死字段 → 立即派补漏 agent, 不能等
- "工作量越大越要地毯式 — 越多越容易漏" (4/28 教训, Wave 11.x 再次验证)
- 内测启动前必做 Pre-内测 audit (PM + Explore agent very-thorough)

**实证**: PM Wave 11.4 + Pre-内测 audit 抓出 3 个隐藏问题 → 全部立即补漏 → 内测就绪度 A

---

## 2026-05-14 Wave 10 收尾 4 条新教训（Test16 暴露 + Ben 建议 Wave 10 实践）

### 10. 用户编辑 endpoint 必须用 merge 而非 replace（test16 RISK-T16-4 P0 CRITICAL）

**事件**: test16 Founder 在 /scenes 象征性点修改 → frontend POST modified_scenes (只 4 字段) → Backend B58 用 `json.dumps(payload.modified_scenes)` **完全替换** chapter.scenes_json → action_beats 全丢 → Stage 4 "无 shots" 失败 → Pipeline 全挂。

**Why**: backend 写 endpoint 时不能假设 frontend payload 是完整数据。frontend 可能基于简化 view 只传部分字段。replace 模式 = backend 信任 frontend 传全 = 任何 frontend 漏传都数据丢失。

**How to apply**:
1. **任何 "用户编辑数据" endpoint** 必须用 merge 模式: `existing = json.loads(db.field) → for k,v in payload.items(): existing[k] = v → db.field = json.dumps(existing)`
2. **schema 不强约束内部字段** (如 `modified_scenes: list[dict]` 不限 dict 内字段) — 透传任何 LLM 演化字段
3. **永远保留未传字段** — backend 是 data of record，frontend 只 view，view 漏字段不应改 record
4. 类似 PATCH 语义（partial update）vs PUT 语义（full replace）

### 11. CLAUDE.md 高风险文件改完必须跑 regression test（Wave 10 P2 backend agent 漏跑）

**事件**: Wave 10 Phase 2 Backend agent 改 `reference_image_manager.py` (CLAUDE.md 标 🔴 极高风险) 实现 T14-10 参考图并行化，但 agent 完成报告说"如存在跑"未真跑。PM 审查发现遗漏 → 立即跑 `tests/test_character_consistency_regression.py` 0 fail。

**Why**: CLAUDE.md 明确铁律"修改 storyboard_service.py 或 image_generator.py 时，必须先跑角色一致性回归测试"。reference_image_manager.py 同等高风险。

**How to apply**:
1. **PM spawn agent 修高风险文件时必须 prompt 强制要求跑 regression test** + 等 PASS 报告
2. **Agent 完成报告必须含 regression test 结果** — 不只是新单测
3. **PM 审查时不只看 agent 报告 — 必须自己 grep regression test 文件存在 + pytest 真跑过**

### 12. Test16 暴露的 frontend 容错设计缺陷（B58 merge / network retry / failed UI 三件套）

**事件**: test16 e2e 暴露 3 类 frontend 容错缺陷:
- T16-3: 网络断 → frontend 显示"生成遇到问题"假错误（实际 backend 健康）
- T16-7: Pipeline 失败 → frontend /preview 一片黑无错误提示
- T16-9: 文案诱导用户点修改 → 触发 T16-4 backend bug

**Why**: frontend 错误处理设计太"乐观"，假设网络永远好 + backend 永远成功 + 用户永远不出错。实际 e2e 这三种异常都常见。

**How to apply**:
1. **网络层**: status poller 必须 backoff retry + 监听 `window.online` 事件
2. **Pipeline 失败层**: 关键页面（/preview）必须有 failed state UI（错误信息 + 救济按钮）
3. **文案层**: 不诱导用户做可能触发 backend bug 的操作（test16 文案"可以修改氛围描述" → 用户点 → 触发 B58 bug）
4. 区分 NETWORK error vs Pipeline failed — frontend 不应混淆两者错误展示

### 13. Ben 建议 "纠验机制" 的 Wave 10 深化实践（DEC-030 续）

**事件**: Wave 10 Phase 1A Backend 改 projects.py + job_manager.py（契约文件）→ PM **同步 spawn** Phase 1B Frontend 修配套 (PreviewScene 透传 + StageD failed UI) → 双修同步 PR → 一次到位。这是 Ben 5/13 15:42 微信建议"后端改过功能告知前端"的代码层落地。

**Why**: Wave 9 Ben 方案 A (backend status authoritative + frontend 派生) 是"被动派生"模式 — 适合 status state。Wave 10 是"主动同步修复"模式 — 适合 endpoint behavior 改动（如 B58 merge 改了行为，frontend 需要扩展透传字段）。

**How to apply**:
1. **PM 派任务时**: backend 改契约文件 → 同步 spawn frontend 修配套（不等 backend 完成才 spawn frontend，避免顺序依赖卡死）
2. **Backend 改文件后**: 立即在 SendMessage 给 PM 时附"frontend impact 清单"（哪些 endpoint signature 变了 / 哪些字段加了）
3. **Pre-commit hook**: backend 改 projects.py / chapters.py / pipeline_orchestrator.py 等契约文件时 commit message 必须含 `[frontend-impact: yes/no]` label（Wave 9 已落地）
4. **未来 Wave**: 任何契约级改动 PM 默认假设是双修任务（backend + frontend 配套），PM 提前规划 spawn 时机

---

## 2026-05-13 Wave 9 收尾 3 条新教训（PM 深度审查 + 救场实证）

### 7. dev mode 跑期间不要 `npm run build` (Wave 9 P2 验证踩坑)

**事件**: PM 21:21 重启 frontend dev mode 后跑 `npm run build` 想 verify production build PASS。结果 build 把 `.next/` 改成 production artifacts，dev server (PID 52112) 还在跑但 vendor-chunks 不匹配 → `motion-utils.js / framer-motion.js / motion-dom.js` not found → GET /create 500（其他路由 200 因为不依赖这些 framer-motion chunks）。

**应用**:
- dev mode 跑期间**只跑** `npx tsc --noEmit` verify type errors，不跑 `npm run build`
- 如必须跑 production build verify，**先 kill dev server** + 跑 build + 检查结果 + 再 rm .next + 重启 dev
- 这是 Wave 9 P2 PM 第二次 frontend 救场触发的（第一次是 20:37 hot reload 累积）

### 8. Frontend 大改造后必须 PM 主动 clean rebuild

**应用**: 任何涉及 layout.tsx / createUrl.ts / StageC.tsx / CreateContent.tsx 多文件并行修改的大波次，agent 完成后**PM 必须立即** kill + rm .next + 重启，不要等 monitor 报 500。预防比修复成本低。

### 9. Ben 方案 A 架构改造完美落地，47% bug 根治验证

**事件**: DEC-030 Wave 9 落地 — Backend status authoritative + Frontend state 派生 + STATUS_API_CONTRACT + DevOps pre-commit hook 4 件全闭环。Test15 13 真 RISK 中 7 个前后端契约断裂类（占 47%）全部修复 + 永久治本。

**应用**:
- 跨团队架构建议（Ben 5/13 15:42 一句话）的杠杆效应巨大 — 重大问题主动找 Ben 讨论
- backend status response 作为 single source of truth + frontend state 派生 是企业级标准设计模式
- pre-commit hook 强制 `[frontend-impact: yes/no]` label 是 Ben 方案 B 配套，防止下次前后端契约脱节

---

## 2026-05-13 Test15 6 条核心经验（PM 深度审查产出）

### 1. 前后端契约必须从设计阶段对齐（Ben 5/13 15:42 建议 + test15 实证）

**教训**: test15 暴露 13 真 RISK 中 **7 个 (47%) 都是前后端契约断裂**。Wave 7 修了 T14-1~T14-13，但都没触及"backend Pipeline 设计意图 → frontend state machine"的对接断层。

**应用**:
- 任何新 backend stage / R4-X checkpoint / endpoint 设计时，必须**同步设计** frontend 对应的 hydrate 路径、URL state、subPhase 切换信号
- DEC-030 Wave 9 方案 A 落地: backend status authoritative + frontend state 派生 + STATUS_API_CONTRACT.md 文档 + pre-commit hook

### 2. PM unblock 操作绕过 frontend 揭示 frontend state 设计缺陷

**教训**: PM 5/13 19:33 直接 curl POST /confirm-scenes 解 R4-2（T15-3 临时 unblock），但 frontend generationSubPhase 没切 → 后台按钮不出现（T15-8）。这暴露 **frontend state 不是从 backend status 派生**（应是）。

**应用**: 任何 frontend state 字段，第一原则是"能否从 backend authoritative state 派生"。如果能，必须派生不缓存。Wave 9 方案 A 主修这点。

### 3. ETA monotonicity guard 不应阻止合法跳变（T15-7）

**教训**: UX-7 设计时假设 ETA 单调下降，没考虑 Pipeline 多阶段切换时 backend ETA 会按新 stage duration 上调。结果 frontend ETA 被压到 ≤0 不显示。

**应用**: UX 平滑性 guard 必须有"信号源切换"逃生口。监听 stage 字段变化时重置 ref。

### 4. shot regenerate 是事务，必须更新所有相关持久层（T15-12 + T15-13）

**教训**: regenerate 写了 disk shot_22.png 但漏了 3 处持久层:
- `chapter_generation_jobs.failed_shot_count` (frontend 显示用)
- `5_image_results.json` (frontend hydrate 用)
- `ApiCostLogger.project_id` (成本归属用)

**应用**: regenerate / adjust / 任何"修改既有数据"endpoint 必须列**完整持久层清单**: 哪些表/文件/日志会受影响。代码 review 强制检查清单。

### 5. T17 ShotValidator 重试不应静默使用最后结果（T15-10）

**教训**: Shot 21 T17 两次 retry 都失败（角色数量不匹配 — 预期 1 实际 3 → 4），但最终"使用当前结果"且**无任何用户可见警告**。

**应用**: T17 用尽 retry 后应:
- 在 5_image_results.json 标 `validation_failed=True`
- 在 status response 增加 `validation_warnings` 字段
- frontend /preview 显示 ⚠️ "Shot N 角色数量与预期不符，建议手动重生或编辑 prompt"

### 6. Ben 合伙人价值：跨团队架构建议的杠杆效应 ⭐⭐⭐⭐⭐

**教训**: Ben 5/13 15:37-15:42 微信聊天提的"前后端纠验机制" 不到 5 分钟对话，但**精准命中 47% test15 bug 的根因**。后端 + 数据库 + 架构 CTO 经验给出的"治根方案"远超 PM 单独审查能发现的。

**应用**:
- 重大架构问题主动找 Ben 讨论 (5 min 微信 >> 1h 单独琢磨)
- Ben 团队的"纠验机制" 思路 = 企业研发的"API 契约测试"或"Schema as Source of Truth"
- DEC-030 落地 Ben 方案 A，证明双团队联合决策的价值

---

## 图像生成经验

### 角色一致性的关键

```
成功公式 (2026-04-15 更新):
1. 参考图串行生成 (肖像 → 全身)
2. Shot 生成默认用 NB2 (gemini-3.1-flash-image-preview)，角色一致性 ~95%
3. 角色描述完整复制，不能简化
4. 参考图必须传递到每个 Shot
```

### Prompt 工程要点

```
DO:
✅ 全英文 Prompt（B' 压缩标签格式为默认）
✅ 风格描述放在开头
✅ 角色描述详细完整（identity_line 不动）
✅ 场景描述清晰

DON'T:
❌ 使用中文（会泄露到图像，中文检测阈值 5%）
❌ 简化角色描述
❌ 跳过参考图
```

### 模型选择策略 (2026-04-15 更新)

```
NB2 (gemini-3.1-flash-image-preview，主力，~95%一致性):
- 参考图生成（portrait + fullbody）
- 场景参考图生成
- Shot 图像生成（默认）

Claude Sonnet 4.6 (文本生成):
- Stage 1-4（大纲/角色/剧本/分镜）

Gemini 3.1 Flash Lite (轻量):
- 上传图片分析（风格/角色/场景）
- Prompt 翻译安全网

Gemini 3 Pro Image (贵，~98%一致性):
- 未来 Premium 用户储备，当前不启用
```

---

## 音频处理经验

### TTS 选型

```
火山引擎豆包:
- 中文效果好
- 8种音色
- 支持语速、音量、音调调整
- 成本合理
```

### 时间戳对齐

```
Whisper 返回:
- Word 级别时间戳
- 繁体中文 (需转换)

对齐策略:
1. 精确匹配 (完全相同)
2. 前缀匹配 (开头相同)
3. 子序列匹配 (包含关系)
4. 自动调整误差 ≤80ms
```

### 繁简转换

```
问题: Whisper 返回繁体，TTS 用简体
解决: 统一转换为简体后再匹配
教训: 这个坑花了很长时间才发现
```

---

## 架构设计经验

### 五阶段流程

```
Stage 1: 故事大纲 (Story Outline)
Stage 2: 角色设计 (Character Design)
Stage 3: 剧本编写 (Screenplay)
Stage 4: 分镜脚本 (Storyboard)
Stage 5: 图像生成 (Image Generation)

关键: 必须按顺序，不能跳过
原因: 每个阶段依赖前一阶段的输出
```

### 数据流设计

```
用户输入 (一句话)
    ↓
故事大纲 (JSON)
    ↓
角色设计 (详细描述)
    ↓
剧本 (场景+对话)
    ↓
分镜 (Shot 列表)
    ↓
参考图 (每角色)
    ↓
Shot 图像 (每场景)
    ↓
音频 (TTS)
    ↓
时间轴 (对齐)
    ↓
视频 (合成)
```

---

## 测试经验

### 回归测试重要性

```
每次修改 Prompt 或图像生成逻辑后:
1. 必须运行回归测试
2. 重点检查角色一致性
3. 抽检多种故事类型

教训: 曾经一个小改动导致一致性从100%降到60%
```

### 测试场景覆盖

```
已验证的场景:
✅ 都市情感
✅ 武侠古装
✅ 多人场景 (3人、6人)
✅ 动物角色
✅ 多种视觉风格
```

---

## 成本优化经验

### 当前成本结构 (2026-04-15 更新)

```
NB2 + B' 方案 (官方定价校准):
- 短篇 (3角色, 21shots): ~$3.40/故事
- 中长篇 (6角色, 45shots): ~$6.82/故事
- 费用大头: NB2 图像输出 $0.067/张 (占 70%+)
- 详见 docs/API_COST_CALCULATION.md
```

### 优化方向

```
1. 减少 Shot 数量 (合并相似场景)
2. 优化 Prompt 长度 (精简但保持关键信息)
3. 缓存和复用 (参考图缓存)
4. Flash 精化研究 (特定场景可能可用)
```

---

## 协作经验

### 文档的重要性

```
好的文档 = 减少沟通成本

关键文档:
- claude.md: 核心约束，必读
- ARCHITECTURE.md: 架构设计
- KNOWN_ISSUES.md: 已知问题
- 各 Phase 完成文档
```

### 决策记录的价值

```
记录决策的原因:
1. 避免重复讨论
2. 新人快速了解背景
3. 回顾时知道为什么这样做
```

---

## 产品经验

### 用户视角

```
用户不关心:
- 用了什么模型
- Prompt 怎么写
- 技术实现细节

用户关心:
- 生成的视频好不好看
- 角色一致不一致
- 要等多久
- 要花多少钱
```

### MVP 思维

```
先做核心功能:
1. 能生成故事 ✅
2. 能生成图像 ✅
3. 能生成音频 ✅
4. 能合成视频 (进行中)
5. 有界面使用 (待做)

再迭代优化:
- 更多风格
- 更低成本
- 更快速度
- 更好体验
```

---

## 多 Agent 协作经验

### 自定义 subagent_type 启用 + frontmatter 默认值（2026-04-28 学会）

**之前误判**（2026-04-25 → 2026-04-28 修正）：以为 PM 主对话只能用内置 subagent_type（general-purpose / Explore / Plan / 等），所有 spawn 都得在 prompt 里 paste 角色身份。

**真根因**：CC 扫描自定义 subagent_type 依赖 cwd 下 `.claude/agents/` 可见。本项目 cwd 经常在项目根 `/AIFun/xuhuastory/`，但 agents 真目录在 `xuhua_story/.claude/agents/`，差一层导致扫描为空 → spawn 报 not found。

**修复**：建 symlink `/AIFun/xuhuastory/.claude/agents → xuhua_story/.claude/agents`。验证：spawn `subagent_type: "backend"` 返回 UI 绿色高亮 + 0 tool_uses + 2.8s 完成 + 回复读到 frontmatter color。

**Frontmatter 完整 schema**（官方 https://code.claude.com/docs/en/sub-agents.md L234-256）：
- `name` / `description` / `tools` / `model` / `color` — 已知字段
- `effort` — **5 档**：low / medium / high / xhigh / max（depends on model）
- 其他：`disallowedTools` / `permissionMode` / `mcpServers` / `hooks` / `maxTurns` / `skills` / `initialPrompt` / `memory` / `background` / `isolation`

**项目当前 frontmatter 默认**（DEC-023，2026-04-28 设定）：
- 深度推理类（ai-ml / pm / coordinator）→ `model: opus, effort: xhigh`
- 执行类（backend / devops / frontend / tester / resonance）→ `model: sonnet, effort: xhigh`
- spawn 时显式传 model/effort 可覆盖默认

**教训**：
1. 碰到"X 不工作"先确认环境（cwd / 路径 / 权限），不要凭"工具不工作"下"工具有限制"结论
2. 框架字段是否支持，先查官方文档不要猜（PM 之前用三种可能性猜 effort，官方第一行就写了支持）
3. xhigh 可能是 Opus 4.7 专属（slash command 提示"(Opus 4.7 only)"），Sonnet 写 xhigh 实际可能跑 high — 监控验证

**关联文档**：
- `~/.claude/projects/.../memory/feedback_use_custom_subagent_type.md` — 真根因 + 修复方案 + 验证证据
- `~/.claude/projects/.../memory/reference_subagent_symlink.md` — symlink 路径 + 重建命令
- `.team-brain/decisions/DECISIONS.md` DEC-023 — 8 agent frontmatter 升级决策

---

## Bug 诊断与防御设计经验

### 数据契约错配比 prompt 写得差更隐蔽（2026-05-12 AI-ML 学到）

**情境**：写代码时常担心"prompt 写得不够好"或"模型能力不够"，但**真正的隐蔽 bug 是上下游对同一数据的"语义理解不一致"** —— 上游 LLM 把字段当 A 类型写，下游代码当 B 类型读。两端各自看都"对"，错配在中间。

**T17 案例（BUG-T13-T17-VALIDATOR-FALLBACK，DEC-025）**:
- 上游：Stage 4 LLM 把 `composition.foreground` 写成构图描述句（90-300 chars，"blurred edge of monitor in foreground casting cold glow"）— **正确，by-design**，帮 Seedream 生有纵深的画面
- 下游：pipeline_orchestrator.py 当离散道具名读（"is X visible?" 字面匹配）— **接口契约视角看也"合理"**，T28 的设计文档说要做"道具检测"
- 结果：18 shots 11% 误判率，但 prompt 没问题、模型能力没问题、阈值的"50%"看着也合理 — **问题在数据契约错配，不在任何单点**

**判断信号**（怀疑数据契约错配时）:
1. 改 prompt 没效果（修上游不解决）
2. 调阈值治标不治本（修下游也不解决）
3. 单元测试在 mock 数据下都过，但真实数据会 fail（mock 数据没复现错配）
4. 误判率不是 0% 也不是 100%（"5-15% 灰色地带"是契约错配典型）

**修复模式（4 选 1 决策铁律）**:
- ✅ **优先方案**：在中间层加适配（Adapter / Decorator）— 既不破坏上游产品质量，也不超下游权限边界
- ❌ 不要改两端 — 改上游会破坏产品逻辑（如本案缩短 Stage 4 描述会降低 Seedream 生图质量），改下游通常超权限或需重构调用方
- ⚠️ 中间适配要**多层防御**（净化 + 行为引导 + 阈值兜底 + 文档防御），任何单层失效另外三层兜底
- 📋 必须在文档/常量里**留指引**给未来 maintainer（避免下次有人不知道契约错配把适配层删了）

**对应铁律**:
- `feedback_trace_full_callstack_not_pattern.md` — 必须追完整调用栈，不能拿"看到的字符串"反推
- `feedback_diagnose_before_destructive.md` — 先诊断再修复，本案例如果直接调阈值（破坏性快修）就漏掉真因
- `feedback_carpet_review_deep_dive.md` — 地毯式审查必须深挖到调用链路，不能停在"grep 验证存在与否"

**修复 5 个高价值复盘点**（来自 T17 D3 修复经验）:
1. **5 层调用栈追踪比"看 reason 字符串猜根因"重要 100 倍** — 看 reason 能猜 5 个原因，追调用栈只有 1 个真根因
2. **agent 在职责范围内可以自创方案** — PM 给的 A/B/C 不一定最优，agent 应敢于"在权限边界内独立判断"，但要在 SendMessage 时**明确说明越权 + 给对比理由 + 测试证据**
3. **Mock 测试比真 LLM 测试快 100 倍** — 29 项断言 < 5 秒；真 LLM 验证需要重启 backend + 跑新故事 + 等 30 min Pipeline；先 mock 验证逻辑层，真 LLM 测端到端
4. **备份是免费的，不备份才贵** — `.bak-20260512-d3-pre` 让 rollback 1 秒；不备份要 git log + git diff + 手动还原可能 1 小时
5. **多层防御 > 单点解决** — 4 层中任何一层失效，另外三层兜底；单点修复（如只放阈值）失败时无 backup

**关联文档**:
- `.team-brain/decisions/DECISIONS.md` DEC-025 — 完整方案 D 决策记录 + 越权说明 + Founder 批准
- `.team-brain/analysis/T17_VALIDATOR_FIX_ANALYSIS.md` — 9 段深度分析（含 5 层根因 + 4 选 1 评分表 + 单元 29/29 详情）

---

### 项目命名约定必须 grep 全代码再改 env var（2026-05-12 PM 学到）

**事件**: TASK-T13-FRONTEND-A2-URL-FIX (Frontend Sonnet xhigh)，agent 改 `layout.tsx:26` 把 hardcoded `http://localhost:8000/api/_client_log` 改成 env var 驱动。agent 设 `.env.local` `NEXT_PUBLIC_API_URL=http://localhost:8000` + `.env.production` `=https://prefaceai.mov`（**不带 `/api` 后缀**），layout.tsx 自己拼 `${API_BASE}/api/_client_log`。npm build 0 errors，自我 verify 通过。

**真问题（PM 地毯审查发现）**: 项目所有现存代码约定 `NEXT_PUBLIC_API_URL` **必须含 `/api` 后缀**（4 处铁证 — `lib/api.ts:13` / `s/[token]/page.tsx:14` / `(marketing)/contact/ContactContent.tsx:38` 全 fallback `…/api`，`docker/Dockerfile.frontend:11` ENV `https://prefaceai.mov/api`）。Docker 生产 ENV 优先于 .env.production → 生产 ENDPOINT 实际会变成 `https://prefaceai.mov/api` + `/api/_client_log` = **双 /api 路径 404**。

**判断信号**（怀疑命名约定漂移时）:
1. 改 env var 命名/值时，**必须** `grep -rn "ENV_VAR_NAME"` 全代码看现存所有用法（不止 src/，还要 docker/, .env.example, k8s/, README/）
2. 现存 fallback 是写本（`process.env.X || "default_with_/api"`）— **fallback 值就是约定**
3. Dockerfile / docker-compose 的 `ENV` 设置是**硬约定**（运行时优先级最高）
4. agent 自我 verify "build 通过" 不等于"约定一致" — npm build 不会 catch 跨文件约定错配

**修复模式**:
- **Option A**（保持约定）: env var 仍含 `/api`，使用方拼接时**只加 `/_client_log`**（不要重复 `/api`）
- Option B（重命名）: 显式新 var 如 `NEXT_PUBLIC_API_BASE_URL` (无 /api) + `NEXT_PUBLIC_API_PREFIX=/api`，所有使用方一起改
- ❌ 不要单点改 .env 不动 fallback / Dockerfile（约定漂移 = 部分代码 OK 部分坏）

**PM 收尾代补**（5/12 17:00）: layout.tsx:31 改 `${API_BASE} + '/_client_log'` + .env.local `=http://localhost:8000/api` + .env.production `=https://prefaceai.mov/api`。dev build verify `var ENDPOINT = "http://localhost:8000/api" + '/_client_log';` ✅ 拼接正确。

**对应铁律**:
- `feedback_carpet_review_deep_dive.md` — 地毯式审查必须深挖到调用链路，不能停在"agent 自报通过"
- `feedback_code_review_runtime_deps.md` — Review 必须追踪运行时依赖（env var 加载方式 / 文件路径 / Docker ENV）

**关联文档**:
- `frontend/src/app/layout.tsx` — 修复后实现（含约定注释）
- `frontend/.env.{local,production}` — 命名约定文档化
- `docker/Dockerfile.frontend:11` — 生产 ENV 硬约束

---

### PM 5/13 test14 实战 7 个教训（一次 e2e 测试积累的复盘）

#### 1. Monitor task 不能光信"persistent" — 必须主动 verify 还活

**事件**: 5/12 17:58 PM 拉了 4 monitor（persistent + timeout_ms=3600000），告诉 Founder "monitor 自动跟你 e2e"。5/13 Founder 问"monitor 没看到 error 吗"，PM 才 TaskList → "No tasks found" 发现**4 monitor 早已 timeout 死了 22 小时**。

**判断信号**:
- Monitor `timeout_ms=3600000` = 1h cap，超时自动 kill
- Session 跨日期变化（5/12 → 5/13）可能让 session-bound task 失效
- Bash background process 可能存活但 task 元数据已失

**铁律**: 每次 cron 自检或 Founder 询问 monitor 状态时，必须 `TaskList` + `ps -ef | grep tail` 主动 verify。不能光说"4 monitor 自动跟"。

#### 2. GET vs POST endpoint 设计不对称是隐藏 bug

**事件**: test14 Stage 3 完成后 `GET /chapters/1/story` 持续 404，PM 误以为"scenes_json 没写入 DB"。实际 `POST /confirm-scenes` 返回 200 + 完整 7 场戏 → 证明 scenes_json **真在 DB**，是 GET endpoint 条件错（看 `full_script` 而非 `scenes_json`）。

**判断信号**:
- 同一资源 GET 和 POST 行为不一致 = 设计漏洞
- POST 写后 GET 不读到 = 99% endpoint 条件错，不是数据丢

**铁律**: 调试 endpoint 404 时**双向 verify** — curl 两个相关 endpoint 看实际数据。不要凭"应该写入了"假设。

#### 3. 不要凭"标准目录结构"猜测 bug

**事件**: BGM 生成完成后 PM 发现 `output/{uuid}/audio/` 目录不存在，**误判 BGM 文件没保存**。实际 BGM 真实路径是 `output/{uuid}/bgm_chapter0.mp3`（平级，不在 audio/ 子目录）。

**铁律**: 验证文件是否生成必须 `find` 不限定子目录 + curl 对应 endpoint 看 url 字段。不要凭"应该在 X 目录"主观判断。

#### 4. grep 模式必须考虑 CamelCase / snake_case 差异

**事件**: PM grep `adjust_character|regenerate` 在 backend log 找不到结果，**误以为前端点'重新生成'没真触发 API**。实际 backend log 用的是 `[AdjustCharacter]` CamelCase 标签，grep 模式没匹配。

**铁律**: grep 关键事件时用宽 case-insensitive `-i` 或同时 grep 多种命名风格（`adjust_character|AdjustCharacter`）。

#### 5. 客户端 log monitor 已就绪后，不要让 Founder 再手动开 DevTools

**事件**: PM 提"你打开 DevTools console 看是否有 setState warning"。Founder 反问"你不是在 monitor 里看到了 还要我看？" — PM 误让 Founder 重复劳动。

**真相**: B1 `layout.tsx` 注入 console proxy + client log monitor `bjzucqmcp` 实时 grep — 浏览器所有 console.error/warn/uncaught/promise-reject 都在 logs/client.log。**PM 自己看 monitor 即可**，不需要 Founder 手动开 DevTools。

**铁律**: 拉 monitor 的初心 = 不让 Founder 手动复检。如果让 Founder 看 DevTools = 违背 TASK-CLIENT-LOG-PIPE 初心。

#### 6. 误以为已记 PENDING ≠ 真的有独立 entry

**事件**: PM 多次自检报告说"RISK-T14-4 ETA 不准 ✅ 已记 PENDING"。Founder 要求 double-check 后 grep PENDING **没有 RISK-T14-4 独立 entry**，只在 RISK-T14-5-v2 "关联"字段提了一下。

**铁律**: 自检报告说"已记"必须 grep verify 真有独立 entry。不能凭"我应该记过了"假设。

#### 7. 产品设计层面问题不能只看代码层面 prompt

**事件**: PM 第一版 RISK-T14-11 BGM 古风问题诊断为"Haiku prompt 没注入古琴/笛/箫，加进去即可"。Founder 5/13 16:09 升级："要的是通用性 风格也是要传入的 比如情绪是悬疑但画面风格是中国古风水墨 综合 听感节奏韵律全维度"。

**真根因（PM 重读代码后才发现）**:
- `story_music_extractor.py` 15 字段**缺 style_preset / style_category** 维度
- `meta_mixed_v3_quote_picking.md` 47KB template 的 **6 桶 mood 映射只按 mood 走，不考虑 style** — Mysterious 桶"必备调性词"是 "minor key / dissonant cluster on strings / ambient drone" 不区分中国/西方
- 元原则 D"文化映射"是软提醒非硬约束

**铁律**: 看到 prompt 输出问题不要急于"补 keyword"。先深挖：(a) Input 维度全不全 (b) Template mapping 是否多维度综合 (c) 软规则 vs 硬约束。**产品设计层面**问题需要 style × mood 矩阵这类**框架性**修复，不是单点 prompt 补丁。

---

**关联**:
- 5/13 16:30 Wave 7 启动 — Backend + Frontend + AI-ML 三 agent 派工修 13 个 RISK-T14-*
- DEC-026/027/028/029 Founder 5/13 4 个决策已落 DECISIONS.md

---

### 软提醒 vs 硬约束的分水岭（AI-ML 2026-05-13 Wave 7 BGM 修复学到）

**症状**: Prompt 加了"中国故事承载中国声音记忆"软提醒，但 Haiku 仍按训练数据回归西式悬疑配乐。

**真根因**: LLM 训练数据中悬疑类范例最强烈的就是西式电影配乐。看到 mood=悬疑 → 立即回归。**软提醒（人类视角的"建议"）的权重远低于训练数据偏置**。

**修复模式**: 把软提醒升级为按显式参数（如 style_category）的硬约束 + 外部独立 linter 兜底验证 + 1 次 repair retry 闭环。

**判断信号**:
1. Prompt 内有"应该"/"建议"/"先考虑"等措辞 → 软提醒
2. 实测多次后行为不稳定 → 软提醒在不同 context 下被忽略
3. 加了软提醒但 fail rate 仍 > 30% → 必须升级为硬约束

**通用模式**:
```
软: "请考虑使用中国乐器"
硬: STYLE_REQUIRED_KEYWORDS[chinese_traditional] = ["guqin", "dizi", ...]
    + STYLE_FORBIDDEN_KEYWORDS[chinese_traditional] = ["cello as primary", "808", ...]
    + 下游 linter 验证 + 失败重试一次
```

**8 个常见软提醒陷阱**: "请保持..." / "建议使用..." / "先考虑..." / "尽量..." / "更好的做法是..." / "如果可能..." / "在合适的情况下..." / "通常..."

---

### 中文单字关键词在现代上下文中极易误匹配（AI-ML 2026-05-13）

**症状**: 写 setting_period detector，用朝代单字"明"/"清"/"宋"作 ancient_china 关键词。实测发现现代故事"明天再来"/"清晨煎饼"/"宋词朗诵"全部错误归到 ancient_china。

**真根因**: 中文单字承载语义密度高，朝代名跟日常词共享单字（明朝 vs 明天 / 清朝 vs 清晨 / 宋朝 vs 宋词），子串匹配无法区分。

**修复模式**: 全部用 2 字以上组合词（明朝/清朝/盛唐/古风/古代）+ 专属名词（凤冠/霞帔/驿站/镖局）+ 单元测试覆盖至少 6 个边界 case。

**通用规则**: 任何中文关键词列表设计，单字关键词必须严格审查上下文，优先用 2+ 字组合。

---

### PM Explore 误判要靠 PM 仲裁（PM 2026-05-13 Wave 7 学到）

**事件**: Explore 地毯审查 AI-ML 工作时，看到 5/13 16:30 之后修改的 8 个 .py 文件（chapters.py / projects.py / pipeline_orchestrator.py / job_manager.py / storyboard_director.py 等），**误判**"AI-ML 越权改 backend 文件"。

**真相**: 这些文件实际是 Backend R1+R2 改的（mtime 5/13 16:34-16:55 都在 Backend 工作窗口）。Explore 误把所有 5/13 16:30+ 改动归到最后完成的 agent（AI-ML 17:13 完成）。

**判断信号**:
- Wave 任务有多个 agent 并行 spawn 在同一时间窗口
- find -newermt 给出的文件 list 跨多个 agent 工作时段
- 单次 Explore 审查时间窗口（5/13 16:30+）覆盖多 agent

**铁律**: Explore 报告 "agent X 改了 Y 文件" 时 PM 必须**精确按 mtime 比对 agent spawn / completion 时间窗口**仲裁。不能完全信 Explore 的归属判断。**特别是 Wave 多 agent 并行场景**。

**修复模式**:
1. PM 自己 ls -la 4 个 agent 改的所有文件 mtime
2. 跟 4 个 agent spawn/completion 时间表对照
3. 真改的 agent = 在该 agent 工作窗口内 + 该 agent 自报清单包含

**对应铁律**: `feedback_carpet_review_deep_dive.md` 升级版 — 地毯式审查必须**追完整调用链 + 仲裁归属冲突**

---

### Integration 集成测试发现 P0 死代码（PM 2026-05-13 Wave 7 学到）

**事件**: AI-ML 完美完成 BGM 通用性框架（71/71 单测 + 5/5 Mureka 真测），signature 加 style_preset 参数。但 PM Integration Explore 审查发现 **3 处 generate_bgm_for_chapter 调用方没传 style_preset** → AI-ML 框架空跑 = P0 死代码！

**真根因**: AI-ML 自己改 service 层 OK，但**调用方在 backend 文件**（pipeline_orchestrator.py + chapters.py），AI-ML 权限边界外。AI-ML 自报"待 @backend 1 行 wiring"但 Backend R1+R2 没收到 PM 派活做这个（PM 派活时也没明确包含 wiring）。

**铁律**: 任何"signature 加参数 + 待调用方传新参数"的设计**必须分两步派活**:
1. service 层加参数 (本 agent 做)
2. **所有调用方传新参数** (派对应 agent 或 PM 自修，**必须包含在派活清单**)

否则会出现"服务层升级 + 调用方未升级 = 死代码"的整合断裂。

**修复模式**: PM 派活前 grep `function_name(` 看所有调用方，确保都在某个 agent 派活范围内。

**对应铁律**: 升级 `feedback_carpet_review_deep_dive.md` 的"signature 加 ≠ 参数被传值"经验，Wave 设计层面避免。

---

### 关联

- DEC-026 BGM 通用性框架
- analysis/BGM_UNIVERSAL_FRAMEWORK_2026-05-13.md
- PENDING.md Wave 7 13 RISK-T14-* 全闭环

---

## #24 [2026-05-18] Keyword fallback 永远修不完, 信任 LLM 决策最 universal (T20-3 实证)

**事件**: SceneRefManager._detect_signage_name keyword fallback (`_SIGNAGE_KEYWORDS_ZH = {'楼', '店', '铺'...}`) 把含"楼"字的"陈默租住楼的雨夜楼道口" 整段当招牌注入 prompt → 中文招牌污染所有 shot.

**真相**: Stage 1 outline LLM 已经做了正确决策 (signage_text 字段, 实证 4 location 中 3 个留空 + 1 个填"万象珠宝") — 是 fallback "不信" LLM 强行猜导致错误.

**教训**:
- Keyword 方案永远修不完, 任何故事类型 (办公楼/教学楼/出租屋/茶馆/书坊...) 都可能新 case 翻车
- 信任 LLM 决策 = 最 universal 解决方案
- 删 fallback 比加严 fallback 更稳

**修复**: 完全删除 keyword fallback (L746-757), 仅保留 `if signage_text: return signage_text`.

## #25 [2026-05-18] Fallback prompt 必须保留 screenplay 数据 (T20-7 实证)

**事件**: B51 fallback (LLM 3 次返空后兜底) 模板只用 scene_heading + atmosphere + "wide angle + No specific character interaction required" — 完全抛弃 Stage 3 screenplay 已生成的 action_beats + narration. Seedream 拿模糊 prompt 直接复制 scene_ref → 多 fallback shot 几乎一样 + 全部失去剧情.

**根本错误**: fallback 是"故障兜底"心态, 而非"降级保质"心态. "兜底"≠"放弃质量".

**修复架构 (v1 静态 + v2 LLM 治本)**:
- v1: 从 screenplay 提取 characters/emotional_note/english_action 已英文部分 (universal 但中文场景信息丢失)
- v2: 当 narration/action 是中文时, 调 LLM 翻译为英文 image_prompt 片段 (8 层兜底: Claude → Gemini → 静态)

**教训**: 不要让 fallback 抛弃上游已生成的数据. 即使 LLM 故障, 也应该从既有数据降级提取最大信息.

## #26 [2026-05-18] ShotValidator 必须 universal 判断 skip (T20-6 实证)

**事件**: ShotValidator 报 Shot 5/13 "角色数量不匹配预期2实际0" — 但 Shot 5/13 是 B51 fallback, prompt 明确"No character interaction required" → 故意不画人. Validator 检查时仍用原 scene 的 characters_in_scene 强检 → false positive.

**教训**:
- Validator 不能"一刀切"检查 — 必须知道哪些 shot 不该被检查
- universal 判断维度: _is_fallback / shot_type (wide/establishing) / prompt 含 "No characters" / prompt 含 "environmental composition"
- vision LLM 检测 (e.g. has_duplicate_bubbles) false positive 多 — 简单关闭比复杂改进更稳 (B36 本是 warning mode)

## #27 [2026-05-18] Ben 教训再实证: 函数定义 ≠ 函数被使用 (T20-6 wiring)

**事件**: AI-ML 在 shot_validator.py 加了 `validate_shot(..., shot: Optional[dict] = None)` + `should_skip_character_count_check(shot)` helper. 单测 30/30 PASS. 但 pipeline_orchestrator.py L1285 调用 validate_shot 时**没传 shot=shot** → universal skip 函数定义存在但 0 调用 → skip 完全没生效.

**Ben 教训 (再实证)**: grep "函数存在" 远远不够. 必须追完整调用链路 (函数定义 → 调用点 → 参数传递 → 数据流向 → 消费点).

**修复**: pipeline_orchestrator.py L1289 加 `shot=shot` 1 行, 服务重启, 5 维度链路验证全过.

**对所有 PM 审查的提醒**: 任何"新加函数 + 改函数签名"的工作, 必须验证调用方真的传了新参数, 不能仅看函数定义.

## #28 [2026-05-18] ETA UX 设计原则 — 平滑 + 不消失 + 真收尾 (T20-2 实证)

**事件**: Wave 11.3 useETA hook 3 bug 复合:
- Bug 1: STAGE_BUDGET_SECONDS 切换硬切 → ETA 一次性减 5 min 跳变
- Bug 2: Monotonicity guard 强制每 poll 减 1.5s → ETA 用尽到 0 → Math.ceil(0/60)=0 → null → 消失
- Bug 3: actualElapsedSec >= 30 min 触发"正在收尾" → Pipeline 全程长就误触

**教训 (UX 设计原则)**:
1. **平滑过渡**: stage 切换不要硬切 budget, 用 sliding window 渐变 (MAX_STEP_PER_POLL=3s/2s poll)
2. **不消失**: ETA=0 时显安心文案 ("即将完成"/"还需不到 1 分钟"), 不返 null
3. **真收尾**: "正在收尾" 文案触发条件用 Pipeline 真实状态 (stage=bgm OR (image_generation AND progress>=95%)), 而非 elapsed 时长阈值

**普适意义**: 任何 ETA/progress UI 都适用 — 用户的"信任感"来自一致性, 不是精度. 跳变/消失/误导比"晚 1 min"更伤信任.

## #29 [2026-05-18] PM audit 表象诊断 ≠ 代码层真根因, 必须地毯式 (T20-9 实证)

**事件**: PM TEST18_SECOND_RUN_AUDIT 诊断 T20-9 ETA 偏快根因 = "Frontend useETA hardcoded 1440". 但 Backend #1 agent 地毯式查代码后发现 backend `estimated_remaining_seconds` 字段早已存在, frontend useETA 也已 prefer backend value. 真根因是 chapters.py:344 fallback hardcoded `stage_progress=0.5` + per_shot_seconds=60s 过乐观.

**教训**:
- PM 看症状 (ETA 偏快 100%) 推测根因 ("frontend hardcoded") 可能漏掉真实代码层问题
- agent 地毯式 grep + 读代码上下文 + 算实际数学验证比表象诊断更精准
- 当 audit 和实际差距大 (修复后 42% → 6%) 应承认 agent 发现更深, 反过来纠正 audit

**实际操作**: agent 拿到 audit + 任务后, 应该:
1. 验证 audit 诊断 (grep 实际代码确认)
2. 如果发现真根因不同, SendMessage 告知 PM
3. 实施真正修复方案, 不照搬 audit 推荐方案

**普适意义**: 任何 PM audit 都可能有偏差, agent 不应盲从, 必须独立验证根因. Ben 教训"工作量越大越严"延伸: 不只是审查越严, 也是诊断越严.

## #30 [2026-05-19] Wave 14 "修了一半" 教训 — Schema 验证层 + 5+ 下游 consumers 都要改 (T20-10 实证)

**事件**: Wave 14 RISK-T19-6 修 anthropomorphic_animal LLM prompt 让动物角色用 species/fur_color (5 处映射), 但漏改:
1. CharacterSchema Pydantic 校验层 (仍强制 human-only fields required) → Stage 2 100% 崩
2. 5 处下游 consumers (storyboard_service 2 + storyboard_prompts 2 + pipeline_orchestrator 1) hardcoded human 字段 → 即使 schema 过, Stage 4 prompt 也是 "young Asian woman with fox tail" 荒谬输出

**Wave 14 之前隐藏**: 因为旧版 LLM 把所有非 human 误判 human, 写 hair_color 假数据, schema 才没暴露. Wave 14 修判断 → bug 浮出.

**教训**:
- "修了一半" 是结构性问题, 不是孤立 bug
- 任何"新 type/字段"修复必须 5 维度地毯式: schema + LLM prompt + 5+ 下游 consumers + tests + 未来扩展
- Wave 14 没用 Explore agent 地毯式查 → 漏 6 处, 用 Explore 后 5/19 一次全清
- 修复架构: 收敛重复实现 (5 处 hardcoded → 1 个 CharacterPromptBuilder dispatch), 类型语义清晰 + 未来加新类型成本极低

**普适意义**: 任何"修了一半"问题, 必须先 Explore agent 跨 backend + frontend + schema + tests + 下游 consumers 完整审查, 列全漏修点, 再统一 fix. PM 表象诊断不一定准.

## #31 [2026-05-19] 产品形态变了, Pipeline 必须同步重构 — 旁白时代结束 (T20-21 实证)

**事件**: 产品最终形态收敛到 "shots + BGM 无 TTS" (DEC-044), 但 ScreenplayWriter 还按"含 TTS 旁白朗读"时代写 narration_segment (全文旁白). 用户脱旁白故事晦涩.

**根因**: 产品决策和 Pipeline prompt 工程脱节. Stage 3 输出 30-40% 关键情节在 narration_segment, 但这些信息不再被用户看到.

**教训**:
- 产品形态决策必须同步审查 Pipeline 各 Stage 的 prompt 假设是否还成立
- "旁白只是辅助" → "用户必须脱旁白可读" 是大方向变化, 不是 UI 微调
- prompt 重构属于 AI-ML 主战场, 必须用 Opus 4.7 max thinking (复杂语义/叙事重组)

**普适意义**: 任何产品形态变化 (去 TTS / 去视频 / 改漫画), 必须问"原 prompt 的输出假设还成立吗?" 不只是 UI 改, 更是内容生成层重构.

## #32 [2026-05-19] 网络抖动期 vs 稳定期 — Shot 失败/成功的运气因素 (重生流程实证)

**事件**: test17 v2 Shot 14/19 在 15:34/15:35 网络抖动期 (24 IncompleteRead + 18 Anthropic 529 集中爆发) 走完 4 次 retry 失败. 16:03/16:05 Founder 手动重生, 网络已稳定 (0 IncompleteRead), 两次都 attempt 1 一次过.

**教训**:
- Pipeline 单 shot 成功率严重依赖外部网络/API 可用性
- 4 次 retry 是兜底不是保险 (Shot 7=11min, Shot 16=14min, Shot 14/19=失败)
- 重生流程 = 给用户"换个时间窗试一次", 比追求"一次性 100% 成功"更现实
- Frontend 失败容错 UI (顶部红色提醒 + "查看并重生" 按钮) 是关键产品能力

**普适意义**: 任何依赖外部 API 的生成式产品, 必须设计"重试 + 用户感知 + 手动重生" 三层兜底. 单纯优化"一次成功率"无法解决长尾.

## #33 [2026-05-19] 前后端状态字段断裂 → ETA 必然失真 (T20-13 实证)

**事件**: test17 v2 监控全程 Backend status API 返回 `shots_total=null, shots_completed=null`, 但 message 字段写 "已生成 X/20". Frontend 只能 regex parse message 字符串算 ETA, 加 message 字段更新延迟 → ETA 3 层失真.

**教训**:
- Backend 内存里有的状态字段必须 expose 到 API response, 否则前端只能"猜"
- 用 message 字符串传结构化数据是反模式 (string 解析 + 国际化失败 + 易出错)
- 前后端契约必须**字段级 explicit**, 不能依赖 message 文本
- Founder 原话: "前端在自说自话"

**普适意义**: 任何 status/progress API 必须返回**机器可读的结构化字段** (total/completed/failed). message 字段只用作 UI 显示文案, 不参与计算.

## #34 [2026-05-19] Anthropic 服务过载 → ShotValidator fail-open 形同虚设 (T20-14 实证)

**事件**: test17 v2 Stage 5 触发 18 次 Anthropic 调用, **全部 529 Overloaded**, skipped_count=9, 本轮 0 个 shot 被 ShotValidator 真验证过. B51 fallback (T20-1) 形同虚设.

**教训**:
- 依赖外部 LLM 做关键验证时, 必须设计**API 不可用时的退避重试**, 而不是直接 fail-open
- fail-open 是不得已的兜底, 不是默认策略
- 当外部 API 过载是周期性 (Anthropic 高峰), 退避重试 + 队列才能保证最终有验证

**普适意义**: 任何 LLM-based 验证/质控, 必须设计 429/529 退避重试 (指数 backoff + jitter), 至少保证关键路径真被验证. fail-open 只是最后兜底.

## #35 [2026-05-19] GC 兜底 = 延后机制 (不是丢图) — 初判 P0 实证降级 P2 (T20-16 实证)

**事件**: test17 v2 Pipeline 15:03:16 同一秒触发 Shot 6/11/16 "GC 兜底（shot_index=5/10/15）", PM 初判用户成片永久缺 3 张 P0. 后续 15:35-15:52 三张全部补跑成功. 是延后机制不是丢图.

**教训**:
- PM 看到"跳过"日志不能立即判 P0, 必须追踪日志看后续是否补救
- pipeline_orchestrator 的"GC 兜底"是 batch 调度策略 (每 5 shots 跳 1 个延后), 不是 bug
- 残留 UX 问题: progress UI 跳变 (1→2→3→4→5→7...→6 补跑), 用户感觉乱序 → P2

**普适意义**: 任何"跳过"/"延后"/"队列重排"机制, 都要追踪完整生命周期再判定是 bug 还是 feature. 早期日志可能误导.

## #36 [2026-05-19] Backend agent 漏改 STATUS_API_CONTRACT.md 违反 Ben 5/13 铁律 (T20-13 实证)

**事件**: Wave 1 Backend agent 完成 T20-13 (chapters.py 加 shots_total/completed/failed 3 字段), 但**完全没改 STATUS_API_CONTRACT.md** (Ben 5/13 规则 1: 加字段必须先 PR 改契约文档; 规则 2: 必须升级版本号 v1.0 → v1.1). PM 审查时发现, 立即补救升级 v1.1 + 加字段 §1.2 + 加 v1.1 历史条目.

**根因**: agent 任务描述里 PM 强调"加字段", 但没强调"必须改契约文档". agent 默认按代码完成度交付, 忘了文档同步.

**教训**:
- spawn agent 改 6 监控文件 (app/api/chapters.py / pipeline_orchestrator.py / job_manager.py / app/schemas/project.py / app/api/projects.py / app/models/project.py) 时, PM **必须在 spawn prompt 明确要求**: 改字段 → 先改 STATUS_API_CONTRACT.md (升版本号 + §1.2 + 历史条目 + commit message [frontend-impact: yes] label)
- PM 审查 Backend agent 改 6 监控文件之一时, **必须 check STATUS_API_CONTRACT.md mtime + 版本号 + 字段是否在 §1.2**
- 如 agent 漏改, PM 可直接补救 (PM 有 contracts 文档编辑权), 但 KEY_LEARNINGS 必须记录避免下次重犯

**实证**: PM 用 stat -f 看 STATUS_API_CONTRACT.md mtime 仍是 5/13 21:37 (Backend agent 完成 5/19 17:18 一分没动), 立即抓出漏改, 补 v1.1 总耗 3 min. 如果没抓出, Frontend Wave 2 agent 没契约可对照 → 字段命名漂移风险.

**普适意义**: 任何 contract-driven 开发, 文档同步必须像代码同步一样严格 — 一不可缺. spawn prompt 必须在 owner 任务里**显性写 contract 文档更新要求**, 不能假设 agent 会自动做.

## #37 [2026-05-19] Seedream 暗黑题材敏感词 (ghost/double-exposure/deceased/overlap) — test19 Shot 15 实证

**事件**: test19《独眼鸦的第二十七年》Shot 15 "祖孙叠影" 关键转折, Seedream 5 次拒绝 content_safety_failure. 即使 Founder 改 prompt intent 4 种不同方向都失败.

**根因 (5 维度排查)**:
Seedream 内容安全策略对以下词明确敏感:
- `"ghost of XXX"` / `"ghost of light"`
- `"double-exposure of deceased"`
- `"face overlapping"` / `"two faces merging"`
- `"younger face emerges"` (已故角色面孔浮现)
- `"identical jaw/scar"` (暗示已死自我重叠)

**普适意义**:
1. Stage 4 StoryboardDirector prompt **必须主动 strip 暗黑题材敏感词**, 改用安全替代:
   - "ghost" → "虚化" / "记忆" / "梦境" / "光晕" / "倒影"
   - "double-exposure of two faces" → 角色单独场景 + symbolic 远处虚化身影 (不重叠)
   - "deceased XXX emerges" → "in memory" / "lingering presence" / "warm light"
2. 任何"暗黑/恐怖/悬疑/灵异"类故事, image_prompt 不能含 "ghost / double-exposure / overlap / merging / deceased emerges" 字眼
3. PromptRewriter (Haiku) 改写时**必须强制 strip** 这些已知敏感词 list, 不能只追加用户 intent

**实证教训**: 5 次 Shot 15 重生失败导致 Founder 接受 18/19 缺图发布. 这是产品体验损失.

**修复落地**: Wave 4 派活 — AI-ML 改 Stage 4 prompt 加避开规则 + Haiku PromptRewriter 加强制 strip (T20-26).

## #38 [2026-05-19] PromptRewriter 必须 replace 不能 append (T20-26 真根因)

**事件**: test19 Shot 15 重生 5 次都失败, PM 深挖发现 Haiku PromptRewriter 是 **append-only 追加** 策略 — 把 Founder intent 追加到原 prompt 末尾, **不删** 原 prompt 中的 ghost/double-exposure/overlap 段落.

**实证数据**:
- 原 4_storyboard.json shot 15 image_prompt: **814 chars** (含 ghost/double-exposure/overlap/vision)
- Haiku 改写后发给 Seedream: **2203 chars** (原 814 + Founder intent ~1389 chars 追加)
- 即使 Founder intent 是 "陈砚跪在雪地, 不要叠影", Seedream 仍看到原 ghost 段落 → 拒绝

**根因架构**: Wave 5.1 PromptRewriter 设计错了 — 设计意图是"基于 intent 重写", 但实现是"追加 intent". Haiku prompt 没明确告诉它"必须 REPLACE 原 prompt 中含敏感词的句子".

**普适意义**:
1. 任何 "Rewriter" / "Editor" agent 必须明确 strategy: **replace** 还是 **append**
2. Haiku prompt 必须有 "DELETE these phrases" 强制规则, 不能依赖 LLM 自己理解 "改写"
3. 重生流程必须**真正基于 scene 元数据重新生成 image_prompt**, 不是 patch 原 prompt
4. Test 用例必须验证: 输入含敏感词的原 prompt + 干净 intent → 输出不应含原敏感词

**修复落地**: Wave 4 T20-26 P0 派活 — AI-ML 改 Haiku PromptRewriter prompt 为 replace 策略 + Backend 配合实现真 replace 流程.

## #39 [2026-05-19] "修了一半" 教训第 3 次重复实证 (T20-22 + T20-23 = Wave 14 → T20-10 → T20-22 → T20-23 漏点链)

**事件**: test19 Stage 2 连续失败 2 次, 每次都是新的 character_type='animal' 相关 schema/validation 漏改:
- 第 1 次 (T20-22): `_TYPE_REQUIRED_GROUPS['animal']` 只接受 fur_color/feather_color/scale_color, 缺 plumage_color (鸟类专用)
- 第 2 次 (T20-23): `character_designer.py:_validate_characters()` else 分支硬要求 4 个 human 字段, T20-10 Wave 1 漏改这一处

**追溯历史**:
1. Wave 14 (5/15): RISK-T19-6 修 anthropomorphic_animal LLM prompt 5 处映射
2. T20-10 (5/19 上午): 修 Schema + 5 处下游 dispatch (storyboard_service 2 + storyboard_prompts 2 + pipeline_orchestrator 1)
3. T20-22 (5/19 20:43): test19 暴露 schema 没 cover 鸟类 plumage_color, AI-ML 补
4. T20-23 (5/19 20:59): test19 暴露 character_designer 还有第 6 处漏改, Backend 补

**普适教训**:
- 任何"新 type / 新字段"修复必须**首先用 Explore agent 5+ 维度地毯式查全 codebase**, 列出所有相关下游 consumers + tests + validation 函数 (函数级粒度, 不只是文件级)
- "修了一半" 是结构性问题, 不是孤立 bug. 每次发现新漏点都暴露上次 audit 不够细
- spawn agent 修复前必须给清单: "这些是 KEY_LEARNINGS 记录的可能漏点, 请优先 grep + 测"
- pytest 不退化 ≠ 修复完整 — 必须真实数据端到端 (test17 真实 anthropomorphic_animal / test19 真实 animal 物种验证 schema + validation 全链路)

**修复落地**: Wave 4 不再有第 4 处漏点 (PM 已 audit 全 codebase grep 无其他 hardcoded human 字段检查). 但 KEY_LEARNINGS 永久警示, 防未来类似 bug.

## #40 [2026-05-20] 文字密度 ≠ 故事可读性, 风格/视角/留白才是核心 (T20-28 Founder 真根因)

**事件**: test19 T20-21 v1 (25 字) + v2 (35 字) Founder 仍反馈 "对话气泡/心理描述/旁白说明都还有点过于简短, 不直观通俗易懂". PM 5/19 23:15 读 storyrefs/story1 (12 张参考漫画) 后真根因排查:

**误区**: Wave 2 + Wave 4 修 T20-21 时只关注**字数** (旧 245-370 字 → v1 25 字 → v2 35 字), 但 Founder 真痛点不是字数, 是**风格 + 视角 + 留白哲学**.

**真正影响"故事可读性"的 15 维度** (从参考漫画 + 跨题材抽象):

**核心 6 原则** (所有故事类型通用):
1. 视角灵活 (LLM 由 style 选: 第一人称代入 vs 第三人称客观)
2. 语言风格匹配题材 (日常口语 vs 文言书面 vs 拟声词)
3. 情感强调机制 (红字 + !!! 突出, emphasis_words 结构化)
4. 留白哲学 = 节奏 (高潮多, 转场少, 不强求每 shot 都满)
5. 画面 ↔ 文字互补 (文字补心理动机, 画面表情绪动作)
6. 极简对话原则 (允许 1-3 字 dialogue 表态度)

**补充 9 原则** (跨题材必考虑):
7. 角色锚定 (重复 name 防混淆)
8. 角色关系上下文 (跳跃看时让用户记住关系)
9. 时间线跳转标记 ("三年后/深夜/回到那天")
10. 叙事结构 (起承转合 / 三幕剧 / kishōtenketsu)
11. 观众预期管理 (揭示/误导/反转)
12. 多角色对话区分 (speaker_position 锚定)
13. 副线/支线处理 (A 线/B 线明确)
14. 隐喻/象征运用 (银扣/乌鸦/风雪)
15. 文化/时代背景 (中国节气 / 西方圣诞 / 童话开头)

**按故事类型聚类** (8 cluster, 每类 TOP 5 关键原则):
- Cluster 1 强情感代入类 (恋爱/家庭/治愈) → 视角 1 + 风格 2 + 极简 6 + 强调 3 + 象征 14
- Cluster 2 悬念反转类 (悬疑/恐怖/惊悚) → 视角 1 + 留白 4 + 预期 11 + 节奏 10 + 跳转 9
- Cluster 3 奇幻冒险类 (西/东方魔幻) → 角色锚定 7 + 关系 8 + 多线 13 + 世界观 (15) + 节奏 10
- Cluster 4 童话绘本类 → 视角第三人称叙述 1 + 拟声 2 + 留白 4 + 极简 6 + 文化"很久以前" 15
- Cluster 5 古风历史类 → 语言适度文言 2 + 关系 8 + 世界观术语 15 + 跳转 9 + 象征 14
- Cluster 6 科幻类 → 视角第三 1 + 简洁理性 2 + 世界观概念 15 + 节奏 10 + 反转 11
- Cluster 7 喜剧吐槽类 → 全知视角 1 + 反差感 2 + setup/punchline 节奏 10 + 强调 3 + 极简 6
- Cluster 8 现实题材类 → 视角灵活 1 + 行业术语 + 通俗解释 2 + 关系 8 + 多线 13 + 真实留白 4

**普适意义**:
- 任何"文字密度"类 prompt 优化必须**首先看产品形态参考样本**, 不能凭空设字数上限
- 字数是表象, 风格/视角/留白/视觉互补才是用户感受核心
- "通俗易懂"反馈不要立即归到字数, 必须看实际样本对照学习
- 通用工具 (任意故事类型) 必须支持多种叙事风格, **按故事类型聚类应用关键原则**, 不一刀切
- KPI 量化: 让 Founder 真人测验证, 整个故事 ≥ 85% 可懂 (留 15% 给想象/思考)

**实证教训**: T20-21 v2 加 hard cap 35 字是治标; v3 必须重写整套**叙事原则 + cluster 映射**.

## #41 [2026-05-20] Prompt 工程要分操作层 vs 思维层 (T20-28 v3 实证, AI-ML 提议)

**事件**: T20-21 v1 (25 字 hard cap) + v2 (35 字 hard cap) 都是"加操作层规则", Founder 反复反馈"不够". v3 升到思维层 (8 cluster dispatch + LLM 自选 TOP 5 原则 + 85% KPI 自评) 才真根本解决.

**操作层 vs 思维层定义**:
- **操作层**: 字数限制 / 禁用词清单 / 强制字段 / 模板填空
  - 治表面 bug, 快但脆
  - 例: "narration ≤ 35 字" / "image_prompt 必须含 species"
- **思维层**: 分类决策 / 自选策略 / 自评校验 / 抽象框架
  - 治根本, 慢但稳
  - 例: "按 cluster 选 TOP 5 关键原则" / "LLM 自评 85% KPI 调整"

**普适规律**: 当反复"加字段加限制还是不达标"时, 应该**升一层抽象**, 让 LLM 自选策略而非死规则.

**应用建议**:
- 简单 bug (schema 缺字段, 内容安全过敏) → 操作层 (T20-22 plumage_color / T20-26 strip 敏感词)
- 复杂叙事/审美问题 (通俗易懂, 可读性, 情感张力) → 思维层 (T20-28 v3 cluster + 自评)
- 任何 prompt 改 2 轮还不达标 → 必须升思维层

**实证教训**: v1+v2 浪费 2 轮在字数, v3 用 4 倍代码量 (829→1981 行) + 8 cluster + 自评机制才根本解决.

---

## #42 [2026-05-20] Prompt/规则审查必须覆盖 LLM 输出端 (T20-29 PM 自查实证)

**事件**: Wave 5 v3 派 Backend wire 完成后, PM 第一轮 grep 验证: import ✅ + 函数定义 ✅ + f-string 注入 prompt ✅. Founder 提醒"地毯式深度审查铁律", PM 再深查发现 3 处真断裂:

1. **Schema 丢字段**: SceneSchema / ScreenplaySchema 无 `extra='allow'` → LLM 输出 `narrative_cluster` + `scene_self_evaluation` 被 Pydantic 静默丢弃, 后续验证拿不到字段
2. **验证死代码**: `validate_scene_self_evaluation()` 函数定义存在但 0 处调用 → 85% KPI 完全没生效
3. **fallback 死代码**: `detect_narrative_cluster()` 函数定义存在但 0 处调用 → LLM 漏输出 cluster 时无兜底

**真根因**: PM 只查"prompt 注入端" (规则进 LLM 了吗?), 没查"LLM 输出端" (LLM 写的字段被消费了吗?). prompt 工程是双向闭环 — 输入侧 (规则注入) + 输出侧 (字段消费 + KPI 验证).

**为什么这个最隐蔽**: 比 KEY_LEARNINGS #29 (函数定义 ≠ 函数被调) 更深一层 — 即使函数被调, 如果 schema 把字段丢了, 调用 == 拿到 None == 软警告永远不触发 == 等价死代码.

**审查清单升级 (PM 必查 5 项, T20-29 后)**:
1. 规则注入 prompt 文本 (老的) ✅
2. **Schema 接受 LLM 新字段** (extra='allow' 或显式 Optional 字段) 🆕
3. **验证/分类/fallback 函数真被调** (grep 调用点 ≥ 1) 🆕
4. **被调函数返回值真被消费** (后续逻辑用了 result 字段, 不是丢弃) 🆕
5. **真实数据测试** (mock 完整字段名调函数, 看返回结构 — 不是只 grep 存在) 🆕

**实证教训**: T20-29 mini wire 第 2 派加 2 行 schema config + 4 行真调用就修复了, 但 PM 第一轮没发现 == 等于 Wave 5 v3 浪费. 工作量越大越要双向审查 (输入侧 + 输出侧).

---

## #43 [2026-05-20] "修了一半" 第 4 次重演 — supernatural 人形外貌兜底 (test20 镜中人实证)

**事件**: Founder 跑 test20 (horror 电梯镜中人, gothic), Stage 2 CharacterDesigner 挂在 char_002 镜中人:

```
Value error, character_type=supernatural physical 字段缺少最小集:
需要至少满足 [being_type OR base_form]，
实际 physical keys=['hair_color', 'skin_tone', 'face_shape', ...]
```

LLM 把镜中人识别为 supernatural（合理 — 镜中人本质是超自然实体），但给的是人类外貌字段（也合理 — 镜中人看起来像人）。schema 设计错误地要求 supernatural 必须有 being_type/base_form。

**真根因**: 4 种"可能呈人形"的 character_type（supernatural / undead / mythological / fantasy_creature）在恐怖/奇幻/古风题材里是常见配置（鬼 / 魂 / 山神 / 仙人 / 妖 / 镜中人 / 影子人 / 死灵），但 `_TYPE_REQUIRED_GROUPS` 这 4 个 type 只接受种族字段（being_type/undead_type/creature_type 等），没把"人类外貌字段"作为合法兜底。

**"修了一半"链条 (第 4 次)**:
- T20-10 修 19 种 character_type 总框架
- T20-22 修 'animal' 加 plumage_color / skin_color / chitin_color
- T20-23 修 character_designer.py 按 type 分类验证
- **T20-43 (本次)** 修 supernatural / undead / mythological / fantasy_creature 加人类外貌字段 fallback

**修复 (5 行 + 1 条注释)**: `pipeline_schemas.py:L213-245` 4 个 type 每个 group 内加 `hair_color, skin_tone, face_shape`：
```python
'supernatural':     [('being_type', 'base_form', 'hair_color', 'skin_tone', 'face_shape')],
'undead':           [('undead_type', 'original_form', 'hair_color', 'skin_tone', 'face_shape')],
'mythological':     [('creature_type', 'origin_culture', 'hair_color', 'skin_tone', 'face_shape')],
'fantasy_creature': [('creature_type', 'base_form', 'hair_color', 'skin_tone', 'face_shape')],
```

**审查 5 维度通用规律 (第 4 次重演后必查)**:
1. 任何 character_type 最小集 schema 改动 → 必须**同时**审查 19 种 type 是否都有"题材常见配置" fallback
2. 重点审查"可能呈人形"的 type (rule of thumb): supernatural / undead / mythological / fantasy_creature / hybrid / digital_virtual
3. 重点审查"可能呈动物形"的 type: anthropomorphic_animal (✅ T20-22 已修) / mythological (人形/兽形都可) / fantasy_creature
4. 重点审查"可能呈物形"的 type: object / vehicle_character / concept_personified
5. 每次修一个 type 必须同时跑覆盖性回归测试 (19 种 type × 3-5 个题材组合 = 57-95 case)

**长期修**: AI-ML 在 CharacterDesigner prompt 里告诉 LLM 选 supernatural/undead/mythological/fantasy_creature 时**优先**填 being_type/undead_type/creature_type，否则填完整人类外貌字段. (schema 端已兜底, prompt 端补强)

**Founder 提醒**: 这是第 4 次"修了一半"重演 (#30 + #39 + 本次), PM 派活时**必须先列完整 type 清单**让 Backend 一次性扫完, 不能"修哪个 type 就只修哪个".

---

## #44 [2026-05-20] PM 第一轮 BGM 表象诊断错误 — 必须先查 API 文档 + 历史数据

**事件**: Founder 发现 test20 BGM 仅 36s (故事 3min), PM 第一轮诊断 = "Mureka payload 缺 duration 字段"。Founder 反驳"之前 BGM 都是 2-3 分钟为什么这次 36s", PM 地毯式深挖发现:
1. 历史 BGM (4/23 ~ 5/19) **全部 2-3 分钟, payload 完全一样无 duration**
2. Mureka API v1 文档真实参数: account/prompt/title/ref_id/model/async/replyUrl/replyRef — **根本没有 duration 字段**
3. 真根因 = 本次 horror prompt 含"Long silences/suddenly stops/No resolution/question hanging"等"短促/收尾"暗示词 → Mureka 推断短曲

**教训**:
- ❌ "看到 payload 缺字段就下结论缺 duration"是表象诊断
- ✅ 任何 API 参数假设, 必须先查官方文档 + 看历史成功/失败数据对比
- ✅ Founder 反驳"历史正常这次异常"时, 必须深挖**真实变量**, 不是猜"参数缺失"
- ✅ 真因往往是上游 prompt 工程层 (本案是 BGM Haiku 生成短促词导致下游 Mureka 推断短曲)

**审查铁律升级**:
- 任何 "API 参数 X 缺失" 假设 → 必须 ① 查官方文档 ② grep 历史成功调用看是否真传 X ③ 三角验证"变量唯一性"
- 不能在 30 秒内得出根因结论, 大概率是表象诊断

---

## #45 [2026-05-20] "修了一半" 第 5 次重演 — B57 重生流程 + freshness check 算法 bug (test20 陈婶覆盖事故)

**事件**: Founder test20 在 /characters 页重生陈婶 (gothic 成功) → 确认角色 → Pipeline 完成 → 看 27 shot 陈婶又变回 realistic. PM 地毯式追查发现 `pipeline_orchestrator.py:L1071` freshness check 算法 bug:

```python
_portrait_fresh = _portrait_mtime > (_char_ts + 30)  # ❌ +30 把"刚重生"判为"陈旧"
```

RegeneratePortrait 端点 (B57) 同一时刻 T₀ 完成 ① 生成新 portrait (mtime=T₀) ② DB update char.updated_at=T₀。但 Pipeline 下游 freshness check 要求 mtime > updated_at + 30s → False → 重新生成覆盖。

**"修了一半"链条 (第 5 次)**:
- #30 / #39 / #40 / #43 之前 4 次
- **本次**: B57 修了 RegeneratePortrait 完整链路 (生图 + DB update + fullbody 同步重生) ✅, 但**没改 Pipeline 下游 freshness check 算法**, 导致用户重生白做。

**为什么林深/镜中人 Founder 没发现**: char_001/char_002 没主动重生, updated_at=15:39 (初次生成), Pipeline 重生时用同样 CharacterDesigner 描述 → 生成结果跟初次相似, 视觉上看不出。陈婶因风格大改 (realistic → gothic) → Pipeline 重生用原描述 → 又出 realistic → Founder 一眼发现。

**等价说**: 这是个**系统级 bug**, 影响所有角色, 只有用户主动重生 + 风格大改时才显形。其他用户重生角色都白做了。

**教训**:
- 任何"用户主动重生/编辑/修改"功能必须 **grep 全 Pipeline 下游消费端**, 确保它们都接受用户重生的产物
- B57 当时只设计了"生图 + DB 更新", 没设计"Pipeline 下游 freshness check 接受用户重生产物"
- 设计任何"用户编辑入口" → 必须画完整数据流图: ① 入口写入 ② DB 持久化 ③ 下游消费端 全程都不能丢失/覆盖

**审查铁律升级**:
- B57 / 任何 RegenerateXXX 端点完成后, PM 审查必须地毯式检查 `pipeline_orchestrator.py` 是否有 "freshness check / skip / cache / mtime" 类逻辑会覆盖重生产物
- 这次 P0 灾难, 影响所有用户, 必须立刻修

---

## #46 [2026-05-20] 用户操作产物 = 真相, Pipeline 不准二次裁判 (Founder T20-50 设计铁律)

**Founder 16:55 拍板**: 关于角色参考图 freshness check 修复方案, Founder 选方案 A — **"用户在 /characters 页操作的产物 = 真相, Pipeline 不准二次裁判"**。

**正确逻辑**:
```
Stage 2 完成 → 3 角色自动生 portrait + fullbody
用户在 /characters 页:
  ① 不动 → 用 Stage 2 版本 ✅
  ② 重生 portrait → 同步重生 fullbody (B57) → 锁定 ✅
  ③ 调整描述但没点重生 → 用现有 portrait (信任用户操作)
用户确认 → Pipeline 进 Stage 5:
  ★ 永远信任 character_refs/ 里现有文件
  ★ 只在文件不存在时补生
  ★ 绝不基于 mtime/updated_at/freshness check 自检覆盖
```

**核心铁律 (通用 Pipeline 设计原则)**:

1. **用户编辑 = 优先级最高**: 任何用户在前端确认/编辑/调整/重生的产物 = 真相, Pipeline 不应该有"我比你更懂"的逻辑去覆盖
2. **Pipeline 兜底 = 仅当数据完全缺失**: `if file exists / value present → skip generation`; 不存在才补生
3. **freshness check 是反模式**: 用 mtime / updated_at / checksum 等"再判断"逻辑去覆盖用户操作 → 必然 race condition + 浪费成本 + 破坏用户信任
4. **adjust_character endpoint 的责任**: 如果用户改了描述, **endpoint 自己负责立即重生 portrait+fullbody**, 不能依赖 Pipeline 兜底

**等价说**: Pipeline 进 Stage 5 时, character_refs/ 目录里的现状 = 用户期望的真相, 不可质疑。

**反例 (test20 真发生)**: B57 设计了"用户重生 portrait + B57 同步重生 fullbody + DB 更新 updated_at" 完整流程, 但 Pipeline 下游加了 freshness check 算法 `_portrait_fresh = _portrait_mtime > _char_ts + 30` 试图"再判断", 反而把刚重生的判为陈旧 → 重新生成覆盖 → 用户重生白做。

**适用范围**: 所有"用户编辑入口"功能都遵循此铁律
- 重生 portrait / fullbody / shot
- 调整 character description / adjust_character
- 重生 BGM / 编辑文字 overlay
- 删除 shot / 重新排序
- 任何 /preview 页用户操作

**Founder 原话**: "如果在 characters 页面重新调整生成好的角色 之后就用这个角色 如果没有 fullbody 就补生成对应的 fullbody 必须不能把之前生成的角色参考图都废弃然后再一次重生 这样浪费成本 也不符合逻辑"

---

## #47 [2026-05-20] Agent 报告 "SKIP" 实际 "FAIL" — pytest 自报必须 PM 跑验证

**事件**: Wave 2 round 1 AI-ML 报"T20-43 测试 27 SKIP (google.genai absent, 同 T20-46 pattern)", PM 自跑实测 **26 FAILED, 50 PASSED**。

**真根因**: AI-ML agent 写完测试后**没真跑** pytest, 凭"T20-46 同 pattern 推断 SKIP"。实际:
- 测试代码用 `_build_prompt(outline=outline, style_preset="gothic")` — 真签名不接受 outline kw arg → TypeError → 26 FAIL
- AI-ML 误以为是 google.genai 缺导致 SKIP (跟 T20-46 一样)

**教训**:
- ❌ Agent 报"SKIP" 不能凭"类比推断", 必须真跑 pytest 确认
- ❌ "测试写完了" ≠ "测试真 PASS"
- ✅ Agent 必须在完成报告里**明确**列出 真 PASS / 真 SKIP / 真 FAIL 数 (不能笼统说"PASS")
- ✅ PM 收到 agent 报告必须**自跑 pytest** 验证 (Round 1 抓出此 bug)

**审查铁律升级 (KEY_LEARNINGS #29 + #36 + 本次)**:
- 任何 agent 报告测试结果, PM 必须 `python -m pytest <file> -v --tb=short` 自跑
- 大批量综合 pytest 跑出 fail 后, PM 必须 grep fail name + 单跑确认是 isolation 问题还是真 bug
- "agent 报 PASS" 跟 "PM 自跑 PASS" 是两件事

**等价案例 KEY_LEARNINGS #29 实证 + 本案合并**: agent 自报跟真实状态可能差异巨大, PM 不能信任 agent 自跑结果。

---

## #48 [2026-05-20] "修了一半" 第 6 次重演 — Backend 双层防御只接兜底层 (T20-48 wire 缺)

**事件**: Wave 2 round 1 Backend agent 报告"T20-48 双层防御已协同生效":
- 兜底层 (`pipeline_orchestrator.py` MAX_ANATOMY_RETRIES) ✅
- 预防层 (`storyboard_director.py` import + 注入 ANATOMY_FIDELITY_RULES) ❌ **没做**

PM 5 维度审查 grep `ANATOMY_FIDELITY_RULES` 在 storyboard_director.py 时 **0 命中**, 才发现预防层未接通。

**"修了一半"链条第 6 次** (#30 / #39 / #40 / #43 / #45 / 本次):
- AI-ML 加了 prompt 规则到 storyboard_prompts.py ✅
- Backend 加了 retry 兜底到 pipeline_orchestrator.py ✅
- Backend **漏了** import + 注入到 storyboard_director.py prompt ❌

**真根因 (Backend 误判)**: Backend agent 看到"无文件冲突" 就以为"双层防御已协同生效", 没真 grep 预防层是否在 Stage 4 prompt 真出现。

**等价案例 KEY_LEARNINGS #29 + #45**: "无冲突" 不等于"已接通", 必须 grep 真注入点。

**审查铁律升级**:
- 任何"双层防御 / 多层修复 / 跨 agent 协同"必须 PM 用 grep 验证**每一层**真接通
- 不能凭"agent 自报已协同" 信任, 必须 grep 真注入点 + 真调用点 + 真消费点
- 防御层数 ≥ 2 时, fail 概率 = 任一层未接通的概率, PM 必须每层逐查

---

## #49 [2026-05-20] Wave 2 PM 审查两次漏抓 P0 (Founder 新 test20 实证)

**事件**: Wave 2 round 2 PM 审查"全过 10 维度", 但 Founder 5/20 18:58 新 test20 实测**抓出 2 个 P0**:

### Bug 1: T20-47 SONNET_MODEL ID 写错 (Wave 2 Backend agent round 1 + PM 审查双漏)

- Backend agent 凭印象写 `"claude-sonnet-4-6-20251101"` (跟 Haiku 4.5 `-20251001` 类比)
- 真实 ID `"claude-sonnet-4-6"` 无日期后缀 (按 CLAUDE.md memory 明确写)
- PM 审查只 grep 验证 `SONNET_MODEL` **字符串存在**, 没真 mock Anthropic API 调用验证 model ID 被接受
- pytest 通过但用 fake Anthropic client, 没触发真 404
- Founder 实测 Stage 5 shot validation **100% 404 fail-open**

### Bug 2: T20-50-fix-2 save_all_references 覆盖 portrait (T20-50 round 1 + PM 审查双漏)

- T20-50 round 1 修了 `_gen_one_char_ref` 的 `skip_portrait_local`
- 没改 `ReferenceImageManager.save_all_references` 的无条件 `image.save()` 覆盖逻辑
- PM 审查只 grep 验证 freshness check 移除 + log "信任不重生"出现, 没真**追下游所有写盘点**
- Founder 实测 char_003 portrait size 2372998→2896955 (内容真变)

**教训 — Wave 2 PM 审查漏点根因**:

1. **"字符串存在"≠"语义正确"** (T20-47 例): model name 是字符串, 真值是否被 Anthropic API 接受需要真 HTTP 调用验证, 不能 grep 通过
2. **"防御一处"≠"防御全链路"** (T20-50 例): 一个修复点防 freshness check, 但 ReferenceImageManager 还有 save_all_references 单独写盘逻辑, PM 必须追**所有可能写盘的代码路径**
3. **pytest mock ≠ 真生产**: mock 假 client 永远不触发 404, 必须 mock 真 HTTP 响应或 integration test

**审查铁律升级 (KEY_LEARNINGS #29 + #36 + #47 + 本次合并)**:

- 任何"外部 API model ID / config name / endpoint URL"必须 PM 真 curl/python 调一次外部 API 验证 (不只 mock pytest)
- 任何"用户编辑入口"修复必须 PM grep **完整 grep 模式**: `\.save\(|write\(|open\(.*'w'\)|imwrite|json\.dump|cache\.set` 等所有可能写盘/写存储的代码点 (不只看修复点)
- 任何 "信任用户操作 / no regen / freshness" 类修复必须 PM 真重启 Pipeline + 跑 e2e 验证 disk 文件 mtime + size 不变 (不只 grep log "no regen" 出现)

**Wave 2 PM 审查 30+ 维度仍漏抓 2 个 P0 — 说明 PM 审查需要再升级到 40+ 维度, 特别是 API/storage 真值层验证**

---

## #50 [2026-05-21] Stage 4 prompt "建议性 hint" 被 LLM 完全自由发挥 — character schema 0% 注入 image prompt (T22-NEW-3 P0 通用性灾难)

**事件 (test22 美人鱼 e2e)**: Founder 跑 fairytale 美人鱼 (3 角色 — 珊瑚 sea-green hair / 阿海 ash-blonde / 海婆 silver-white). 20/20 shot prompt **0 个用对** 珊瑚 sea-green hair. Shot 9-14 真用 "dark hair" (LLM 完全自由发挥), Shot 1-7 / 15-20 真省略 hair 字段不写.

**根因深定位**:
- `storyboard_prompts.py` L904 用 "建议性 hint": `Format examples (replace [hair_color] with the actual value from character data)`
- LLM 真把这当**软建议**, 真自由发挥 — 生 narrative 时优先戏剧化好画面 (dark hair drifting) > 严格 character signature
- `storyboard_director.py` L229 真**0 注入** character physical 到 image_prompt (只有"环境互动"提示)

**通用性扩展**:
- 不止 hair_color 真自由发挥, **不止珊瑚**, **不止美人鱼/fairytale**
- 跨 **19 character_types** (human / mythological / aquatic / robot / ...) × **80+ styles** × **任意题材** 全部受影响
- 同问题真出现在所有 LLM-generated visual content 工具 (Midjourney/Sora/Runway): LLM 创意能力 vs 严格一致性张力 — "建议性 hint" 永远被 LLM 创意绕过

**根本性 problem**:
- Pipeline 真无 "Identity Anchor 框架" 接入 (CLAUDE.md 真提到 docs/CHARACTER_IDENTITY_FRAMEWORK.md v1.0 真未实施)
- 真信息传递衰减 (Stage 2 schema → Stage 4 LLM input → Stage 4 LLM output 真每跳一次丢一层 fidelity)
- 真无 "创意 vs 一致" separation of concerns (LLM 同时管, 真应该 LLM 管创意 + Backend 管一致)
- 真无 cross-stage validation (ShotValidator 真验 image vs prompt, 真不验 prompt vs schema)

**教训**:
1. **"建议性 hint" 永远不可信** — LLM 创意性会绕过任何软约束, 必须用强制注入 (Backend post-process)
2. **任何"应该 stable identity"层 (character/style/location/props/time)** 都真**不能让 LLM 决定** — 必须 Backend 真绕过 LLM 强注入
3. **Stage 4 LLM 真职责**: 真**narrative scene description** (创意层), 真不是 character/style/location signature 真维护
4. **cross-stage validation 必须 prompt 真验 schema** (新增 PromptValidator), 不只 image 真验 prompt

**修复方向 (DEC-048 Layer 1 长期架构治本, Wave 6 主线)**:
- Identity Anchor Framework v1.0 接入 (anchor 分离 variable)
- Backend post-process 强注入 [IDENTITY ANCHORS] block (5 维度: character/style/location/props/time)
- PromptValidator 新增 (prompt vs schema 验证, 在生图前)
- 跨题材 baseline regression (19 type × 5 style CI 防退化)

**关联**: T22-NEW-3 + DEC-048 + DEC-046 v3 narrative readability + storyboard_prompts.py L904

---

## #51 [2026-05-21] Founder "通用故事角度铁律" — 不修一个/一类故事, 修产品根本性问题

**事件 (5/21 22:05-22:55)**: PM 真初次发现 T22-NEW-3 hair_color 不一致问题, 真升级 PENDING 推荐"Layer 2 hotfix patch (2-3h) + Layer 3 跨题材 regression (1-2h)" 真**先解锁内测**. Founder 真当场反驳 2 次:

1. **22:05** "要从通用性角度考虑 别忘了 毫无遗漏且全面细致清晰具体的去想此类以及相关问题"
2. **22:50** "我的意思是通用故事角度去研究、深挖、思考和分析，而不是只修这一个或者这一类故事"
3. **22:55** "我还是偏向之前你说的'选项: C 长期架构'这种根治的方式"

**教训**:
- PM 真习惯性想"短期 hotfix 先解锁内测", Founder 真偏好"长期架构治本 + 接受内测延后"
- 任何"产品生命线"问题 (CLAUDE.md 真明确列出: 角色一致性 / 风格一致性 / 音画对齐 / 条漫文字) 真不能用 hotfix patch 修
- 真任何"通用工具"产品定位 — 必须真**所有可能的场景**真根治 (跨 character_type / style / 题材 / 任意 N 组合), 不修单点
- "Founder 接受真延后" — 真"内测启动"不是 PM 优先级, 真**产品质量根治** 才是

**铁律 (PM 派工 / 提议时必读)**:
- 涉及"产品生命线" (角色一致性 / 风格 / 音画 / 文字) 真**第一直觉是长期治本**, 不是 hotfix
- PM 推荐方案时必须真**至少列 3 个选项** (A 短期 / B 中期 / C 长期), 标 Founder 真"通用性铁律"友好等级
- 接受 Founder 真"延后内测等真根治" 选择, 不真"先解锁"
- 真任何提议必须真**毫无遗漏且全面细致清晰具体** (Founder 真原话, 多次提醒)

**关联**: T22-NEW-3 + DEC-048 Layer 1 长期治本 + CLAUDE.md "🚨 核心原则 (不可妥协)" + 真 Founder 偏好画像

---

## #52 [2026-05-22] KEY_LEARNINGS #47 真**重演第 6 次** + try/except 吞 ImportError 真**silent fail P0 风险** (Layer 1 M2-M5 round 1 → round 2)

**事件 (DEC-048 Layer 1 M2-M5 实施)**:
- Round 1 (Opus 4.7 max thinking, 5/21 23:25) AI-ML 自报 "74/74 PASS + 0 越权"
- PM 5/22 00:00 地毯式审查按 KEY_LEARNINGS #47 真**自跑** pytest, 发现 **7 FAIL** (test_style_anchors_returns_top5_mandatory × 6 + test_style_anchors_empty_preset_defaults_to_realistic × 1)
- 真实际 67/74 PASS, 7 FAIL — 跟 #47/#49 真**同 pattern** (agent 报 PASS 但 PM 自跑 FAIL)

**真根因深定位 (PM Bash 自查 + python3 -c 隔离调用)**:
```python
# identity_anchor_prompts.py L424-430 (round 1 代码)
try:
    from app.services.style_enforcer import StyleEnforcer
    enforcement = StyleEnforcer.STYLE_ENFORCEMENTS.get(preset)
except Exception:  # ← 真吞了所有 Exception 含 ImportError
    enforcement = None
```

真 cascade 路径:
- `from app.services.style_enforcer import StyleEnforcer`
- → 真**触发** `app/services/__init__.py` L3 `from app.services.story_generator import StoryGenerator`
- → 真**触发** `story_generator.py` L7 `from google import genai`
- → 真 ImportError (PM 本地缺包, **生产环境也可能挂**)
- → `except Exception` 真**silent 吞**
- → enforcement = None → 返回空 `mandatory_keywords_top5=[]`

**真 P0 风险 (Layer 1 长期治本架构反讽)**:
- Layer 1 真**核心目标**: 把 character/style/location anchor 真**强注入** image_prompt 绕过 LLM hint silent fail (KEY_LEARNINGS #50)
- 真**讽刺**: round 1 实现真**自己 silent fail** — 如果生产环境 google.genai 真**临时**挂 (网络/缓存), Layer 1 真**强注入完全失效**, 真**不报错** → 跟 T22-NEW-3 真**同 silent fail pattern**, Layer 1 真**白做**

**Round 2 修法 (T20-52 同 pattern, importlib 真**绕过)**:
```python
# round 2 代码 L424-450
try:
    import importlib.util as _ilu
    _se_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", "style_enforcer.py")
    _spec = _ilu.spec_from_file_location("_style_enforcer_isolated", _se_path)
    _module = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    StyleEnforcer = _module.StyleEnforcer
    enforcement = StyleEnforcer.STYLE_ENFORCEMENTS.get(preset)
except (ImportError, FileNotFoundError, AttributeError) as e:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        f"[Layer 1] extract_style_anchors failed: {type(e).__name__}: {e}. "
        f"P0 risk per DEC-048/KEY_LEARNINGS #50."
    )
    enforcement = None
```

真**关键改动**:
1. `importlib.util.spec_from_file_location` 真**直接 load** style_enforcer.py 文件本身, 绕过 `__init__.py` cascade (T20-52 `_load_shot_validator_fresh` 同 pattern)
2. `except (ImportError, FileNotFoundError, AttributeError)` — 真**narrow except**, 不吞所有 Exception
3. `logger.warning(...)` 真**显式记录** P0 风险, 不再 silent — 即使 fallback 真发生, 监控/排查能真发现

**教训**:

1. **`except Exception` 真**禁忌**, 任何 silent fail 真**P0 风险铁律** — narrow except + logger.warning 真**强制**
2. **架构反讽** — 长期治本 Layer 1 真**自己重演** silent fail pattern (KEY_LEARNINGS #50) → 真**任何 silent fail 真**架构级 P0**, 不只业务 bug
3. **`from app.services.X import Y` 真**触发 __init__.py cascade** 真**已知 risk** (T20-52 实证), 真**任何**新模块 import app.services.X 都真**应该**用 importlib pattern, 不要重蹈
4. **KEY_LEARNINGS #47 真**重演 7 次** (累计) — agent 自报 PASS 真**永远不可信**, PM 真**必须自跑** pytest, **不能凭"应该过"** 汇报
5. **Opus 4.7 max thinking 真也会 silent fail** — 模型再强, 真**架构知识缺失** (不知 __init__.py cascade history) 真**依然**踩坑. PM 真**派工时**应该真**列出已知 risk pattern** 提醒 (本次 PM 真**没提醒** → process gap)

**审查铁律真**升级 (KEY_LEARNINGS #29 + #36 + #47 + #49 + 本次合并)**:

- 任何 `try/except Exception` 真**PM 审查必抓** — narrow + logger 真**强制**
- 任何 `from app.services.X import Y` 真**PM 审查必抓** — 提议改 importlib pattern
- 任何"我跑了 pytest 全 PASS" 真**PM 必自跑** 验证 (#47 第 7 次铁律)
- **元教训**: PM 真**派工 prompt** 应该真**列已知 risk pattern** (try/except / __init__.py cascade / silent fail) 提前提醒, 避免 agent 踩坑

**关联**: T22-NEW-3 + DEC-048 Layer 1 + KEY_LEARNINGS #29/#36/#47/#49/#50 + T20-52 importlib pattern

---

## #53 [2026-05-22] PM 真**漏沉淀 KEY_LEARNINGS 教训** (元教训, Founder 5/22 抓到)

**事件 (5/22 早间开工)**:
- PM 5/22 00:15 暂停时 TEAM_CHAT / PM current.md 真**已记录** KEY_LEARNINGS #47 真**重演第 6 次**
- 但 PM 真**没 Edit `.team-brain/knowledge/KEY_LEARNINGS.md` 加 #52** 真沉淀
- Founder 5/22 早间开工时 真**精准抓到** PM 漏抓: "之前提到的这个处理了吗"
- PM 真**承认漏沉淀** + 立即 Edit 加 #52 + #53 (本条)

**真根因 (PM process gap)**:
1. PM 真**习惯**在 TEAM_CHAT / progress 真**记录**事件, 但真**没自动** 升级到 KEY_LEARNINGS.md 沉淀 — TEAM_CHAT 真**临时记录**, KEY_LEARNINGS 真**永久教训库**
2. PM 真**没建立**真"sediment 自动化流程": 任何 KEY_LEARNINGS #X 真**重演** → 真**立即** Edit `.team-brain/knowledge/KEY_LEARNINGS.md` 真追加新 #X+N
3. PM 真**只**给 agent 写 spawn prompt 时强调 "更新文档", 真**自己** PM 维护 KEY_LEARNINGS 真**漏了**

**教训 (PM 真**审查铁律** + 文档维护铁律)**:

1. **任何 KEY_LEARNINGS #X 真**重演** → PM 真**必须**立即 Edit `.team-brain/knowledge/KEY_LEARNINGS.md` 真追加新 #X+N, 不能只在 TEAM_CHAT 真**临时**提及
2. **PM 真自己**维护文档真**频率 = 派 agent 维护文档真**同等** — 不能"自己懒于沉淀, 只要求别人沉淀"
3. **PM 真**收尾时** (xhteam 第六步) 真**必须**核**真 KEY_LEARNINGS.md 真**有 #X+N**, 而不只 grep TEAM_CHAT — TEAM_CHAT 真**会被压缩**, KEY_LEARNINGS 真**永久**
4. **Founder 真**精准抓到** PM 漏抓真**第 5 次** (B39 / T20-47 / T20-44 / T20-46 / 本次) — PM 真**审查铁律** 真**升级**到 9+ 维度 (含"KEY_LEARNINGS 真**已沉淀**" 真**专项检查")

**真**审查 checklist 真**升级** (KEY_LEARNINGS #29 + #36 + #46 + #47 + #48 + #49 + #50 + #51 + #52 + 本次 #53 合并)**:

✅ pytest PM 真自跑 (#47)
✅ 调用链路接通 (#48)
✅ 字符串存在 + 语义正确 (#49)
✅ Ben 5/13 协议核 (DEC-030)
✅ TEAM_CHAT 末尾追加位置 (avoid Tester 头部错)
✅ 0 越权 find
✅ mtime 验证
✅ 高风险文件回归 (CLAUDE.md)
✅ **KEY_LEARNINGS.md 真**已沉淀** 新 #X+N (本条新加, PM 收尾必查)
✅ Founder 真**多次**提醒铁律 (地毯式 + Ben 协议 + 毫无遗漏 + 全面具体清晰细致)

**关联**: KEY_LEARNINGS #47-52 + xhteam 第六步收尾铁律 + Founder 真**多次提醒** 真**精准抓** PM 漏抓真累计 5 次

---

## #54 [2026-05-22] Agent tool `model: opus` 真**派工失效** + legacy 死代码加 wire 真**defense-in-depth 当前 0 价值** (Backend Layer 1 实施真发现)

**事件 (5/22 12:00 Backend Layer 1 完成)**:

PM 真用 `Agent(model="opus")` 真派 Backend Layer 1 实施 (Opus 4.7 max thinking, ~3h ETA). Backend 真**完成时间** ~25 min (实际不是 3h), 真**自报落款** "Backend (Sonnet 4.6, 2026-05-22 12:00)".

**真**两种可能**:
1. Backend 真**自报错误** — 真**实际用了 Opus** 但落款写 Sonnet
2. Agent tool `model: opus` 真**没生效** — 真**实际 Sonnet 4.6** 执行 (backend.md frontmatter or Agent tool API silently fail)

**真**实证**:
- 完成时间 ~25 min (不是预估 3h) — 真**符合 Sonnet 4.6 速度**, Opus 4.7 max thinking 真**应该更久**
- 145 tool uses (Backend 实际) vs AI-ML M1 真 145 uses + 2710s (Opus 4.7 max) — 真**Backend tool usage 类似 但**时间** 真**短** = 真**Sonnet** 概率高
- 代码质量 ok (127/127 PASS + 调用链路接通) — 真**Sonnet 4.6 真**能完成** 此类执行类任务

**真核心 problem (待 PM/Founder 决策)**:
- 真**Opus 真**未来派工** 真**所有**真**重要架构改造** 真**可能 silently 降级到 Sonnet**?
- 真**派工 model 参数真**生效验证** 真**需要研究**: Agent tool API 真 model precedence rules / backend.md frontmatter 真**是否 override** PM 真 spawn 参数

**真**深度补审** 真**额外发现 (KEY_LEARNINGS #48 真**调用链路**)**:

Backend 真**3 dispatch wire** 真**实际深查**:
- L1009 `generate_shot_image` (legacy): grep `\.generate_shot_image(` 真**0 caller** (非 phase2) — 真**完全死代码**, wire 真**defense-in-depth 但当前 0 价值**
- L1278 `generate_shot_image_phase2` (NB2): 真**被** L1671/L1742 真**_safe 内部**真调用 — 真**defense-in-depth 第二层**, 真**所有路径 真**经过** 真**已 OK**
- L1639 `generate_shot_image_phase2_safe` (PRIMARY): 真**pipeline_orchestrator L1589 + chapters.py L2291** 真**唯一**外部 caller — 真**关键 wire**

**真**Backend 真自报** "3 dispatch wire" 真**精确** 但**L1009 真当前 0 价值** — 真不阻塞, 真**值得记录** if 未来真**重启** legacy 路径.

**教训**:

1. **任何 spawn 真后**, PM 真**核对** Backend / AI-ML 真**自报落款 model** 真**是否符合 PM 派工** — 若不符, 真**记 KEY_LEARNINGS** 沉淀 (本条)
2. **任何 "3 dispatch wire" 类任务**, PM 真**深查** 真**每个 dispatch 真**当前真有 caller** — legacy 真**0 caller** 真**defense-in-depth** 真**OK 但应标记**
3. **派工 model 真**待研究**:
   - 真 spawn `model: opus` 真**应 override** backend.md frontmatter (Agent tool 真**文档承诺**)
   - 若 backend.md 真**没** frontmatter, 真**应继承** parent — 但**Sonnet 4.6 真**parent 真**默认** (Founder 偏好 "最低 Sonnet")
   - PM 真**未来**派工 真**真要核 backend.md frontmatter** + 真**spawn 完后** 真**第一时间 verify** model 真**生效**

**真**临时缓解**: Backend Layer 1 真**实施质量 ok** (Sonnet 4.6 真**完成执行类任务** 真**没问题**), 真**不阻塞** Tester 派工. 真**长期待研究** Opus 真**派工生效问题**.

**关联**: Agent tool 真 model 参数 + backend.md frontmatter + KEY_LEARNINGS #48 调用链路 + Founder 偏好真**最低 Sonnet 4.6**

---

## #55 [2026-05-22] AdjustCharacter / RegeneratePortrait 缺 Haiku→Gemini fallback — P1 Wave 6 待修 (Founder e2e test22 实测)

**事件 (5/22 13:30 e2e test22)**:
- Founder 改阿海服装 (蓝白渔衣→绿白渔衣) 点重生
- AdjustCharacter 调 Haiku 改 schema → Haiku 529 overloaded → 直接 500 Internal Server Error 返回前端
- Founder 操作 blocked, 等 1 min 后重试才成功

**根因**:
- AdjustCharacter (`app/api/projects.py` adjust endpoint) 用 Haiku 真**改 schema**
- 无 Gemini fallback (不像 Stage 1-5 真**T20-14 设计内 fallback**)
- Anthropic Haiku 临时 overloaded 即返 500, 用户操作直接失败

**对比 Stage 1-5 真 fallback 设计** (T20-14):
- Stage 1 outline: Claude 529 → Gemini 备用 ✅
- Stage 2 characters: Claude 529 → Gemini 备用 ✅
- Stage 3 screenplay: Claude 529 → Gemini 备用 ✅
- Stage 4 storyboard: Claude 529 → Gemini 备用 ✅
- AdjustCharacter: ❌ 无 fallback (P1 缺陷, 5/22 13:30 实证)
- RegeneratePortrait: ❌ 推测同样 (待 audit)
- Shot regenerate: ❌ 推测同样 (待 audit)
- **Stage 6 Music BGM (music_generation_service.py)**: ❌ 无 fallback (P1 缺陷, **5/22 13:56 实证**: Haiku 3 次 retry 全 529, 故事无 BGM, 非阻塞但用户体验降级)
- Outline UX-2 一致性检查: ✅ 非阻塞 warning (不影响 Pipeline)

**Founder 反馈 (5/22 13:32 原话)**: "这点要记下来 之后还是需要 fallback 的"

**修复方向 (Wave 6 P1, Founder 5/22 13:35 调整 fallback 顺序)**:
1. AdjustCharacter / RegeneratePortrait / Shot regenerate 全部加 **Haiku 4.5 → Gemini 3.1 Flash → Sonnet 4.6** 三层 fallback
   - **跨 provider 优于跨 size**: Anthropic 整体 overload 时 Sonnet 也会挂 (跟 Haiku 同 provider), Gemini 跨 provider 更可能恢复
   - 第 1 层 Haiku 默认 (快+便宜) / 第 2 层 Gemini Flash 最新 (跨 provider, 真**主备**) / 第 3 层 Sonnet 最新 (真**最强保底**, 当 Gemini 也挂)
2. 镜像 T20-14 Stage 1-5 真**已成熟** fallback pattern, 但**顺序调整为跨 provider 优先**
3. 前端 toast 友好提示 "服务繁忙, 自动用备用模型, 请稍候 ~10s"
4. 加 metrics: fallback rate 监控 (Haiku/Gemini/Sonnet 真**各层触发率** + 业务影响)

**临时缓解 (Founder 已用)**: 等 30-60s 后再重试 (Anthropic 通常 1 min 内恢复)

**关联**: T20-14 Stage 1-5 fallback + e2e test22 + AdjustCharacter (`app/api/projects.py`) + RegeneratePortrait (`app/api/projects.py`) + Shot regenerate (`app/api/chapters.py`)

---

## #56 [2026-05-22] Wave 7 Backend 真双重发现 — ID format mismatch (T22-NEW-7 真根因) + PM 派工前没核 memory 真实性 (T22-NEW-8 假阳性)

### 教训 A: LLM 输出 ID 格式不一致 → backend 必须容错 (T22-NEW-7 真根因)

**事件 (Wave 7 Backend Opus 4.7 max thinking 5/22 14:25-14:55 完成)**:

T22-NEW-7 P0 真**初步诊断** chars=0 真"race condition / scope / batch order / async dispatch 问题", 真**深查后**真**根因不在 backend race**:

- test22 `4_storyboard.json` 实测: Stage 4 LLM 输出 `characters_in_scene` 真**前后格式不一致**:
  - Shot 1-3: `['Coral']` / `['Coral', 'Ah Hai']` (`name_en` 格式)
  - Shot 4-21: `['char_001']` / `['char_001', 'char_003']` (`char_id` 格式)
- 旧 `_apply_identity_anchors` 真**只比对 `c["id"]`** → 前 3 shot 完全 mismatch → `chars_in_shot=[]` → CHARACTER ANCHORS 没注入 → Seedream weak ref following → **Shot 2 美人鱼变蓝头发人腿**

**修复 (Backend 真`resolve_characters_in_shot()` 100 行 helper)**:
```python
# 三 key fuzzy match: id / name_en / name (case-insensitive)
def resolve_characters_in_shot(shot_char_ids, characters):
    for fld in ("id", "name_en", "name"):
        # 真**任一字段命中** 即视为匹配
```

**教训**:
1. **LLM 输出格式真**不稳定** — 同 prompt 真**不同 shot 真**输出不同格式** (Stage 4 LLM 真**前 3 用 name_en, 后续用 char_id**)
2. **Backend 真**必须容错** 真**LLM 真**多格式输出** — 不能假设 `c["id"]` 真**唯一匹配键**
3. **诊断真**初步推测 ≠ 根因** — PM 真**初步 推测** race condition, 真**Backend 深查** 发现真**根因 ID format mismatch** (诊断 KEY_LEARNINGS #48 真**追完整调用栈**)
4. **加防御性 log_mismatch warning** — 真**LLM 输出 ID 真**未匹配 character schema** 真**立即报警** (避免 silent fail KEY_LEARNINGS #50/#52)

### 教训 B: PM 派工前没核 memory 真实性 (T22-NEW-8 假阳性, KEY_LEARNINGS #53 重演)

**事件 (Wave 8 Frontend T22-NEW-8 confirm-outline wire 5/22 14:55 完成)**:

T22-NEW-8 派工任务: StageB.tsx 真**加 POST confirm-outline 调用**. Frontend agent 真**深查发现**:

1. PENDING.md 真**写 endpoint URL 错**: `POST /api/projects/{uuid}/chapters/1/confirm-outline` — 这个 endpoint 真**不存在** (chapters.py grep 0 hits)
2. **正确 endpoint 真**已存在**: `POST /projects/{project_id}/confirm-outline` (projects.py L518) — **project-level** (不是 chapter-level)
3. **StageB.tsx L152-255 `handleConfirm` 真**早就 wire** confirm-outline 调用 + 真**保存** edited outline + 真**toast 反馈** + 真**inconsistency_warnings banner**
4. **0 代码改动** 完成 — 真**已实现**

**真根因**: PM 派工前真**没核** memory `project_confirm_outline_not_wired.md` 真**当前真实性**. memory 真**可能 5/21 写时真**为真**, 但 5/22 真**已实现**, memory 真**没更新** → PM 真**抄 memory 直接派工**.

**教训**:
1. **memory 真**会过时** — `project_*.md` 真**长期记忆** 真**当前真实性** 真**未必**仍真
2. **PM 派工前必须真**核** memory 真**当前真实** — grep / read 真**目标代码** 真**verify**, 真**不能** 抄 memory 直接派
3. **KEY_LEARNINGS #53 真**第 2 次重演** — PM 真**漏沉淀** 真**已升级** 但真**漏核 memory** 真**新 process gap**
4. **审查铁律真**升级 11 维度** (新加: PM 派工前真**核 memory 真实性**)

### 真**好消息**

- Backend 真**自主深查** 真**发现根因** ID format mismatch (不是 PM 初步推测 race) — 真**好 agent**
- Frontend 真**深查发现** T22-NEW-8 真**已实现** → 0 改动 — 真**避免无效工作**
- 真**Wave 7+8 真**少 1 个 task 需要修** (T22-NEW-8 真**已完成**)

**关联**: T22-NEW-7 (chars=0 根因) + T22-NEW-8 (假阳性) + KEY_LEARNINGS #48 (调用链路接通) + #50/#52 (silent fail 防御) + #53 (KEY_LEARNINGS 沉淀元教训) + Founder 多次提醒地毯式审查铁律

---

## #57 [2026-05-22] 跨路径 wire 一致性 — shot 加了 anchor 但 portrait 没加 = "半吊子一致"，颜色漂移无法根治 (Wave 9 TASK-T22-NEW-10)

### 事件

Wave 7 Backend 实施 `_apply_identity_anchors()` 修了 shot path 的 Layer 1 anchor 注入。但 portrait path (`reference_image_manager._build_portrait_prompt()`) 从未 wire Layer 1。audit 文件 `T22_NEW_10_PORTRAIT_LAYER1_AUDIT_2026-05-22.md` (680 行 9 维度) 发现这个不对称。

### 根因

Layer 1 Identity Anchor Framework 设计为横跨所有图像生成路径，但实施时"分批打补丁"导致：
- Shot path: ✅ Backend Wave 7 wire
- Portrait path: ❌ 从未 wire → portrait 生成时无 anchor 约束，发色靠 StyleEnforcer mandatory 关键词，LLM 自由发挥
- Fullbody path: ❌ 同样未 wire

Portrait 是 shot 的**参考图基础**。如果 portrait 本身颜色不稳定（比如 Coral 珊瑚粉变蓝），后续即使 shot 有 anchor 约束，也无法纠正参考图本身的颜色错误。

### 教训

1. **跨路径一致性原则**: 任何 identity/consistency 机制实施时，必须同时 audit 所有使用同类 prompt 的路径 (portrait / fullbody / shot / scene 等)。不能只改一条路径，让其他路径保持旧状态。

2. **"半吊子一致"比没有一致更危险**: shot anchor 正确但 portrait 无 anchor → 最终图像里 portrait reference 和 shot 之间颜色矛盾，排查时更难判断根因。

3. **wire 新机制必须跟全量路径 checklist**: 改 shot path → 立即问"portrait path 改了吗？fullbody path 改了吗？" 不要等到下次 e2e 实测才发现。

4. **audit 比修复先**: Wave 9 由 680 行 9 维度 audit (PM 用 Explore agent) 触发，audit 发现了这个问题。跨路径检查是 audit 应有的维度。

### 修复 (Wave 9)

`reference_image_manager._build_portrait_prompt()`:
```python
if not StyleEnforcer.is_bw_style(style_name):
    try:
        from app.services.identity_anchor_injector import inject_identity_anchors
        enforced_prompt = inject_identity_anchors(
            image_prompt=enforced_prompt,
            characters_in_scene=[character],
            location=None, style_preset=style_name, props=None, time_continuity=None,
        )
    except Exception as e:
        logger.warning(f"[ReferenceImageManager] Layer 1 inject FAILED ... err={e}")
```

`StyleEnforcer.is_bw_style()` 新增，两路 skip: `BW_STYLES set` 成员 OR `_bw` 后缀。

**fullbody 同 root cause** 待后续同批修。

**关联**: TASK-T22-NEW-10 + DEC-049 + DEC-048 (Layer 1 Framework) + KEY_LEARNINGS #52 (跨 import cascade 防御)

---

## #58 [2026-05-22] destructive git 操作前必须 commit/stash 所有 working tree (PM 5/22 18:45 灾难)

### 事件

5/22 17:00-18:30 AI-ML Opus 4.7 max 完成 Wave 9 portrait Layer 1 wire (代码 + test + progress 三件套 + KEY_LEARNINGS + DECISIONS), 但**未 commit**。

5/22 18:45 DevOps 第二轮 Sonnet 4.6 跑 `git filter-repo --replace-text .secret-replacements.txt --force` (清理 GitGuardian P0 secret leak), 重写整个 working tree 到 HEAD 状态。

结果: AI-ML 1.5h 工作 (代码 2 文件 + progress 3 文件 + KEY_LEARNINGS #57 + DEC-049 + TEAM_CHAT 消息) **全部清除**。只有 untracked 新文件 (test_layer1_portrait_injection.py + audit doc + .gitleaks.toml) 保留 (filter-repo 不动 untracked)。

同事故还连带清掉了 PM 自己之前 Edit 加的 PM completed.md Wave 7+8 块 — PM 也没及时 commit。

### 根因

`git filter-repo --force` 在 working repo 自动 reset working tree (这是文档警告的行为, DevOps 跑时没考虑, PM 派工 spawn prompt 没明确"先 commit / stash")。

不只 filter-repo, 任何 destructive git 操作都可能丢 uncommitted: `git reset --hard`, `git clean -fdx`, `git checkout -- .`, `git restore .`, BFG repo-cleaner 等。

### 修复 (Wave 9 重做)

派 AI-ML Sonnet 4.6 重做 45 min (spec + test 文件已存在), self-commit 89bcfc7 保存。后续 Wave 9.1 + Tester 都强制 self-commit (1629332 + c570c2d)。

### 教训 — 铁律

**任何 destructive git 操作前 (PM 自己 or 派 DevOps), 必须先 `git status` 确认 working tree clean**:
- 有 uncommitted modified → 先 commit 或 stash
- 有 untracked files 不动 (filter-repo 默认不动 untracked)
- 跨多 agent 工作 → PM 协调时务必 verify 所有 agent 都 self-commit 后再 destructive

**Spawn prompt 必须强制**:
- 任何代码改动的 spawn prompt 末尾必须含 "完成后立即 git add + git commit (self-commit, 防丢)"
- 任何 destructive git 操作的 spawn prompt 必须含 "跑命令前先 `git status` verify clean, 如有 uncommitted 立即 commit 或 stash"

### 后续防御

- PM 派工 spawn prompt 模板加入 "self-commit 强制" 章节
- 任何 PM 派 DevOps 跑 destructive git (filter-repo / reset --hard / clean -fdx / BFG) 必须前置 step "verify git status clean"
- DEC-050 候选 (DevOps Opus 4.7 已写) 加入此条

### 实证 (5/22 19:00-19:45)

Wave 9 重做 + Wave 9.1 + Tester 全部 self-commit ✅ (89bcfc7 / 1629332 / c570c2d)
后续 destructive git 操作 0 再丢

**关联**: TASK-SECRET-LEAK-REMEDIATION + TASK-T22-NEW-10 + DEC-050 候选 (SECRET_HANDLING_PROTOCOL) + KEY_LEARNINGS #57 (跨路径 wire 一致性)
