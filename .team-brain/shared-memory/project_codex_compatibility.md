---
name: Codex 与 Claude Code 兼容性分析
description: OpenAI Codex CLI 与 Anthropic Claude Code 在序话Story 项目中的兼容性技术分析，用于所有涉及双工具协作的决策
type: reference
---

## OpenAI Codex CLI 概述

- **官方仓库**: https://github.com/openai/codex
- **驱动模型**: GPT-5.3-codex（专为软件工程优化）
- **快速变体**: GPT-5.3-Codex-Spark（ChatGPT Pro 用户可用）
- **形态**: 终端全屏 UI，可读取仓库、编辑文件、运行命令
- **安全模式**: 三种审批模式（只读/建议/完全访问）
- **平台**: macOS, Windows, Linux
- **订阅**: ChatGPT Plus/Pro/Business/Edu/Enterprise
- **特性**: 多步骤跨文件修改、命令执行、结果验证、内置 web 搜索

## 与 Claude Code 的关键差异

| 维度 | Claude Code | Codex CLI |
|------|------------|-----------|
| 模型 | Claude Opus 4.6 (1M context) | GPT-5.3-codex |
| 上下文文件 | `CLAUDE.md`（自动读取） | `AGENTS.md` 或自定义指令文件 |
| Agent 系统 | `.claude/agents/*.md` 原生多角色 | 无原生多角色，可通过多终端+不同指令模拟 |
| Session 恢复 | `--resume <session-id>` | 有类似机制 |
| 持久记忆 | `.claude/projects/*/memory/` 自动加载 | 无等价物 |
| 技能系统 | `/skill` 内置 + 用户自定义 | Agent Skills 系统 |
| 子代理 | 支持 Agent 工具调用子代理 | 未知 |

## 项目中的实际影响

### Ben 用 Codex 可以做的
- 读取仓库中所有文件（包括 CLAUDE.md, .team-brain/, progress 文件）
- 创建/编辑/删除文件
- 运行命令（git, python, npm 等）
- 搜索代码库
- 理解项目结构和代码逻辑

### Ben 用 Codex 不能自动做的（需要手动或额外配置）
- 自动读取 CLAUDE.md 作为项目上下文（需在 Codex 中手动指定或创建 CODEX.md）
- 使用我们的 Agent 角色定义体系
- 跨 session 保持持久记忆
- 自动更新 progress 文件

### 解决方案
1. 创建 `.team-brain/team_ben/CODEX.md` — Codex 启动时可以指定读取此文件
2. `.team-brain/team_ben/` 目录 — 存放 Ben 的 Agent instruction 文件和进度文件
3. Ben 需要时手动让 Codex 读取特定文档（如 TEAM_CHAT.md、DECISIONS.md）
4. Progress 更新由 Ben 手动完成或通过 TEAM_CHAT 通知
