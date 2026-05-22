# Backend 契约改动 Pre-commit Hook

## 为什么有这个 Hook

**背景**：test15 e2e（2026-05-13）暴露 13 个真实 bug，其中 7 个（47%）属于"前后端契约断裂"模式 —— backend 改了 API response 格式或阶段状态，frontend 没有同步更新，导致用户看到转圈、404、错误状态显示等 P0 问题。

**合伙人 Ben（2026-05-13 15:42）建议**：建立一种纠错机制，backend 改过功能后主动询问是否需要对应修改 frontend。Founder 采纳，记录为 DEC-030。

**这个 hook 的作用**：当 backend 改动以下高风险契约文件时，强制要求 commit message 带 `[frontend-impact: yes/no]` 标签，迫使开发者在 commit 时**有意识地判断**是否影响 frontend 契约，而不是让契约断裂悄悄埋下。

监控的文件（backend 契约高风险区）：
- `app/api/projects.py` — Projects API 端点
- `app/api/chapters.py` — Chapters API 端点（含 status response）
- `app/services/pipeline_orchestrator.py` — Pipeline 阶段状态更新
- `app/services/job_manager.py` — Job 状态管理
- `app/models/project.py` — 数据模型
- `app/schemas/project.py` — API Schema

---

## 如何安装

在项目根目录运行：

```bash
bash scripts/install_pre_commit_hook.sh
```

这会创建一个软链接 `.git/hooks/pre-commit -> scripts/pre-commit-frontend-impact.sh`。

**验证安装成功**：

```bash
ls -la .git/hooks/pre-commit
# 应显示: .git/hooks/pre-commit -> .../scripts/pre-commit-frontend-impact.sh
```

每个开发 agent 或团队成员在克隆或新建工作目录后都需要运行一次安装脚本（`.git/hooks/` 目录不被 git 追踪，不会自动同步）。

---

## 如何使用

当你修改了上述任意一个被监控的文件并执行 `git commit` 时，hook 会自动检测并要求你在 commit message 里加上 label：

```
[frontend-impact: yes]   # 此改动影响 frontend 契约，frontend agent 需要同步
[frontend-impact: no]    # 此改动为内部逻辑，不影响 frontend 契约
```

**合格的 commit message 示例**：

```
fix: chapters.py regenerate endpoint update failed_shot_count [frontend-impact: yes]

feat: pipeline_orchestrator.py add internal retry queue for image generation [frontend-impact: no]
```

**判断标准**（参考 DEC-030）：
- 改了 API response 的字段名/类型/结构 → `yes`
- 新增或删除了 API 端点 → `yes`
- 改了 pipeline stage 的枚举值或状态机 → 大概率 `yes`
- 仅改了内部逻辑（队列顺序、retry 次数、日志）且 response schema 不变 → `no`
- 不确定时选 `yes`，总比漏通知强

当标为 `[frontend-impact: yes]` 时，请同步在 `.team-brain/TEAM_CHAT.md` 通知 frontend agent 查看变更。

---

## 如何临时跳过

```bash
git commit --no-verify -m "your message"
```

**强烈不建议**跳过。这个 hook 是轻量提示机制，不是性能瓶颈。绕过它的每一次，都是在重新拉开契约断裂的风险。

如果你有合理理由跳过（如纯文档改动、测试脚本、非监控文件），请在 commit message 里说明原因，方便后续 review。

---

## 技术细节

hook 脚本位置：`scripts/pre-commit-frontend-impact.sh`

工作原理：
1. `git diff --cached --name-only` 获取 staged 文件列表
2. 逐一检查是否与 WATCHED_FILES 数组匹配
3. 无命中 → `exit 0`（直接放行）
4. 有命中 → 读取 `.git/COMMIT_EDITMSG`（git 已写入 commit message）
5. 用正则 `\[frontend-impact: (yes|no)\]` 检查 label 存在性
6. label 存在 → `exit 0`（放行）
7. label 不存在 → 打印错误 + `exit 1`（block commit）

**决策文档**：`.team-brain/decisions/DECISIONS.md` DEC-030

**分析依据**：`.team-brain/analysis/TEST15_DEEP_AUDIT_2026-05-13.md` B 章节（Ben 建议落地方案）
