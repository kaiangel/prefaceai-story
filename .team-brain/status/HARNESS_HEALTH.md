# Harness 健康度看板

> 上次更新: 2026-04-14
> 更新者: PM
> 更新频率: 每周一次，或每个重大 TASK 完成后

---

## Sensor 覆盖率

| 架构规则 | 文档记录 (Guide) | 自动化测试 (Sensor) | Hook 强制 |
|---------|:---:|:---:|:---:|
| Shot 用 NB2 模型（默认） | ✅ claude.md | ✅ test_architecture | — |
| Image prompt 纯英文 | ✅ claude.md | ✅ test_architecture + test_quality_gates | — |
| 参考图串行生成 (portrait→fullbody) | ✅ claude.md | ✅ test_architecture | — |
| 前后端代码隔离 | ✅ TEAM_PROTOCOL | ✅ test_architecture | — |
| Pipeline 5 阶段文件完整 | ✅ claude.md | ✅ test_architecture | — |
| .env.example 存在 | — | ✅ test_quality_gates | — |
| 项目目录结构完整 | — | ✅ test_quality_gates | — |
| Story JSON Schema 合规 | ✅ claude.md | ✅ test_quality_gates | — |
| Python 类型安全 | — | — | ✅ pyright PostToolUse hook |
| TypeScript 编译安全 | — | — | ✅ tsc PostToolUse hook |
| 提交前测试 | — | ✅ test_architecture + test_quality_gates | ✅ PreCommit hook |
| 推送前全量测试 | — | ✅ tests/* | ✅ PrePush hook |

**覆盖率**: 12 条规则，10 条有自动化 Sensor，2 条仅有 Hook

---

## 错误模式防护率

> 详见 `.team-brain/knowledge/ERROR_PATTERNS.md`

- 已记录错误模式: **14 个**
- 有工程化防护 (Sensor/Hook): **8 个** ✅
- 仅文档记录: **6 个** ❌
- **防护率**: **57%**

### 无防护的错误模式（需后续补 Sensor）

| EP | 错误 | 建议的 Sensor |
|----|------|--------------|
| EP-005 | Shot 拆分后丢失 characters_in_scene | test_quality_gates 检查 storyboard 输出 |
| EP-006 | 繁简体不匹配 | alignment 单元测试 |
| EP-007 | 条漫 Gemini 渲染中文乱码 | 检查条漫模式 prompt 不含文字指令 |
| EP-009 | IMAGE 编号与 contents 不对应 | prompt builder 单元测试 |
| EP-013 | JSON 引号修复不完整 | JSON 鲁棒性回归测试 |
| EP-014 | confirm-outline 数据未传入 Pipeline | confirm 数据完整性测试 |

---

## 上下文预算

> 详见 `TEAM_PROTOCOL.md` "上下文预算管理" 章节

| Agent | 必读文件数 | 估计 token | 状态 |
|-------|:---------:|:---------:|:----:|
| Backend | 4 | ~3,000 | 🟢 |
| Frontend | 4 | ~3,000 | 🟢 |
| AI-ML | 4 | ~3,000 | 🟢 |
| Tester | 5 | ~3,500 | 🟢 |
| DevOps | 3 | ~2,000 | 🟢 |
| PM | 8+ | ~6,000 | 🟡 需关注 |

---

## TEAM_CHAT 文件状态

| 指标 | 值 |
|------|-----|
| 当前行数 | 2,387 |
| 上次归档 | 2026-04-14 |
| 归档月份 | 4 个 (2026-01 ~ 2026-04) |
| 归档脚本 | `scripts/archive_team_chat.sh` |
| 状态 | 🟢 健康 (< 3,000 行) |

---

## Harness 评分

| 维度 | 改前 | 改后 | 目标 |
|------|:----:|:----:|:----:|
| Guides（前馈） | 8.5/10 | **9/10** | 9/10 ✅ |
| Sensors（反馈） | 4/10 | **7/10** | 7/10 ✅ |
| 计算性控制 | 3/10 | **6/10** | 6/10 ✅ |
| 编排设计 | 7.5/10 | **8/10** | 8/10 ✅ |

---

## Phase 3 完成

| # | 任务 | 负责 | 状态 |
|---|------|------|:----:|
| TASK-HE-AIML-1 | Prompt Format A/B Test 分析 | @ai-ml | ✅ 推荐 B'（-38% token） |
| TASK-HE-BACKEND-1 | Pipeline Pydantic Schema 验证 | @backend | ✅ Stage 2→3 + Stage 4→5 |

## A vs B' 盲测实验结果 (2026-04-14)

| 指标 | A (当前) | B' (压缩标签) |
|------|:--------:|:------------:|
| 平均 prompt 字符数 | ~7100 | ~3800 (**-46%**) |
| Founder 偏好次数 (10 shots) | 4 | **5** |
| PM 偏好次数 (10 shots) | 3 | **4** |
| 角色一致性 | 稳定 | 稳定 |
| 风格漂移 | 零 | 零 |

**结论**: B' 质量等价于 A，省 46% token。差异为随机噪声，非格式导致。**B' 可作为默认格式切换。**

## 待办（后续优化）

| # | 任务 | 说明 |
|---|------|------|
| B' vs D+ 对比测试 | 验证更极端的压缩（-57% token）是否仍等价 |
| B' 切换为默认格式 | 需 Backend 修改 prompt 组装逻辑 |
| EP-005~014 补 Sensor | 6 个仅文档记录的错误模式需补自动化防护 |
