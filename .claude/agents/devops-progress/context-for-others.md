# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-03-06

---

## 当前状态速览

状态: ✅ **VPS 部署完成**，等待 Founder 填入 API Key
域名: `https://prefaceai.mov` 已上线（前端可访问，API 健康检查通过）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

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
- 旧站 prefaceai.net 未受影响 ✅

---

## 待其他 Agent 注意

- **API Key 未填入**: `.env.production` 使用占位符，API 服务能启动但无法调用 AI 模型
- **前端已可访问**: `https://prefaceai.mov` 返回 Landing Page
- **API 已可访问**: `https://prefaceai.mov/api/health` 返回 healthy
- **CORS 仍为全开放**: `allow_origins=["*"]`，后续需限制为 prefaceai.mov
- **代码通过 rsync 部署**: 非 git clone（私有仓库认证问题），后续可配置 deploy key

---

## Git 仓库状态

```
远程仓库: https://github.com/kaiangel/prefaceai-story (private)
分支: main (tracked → origin/main)
最新 commit: 702361d infra: add Docker Compose deployment config
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-06 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **已部署**（等待 API Key） | 2026-03-06 |
