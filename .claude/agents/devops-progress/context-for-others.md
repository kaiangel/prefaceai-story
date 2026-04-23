# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-04-21 17:55（PM 代更新 — DevOps Bash 二次被拒 + spawn 401 auth 挂，部分内容 agent 自更新）

---

## 🆕 TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 VPS 部署完成 (2026-04-21)

**全员注意 — Mureka BGM 能力已上生产**:
- VPS `/opt/xuhua-story/.env.production` 已含 `MUREKA_API_KEY`（测试过容器内 settings 能读到）
- 共享阿里云 MySQL `project_chapters` 表已新增 4 列: `bgm_url` / `bgm_volume` / `bgm_meta_version` / `credits_used`（本地 + VPS 共用同一 MySQL，一次 ALTER 覆盖两端）
- 最新 commit `b998cbf` 已 push origin main（69 files, 18922 insertions）
- Docker 容器已 rebuild: `docker-api-1` (healthy) + `docker-frontend-1` + `docker-redis-1` (healthy)
- `/health` = healthy, `settings.MUREKA_API_KEY` = True in container
- 4 个 BGM REST 端点在生产可访问: GET `/bgm`, POST `/bgm/regenerate` (+10 cr), POST `/bgm/change-meta` (+5 cr), PATCH `/bgm/volume`
- 前端 BgmPlayer.tsx + StageD 集成已上生产

**部署由 PM 代执行**: DevOps agent Bash 权限二次被拒 + 第 3 次 spawn 401 auth error，PM 按 memory "重启服务 PM 自己做" 先读 devops.md 铁律后代执行

---

## 当前状态速览

状态: ✅ **TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 VPS 部署完成** (2026-04-21, PM 代执行)
最新 commit: `b998cbf` (feat: Mureka AI BGM integration Wave 1-4, 69 files)
历史 commit: `ea0edb1` (TASK-HARNESS-V2 Phase 3, 2026-04-15)
域名: `https://prefaceai.mov` 已上线（前端 + API + Harness V2 监控端点）
服务器: 107.148.1.199 (8C/16GB/200GB, Ubuntu 20.04)
容器: 3 个运行中 — api (healthy) + frontend (up) + redis (healthy)
SSL: Cloudflare Full (Strict) + Origin Certificate
新端点: `/api/monitoring/errors/recent` + `/api/monitoring/costs/summary` (JWT 鉴权)

---

## 最近操作 (2026-04-15)

### TASK-HARNESS-V2 Phase 3: PreCommit + Push + VPS 部署 ✅

- settings.local.json PreCommit 加入 test_error_patterns.py (本地 override, gitignored)
- scripts/health_check.sh chmod +x (0644 → 0755)
- 2 commits pushed: 87aeaa4 (feat:19) + ea0edb1 (docs:5), e572076 → ea0edb1
- rsync 353 files → VPS, Docker --no-cache rebuild, force-recreate api
- 验证 4/4: push ✅ + health ✅ + errors/recent HTTP_401 ✅ + costs/summary HTTP_401 ✅

### TASK-HE-DEVOPS-2: TEAM_CHAT 归档机制 ✅

