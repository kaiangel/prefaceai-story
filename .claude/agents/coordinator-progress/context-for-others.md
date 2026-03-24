# Coordinator — 其他 Agent 需要知道的

> 最后更新: 2026-03-19 14:00

## 项目总体状态

**双团队协作模式已启动** (2026-03-19)

### 团队组成
- **Founder 团队**: Coordinator + PM + Backend + AI-ML + Frontend + Tester + DevOps + Resonance (8个 Claude Code Agent)
- **Ben 团队**: backend_Ben + frontend_Ben + pm_Ben (3个 Codex Agent)

### 主线状态
- Pipeline 主线 + 并行线全部完成已部署 (commit c6d697a)
- 安全加固: CORS + 日志脱敏 已派发 @Backend
- 等待 Founder 填 API Key

### 新增文件（所有 Agent 需知）
| 文件 | 说明 | 权限 |
|------|------|------|
| `.team-brain/team_ben/CODEX.md` | Ben 的 Codex 上下文 | 我们只读 |
| `.team-brain/team_ben/TEAM_CHAT.md` | Ben 团队群聊 | 我们只读 |
| `.team-brain/team_ben/` | Ben 的 Agent 文件 | 我们只读 |
| `.team-brain/shared-memory/` | 双团队共享记忆 | 双方可读 |

### 互相只读规则
- **不修改** `.team-brain/team_ben/` 下的任何文件

## @PM 当前任务
- 更新 TEAM_PROTOCOL.md 加入双团队协作规则
- CORS + 日志脱敏 的 Backend 完成后做 Code Review
- 等 Founder 填 API Key 后协调验证

## 各 Agent 无需改变工作方式
Ben 团队的加入不影响 Founder 团队的日常工作流。你只需要知道:
1. Ben 团队存在，文件在 `.team-brain/team_ben/`
2. 他们有自己的群聊 `.team-brain/team_ben/TEAM_CHAT.md`
3. 互相只读，不要动对方的文件
