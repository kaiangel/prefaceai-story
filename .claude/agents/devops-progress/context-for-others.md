# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-03-16

---

## 当前状态速览

状态: ✅ **VPS 已更新部署 (TASK-DEPLOY-R8B)** — N13-FIX + IMG-SAFETY + BRAND + LOGO 全部推送 + 部署
域名: `https://prefaceai.mov` 已上线（前端 + API + 新 logo + V2 品牌宣言）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

---

## 最近部署 (2026-03-16)

### TASK-DEPLOY-R8B

**部署内容**:
1. N13-FIX: spouse_of 对称关系自动补全
2. IMG-SAFETY-RETRY: 场景/角色参考图 CONTENT_SAFETY 恢复机制 (L1+L2+L3a+L3b)
3. AI-ML: 5 类 75 词条安全替换 + 场景/角色改写模板 + "No people" 前置
4. T-J: 测试脚本 N12/N14/N15 bug 修复
5. BRAND-MANIFESTO: Pipeline V2 slogan + About V2 宣言 + 技术基座段
6. LOGO-REPLACE: 全站 Sparkles→Image logo + favicon 更新 + 19 brand PNGs

**Git**: 3 commits pushed → `ec3b4fd` (main)
**Docker**: api + frontend 容器重建 + 重启

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
- **CORS 仍为全开放**: `allow_origins=["*"]`，后续需限制为 prefaceai.mov
- **代码通过 rsync 部署**: 非 git clone，后续可配置 deploy key
- **SSH 端口 58913**: 非默认 22

## 运维风险摘要 (详见 devops-progress/current.md)

| 风险 | 级别 | 关键时间点 |
|------|------|-----------|
| API Key 未填入 | 🔴 P0 | Founder 决定时 |
| CORS 全开放 | 🟡 P1 | API Key 填入前必须修 |
| 无 CI/CD | 🟡 P1 | 部署稳定后 |
| 无监控告警 | 🟡 P1 | 第一个用户前 |
| 无数据备份 | 🟡 P2 | 有生产数据后 |
| 无日志脱敏 | 🟡 P2 | API Key 填入前必须修 |

---

## Git 仓库状态

```
远程仓库: https://github.com/kaiangel/prefaceai-story (private)
分支: main (tracked → origin/main)
最新 commit: ec3b4fd docs: agent progress + team-brain sync + R8 E2E + IMG-SAFETY-VERIFY test scripts
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-16 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **已部署**（等待 API Key） | 2026-03-16 |
