# Harness Engineering V2 差距分析 + 执行规划

> **日期**: 2026-04-15
> **来源**: Founder 与 PM 讨论
> **目标**: 自动化验证 7→10, 代码强制执行 6→10

---

## 一、自动化验证 (Sensors) 7/10 → 差 3 分在哪

### 已有（7 分来源）

| 已有 | 触发时机 | 覆盖范围 |
|------|---------|---------|
| pyright | 编辑 .py 后 | Python 类型错误 |
| tsc | 编辑 .tsx 后 | TypeScript 编译错误 |
| 6 架构测试 | commit 前 | 前后端隔离、NB2 默认、prompt 英文、Pipeline 完整、参考图串行 |
| 4 质量门测试 | commit 前 | 角色 Schema、prompt 语言、.env.example、目录结构 |
| 全量测试 | push 前 | 所有 tests/ |
| Pydantic Schema | Pipeline 运行时 | Stage 2→3 角色数据 + Stage 4→5 分镜数据 |

### 缺口 1：没有服务器端 CI（+1 分）

**问题**: 所有检查都在本地。`git commit --no-verify` 可跳过全部 hook，坏代码直接推到 GitHub。

**案例**: DevOps 在 VPS 上紧急修 bug，`git commit --no-verify && git push`，所有架构测试被跳过，带中文 prompt 的改动推上去了。

**补齐**: GitHub Actions CI — push 到 main 后自动跑 `test_architecture.py` + `test_quality_gates.py`。即使本地跳过，服务器端还有一道关。

### 缺口 2：没有生产环境监控和告警（+1.5 分）

**问题**: 代码部署到 VPS 后，Pipeline 报错、API 调用失败、Gemini 返回 500，没有人知道，直到用户反馈。

**案例**: 某天 Gemini API 配额用完了，所有用户的图片生成全部失败。没有告警，Founder 12 小时后才发现。

**补齐（自建方案，不需要第三方注册）**:
- Pipeline 出错时写入 DB `error_message` 列（已有）
- 新建 `/api/errors/recent` 端点给 PM/Founder 查近期错误
- API 成本计数 — 每次调用记录费用，超阈值写入告警表
- 健康检查定时探测 — 脚本每 5 分钟检测 `prefaceai.mov/api/health`

**Founder 决策**: 现阶段用自建方案，不接 Sentry。等用户量上来再考虑。

### 缺口 3：6 个历史错误模式没有自动化防护（+0.5 分）

**问题**: ERROR_PATTERNS.md 记录了 14 个错误，只有 8 个有 sensor。剩下 6 个仅文档记录。

| EP | 错误 | 为什么还没有 sensor |
|----|------|-------------------|
| EP-005 | Shot 拆分后丢失 characters_in_scene | 需要检查 storyboard 输出的每个 shot |
| EP-006 | 繁简体不匹配导致音画对齐失败 | 需要 alignment 单元测试 |
| EP-007 | 条漫 Gemini 渲染中文乱码 | 需要检查条漫模式 prompt 不含文字指令 |
| EP-009 | IMAGE 编号与 contents 不对应 | 需要 prompt builder 单元测试 |
| EP-013 | JSON 修复不完整 | 需要 JSON 鲁棒性回归测试 |
| EP-014 | confirm-outline 数据未传入 Pipeline | 需要 confirm 数据完整性测试 |

**案例（EP-005）**: Backend 优化 `_split_scene_to_shots()` 但忘了继承 `characters_in_scene`。没有 sensor，代码提交了。用户生成故事时某些 shot 没有角色参考图，角色变脸了。

**补齐**: 给每个 EP 补一个 pytest 测试函数。

---

## 二、代码强制执行 (Computational Control) 6/10 → 差 4 分在哪

### 已有（6 分来源）

| 已有 | 强制什么 |
|------|---------|
| pyright hook | Python 类型必须正确 |
| tsc hook | TypeScript 必须编译通过 |
| PreCommit 架构测试 | 前后端隔离、NB2 默认等 6 条规则 |
| Pydantic Schema | 角色/Shot 数据格式必须合规 |
| StyleEnforcer | 风格关键词必须注入 prompt |

### 缺口 1：Agent 没有文件级权限隔离（+1 分）

**问题**: 所有 agent 共享同一套文件权限。Frontend agent 可以修改 `image_generator.py`，Backend 可以改 `frontend/src/`。

**案例（真实发生过）**: DevOps 擅自修改 PM 的共享文档。Frontend 改了 Backend 文件。每次人工发现和回退。

**补齐**:
- 在各 agent 角色 .md 中明确"可修改文件白名单"
- 写 PreCommit 测试：检查修改的文件是否在白名单内（受 Claude Code 限制，需要知道"谁在操作"）

