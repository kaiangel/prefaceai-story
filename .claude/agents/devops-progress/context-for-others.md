# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-03-19

---

## 当前状态速览

状态: ✅ **双团队协作文件已推送 + main 分支保护已启用**
域名: `https://prefaceai.mov` 已上线（前端 + API + 新 logo + V2 品牌宣言）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

---

## 最近操作 (2026-03-19)

### TASK-GIT-PUSH-DUAL-TEAM ✅

**Git**: `33eaac6` pushed → `origin/main` (59 files, Ben onboarding)
**VPS**: 不需要部署（开发协作文档）
**Ben 可 git pull 获取全部内容**

### ✅ TASK-GIT-BRANCH-PROTECTION 完成

Founder 升级 GitHub Pro → main 分支保护已启用:
- 必须通过 PR 合并，禁止直接 push ✅
- 管理员也受约束 ✅
- 禁止 force push + 禁止删除 ✅
- PR #1 验证通过 ✅

**新工作流**: `founder/xxx` 或 `ben/xxx` 分支 → PR → 合并 main

---

## 已完成的部署

### 基础设施
- Swap 4GB ✅
- Docker 28.1.1 + Compose v2.35.1 ✅
- FFmpeg 4.2.7 ✅
- trader 用户已加入 docker 组 ✅

### 容器
- redis:7-alpine — 内部 6379，健康检查 PONG ✅
- api (Python 3.11 + Uvicorn) — 127.0.0.1:8000，`/health` 正常 ✅
- frontend (Next.js 14 standalone) — 127.0.0.1:3000，200 OK ✅
- worker (Celery) — profiles: ["celery"]，初始不启动 ✅

### Nginx HTTPS
- HTTP 80 → 301 HTTPS ✅
- HTTPS 443 + Origin Certificate ✅
- `/api/` → :8000 (proxy_read_timeout 300s) ✅
- `/` → :3000 ✅
- 安全头 (HSTS, X-Frame-Options, etc.) ✅
- Cloudflare 真实 IP 还原 ✅

---

## 待其他 Agent 注意

- **API Key 未填入**: `.env.production` 使用占位符，API 服务能启动但无法调用 AI 模型
- **前端已可访问**: `https://prefaceai.mov` 返回 Landing Page（V2 品牌宣言 + 新 logo + 风格缩略图）
- **API 已可访问**: `https://prefaceai.mov/api/health` 返回 healthy
- **CORS 已限制**: `allow_origins=["https://prefaceai.mov", "http://localhost:3000"]` ✅
- **代码通过 rsync 部署**: 非 git clone，后续可配置 deploy key
- **SSH 端口 58913**: 非默认 22

## 运维风险摘要 (详见 devops-progress/current.md)

| 风险 | 级别 | 关键时间点 |
|------|------|-----------|
| API Key 未填入 | 🔴 P0 | Founder 决定时 |
| ~~CORS 全开放~~ | ✅ 已解决 | 03-18 部署 |
| 无 CI/CD | 🟡 P1 | 部署稳定后 |
| 无监控告警 | 🟡 P1 | 第一个用户前 |
| 无数据备份 | 🟡 P2 | 有生产数据后 |
| ~~无日志脱敏~~ | ✅ 已解决 | 03-18 部署 |

---

## Git 仓库状态

```
远程仓库: https://github.com/kaiangel/prefaceai-story (private)
分支: main (tracked → origin/main)
最新 commit: 33eaac6 feat: dual-team collaboration system — Ben team onboarding
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-19 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **安全加固已部署**（等待 API Key） | 2026-03-18 |
| git | ✅ 双团队文件已推送 + main 分支保护已启用 | 2026-03-19 |