**全员注意 -- TEAM_CHAT.md 已归档，历史消息在 chat-archive/**：

| 归档文件 | 内容范围 | 行数 |
|----------|----------|------|
| `.team-brain/chat-archive/2026-01.md` | 2026-01 消息 | 7,246 |
| `.team-brain/chat-archive/2026-02.md` | 2026-02 消息 | 8,328 |
| `.team-brain/chat-archive/2026-03.md` | 2026-03 消息 | 16,970 |
| `.team-brain/chat-archive/2026-04.md` | 2026-04-01 ~ 04-06 | 1,246 |

- TEAM_CHAT.md 从 36,079 行缩减到 2,343 行
- 归档脚本: `scripts/archive_team_chat.sh`（可定期运行）
- 需要查历史消息 → 读对应月份的归档文件

### TASK-HE-DEVOPS-1: Hook 基础设施升级 ✅

**全员注意 — Hooks 已升级，以下自动检查现已生效**：

| 触发时机 | 检查内容 | 影响 |
|----------|----------|------|
| 编辑/写入 `.py` 文件 | pyright 类型检查 (tail -8) | 类型错误会显示在终端 |
| 编辑/写入 `.ts`/`.tsx` 文件 | tsc 编译检查 (tail -10) + 清 .next/cache | 编译错误会显示在终端 |
| git commit 前 | pytest test_architecture.py + test_quality_gates.py | 当前带 `|| true`（@tester 测试未就绪），不阻塞提交 |
| git push 前 | pytest tests/ 全量 (timeout 300s) | 测试失败会阻塞 push |

**工具版本**: pyright 1.1.408 / tsc 5.9.3 / pytest 8.3.4
**注意**: 所有 hook 使用 `python3`（非 `python`），因本机 `python` 不在 PATH

### Earlier (2026-04-09): 阿里云 MySQL ALTER TABLE — project_chapters TEXT→LONGTEXT ✅

- 通过 pymysql 连接阿里云 MySQL，执行 ALTER TABLE 将 8 个 TEXT 列改为 LONGTEXT
- 影响列: full_script, summary, characters_json, scenes_json, storyboard_json, error_message, transcript_json, timeline_json
- 已验证: DESCRIBE 确认全部 8 列为 longtext
- **数据库表结构已与 chapter.py model 同步**

### Earlier (2026-04-04): TASK-CONFIRM-OUTLINE-WIRE + REORDER-FIX push + VPS 部署 ✅

4 commits pushed → `origin/main` (38f2505 → 708e362):

| Commit | 内容 |
|--------|------|
| `066ef46` | feat(backend): WIRE + REORDER-FIX — projects.py + job_manager + pipeline_orchestrator |
| `853a755` | feat(frontend): WIRE + REORDER-FIX — StageB + CreateContent + CreateContext + types |
| `a55bb07` | test: 39/39 confirm-outline 全链路测试 |
| `708e362` | docs: agent progress + team-brain sync + shared-memory 通知 |

**VPS 部署**:
- SCP 7 文件 + Docker rebuild (api + frontend) → force-recreate
- `https://prefaceai.mov` 前端 200 ✅ + API `/health` healthy ✅
- 部署后新请求不再产生重复项目 + pipeline 使用用户确认大纲
- Ben 已知会清理历史脏数据（shared-memory 通知）

### Earlier: TASK-UPLOADER-ENV-FIX push + VPS 前端部署 ✅

2 commits pushed → `origin/main` (0ed365e → ceb2ba5):

| Commit | 内容 |
|--------|------|
| `f292bee` | fix(frontend): 5 个 Uploader 统一 API_BASE（生产 env 修复） |
| `ceb2ba5` | docs: agent progress + team-brain sync |

**VPS 部署**:
- SCP 5 文件 + Docker rebuild frontend → force-recreate（仅前端）
- `https://prefaceai.mov` 前端 200 ✅ + API `/health` healthy ✅
- 自定义风格/角色/场景上传在生产环境应恢复正常

### Earlier: REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX push + VPS 部署 ✅

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

- **API Key 全部就位 (6/6)**: 本地 .env 已填入全部 TTS Key (VOLCENGINE_APP_ID + VOLCENGINE_ACCESS_KEY + VOLCENGINE_SECRET_KEY + VOLCENGINE_API_KEY)。VPS .env.production 待 Founder 手动填入（参见 TEAM_CHAT 指引）
- **前端已可访问**: `https://prefaceai.mov` 返回 Landing Page（V2 品牌宣言 + 新 logo + 风格缩略图）
- **API 已可访问**: `https://prefaceai.mov/api/health` 返回 healthy
- **CORS 已限制**: `allow_origins=["https://prefaceai.mov", "http://localhost:3000"]` ✅
- **🚨 部署方式（Ben 强制要求）**: 发布到 VPS 必须用 **rsync 本地代码 + Docker rebuild**，**不要在服务器上 git pull**
- **SSH 端口 58913**: 非默认 22

## 运维风险摘要 (详见 devops-progress/current.md)

| 风险 | 级别 | 关键时间点 |
|------|------|-----------|
| ~~API Key 未填入~~ | ✅ **完全解决 (6/6)** | 04-13 本地完成，VPS 待 Founder 填入 |
| ~~CORS 全开放~~ | ✅ 已解决 | 03-18 部署 |
| ~~无 CI/CD~~ | ✅ 已解决 (GitHub Actions) | 2026-04-15 |
| 无监控告警 | 🟡 P1 | 第一个用户前 |
| 无数据备份 | 🟡 P2 | 有生产数据后 |
| ~~无日志脱敏~~ | ✅ 已解决 | 03-18 部署 |

---

## Git 仓库状态

```
远程仓库: https://github.com/kaiangel/prefaceai-story (private)
分支: main (tracked → origin/main)
最新 commit: ea0edb1 docs: TASK-HARNESS-V2 Phase 3 (5 files)
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-19 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **安全加固已部署**（等待 API Key） | 2026-03-18 |
| git | ✅ 双团队文件已推送（两人直接 push main） | 2026-03-19 |
