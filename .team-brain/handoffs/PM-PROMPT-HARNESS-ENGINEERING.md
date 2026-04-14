# PM Agent 启动 Prompt — Harness Engineering V1

> 将以下内容完整复制粘贴到 PM Agent 的 session 中

---

## Prompt 开始

@pm，Founder/Coordinator 给你一个 P0 级别的新任务：**序话Story Harness Engineering 升级**。

### 背景速览

Harness Engineering 是 2026 年 AI 工程领域最重要的概念。核心公式：`Agent = Model + Harness`。决定 AI agent 成败的不是模型本身，而是包裹模型的系统——工具配置、验证循环、权限控制、自动化检查等。

经过独立审计，我们的 Harness 现状是 **严重偏科**：
- Guide（前馈控制/文档规则）：**8.5/10**——claude.md、agent 定义、协议做得很好
- Sensor（反馈控制/自动化验证）：**4/10**——几乎没有自动化检查，全靠人手动

这意味着我们"写了完美的规则手册，但办公室没装门禁和监控"。行业实证表明，加自动化 Sensor 是投入产出比最高的改动（OpenAI 靠这一招让 3 人团队写了 100 万行代码）。

### 你的任务

**仔细阅读** `.team-brain/handoffs/TASK-HARNESS-ENGINEERING-V1.md`，这是 Founder 批准的完整任务书，包含：

1. **6 个缺陷的修复方案**：
   - 缺陷1: 没有自动化验证循环（Sensor 最大缺口）→ 加 PostToolUse/PreCommit/PrePush hooks
   - 缺陷2: 所有 Agent 共享同一套权限（无角色隔离）→ 架构测试强制前后端隔离 + agent 文件白名单
   - 缺陷3: TEAM_CHAT.md 已 35,178 行（定时炸弹）→ 自动归档机制
   - 缺陷5: 错误修复没有系统化沉淀 → ERROR_PATTERNS.md + 工程化防护追踪
   - 缺陷6: 没有上下文预算管理 → 各角色分级阅读清单
   - 缺陷7: Hooks 严重不足（只有 1 个）→ 加 pyright/tsc/PreCommit/PrePush 共 4 个新 hook
2. **Pipeline 翻译层优化方案**（Can Boluk 式 A/B 测试 + Pydantic Schema 验证）
3. **OpenAI Codex 式结构性测试方案**（架构适应度测试 + 质量门测试）
4. **Bockeler 框架的三大调节领域改进**（可维护性 + 架构适应度 + 行为）
5. **9 个具体子任务**，已分配到 @devops、@tester、@ai-ml、@backend、以及你自己
6. **4 个 Phase 的执行顺序和依赖关系**
7. **成功标准**（Sensor 从 4/10 提升到 7/10）

### 你需要做的

1. **读完** TASK-HARNESS-ENGINEERING-V1.md 全文
2. **立即派发 Phase 1 的两个 P0 任务**：
   - **TASK-HE-DEVOPS-1**（hooks 配置升级）→ @devops
   - **TASK-HE-TESTER-1**（架构测试 + 质量门测试）→ @tester
   - 这两个可以**并行执行**
3. **在 TEAM_CHAT.md 追加公告**，通知全团队 Harness Engineering 升级已启动
4. **在 TODAY_FOCUS.md 更新**，加入 TASK-HARNESS-ENGINEERING-V1 相关内容
5. **派发时**，把任务书中每个子任务的"具体任务"和"验收标准"完整传达给对应 agent，不要省略细节
6. Phase 1 完成后，继续推进 Phase 2（PM 自己的 PM-1、PM-2 + DEVOPS-2）
7. Phase 2 完成后，推进 Phase 3（AIML-1 + BACKEND-1）
8. 全部完成后，创建 HARNESS_HEALTH.md（PM-3）

### 派发模板

给每个 agent 派发任务时，使用以下格式：

```
@{agent}，新任务 TASK-HE-{AGENT}-{N}：{标题}

优先级：P{X}
预计工作量：{估计}

背景：{为什么要做这个}

具体任务：
{从 TASK-HARNESS-ENGINEERING-V1.md 中完整复制该 agent 的任务描述}

验收标准：
{从 TASK-HARNESS-ENGINEERING-V1.md 中完整复制验收标准}

完成后：
1. 更新你的 {agent}-progress/ 三文件
2. 在 TEAM_CHAT.md 追加完成报告
3. 通知 @pm review

⚠️ 干活前：仔细阅读群聊最新消息 + 相关文档，确保理解上下文。
⚠️ 干完后：double check 更新群聊、progress 文件。文档未更新 = 任务未完成。
```

### 关键提醒

- **不要跳过 Phase**：Phase 1 的 hooks 和测试是基础设施，Phase 2-3 依赖它们
- **测试代码是框架**：TASK-HE-TESTER-1 中提供的 Python 代码是方向和框架，@tester 需要根据实际代码结构调整具体断言逻辑
- **PreCommit hook 的安全启动**：先用 `|| true` 防止未创建测试时阻塞所有提交，等 @tester 的测试文件就绪后再激活
- **PM-1（错误模式追踪）是核心**：回顾 DECISIONS.md、KEY_LEARNINGS.md、TEAM_CHAT 历史中的所有 bug/错误决策，至少记录 10 个
- **改完后跑一次全量验证**：确认所有 hooks 生效、所有测试通过、TEAM_CHAT 归档正常

立即开始，先读 TASK-HARNESS-ENGINEERING-V1.md。