### 缺口 2：Pipeline 只验证了 2 个转换点，还差 2 个（+1 分）

**问题**: Pydantic 验证只覆盖 Stage 2→3 和 Stage 4→5。

| 转换点 | 有验证吗 | 风险 |
|--------|:-------:|------|
| Stage 1→2（大纲→角色设计） | ❌ | LLM 输出的大纲缺 characters_overview |
| Stage 2→3（角色→剧本） | ✅ | — |
| Stage 3→4（剧本→分镜） | ❌ | 剧本 scenes 数据结构不完整 |
| Stage 4→5（分镜→生图） | ✅ | — |

**案例（Stage 1→2）**: Claude 生成的大纲 JSON 中角色只有 `name` 没有 `description`。Stage 2 设计出来的角色没有明确外貌。如果有 Schema 验证会立刻拦住。

**补齐**: 在 `pipeline_schemas.py` 增加 `OutlineSchema` + `ScreenplaySchema`，在 orchestrator 增加验证调用。

### 缺口 3：LLM 输出没有运行时验证（+1 分）

**问题**: 检查了代码模板（prompt 模板不含中文），但不检查 LLM 实际输出。

**案例**: Stage 4 的 Claude 生成分镜时，image_prompt 里夹带了中文角色名"苏晚"没翻译成英文。代码模板是英文的测试通过了，但运行时输出有中文。

**现状**: ShotSchema 的 image_prompt 中文检测阈值 15% 太宽松，且只在 Stage 4→5 才检测。

**补齐**:
- 收紧 image_prompt 中文检测阈值（15% → 5%，排除合法中文名）
- 每个 Stage 的 LLM 调用返回后立即验证输出格式
- 对 LLM 输出做 output guardrail：必需字段存在、类型正确、值合理

### 缺口 4：没有成本熔断和配额保护（+1 分）

**问题**: 代码中没有防止 API 调用失控的机制。

**案例（真实发生过）**: Backend 的 retry 循环没有退避，Gemini 返回 529 时 1 秒内重试了 84 次（R2 的 529 问题）。如果是 Claude API 按 token 计费，84 次调用可能花 $50+。

**另一个案例**: 如果 bug 导致 20 shots 变成 2000 shots 循环调用，没有任何代码说"超预算了"。

**补齐**:
- API 调用计数器 + 单次 Pipeline 成本上限（Founder 定金额）
- 超过上限自动中止 Pipeline + 告警
- Gemini/Claude 调用的 rate limiter

---

## 三、执行规划

### 涉及的 Agent

| 同事 | 工作项 | 预估 |
|------|--------|------|
| **@devops** | GitHub Actions CI + 健康检查探测 | 1-2 小时 |
| **@backend** | Pipeline Schema 扩展(+2 转换点) + LLM 输出 guardrail + 成本熔断 + 错误查询端点 | 3-4 小时 |
| **@tester** | 6 个 EP 补 sensor + Agent 文件边界测试 | 2 小时 |
| **@ai-ml** | 每个 Stage 的 LLM 输出验证规则定义 | 1 小时 |
| **@pm** | Agent 角色文件增加"可修改文件白名单" | 30 分钟 |

### 执行顺序

```
Phase 1（并行，无依赖）
  ├── @devops: GitHub Actions CI (.github/workflows/ci.yml)
  ├── @tester: 6 EP sensor + Agent 文件边界测试
  ├── @ai-ml: 4 个 Stage 的 LLM 输出验证规则
  └── @pm: 6 个 Agent 角色文件加白名单

Phase 2（并行，部分依赖 Phase 1）
  ├── @backend: Pipeline Schema 扩展（依赖 @ai-ml 的验证规则）
  ├── @backend: 成本熔断 + 配额保护
  └── @devops: 错误查询端点 + 健康检查探测 + 成本计数

Phase 3（收尾）
  ├── @devops: PreCommit hook 更新（加入新测试）
  ├── PM: 审查全部 + HARNESS_HEALTH.md 更新
  └── @devops: push + VPS 部署
```

### 预期成果

| 维度 | V1 完成后 | V2 完成后 |
|------|:--------:|:--------:|
| 自动化验证 | 7/10 | **10/10** |
| 代码强制执行 | 6/10 | **10/10** |
| Guides（前馈） | 9/10 | 9.5/10 |
| 编排设计 | 8/10 | 8.5/10 |

### 待 Founder 确认

1. 成本熔断的单次 Pipeline 上限金额？（建议 $20）
2. 监控方案确认自建（不接 Sentry）
3. 何时开始执行？
