# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-03-19

---

## 当前状态速览

状态: ✅ **Frontend Batch 1A-4 全部 push 完成**（两人直接 push main，无分支保护）
域名: `https://prefaceai.mov` 已上线（前端 + API + 新 logo + V2 品牌宣言）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

---

## 最近操作 (2026-03-22)

### Frontend Batch 3+4 push ✅

3 commits pushed → `origin/main` (8d51108 → 8ab7057):

| Commit | 内容 | 文件数 |
|--------|------|--------|
| `5f55e57` | feat(frontend): Batch 3 — story input (OCR, voice, templates) + skeleton | 2 |
| `d37b4e5` | feat(frontend): Batch 4 — membership tiers + aspect ratio + pricing | 4 |
| `8ab7057` | docs: agent progress + team-brain sync | 9 |

**VPS**: 不需要部署（纯前端改动）

### Frontend Batch 1A+1B+2 push ✅ (earlier today)

3 commits pushed → `origin/main` (20641ac → 9c29aa6):

| Commit | 内容 | 文件数 |
|--------|------|--------|
| `336a646` | feat(frontend): Batch 1A+1B — Create preview + MVP auth + settings | 10 |
| `955f45d` | feat(frontend): Batch 2 — Dashboard enhancements | 11 |
| `9c29aa6` | docs: agent progress + team-brain sync | 13 |

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
最新 commit: 8ab7057 docs: agent progress + team-brain sync (Batch 3+4 review pass + DevOps push status)
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-19 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **安全加固已部署**（等待 API Key） | 2026-03-18 |
| git | ✅ 双团队文件已推送（两人直接 push main） | 2026-03-19 |
