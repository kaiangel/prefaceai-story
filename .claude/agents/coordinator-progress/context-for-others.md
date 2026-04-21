# Coordinator — 其他 Agent 需要知道的

> 最后更新: 2026-04-13

## 项目总体状态

**R6 Founder 实测通过 + Harness V2 工程化完成 + Prompt B' 默认化**

### 团队组成
- **Founder 团队**: Coordinator + PM + Backend + AI-ML + Frontend + Tester + DevOps + Resonance (8个 Claude Code Agent)
- **Ben 团队**: backend_Ben + frontend_Ben + pm_Ben (3个 Codex Agent)

### 基础设施
- 网站: https://prefaceai.mov 在线
- API Key: 4/6 已填（TTS 2 个 key 即将填入）
- CI/CD: ✅ GitHub Actions 上线 (`.github/workflows/ci.yml`)
- TEAM_CHAT: 已按月归档到 `.team-brain/chat-archive/`
- 最新 commit: ea0edb1 (2026-04-15)

### 新增文件（3.23 以来）
| 文件 | 说明 |
|------|------|
| `app/api/monitoring.py` | 监控端点（错误/成本） |
| `app/models/api_cost_log.py` | 成本日志模型（表待建） |
| `app/prompts/shot_adjustment_prompt.py` | Haiku 调整 prompt |
| `.github/workflows/ci.yml` | GitHub Actions CI |
| `scripts/health_check.sh` | 健康检查脚本 |
| `docs/API_COST_CALCULATION.md` | API 成本 V5（官方定价） |
| `.claude/skills/music-prompt/` | 音乐 prompt 技能 |

### 互相只读规则
- **不修改** `.team-brain/team_ben/` 下的任何文件

### 待定事项（等 Founder 决策）
- Resonance 新时间线（旧的 Phase 0/1/2 日期已清理）
- 续写模式 Phase 3 #11 是否开始设计
- api_cost_logs 表需要建

## 各 Agent 无需改变工作方式
Ben 团队的加入不影响 Founder 团队日常工作流。文件在 `.team-brain/team_ben/`，互相只读。
