# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-03-10

---

## 当前状态速览

状态: ✅ **VPS 已更新部署** — 最新代码已推送 + 部署
域名: `https://prefaceai.mov` 已上线（前端 + API + 静态资源全部正常）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

---

## 最近部署 (2026-03-10)

### TASK-DEPLOY-UPDATE

**部署内容**:
1. E2E R2/R3 pipeline fixes (T1-T16 + backup model Flash + NB2 rename)
2. TASK-GCLOUD-OPT (Google Cloud 申请优化)
3. Contact 页面更新 (微信/地址)
4. TASK-STYLE-THUMBNAILS 集成 (15 种风格缩略图)
5. 团队照片 + 产品 Demo 视频
6. Agent progress + team docs 同步

**Git**: 3 commits pushed → `232f2f0` (main)
**Docker**: frontend + api 容器重建 + 重启

**新增静态资源**:
- `/styles/*.jpg` — 15 张风格缩略图 (400×400 JPEG, ~1MB)
- `/team/*.jpg` — 3 张团队照片
- `/demo.mp4` — 产品 Demo 视频

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
- **前端已可访问**: `https://prefaceai.mov` 返回 Landing Page（含风格缩略图、团队照片、Demo 视频）
- **API 已可访问**: `https://prefaceai.mov/api/health` 返回 healthy
- **CORS 仍为全开放**: `allow_origins=["*"]`，后续需限制为 prefaceai.mov
- **代码通过 rsync 部署**: 非 git clone（私有仓库认证问题），后续可配置 deploy key

---

## Git 仓库状态

```
远程仓库: https://github.com/kaiangel/prefaceai-story (private)
分支: main (tracked → origin/main)
最新 commit: 232f2f0 docs: agent progress + team-brain sync + E2E R2/R3 test scripts
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-10 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **已部署**（等待 API Key） | 2026-03-10 |
