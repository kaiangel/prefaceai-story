# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-04-01

---

## 当前状态速览

状态: ✅ **REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX push + VPS 部署完成**
域名: `https://prefaceai.mov` 已上线（前端 + API + 新 logo + V2 品牌宣言）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate

---

## 最近操作 (2026-04-01)

### REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX push + VPS 部署 ✅

3 commits pushed → `origin/main` (3a437bd → d7eb28c):

| Commit | 内容 |
|--------|------|
| `2520fc5` | feat(backend): TASK-JSON-REPAIR-V3 状态机 + LOGGING-FIX 增强 |
| `029841a` | feat(frontend): TASK-OUTLINE-PROGRESS 大纲生成进度页面 |
| `d7eb28c` | docs: agent progress + team-brain sync |

**VPS 部署**:
- SCP 关键代码文件 + Docker rebuild (api + frontend) → force-recreate
- 权限修复: Docker alpine 容器修复文件所有权
- `https://prefaceai.mov` 前端 200 ✅ + API `/health` healthy ✅
- DB 驱动: `asyncmy`（不变）

### Earlier (2026-03-30): 大纲生成全链路 push + Ben 融合 + VPS 部署 ✅

3 commits pushed + merge → `origin/main` (9ca87bc → 8b5c36a):

| Commit | 内容 |
|--------|------|
| `56aa22b` | feat: 大纲生成全链路打通 — logging 标准化 + JSON 鲁棒性 + 诊断埋点 |
| `c37d392` | docs: 大纲生成里程碑 — LOGGING-FIX + Ben 反馈 + team-brain sync |
| `8b5c36a` | merge: 融合 Ben int-id+uuid 重构 |

**VPS 部署**:
- rsync → Docker rebuild (api + frontend) → force-recreate
- `.env.production` 真实 API Key 已填入（Gemini + Anthropic + OpenAI + 火山引擎）
- DB 驱动: `asyncmy`（与 Ben 一致）
- `https://prefaceai.mov` 前端 200 ✅ + API `/health` healthy ✅
- Founder + Ben 可直接在线联调

### Earlier (2026-03-29): 6 TASK + REPAIR-V2 + PERSISTENT-LOG

Multiple pushes — 10 commits total (faf594f → 77ef5f9)

| Commit | 内容 |
|--------|------|
| `3975901` | fix(frontend): TASK-AUTH-RESILIENCE — silent logout on 401 |
| `3b55f4d` | fix(backend): TASK-JSON-REPAIR — unescaped quotes in LLM JSON |
| `cdc2d22` | fix: TASK-DOC-ONLY-FIX + TASK-DOC-FORMAT — document-only upload |
| `171803f` | feat(frontend): TASK-STYLE-PRIORITY — custom style priority + UX |
| `9ea6014` | feat(backend): TASK-DEBUG-LOGGING — 7 diagnostic log points |
| `0ed98de` | docs: 6 TASK completions + team-brain sync |

**VPS**: 不需要部署。

### TASK-SHARED-DB ✅ (2026-03-27)

切换到阿里云共享 MySQL (101.132.69.232:3306/prefacestory)。本地 Docker 已停。

### Phase 1+2 全部 push ✅ (2026-03-26)

4 commits pushed → `origin/main` (40ca049 → dc6ef0d):

| Commit | 内容 | 文件数 |
|--------|------|--------|
| `673a907` | feat(frontend): 13 new style thumbnails (28 total) | 14 |
| `1bbfebf` | feat(backend): Phase 2 — image analysis + seed refs + dynamic style | 18 |
| `408ae6a` | feat(frontend): Phase 2 — real image analysis + 28 styles + uploaders | 10 |
| `dc6ef0d` | docs: Phase 1+2 complete — agent progress + team-brain sync | 16 |

**VPS**: 不需要部署。

### Earlier (2026-03-24): ENVVAR-FIX + LLM-FIX + MySQL + Stage 1

Multiple pushes — Stage 1 E2E 联调通过。

### MySQL 搭建 + Stage 1 pipeline push ✅ (earlier)

**本地 MySQL**: Docker `mysql:8.0` on port 3306, 11 tables auto-created, `/health` healthy

4 commits pushed → `origin/main` (d1d2705 → ef4acca):

| Commit | 内容 | 文件数 |
|--------|------|--------|
| `5dec834` | feat(ai-ml): Stage 1 prompt upgrade — summary, endings, mood, char fields | 1 |
| `33f4725` | feat(backend): Stage 1 generate-outline API + MySQL model fixes | 3 |
| `e063b23` | feat(frontend): Stage 1 real API integration | 1 |
| `ef4acca` | docs: Stage 1 progress + MySQL setup + team-brain sync | 18 |

**VPS**: 不需要部署（本地联调阶段）

### Earlier today: register fix + Resonance + Ben pull

- `7b973fc` + `da291e0`: register fix + Resonance agent + marketing skills (186 files)
- `e4ada3e`: Ben MySQL user flows (git pull + TEAM_CHAT 冲突解决)

### Frontend review fixes + text-gen hint push ✅ (2026-03-23)

2 commits (a2f61f0 + afeae40), 866ea71 → afeae40

### Frontend Batch 1A-4 push ✅ (2026-03-22)

8 commits total (Batch 1A+1B+2+3+4 code + docs), 20641ac → 8ab7057

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
- **🚨 部署方式（Ben 强制要求）**: 发布到 VPS 必须用 **rsync 本地代码 + Docker rebuild**，**不要在服务器上 git pull**
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
最新 commit: 8b5c36a merge: 融合 Ben int-id+uuid 重构
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-19 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **安全加固已部署**（等待 API Key） | 2026-03-18 |
| git | ✅ 双团队文件已推送（两人直接 push main） | 2026-03-19 |
