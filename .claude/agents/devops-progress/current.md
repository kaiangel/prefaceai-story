# DevOps Agent - 当前任务

> **最后更新**: 2026-05-21 23:XX（自补 5/19-5/21 进度归档 + VPS 部署清单准备）
> **状态**: ⏳ **等 VPS 部署派工** — 5/19 之后 PM 未派活给 DevOps，本地重启/Alembic PM 自己直接做（常规重启 PM 直接 Bash）。等 Layer 1 (T22-NEW-3 Identity Anchor Framework) 完成 + Founder 签字内测启动后，PM 派 VPS 部署任务。

---

## 当前状态 (5/21 23:XX)

**5/19 22:57 以来 DevOps 做了什么**: 无派工。本地服务管理（重启 + Alembic）全是 PM / Founder 自己做的，符合 memory feedback_restart_services_pm_do.md 协议。

**5/20-5/21 间 PM 直接做的本地服务操作（DevOps 未参与）**：
- Wave 1 17:20 重启 backend（Backend agent PID 68942）
- Wave 2 17:45 重启 backend（PID 68942 → 71758）
- Wave 2 round 2 后重启 backend（PID 71758 → 77188）
- Wave 3 19:50 前后 backend 维持 87388（未重启，Wave 3 改完等下次重启）
- Wave 4 21:10 前后：PM 干净重启（合并加载 T21-NEW-1 + T21-NEW-2 schema 13 type）
- Wave 5 22:30 Backend Opus 4.7 完成 5 task（T21-NEW-3/4/5/6/7），未重启（等 PM 审查）
- Wave II 22:50 Frontend Opus 4.7 完成 T21-NEW-7 Frontend
- Wave III（PM 承诺自做）: alembic upgrade head + 干净重启 backend + frontend + monitors + cron

**Alembic 006 执行过程（PM 操作，2026-05-21 ~20:35）**：
- `alembic upgrade head` 第一次 fail（revision id `006_add_scene_references_t21_new7` 超长 MySQLChar 限制）
- 第二次 fail（Duplicate column name，部分 ALTER 已 apply）
- Backend agent 在 upgrade() 方法加幂等 try/except 兜底（`1060` / `Duplicate column` → 跳过）
- 第三次 `alembic upgrade head` 成功 ✅（2 列已 apply + Backfill 老项目 scene_references_confirmed=TRUE）

**等待 VPS 部署任务**（Layer 1 完成 + 内测启动后）：

见下方"VPS 部署清单（待执行）"

---

## VPS 部署清单（待执行）

**触发条件**: Layer 1 (T22-NEW-3 Identity Anchor Framework) 完成 + Founder 签字内测启动

**部署顺序（严格执行）**：

### Step 0: Push GitHub（必须先于 VPS 部署）

```bash
git status        # 确认有哪些改动
git add <files>   # 精确 add，避免 .env 等敏感文件
git commit -m "..."
git push origin main
# 验证: push 成功后再做 Step 1
```

**注意**: DevOps 部署铁律 — 先 push GitHub 再 VPS，不分批，一次完成（memory feedback_push_deploy_together.md）。

### Step 1: rsync 本地代码到 VPS

```bash
# 注意 trailing slash 陷阱！（feedback_rsync_trailing_slash.md 2026-04-15 踩坑）
# 正确：目标路径也要有 app/ 子目录
rsync -avz -e "ssh -p 58913" app/ trader@107.148.1.199:/opt/xuhua-story/app/
rsync -avz -e "ssh -p 58913" frontend/src/ trader@107.148.1.199:/opt/xuhua-story/frontend/src/

# 如有新建文件（如 app/api/ 下新 endpoint），先 ssh 确认目标路径存在
# 确认方式: docker exec docker-api-1 ls /app/app/api/
```

**不要在 VPS 上 git pull（Ben 强制协议，feedback_deploy_rsync_not_gitpull.md）**。

### Step 2: Alembic 006 迁移（VPS 容器内）

```bash
ssh -p 58913 trader@107.148.1.199
cd /opt/xuhua-story/docker
docker compose exec api alembic current          # 确认当前 head
docker compose exec api alembic upgrade head     # 应用 006_add_scene_references_t21_new7
# 验证新列:
docker compose exec api python3 -c "
import asyncio, aiomysql, os
async def check():
    conn = await aiomysql.connect(host='101.132.69.232', port=3306,
        user=os.getenv('MYSQL_USER'), password=os.getenv('MYSQL_PASSWORD'),
        db='prefacestory')
    cur = await conn.cursor()
    await cur.execute('SHOW COLUMNS FROM projects LIKE \"scene_references_confirmed\"')
    print('projects.scene_references_confirmed:', await cur.fetchall())
    await cur.execute('SHOW COLUMNS FROM project_chapters LIKE \"scene_references_json\"')
    print('project_chapters.scene_references_json:', await cur.fetchall())
    conn.close()
asyncio.run(check())
"
```

**注意**: 本地 Alembic 006 已执行成功（幂等兜底），VPS 需单独跑一次。Alembic 006 升级脚本有幂等兜底，再次执行安全。

### Step 3: Docker rebuild + 重启

```bash
cd /opt/xuhua-story/docker
docker compose build --no-cache api        # 重 bake 新代码（Dockerfile COPY app/）
docker compose build --no-cache frontend   # 如有前端改动
docker compose up -d --force-recreate api
docker compose up -d --force-recreate frontend
```

### Step 4: 健康检查

```bash
# 容器内健康检查（正确路径）
docker compose exec api curl http://localhost:8000/health
# 期望: {"status":"healthy"}

# 外部 HTTPS（Cloudflare）
curl https://prefaceai.mov/api/health
# 注: 外部 /api/health 返回 200 是正常的（Nginx /api/ → :8000 反向代理）
# 注: 容器内 /health 正确；外部 /api/health 返回 404 属正常（Nginx 路由，reference_health_endpoint_path.md）

# 确认 StartedAt 已刷新
docker compose ps api
```

**监控/告警是 Wave R4 long-tail，不在 Layer 1 范围**（运维风险 R4 待启动）。

---

## 最新完成

**TASK-T20-FIXBATCH-2 T18-I — IncompleteRead 监控 Dashboard [2026-05-18]**

（详见下方"上次完成"块，与 5/18 版本一致）

---

## 上次完成

**TASK-T20-FIXBATCH-2 T18-I — IncompleteRead 监控 Dashboard [2026-05-18]**

**背景**: Seedream 下载偶发 IncompleteRead 网络抖动，Pipeline 内已有 retry（不阻断），需监控频率突增。

**交付 3 文件**:

| 文件 | 说明 |
|------|------|
| `scripts/monitor_incompleteread.py` | 核心监控脚本 (Python stdlib, chmod +x) |
| `scripts/monitor.yaml` | 告警阈值配置文件（唯一调参入口） |
| `docs/MONITORING_INCOMPLETEREAD.md` | 完整部署 + 使用 + 阈值调整文档 |

**本地验证**:
- 解析 test18 第二轮 backend.log (50622 行)
- 8 次 IncompleteRead，8 次 retry 成功，0 次耗尽，Retry 成功率 100.0%
- WARN/CRITICAL/OK 退出码验证 PASS
- HTML 报告生成 PASS (`logs/monitor_reports/incompleteread_2026-05-18.html`)

**阈值（基于 test18 实测基线）**:
- WARN: 每小时 >= 20 次（正常约 16/hr，设 20 留余量）
- CRITICAL: 每小时 Retry 耗尽失败 >= 3 次（正常 0 次）

**约束遵守**:
- 未改 `app/` / `frontend/` / `.team-brain/team_ben/` 任何文件
- 仅改 `scripts/` / `docs/` / `devops-progress` 三件套 / TEAM_CHAT.md

---

## 上次完成

**TASK-WAVE9-P2-DEVOPS-FRONTEND-IMPACT-HOOK — Wave 9 DEC-030 DevOps 配套 [2026-05-13]**

**背景**: test15 e2e 暴露 13 真 RISK 中 7 个 (47%) 属于前后端契约断裂。合伙人 Ben 5/13 15:42 建议纠错机制。Founder 采纳为 DEC-030 Wave 9 一部分，DevOps 负责 pre-commit hook 落地。

**新建 3 个文件**:

| 文件 | 类型 | 作用 |
|------|------|------|
| `scripts/pre-commit-frontend-impact.sh` | 核心 hook 逻辑 | 检测 staged 文件是否含契约高风险文件，有命中则要求 commit message 含 `[frontend-impact: yes/no]` |
| `scripts/install_pre_commit_hook.sh` | 安装脚本 | 一键软链接 `.git/hooks/pre-commit → scripts/pre-commit-frontend-impact.sh` |
| `docs/CONTRACT_HOOK.md` | 文档 | 5 段说明：为什么有 / 如何安装 / 如何使用 / 如何跳过 / 技术细节 |

**监控的 6 个高风险契约文件**:
- `app/api/projects.py`
- `app/api/chapters.py`
- `app/services/pipeline_orchestrator.py`
- `app/services/job_manager.py`
- `app/models/project.py`
- `app/schemas/project.py`

**安装结果**:
```
.git/hooks/pre-commit -> .../scripts/pre-commit-frontend-impact.sh  (symlink)
```

**3 种场景测试结果**:

| 场景 | 描述 | 结果 |
|------|------|------|
| 1 | 改 `app/api/chapters.py` + commit message 无 label | BLOCKED (exit 1) ✅ 符合预期 |
| 2 | 改 `app/api/chapters.py` + commit message 含 `[frontend-impact: yes]` | PASS (allowed) ✅ 符合预期 |
| 3 | 改 `scripts/pre-commit-frontend-impact.sh`（不相关文件）| PASS (直接放行) ✅ 符合预期 |

**约束遵守**:
- ✅ 未改 `app/`, `frontend/`, `.team-brain/team_ben/` 任何文件
- ✅ 未改 backend 代码或 frontend 代码
- ✅ 仅改 `scripts/`, `docs/`, `devops-progress` 三件套

---

## 上次完成

**TASK-DIAGNOSE-MYSQL-V2 — MySQL 二轮深度诊断 [2026-05-08]**

**根因：阿里云 MySQL 101.132.69.232 服务进程异常（不是白名单/本地网络/SQLAlchemy 问题）**

| 诊断项 | 结果 | 结论 |
|--------|------|------|
| `nc -zv 101.132.69.232 3306` | ✅ connected | TCP 3306 端口可达，SYN ACK 正常 |
| Python socket.recv(4) MySQL greeting | 超时 0 bytes | MySQL 握手包永远不到达（本地） |
| aiomysql 直连（绕过 SQLAlchemy） | 2:13 超时 → 2013 | 不是 SQLAlchemy 问题 |
| macOS 防火墙 | block-all disabled，Python.app 允许 | 不是 macOS 本地防火墙 |
| 本机公网 IP | 140.99.222.167 | 白名单嫌疑 IP |
| VPS 容器内 socket.recv(4) | 超时 0 bytes | 不是本地 IP 白名单问题 |
| VPS 容器内 asyncmy 直连 | `Can't connect to MySQL server` | VPS 也连不上 MySQL |
| VPS docker-api-1 health | ✅ healthy（仅有 GET /health 200 日志）| /health 不测 DB，healthy 是假阳性 |
| VPS 容器启动时间 | 2026-04-30T16:08（8 天前）| 8 天前启动时 MySQL 还通，8 天来没有真实 DB 请求（只有 health check） |

**根因链路**：
- 阿里云 MySQL 实例 101.132.69.232 的 TCP 3306 端口接受连接，但 MySQL 进程不发回握手包
- 表现为：TCP connect 成功，但 `recv(4)` 永远超时（0 bytes）
- 本地和 VPS 容器（两个不同 IP）均失败 → 排除白名单
- 本地 macOS 防火墙正常 → 排除本地拦截
- aiomysql 直连也失败 → 排除 SQLAlchemy/pool 配置

**最可能的服务器侧原因（按概率排序）**：
1. **MySQL 进程崩溃/挂起**（最高概率）：mysqld 进程存在但无法处理新连接，端口还在监听但不响应
2. **阿里云 MySQL 实例被暂停/欠费**：实例暂停时 TCP 端口仍会 ACK 但不传数据
3. **MySQL 连接数满**（max_connections 耗尽）：会拒绝新连接但通常立即发错误包，不是无响应

**修复方案（需要 Ben 或 Founder 操作）**：

**方案 A：登录阿里云 RDS 控制台检查 MySQL 实例状态**
1. 阿里云控制台 → RDS → 实例列表 → 找 101.132.69.232 所在实例
2. 检查实例状态：是否"运行中" / "已停止" / "欠费锁定"
3. 若"已停止"：点击启动
4. 若"运行中"但不响应：重启实例（RDS 控制台 → 重启）
5. 若"欠费"：充值后自动恢复

**方案 B（临时替代）：确认问题后如需本地继续开发**
- 暂时无法用本地 backend（必须等 MySQL 恢复）
- VPS 侧同理（VPS 容器的 DB 操作类请求也会失败，只有 /health 正常）

**需要 Founder/Ben 介入**：DevOps 无权访问阿里云 RDS 控制台。
- 预计恢复时间：控制台操作后 2-5 分钟

---

**TASK-DIAGNOSE-BACKEND-LIFESPAN-STUCK — 本地 backend lifespan 卡死诊断 [2026-05-08]**

**根因**: 跨日（5-01→5-02）系统睡眠后重启，TCP 在 MySQL 握手阶段被切断（aiomysql 读 4 bytes 握手包时收到 0 bytes），进程直接 crash 退出（`Application startup failed. Exiting.`）。不是 metadata lock 死锁，不是卡死进程——进程已经不存在了（port 8000 未占用，ps 无 uvicorn）。

**诊断过程**:
1. 检查 `/tmp/backend.log` 完整内容（194 行 traceback，不是"只有 2 行"）
2. 确认 `OperationalError (2013, Lost connection to MySQL server during query)` + `Application startup failed. Exiting.`
3. `ps aux | grep uvicorn` 无进程，lsof 端口 8000 空闲 — 进程已退出
4. VPS `docker-api-1 Up 7 days (healthy)` — MySQL 本身没问题，是瞬时网络问题

**方案**: 方案 E（重启）— 直接重启，无需 kill 任何进程

**给 PM 的重启命令**:
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_restart.log 2>&1 &
# 等 20-30s，观察 /tmp/backend_restart.log 出现 "Application startup complete."
# 再 curl http://localhost:8000/health 验证
```

**备选**: 直接用 VPS prefaceai.mov 测试 Gemini key rotation（docker-api-1 已跑新 key 7 天）

---

**TASK-KEY-ROTATE-GEMINI — Gemini API Key 轮换 [2026-05-01 00:09]**

**背景**: Founder 已授权 — 旧 key `AIzaSyCX...` → 新 key `AIzaSyBm...`（同 Google project + 同配额）+ "必须立即 revoke 旧 key"。10 步流程全 PASS：

| Step | 动作 | 验收证据 |
|------|------|---------|
| 1 | 备份本地 `.env` → `.env.backup-keyrotate-20260501` | ✅ 1608 bytes 0600 |
| 2 | Edit `.env:2` GEMINI_API_KEY 旧→新 | ✅ 新 1 处 / 旧 0 处 (grep 验证) |
| 3 | `pkill -f "uvicorn app.main"` (PID 48766) + nohup 重启不带 --reload | ✅ 新 PID **71921**，`/health` 200 |
| 4 | 本地真测 settings 加载 + 真 Gemini API 调用 | ✅ `gemini-2.5-flash → 'OK'`，AUTH=PASS |
| 5 | SSH VPS (trader@107.148.1.199:58913) ls /opt/xuhua-story/.env.production | ✅ 路径 `/opt/xuhua-story/.env.production` (1376 bytes 0644) |
| 5b | grep VPS 旧 key 与本地一致性自检 | ✅ 都是 `AIzaSyCX...` |
| 6 | VPS cp 备份 .env.production | ✅ 1376 bytes 0644 |
| 7 | VPS sed 精确替换（仅匹配整行 `^GEMINI_API_KEY=AIzaSyCX...$`）| ✅ 新 1 处 / 旧 0 处 |
| 8 | VPS `cd /opt/xuhua-story/docker && docker compose up -d --force-recreate api` | ✅ docker-api-1 Recreated + Started + healthy |
| 9 | VPS 真测：容器内 settings + 真 Gemini API 调用 + HTTPS /api/health | ✅ `gemini-2.5-flash → 'OK'`，prefaceai.mov/api/health 200 |
| 10 | 通知 PM 让 Founder 立即 Google Cloud Console revoke 旧 key | ⏳ 见 TEAM_CHAT.md + SendMessage |

**未动**: 业务代码（app/、frontend/）、其他 agent progress、docker-compose.yml、Dockerfile.*、其他所有 env vars 一字未改。仅修改本地 `.env:2` + VPS `.env.production` 同一行 + 4 处文档（TEAM_CHAT.md 追加 / current.md / context-for-others.md / completed.md）。

**关键风控**:
- 备份文件 `.env.backup-keyrotate-20260501`（本地 + VPS 两端都存）保留至少 48 hr，万一新 key 异常可秒级回滚
- VPS 替换前先 grep 自检旧 key 一致（避免 VPS 上是不同 key 导致 sed 不命中）
- 本地 + VPS 都做了真 LLM 调用（不是只看 settings 加载），确认新 key 实际可用

**等待 Founder 操作**: Google Cloud Console 撤销旧 key `AIzaSyCX***[redacted-key-Apr29-old]`（Founder 已明确授权"必须立即"）

---

## 上次完成

**Wave 5.3 — alembic CLI 工程化补全 [2026-04-30]**

**目标**: 让 schema 改动可走标准 `alembic revision --autogenerate` + `alembic upgrade head` 流程。

| 步骤 | 操作 | 结果 |
|------|------|------|
| Step 1 | pip install alembic（1.18.4 已安装）+ requirements.txt 加 alembic>=1.13.0 + pymysql>=1.1.0 | ✅ |
| Step 2 | 手工创建 alembic.ini（不用 alembic init，保留现有 versions/001/002）| alembic.ini 存在 ✅ |
| Step 3 | 手工创建 alembic/env.py（同步 pymysql driver，target_metadata = Base.metadata）| env.py 存在 ✅ |
| Step 4 | 前置验证：share_tokens ✅ + share_pv_logs ✅ + projects.is_favorite ✅ | DB = 002 ✅ |
| Step 4b | 本地 alembic stamp 002_r7_2_favorite_share | ✅ alembic_version 表建立 |
| Step 4c | 本地 alembic current | 002_r7_2_favorite_share (head) ✅ |
| Step 5 | Dockerfile.api 加 COPY alembic.ini + COPY alembic/ ./alembic/ | ✅ |
| Step 6 | git add + commit c30982f + push c30982f | ✅ |
| Step 6b | requirements.txt 补 pymysql 显式依赖 + commit 26ff792 + push | ✅ |
| Step 6c | rsync alembic.ini + alembic/ + requirements.txt + Dockerfile.api → VPS | ✅ trailing slash 正确 |
| Step 6d | VPS docker compose build --no-cache api (sha256:2d06fcdd) | ✅ Step 9/10: COPY alembic.ini + COPY alembic/ |
| Step 6e | VPS force-recreate api | docker-api-1 Recreated + Started ✅ |
| Step 6f | VPS docker compose exec api alembic stamp 002_r7_2_favorite_share | INFO MySQLImpl + stamp 成功 ✅ |
| Step 6g | VPS docker compose exec api alembic current | 002_r7_2_favorite_share (head) ✅ |
| Step 6h | VPS /health | {"status":"healthy"} ✅ |

**关键配置**:
- alembic.ini: `sqlalchemy.url =` 留空，由 env.py 从 settings 读取
- env.py: `_get_sync_url()` 把 `mysql+asyncmy://` / `mysql+aiomysql://` 替换为 `mysql+pymysql://`
- env.py: `target_metadata = Base.metadata`，`import app.models` 注册所有 ORM 类
- Dockerfile: `COPY alembic.ini .` + `COPY alembic/ ./alembic/`（容器内 alembic 10/10 步）

**踩坑**:
- pymysql 在本地 venv 是 aiomysql 的间接依赖，requirements.txt 没有显式 pin，容器内缺失 → 补加 pymysql>=1.1.0 + 二次 rebuild

**commits**:
- `c30982f` ops(alembic): add alembic CLI engineering — env.py + ini + Dockerfile + stamp 002
- `26ff792` ops(alembic): add pymysql to requirements.txt for alembic sync driver in container

---

## 上次完成

**TASK-T6-FIXBATCH Wave 5.2 — VPS 部署 Wave 5.1 全批修复 [2026-04-30]**

**Step 1: pytest 验证**

| 项 | 结果 |
|----|------|
| 295 passed | ✅ |
| 3 failed (pre-existing: test_api_cost_log_table×2 + test_compat_with_real_data) | ✅ 全部 pre-existing |
| 6 errors (pre-existing: test_character_consistency 等) | ✅ 全部 pre-existing |
| Wave 5.1 无新引入退化 | ✅ 确认（git stash 对比验证）|

**Step 2: commit + push**

| 项 | 内容 | 结果 |
|----|------|------|
| commit 1 | `84e5861` feat(Wave 5.1): D.13/D.14/D.16/D.17/D.18/T-1/T-2/O-1/O-2/R7-2 全批修复（33 files, +1728/-143）| ✅ |
| commit 2 | `2d9eb58` ops(docker): PYTHONUNBUFFERED=1 (OPS-3) | ✅ |
| push range | `ec471a6..2d9eb58` main | ✅ |

**Step 3: Ben 通知**

- `.team-brain/team_ben/TEAM_CHAT.md` 追加 Wave 5.1 完整通知
- 内容: 10 后端文件 + 4 新建 + DB schema 变更清单（Alembic 002 revision id + 3 表变更详情）
- ✅ 已 append

**Step 4: rsync VPS**

| 命令 | 目标 | 结果 |
|------|------|------|
| `rsync app/ → /opt/xuhua-story/app/` | 10 backend 文件（含 3 新建）| ✅ trailing slash 正确 |
| `rsync frontend/src/ → /opt/xuhua-story/frontend/src/` | 7 frontend 文件（含 1 新建 useStageLock.ts）| ✅ |
| `rsync frontend/src/app/s/ → /opt/xuhua-story/frontend/src/app/s/` | share token page.tsx | ✅ |
| `rsync docker/Dockerfile.api` | OPS-3 PYTHONUNBUFFERED | ✅ |

关键新建文件 VPS 确认：
- `/opt/xuhua-story/app/api/share.py` ✅
- `/opt/xuhua-story/app/models/share.py` ✅
- `/opt/xuhua-story/app/services/prompt_safety_advisor.py` ✅
- `/opt/xuhua-story/frontend/src/app/s/[token]/page.tsx` ✅
- `/opt/xuhua-story/frontend/src/hooks/useStageLock.ts` ✅

**Step 5: Docker rebuild + restart**

| 操作 | sha256 | 结果 |
|------|--------|------|
| `docker compose build --no-cache api` (Wave 5.1) | sha256:9012a05e | ✅ |
| `docker compose build --no-cache frontend` | sha256:8d0a47ee | ✅ |
| `docker compose up -d --force-recreate api frontend` | api+frontend Recreated | ✅ |
| api StartedAt | `2026-04-30T02:35:14Z` | ✅ |
| `docker compose build --no-cache api` (OPS-3 PYTHONUNBUFFERED) | sha256:e42582106ede | ✅ |
| `docker compose up -d --force-recreate api` | Recreated | ✅ |
| api StartedAt | `2026-04-30T02:49:17Z` | ✅ |

**Step 6: DB migration 002 (Alembic 002_r7_2_favorite_share)**

| 操作 | 结果 |
|------|------|
| `ALTER TABLE projects ADD COLUMN is_favorite BOOLEAN DEFAULT NULL` | ✅ |
| share_tokens 表（已存在）验证 columns | id/uuid/project_uuid/token/view_count/created_at ✅ |
| share_pv_logs 表（已存在）验证 columns | id/share_token/viewed_at/ip_hash ✅ |
| `SHOW COLUMNS FROM projects LIKE 'is_favorite'` | tinyint(1) YES ✅ |
| 方式 | 直接 Python/aiomysql 执行 DDL（无 alembic CLI，项目无 alembic.ini）| 共享 MySQL 一次覆盖本地+VPS |

**Step 7: /health 验证**

| 验证项 | 期望 | 结果 |
|--------|------|------|
| 容器内 `curl http://localhost:8000/health` | `{"status":"healthy"}` | ✅ |
| PYTHONUNBUFFERED | `PYTHONUNBUFFERED=1` | ✅ |
| 3 容器 | api(healthy) + frontend(up) + redis(healthy) | ✅ |

**Step 8: OPS-3 PYTHONUNBUFFERED**

- `docker/Dockerfile.api` 加 `ENV PYTHONUNBUFFERED=1` ✅
- 单独 commit `2d9eb58` push + rsync + rebuild + force-recreate ✅
- 容器内 `env | grep PYTHONUNBUFFERED` = `PYTHONUNBUFFERED=1` ✅

**Step 9: 本地 backend 重启**

| 项 | 内容 |
|----|------|
| 旧 PID | 27833/27834（Wave 3.5 代码，已 kill）|
| 新 PID | **10711**（Wave 5.1 代码，nohup 无 --reload）|
| 日志 | `/tmp/backend_w52.log` |
| /health | `{"status":"healthy"}` ✅ |

**Step 10: 本地 DB 状态**

- 共享阿里云 MySQL（101.132.69.232），本地与 VPS 共用，一次 migration 覆盖两端
- `projects.is_favorite`: BOOLEAN ✅
- `share_tokens`: 存在 ✅
- `share_pv_logs`: 存在 ✅

**Step 11: 本地 frontend rebuild + 重启**

| 项 | 内容 |
|----|------|
| `npm run build` | ✅ 0 errors, 20 routes（含新 /s/[token] dynamic route）|
| 旧 frontend | next-server pkill 完成 |
| 新 PID | **11608** |
| HTTP 200 | `curl http://localhost:3000/` ✅ |

---

## 上次完成

**TASK-T6-FIXBATCH Wave 4 — VPS 部署 Wave 1.1+1.2+2+2.5+3.5 全批修复 [2026-04-29]**

**Step 1: commit + push**

| 项 | 内容 | 结果 |
|----|------|------|
| commit hash | `84a2d35` | ✅ |
| push range | `434c2f0..84a2d35` | ✅ main |
| commit message | 覆盖 Wave 1.1+1.2+2+2.5+3.5 全部改动 | ✅ |
| 文件数 | 84 files, +18818/-1069 | ✅ |

**Step 2: Ben 通知**

- `.team-brain/team_ben/TEAM_CHAT.md` 追加通知（2026-04-29）
- 列出 10 个后端改动文件 + 无 DB schema 变更说明
- ✅ 已 append

**Step 3: rsync VPS**

| 命令 | 目标 | 结果 |
|------|------|------|
| `rsync app/ vps:/opt/xuhua-story/app/` | backend 全量 | ✅ trailing slash 正确 |
| `rsync frontend/src/ vps:/opt/xuhua-story/frontend/src/` | frontend src 全量 | ✅ |
| `rsync [projectUuid]/ vps:.../[projectUuid]/` | dynamic route 目录 | ✅ |
| `rsync package.json package-lock.json` | 前端依赖 | ✅ |

关键文件 VPS 确认：`seedream_generator.py` / `character_prompt_builder.py` / `[projectUuid]/[stage]/page.tsx` / `url.ts` / `createUrl.ts` 全部到位 ✅

**Step 4: Docker rebuild + restart**

| 操作 | 结果 |
|------|------|
| `docker compose build api` | sha256:... Built ✅ |
| `docker compose build frontend` | sha256:032df3... Built ✅ |
| `docker compose up -d --force-recreate api frontend` | Recreated + Started ✅ |
| api StartedAt | `2026-04-29T08:02:18Z` ✅ |

**Step 5: /health 验证**

| 验证项 | 期望 | 结果 |
|--------|------|------|
| 容器内 `/health` | `{"status":"healthy"}` | ✅ |
| 3 容器状态 | api(healthy) + frontend(up) + redis(healthy) | ✅ |

**关键修复代码落地验证（容器内 grep）**:

| 修复 | 验证项 | 结果 |
|------|--------|------|
| R7-3 character_prompt_builder | `isinstance.*dict` 防御 6 处 | ✅ |
| D.15 aspect_ratio | `pipeline_orchestrator.py L221 aspect_ratio: str = "2:3"` 参数 | ✅ |
| Wave 2.5 seedream | `seedream_generator.py _ASPECT_RATIO_TO_SIZE` 2 处 | ✅ |
| R7-9 mark_completed | `job_manager.py L320 stage="completed"` | ✅ |
| R7-1 dashboard | `schemas/project.py cover_image_url + shot_count` | ✅ |

**Step 6: 生产环境 T8 完整故事验证**

| 项 | 内容 |
|----|------|
| 故事 | 牵手走过的街（晚饭后散步 / 老夫妻 / 简单生活短篇） |
| 画幅 | **1:1（朋友圈）** |
| 项目 UUID | `a3966a40-6d27-42c0-a7cf-109729e453e7` |
| 生成 shots | 16 张（NB2 真实生图，1024x1024 正方形）|
| Pipeline 完成 | stage=completed, progress=100%, message="故事生成完成！" ✅ |

**D.15 / R7-1 / R7-3 / UX-16 关键修复验证**:

| 修复 | 验证方法 | 结果 |
|------|----------|------|
| **D.15** aspect_ratio 不再 hardcoded | 选 1:1 → PIL 实测 1024x1024（NB2 正方形） | ✅ PASS |
| **R7-1** Dashboard 封面+shot 数+时区 | `/api/projects/` cover_image_url + shot_count=16 | ✅ PASS |
| **R7-3** adjust portrait 重生 | adjust 前后 portrait mtime 变化（1777452340→1777452385，+45s）| ✅ PASS |
| **UX-16** URL 动态路由 | `GET /create/{uuid}/preview` HTTP 200 | ✅ PASS |

**注**: T8 临时关 SKIP_IMAGE_GENERATION=false 跑真生图验证，验证完毕后已恢复 true。VPS api 容器最终 StartedAt: 2026-04-29T08:xx:xxZ，SKIP_IMAGE_GENERATION: True。

---

## 上次完成

**TASK-VPS-SKIP-IMAGE — VPS 配置 SKIP_IMAGE_GENERATION=true [2026-04-24 13:32]**

**背景**: PM 地毯式审查发现 VPS `.env.production` 未配 SKIP_IMAGE_GENERATION，Founder 要在 prefaceai.mov 做 MVP 第二轮测试，选项 A 用 R8 mock 图避免 NB2 真实调用成本（~$2/次）。

**执行 4 步**:

| Step | 操作 | 结果 |
|------|------|------|
| 1 | 幂等追加 SKIP_IMAGE_GENERATION=true → .env.production | ✅ 追加成功 |
| 2 | 验证 .env.production 含该行 | ✅ `SKIP_IMAGE_GENERATION=true` |
| 3 | force-recreate api 容器 | ✅ docker-api-1 Recreated + Started |
| 4 | 容器内 3 项验证 | ✅ 全部 PASS |

**3 项验证**:

| 验证项 | 期望 | 结果 |
|--------|------|------|
| `/health` | healthy | `{"status":"healthy"}` ✅ |
| `settings.SKIP_IMAGE_GENERATION` | True | `SKIP_IMAGE_GENERATION = True` ✅ |
| 容器 StartedAt | 2026-04-24 | `2026-04-24T05:30:37.588742043Z` ✅ |

**约束遵守**:
- ✅ 不改代码 / 不 push / 不 commit
- ✅ 不动共享 MySQL / frontend 容器 / redis
- ✅ 幂等操作（grep -q 防重复追加）
- ✅ 未改 PM 维护文档

**Bash 权限**: ✅ 本次可用（一轮通过）

---

## 上次完成

**TASK-BUG-FIX-BATCH-1 Route D — VPS 统一部署 [2026-04-23 17:10]**

**部署范围**: Route B (Backend BE-3/4/5 + /static mount) + Route C (Frontend FE-1~5) + docker-compose output volume 新增

**2 次 commit + push**:

1. `3fa2a73` "fix: Pipeline UX/BGM/SKIP bugs + FE StrictMode completedRef race"
   - 20 files (+1050/-77): 5 代码 + 15 进度/文档
   - push range: `928a621..3fa2a73`

2. `6518563` "fix(docker): add output_data volume mount for /app/output"
   - 1 file (+2): docker/docker-compose.yml
   - push range: `3fa2a73..6518563`
   - **原因**: Step 2 发现 VPS docker-compose.yml 无 output volume，`/static/outputs` StaticFiles 依赖的 `/app/output` 目录需持久化

**rsync**:
- `app/` → VPS (main.py + job_manager.py + pipeline_orchestrator.py)
- `frontend/src/` → VPS (StageC.tsx + CreateContext.tsx)
- `docker/docker-compose.yml` → VPS (output_data volume 新增)

**VPS docker**:
- `docker compose build api` → image sha256:6090c0d4... ✅
- `docker compose build frontend` → 20 routes, 0 errors ✅
- `docker compose up -d --force-recreate api frontend` → Volume "docker_output_data" Created ✅
- api StartedAt: `2026-04-23T09:01:10Z`

**验证 6/6 PASS**:

| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | {"status":"healthy"} ✅ |
| /app/output 目录 | 存在 | ls 返回 0 行（空目录，新 volume）✅ |
| /static/outputs StaticFiles | app.mount 存在 | Line 79: app.mount("/static/outputs"...) ✅ |
| job_manager isinstance 守卫 | isinstance(data, (dict, list)) | Line 202 ✅ |
| pipeline_orchestrator credits_used | checkpoint_callback("credits_used",...) | Line 734 ✅ |
| StartedAt | 2026-04-23 | 2026-04-23T09:01:10Z ✅ |
| 外部 HTTPS | HTTP 200 | prefaceai.mov 200 + /api/health 200 ✅ |
| 无 --reload | Config.Cmd 无 reload | ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"] ✅ |

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确
- ✅ 未碰 .env / DB schema / redis
- ✅ 未在 VPS 上 git pull
- ✅ build + force-recreate（代码变 + compose 变，两者都做）

**新增 output volume 决策**:
- PM 任务说明 Step 6 已授权："如果没挂，必须加 volume mount"
- 选择 named volume `output_data:/app/output`（不用 bind mount，容器内可读写，无权限问题）
- `docker_output_data` 已成功在 VPS 创建

---

## 上次完成

**TASK-LOCAL-BACKEND-HUNG — 本地 backend 卡死诊断 + 修复 [2026-04-23 15:05]**

**根因分析**（4 个维度全部查过）:

1. **MySQL 连接池 zombie 连接**: SHOW PROCESSLIST 显示无本机 IP (140.99.222.167) 的旧连接残留（仅 1 条当前诊断连接），无 zombie。VPS (107.148.1.199) 有 5 条 Sleep 连接，但那是正常连接池。PM kill 掉本地 uvicorn 进程后，aiomysql 连接池已随进程退出，无泄漏。
2. **--reload 触发源**: `backend.log` 显示 14:29:43 一批新 worker 启动（DESCRIBE api_cost_logs），说明一次 --reload 触发了 worker 重启。触发 reload 的文件 mtime 分析：`image_generator.py`、`chapters.py`、`pipeline_orchestrator.py` 的 mtime 比 database.py 更新（均为今日 TASK-P0P1-LOGGING-FIX 改动的文件）— 这是根因触发器。
3. **startup 阻塞根因**: 日志显示两轮 DESCRIBE 都在正常运行（约 ~0.5s/表），但 14:30:14 `DESCRIBE project_chapters` 发出后**没有返回**，而后 10 分钟再无日志。原因推断：uvicorn --reload 的旧 worker（pid 之前启动）正在 startup 阶段对 `project_chapters` 做 BEGIN + DESCRIBE，此时新 worker（14:30 reload 触发）也做同样操作，两个并发 BEGIN implicit 事务在阿里云 MySQL 上对 `project_chapters` 产生了 **metadata lock 竞争**（旧 worker 持有 lock，新 worker 等待）。旧 worker 未来得及 COMMIT 就被 reload kill，导致 lock 永久等待。`INNODB_TRX = 0` 是因为 PM kill -9 后锁已释放。
4. **端口 8000 / 进程**: PM kill 后确认 port 空闲，无 uvicorn 残留。

**根本原因**: `uvicorn --reload` 模式 + 阿里云共享远程 MySQL 的高延迟组合，导致 startup 期间 `metadata_create_all()` 的 BEGIN 事务未提交期间被 reload 中断，新 worker 等待 metadata lock → 死锁。

**修复方案（建议 A: nohup 不带 --reload）**:
- `cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story`
- `source venv/bin/activate`
- `nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > storage/logs/uvicorn_nohup.log 2>&1 &`
- PID: **21995**
- 无 --reload（.env DEBUG=true 但通过 CLI 不传 --reload 来绕过）

**启动日志确认**: 所有 DESCRIBE 表正常完成（~0.5s 每表），15:04:24 "Application startup complete"

**验证 2/2 PASS**:
| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | `{"status":"healthy"}` ✅ |
| POST /api/auth/login (kai@kai.com, wrongpass) | 401（不超时） | `{"detail":"邮箱或密码错误"}` ✅ |

---

## 上次完成

**TASK-P0P1-DEPLOY — 统一部署 + 融合 Ben utf8mb4 commit [2026-04-23 14:35]**

融合 Ben 的 `4725e9e` (utf8mb4 defensive patch) + 今日 P0P1 logging fix（4 处代码 + 1 处 compose）一起上生产 VPS。

**Step 1: git pull --rebase 融合 Ben commit** ✅
- `git fetch origin main` 确认有 Ben 的 `4725e9e`
- stash 未提交改动 → `git pull --rebase origin main` (Fast-forward `cb5e395..4725e9e`, app/database.py +6/-1) → stash pop
- `grep _db_url app/database.py` 确认 patch 落地：`_db_url = settings.DATABASE_URL` + `if "charset=" not in _db_url:`

**Step 2: commit 本地所有改动** ✅
- `git add -A` → 12 files (3 代码 + 1 compose + 8 progress/docs/TEAM_CHAT)
- commit `d154ce1` "fix(logging): P0P1 exception logging + docker log rotate" (+1088/-377)
- message 覆盖：pipeline_orchestrator L1074 bare except / chapters.py 9 GET + 3 BackgroundTasks / image_generator 65 print→logger / docker-compose logging max-size=50m max-file=5 + Co-Authored-By

**Step 3: git push origin main** ✅
- push range: `4725e9e..d154ce1`（Ben 的 commit 已在 origin，本次推送 d154ce1）

**Step 4: rsync → VPS** ✅
- `rsync -avz -e "ssh -p 58913" app/ trader@107.148.1.199:/opt/xuhua-story/app/` — 4 代码文件 (database.py + api/chapters.py + services/image_generator.py + services/pipeline_orchestrator.py)
- `rsync -avz -e "ssh -p 58913" docker/ trader@107.148.1.199:/opt/xuhua-story/docker/` — docker-compose.yml
- trailing slash 正确 ✅

**Step 5: VPS docker build + force-recreate** ✅
- 先 `docker compose up -d --force-recreate api` — 首轮验证发现容器仍跑旧代码（Dockerfile COPY baked-in）
- 补 `docker compose build api` (sha256:aaba97eb5674...) → 再 `up -d --force-recreate api`
- 教训：Dockerfile.api 是 `COPY app/ ./app/` 不是 volume mount，代码改动必须 build

**Step 6: 6 项验证 PASS** ✅

| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | {"status":"healthy"} ✅ |
| logging config | max-size=50m max-file=5 | map[max-file:5 max-size:50m] ✅ |
| logger count in image_generator.py | ≥ 60 | **65** ✅ |
| Ben utf8mb4 patch | _db_url + if "charset=" not in | ✅ 落地 |
| StartedAt | 2026-04-23 | **2026-04-23T06:31:38Z** ✅ |
| bare except in pipeline_orchestrator.py | 0 | **0** ✅ |
| bonus: print count in image_generator.py | 0 | **0** ✅ |

**Bash 权限**: ✅ 本次可用（一轮通过，无被拒，无 auth 错误）

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确
- ✅ 未碰 .env / DB schema / frontend / redis
- ✅ 未在 VPS 上 git pull
- ✅ 未改 PM 维护文档（PENDING / PROJECT_STATUS / TODAY_FOCUS / DECISIONS）

---

## 上次完成

**TASK-P0P1-LOGGING-FIX — docker-compose.yml api 服务加 logging 配置 [2026-04-23 11:30]**

背景：Ben 在生产 VPS 排查 500 错误，PM 检查 `docker logs` 只剩 139 行，Ben 11:50 的 traceback 已丢失。根因：Docker 默认日志驱动无大小限制，但容器重启时缓冲区被截断，有效保留行数极少。

**执行**:
- 修改 `docker/docker-compose.yml` api 服务，在 `healthcheck:` 块之后添加 `logging:` 配置
- 改动位置：原文件第 38-39 行之后（healthcheck retries: 3 末尾）
- 新增内容（5 行）:
  ```yaml
      logging:
        driver: "json-file"
        options:
          max-size: "50m"
          max-file: "5"
  ```
- 其他服务（redis / worker / frontend / mysql）未改动

**语法验证**:
- `docker compose config --no-interpolate` 返回码 0，无 STDERR 错误
- parsed 输出中 api 服务确认有 `logging: {driver: json-file, options: {max-file: "5", max-size: 50m}}`

**未部署**（按任务要求 Step 3：等待 @backend 完成代码改动后 PM 统一安排部署）

---

## 上次完成

**TASK-DEPLOY-LLM-SAMPLING — VPS 同步 LLM sampling 改动 [2026-04-23 10:55]**

今日 @backend 完成的两个 LLM sampling 任务（TASK-LLM-TEMP-AUDIT-FIX + TASK-8631-UNIFY）部署到生产 VPS。

**执行**:
- commit `cb5e395` "chore: unify LLM sampling params (temperature + max_tokens)" (22 files, +812/-38)
- push origin main: `b998cbf..cb5e395`
- rsync `app/` → VPS `/opt/xuhua-story/app/` (trailing slash 正确, 8 代码文件: api/utils.py + services/ 下 7 个)
- VPS `docker compose build api` + `up -d --force-recreate api`
- 无前端/redis/DB/env 改动

**验证 4/4 PASS**:
| 验证项 | 期望 | 结果 |
|--------|------|------|
| `/health` | healthy | `{"status":"healthy"}` ✅ |
| character_designer grep 16384 | ≥2 | 2 ✅ |
| shot_validator grep temperature=0.2 | 1 | 1 ✅ |
| StartedAt | 2026-04-23 | 2026-04-23T02:52:27Z (从 2026-04-21T10:05 刷新) ✅ |
| `grep 8631` in app/ | 0 | 0 ✅ |

**Bash 权限**: ✅ 本次可用（无被拒）。上次 2026-04-21 Mureka 部署 Bash 二次被拒 PM 代执行，本次恢复正常。

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确（`app/` → `/opt/xuhua-story/app/`）
- ✅ 未碰 .env / DB schema / frontend / redis
- ✅ 未在 VPS 上 git pull

---

## 上次完成

**TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 VPS 部署 (2026-04-21 17:55)**

> 注意：本次部署由 PM 代执行。@devops Bash 权限第 2 次被拒，PM 依据 memory "重启服务 PM 自己做" 先读 devops.md 按铁律执行。

- commit `b998cbf` "feat: Mureka AI BGM integration (Wave 1-4)" (69 files, 18922 insertions)
- push origin main: `0fcb65a..b998cbf`
- VPS `.env.production` 追加 `MUREKA_API_KEY=op_1l4kuv9fv...`
- rsync `app/` + `scripts/` + `frontend/src/` → VPS（trailing slash 正确）
- 共享阿里云 MySQL (101.132.69.232) `project_chapters` 表已含 4 BGM 列（本地 migration 一次覆盖）
- `docker compose build api` + `docker compose build frontend`
- `docker compose up -d api frontend` (force recreate)
- 验证: `{"status":"healthy"}` + `settings.MUREKA_API_KEY` = True ✅

---

## 上次完成

**TASK-MUSIC-SEARCH-PY: music-prompt skill search.py 创建 (2026-04-16)**
- 创建 `.claude/skills/music-prompt/scripts/search.py` (chmod +x)
- 搜索 `music_theory.md` + `cross_sensory.md` 两个知识库，支持 `--domain genre/instrument/term/mood/scene/sensory/all`
- 大小写不敏感、中英文双语、± 1 行上下文输出、终端颜色高亮
- 5/5 验收 PASS: 文件创建 ✅ + piano 52 匹配 ✅ + 悲伤 mood ✅ + 雨夜 scene ✅ + jazz genre ✅ + --help ✅

---

## 上次完成

**TASK-ARCHIVE-LINES: archive_team_chat.sh 新增 --max-lines 模式 (2026-04-14)**
- `--max-lines N --keep M` 参数解析 + MODE 分支 `date` / `lines`
- 行数模式: ≤ max_lines → 打印"无需归档"；> max_lines → 中间按月归档 → 重写主文件保留末尾 keep_lines 行
- 4/4 验收 PASS: 可执行 ✅ + 3039<5000→无需归档 ✅ + 日期模式不受影响 ✅ + 幂等 ✅

---

## 上次完成

**TASK-HARNESS-V2 Phase 3: PreCommit + Push + VPS 部署 (2026-04-15)**
- Step 1: settings.local.json PreCommit 加入 test_error_patterns.py
- Step 2: chmod +x scripts/health_check.sh (0644 → 0755)
- Step 3: 2 commits — 87aeaa4 (feat:19 files) + ea0edb1 (docs:5 files)
- Push: e572076 → ea0edb1
- Step 4: rsync 353 files + Docker --no-cache rebuild + force-recreate api
- Step 5: 4/4 PASS (push ✅ + health ✅ + errors/recent 401 ✅ + costs/summary 401 ✅)

---

## 上次完成

**TASK-DEPLOY-STAGED-V2: Push + VPS 部署 (2026-04-14)**
- 3 commits: 611c501 (feat:25) + 68ac04f (frontend:2) + 259f696 (docs:121)
- Push: 69ebc02 → 259f696
- VPS: rsync + Docker rebuild api+frontend
- 验证 10/10 PASS (前端200 + health OK + Shot端点路由 + anthropic 0.89.0)

---

## 上上次完成

**TASK-HE-DEVOPS-2: TEAM_CHAT 归档机制 (Harness Engineering V1 Phase 2)**

### 执行内容 [2026-04-14]

1. **创建归档脚本**: `scripts/archive_team_chat.sh` (chmod 755)
   - Bash wrapper + Python 核心逻辑（精确日期解析）
   - 支持 macOS (BSD date) 和 Linux (GNU date)
   - 日期检测: `### YYYY-MM-DD` + `#### @agent (YYYY-MM-DD)` + `#### @agent [YYYY-MM-DD]`
   - 幂等: 已归档内容不重复写入

2. **首次归档执行**:
   - 归档前: 36,079 行 → 归档后: 2,343 行 (减少 93.5%)
   - 4 个月份归档文件: 2026-01 (7,246行), 2026-02 (8,328行), 2026-03 (16,970行), 2026-04 (1,246行)
   - 幂等验证: 二次运行输出 "No messages to archive"

3. **头部更新**: TEAM_CHAT.md 头部已加入归档说明

### 下一步

- 无待办，等待 PM 下一个任务派发

---

## 上次完成

**TASK-HE-DEVOPS-1: Hook 基础设施升级 (Harness Engineering V1)**

### 执行内容 [2026-04-14]

1. **前置验证**:
   - `python3 -m pyright --version` → **pyright 1.1.408** (pip3 install 安装)
   - `npx tsc --version` (frontend/) → **Version 5.9.3** (已有)
   - `python3 -m pytest --version` → **pytest 8.3.4** (已有)

2. **settings.local.json 升级** (`.claude/settings.local.json`):
   - **PostToolUse**: 合并为统一 hook — .py 文件自动跑 pyright 类型检查，.ts/.tsx 文件自动跑 tsc 编译检查 + 清 Next.js 缓存
   - **PreCommit (新增)**: 提交前自动跑 `tests/test_architecture.py` + `tests/test_quality_gates.py`，带 `|| true` 安全启动（@tester 测试文件未就绪）
   - **PrePush (新增)**: 推送前跑完整 `tests/` 测试套件，timeout 300s
   - **env/permissions**: 保持不变

3. **关键适配**: `python` 命令在本机不可用（仅有 `python3`），所有 hook 命令使用 `python3` 代替 `python`

### 下一步

- 等待 PM 通知：@tester 完成 `tests/test_architecture.py` + `tests/test_quality_gates.py` 后，去掉 PreCommit 的 `|| true` 激活完整闭环

---

## 上次完成

**TASK-CONFIRM-OUTLINE-WIRE + REORDER-FIX — push + VPS 部署**

### 执行内容

1. **Git 提交 (4 commits)**:
   - `066ef46` feat(backend): WIRE + REORDER-FIX — StageB 全链路接通 (3 files)
   - `853a755` feat(frontend): WIRE + REORDER-FIX — StageB 接通 confirm + start-generation (4 files)
   - `a55bb07` test: 39/39 合并逻辑 + Pipeline 跳过 (1 file)
   - `708e362` docs: agent progress + team-brain sync + shared-memory 通知 (18 files)
2. **Push**: `origin/main` 38f2505 → 708e362
3. **VPS 部署**: SCP 7 文件 + Docker rebuild (api + frontend) + force-recreate
4. **验证**: frontend 200 ✅ + API `/health` healthy ✅ + 3 容器运行

---

## 上次完成

**TASK-UPLOADER-ENV-FIX — push + VPS 前端部署**

### 执行内容

1. **Git 提交 (2 commits)**:
   - `f292bee` fix(frontend): TASK-UPLOADER-ENV-FIX — 5 个 Uploader 统一 API_BASE (5 files)
   - `ceb2ba5` docs: agent progress + team-brain sync (10 files)
2. **Push**: `origin/main` 0ed365e → ceb2ba5
3. **VPS 部署**: SCP 5 文件 + Docker rebuild frontend + force-recreate（仅前端，API 不动）
4. **验证**: frontend 200 ✅ + API `/health` healthy ✅ + 3 容器运行

---

## 上次完成

**REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX — push + VPS 部署**

### 执行内容

1. **Git 提交 (3 commits)**:
   - `2520fc5` feat(backend): TASK-JSON-REPAIR-V3 状态机 + LOGGING-FIX 增强 (3 files)
   - `029841a` feat(frontend): TASK-OUTLINE-PROGRESS 大纲生成进度页面 (1 file)
   - `d7eb28c` docs: agent progress + team-brain sync (14 files)
2. **Push**: `origin/main` 3a437bd → d7eb28c
3. **VPS 部署**: SCP 关键文件 + Docker rebuild (api + frontend) + force-recreate
4. **权限修复**: 通过 Docker alpine 容器修复 /opt/xuhua-story/ 文件所有权 (uid 501 → trader 1000)
5. **验证**: frontend 200 ✅ + API `/health` healthy ✅ + 3 容器运行

---

## 上次完成

**TASK-GIT-PUSH-DUAL-TEAM: 双团队协作文件推送**

### 执行内容

1. **Git 提交**: `33eaac6` feat: dual-team collaboration system — Ben team onboarding (59 files)
2. **Push to GitHub**: `origin/main` f76ac1e → 33eaac6
3. **不需要 VPS 部署**（开发协作文档）
4. **跳过的文件**: 118MB .mov 视频 + 简历 PDF + 新照片（不属于协作文件）

### ~~TASK-GIT-BRANCH-PROTECTION~~: 已取消

**Git 工作流变更**: 分支保护已移除，两人（Founder + Ben）都直接 push 到 `main` 分支。
- 分工不同，代码冲突概率极低
- 不再需要 `founder/xxx` 或 `ben/xxx` 分支
- 不再需要 PR

---

## 上次完成

**安全加固部署: TASK-CORS-RESTRICT + TASK-LOG-SANITIZE**

### 执行内容

1. **Git 提交**: `f76ac1e` feat: security hardening — CORS restrict + log sanitizer (1 commit, 3 files)
2. **Push to GitHub**: `origin/main` c6d697a → f76ac1e
3. **VPS 部署**: rsync 3 files + Docker rebuild api + force-recreate
4. **验证**:
   | 验证项 | 结果 |
   |--------|------|
   | `https://prefaceai.mov` | ✅ HTTP 200 |
   | `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
   | CORS 白名单 (prefaceai.mov) | ✅ 返回 allow-origin |
   | CORS 拒绝 (evil.com) | ✅ 无 CORS header |
   | Docker 3 容器 | ✅ 全部 Up (healthy) |

---

## 上次完成

**TASK-DEPLOY-CLEANUP: REWRITER-CLEANUP + OB-1/2/3/4 推送 + VPS 部署**

### 执行内容

1. **Git 提交 (2 commits)**:
   - `1814193` feat: REWRITER-CLEANUP + OB-1/2/3/4 — phase2_safe pipeline integration + model sync (7 files)
   - `c6d697a` docs: agent progress + team-brain sync (REWRITER-CLEANUP + OB-1/2/3/4 + SAFE-DRYRUN) (21 files)

2. **Push to GitHub**: `origin/main` ec3b4fd → c6d697a (2 commits)

3. **VPS 部署**:
   - rsync app/ (6 files) + tests/ (1 file) 同步
   - Docker rebuild: api 容器重新构建
   - `docker compose up -d --force-recreate api` 重启服务

4. **验证通过**:
   | 验证项 | 结果 |
   |--------|------|
   | `https://prefaceai.mov` | ✅ HTTP 200 |
   | `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
   | Docker api 容器 | ✅ Up (healthy) |
   | Docker frontend 容器 | ✅ Up |
   | Docker redis 容器 | ✅ Up (healthy) |

5. **部署前验证**:
   - Python syntax 6/6 ✅
   - Haiku 零残留 ✅
   - gemini-3-pro-preview 零残留 ✅

---

## 上次完成

**TASK-DEPLOY-R8B: N13-FIX + IMG-SAFETY + BRAND-MANIFESTO + LOGO-REPLACE 推送 + VPS 部署**

### 执行内容

1. **Git 提交 (3 commits)**:
   - `935f0b0` feat: N13-FIX spouse_of symmetry + IMG-SAFETY-RETRY scene/char ref recovery + T-J test fixes
   - `34fbcc4` feat(frontend): BRAND-MANIFESTO V2 integration + LOGO-REPLACE full-site
   - `ec3b4fd` docs: agent progress + team-brain sync + R8 E2E + IMG-SAFETY-VERIFY test scripts

2. **Push to GitHub**: `origin/main` 73f8a78 → ec3b4fd (3 commits)

3. **VPS 部署**:
   - rsync 57 文件同步
   - Docker rebuild: api + frontend 两个容器重新构建
   - `docker compose up -d` 重启服务

4. **验证通过**:
   | 验证项 | 结果 |
   |--------|------|
   | `https://prefaceai.mov` | ✅ HTTP 200 |
   | `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
   | Docker 3 容器 | ✅ 全部 Up (api healthy, frontend up, redis healthy) |

---

## 待处理队列

| 优先级 | 任务 | 触发条件 | 状态 |
|--------|------|----------|------|
| P0 | Founder 填入 API Key | Founder 决策 | ⏳ 等待中 |
| ~~P1~~ | ~~CI/CD 基础流水线~~ | ~~部署完成后~~ | ✅ 完成 (GitHub Actions ci.yml, 2026-04-15) |
| P2 | 监控告警系统 | 部署稳定后 | ⏳ 待启动 |

---

## 运维风险清单 (2026-03-17 建立)

> 上线前/用户量上来前必须逐项解决，每次部署后复查

| # | 风险项 | 级别 | 当前状态 | 影响 | 解决方案 | 解决时机 |
|---|--------|------|----------|------|----------|----------|
| R1 | ~~API Key 未填入~~ | ✅ **完全解决 (6/6)** | 全部 Key 已填入本地 .env：ANTHROPIC+GEMINI+OPENAI+VOLCENGINE_APP_ID+VOLCENGINE_ACCESS_KEY+VOLCENGINE_SECRET_KEY+VOLCENGINE_API_KEY | — | ✅ 04-13 本地 .env 完成 | VPS 待 Founder 手动填入（见 TEAM_CHAT 指引）|
| R2 | ~~CORS 全开放~~ | ✅ 已解决 | `allow_origins=["prefaceai.mov", "localhost:3000"]` | — | ✅ 03-18 部署 | — |
| R3 | ~~无 CI/CD~~ | ✅ 已解决 | GitHub Actions CI 上线 | — | ✅ 2026-04-15 | — |
| R4 | **无监控告警** | 🟡 P1 | 无 Sentry、无成本监控 | 线上报错无感知、API 成本失控无预警 | Sentry 错误追踪 + API 成本看板 | 第一个用户前 |
| R5 | **无数据备份** | 🟡 P2 | Redis 无持久化备份 | 重启/宕机丢失任务队列数据 | Redis RDB/AOF + 定期备份脚本 | 有生产数据后 |
| R6 | ~~无日志脱敏~~ | ✅ 已解决 | `log_sanitizer.py` patch print 正则脱敏 | — | ✅ 03-18 部署 | — |
| R7 | **SSH 非标准端口仅有** | 🟢 P3 | 端口 58913，无 fail2ban | 暴力破解风险低但非零 | 安装 fail2ban + 确认密钥登录 | 有空时 |

### 复查节奏

- **每次部署后**: 检查 R1-R2（Key 和 CORS）
- **每周**: 检查 R3-R4（CI/CD 和监控进展）
- **每月**: 全量复查 R1-R7

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-04-24 | TASK-VPS-SKIP-IMAGE: .env.production 幂等追加 SKIP_IMAGE_GENERATION=true + force-recreate api + 3/3 PASS + StartedAt 2026-04-24T05:30:37Z |
| 2026-04-23 | TASK-BUG-FIX-BATCH-1 Route D: commit 3fa2a73+6518563 + push 928a621→6518563 + rsync app/(3)+frontend/src/(2)+docker/(1) + VPS build api+frontend + force-recreate + output_data volume 创建 + 8/8 PASS + StartedAt 2026-04-23T09:01:10Z |
| 2026-04-23 | TASK-P0P1-DEPLOY: rebase Ben 4725e9e + commit d154ce1 + push 4725e9e→d154ce1 + rsync app/(4) + docker/(1) + VPS build+force-recreate + 6/6 PASS + StartedAt 2026-04-23T06:31:38Z |
| 2026-04-23 | TASK-P0P1-LOGGING-FIX: docker-compose.yml api 服务加 logging (max-size=50m, max-file=5)，YAML 验证 PASS，未部署（等统一部署） |
| 2026-04-23 | TASK-DEPLOY-LLM-SAMPLING: commit cb5e395 + push b998cbf→cb5e395 + rsync app/ (8 files) + VPS api rebuild + 4/4 验证 PASS |
| 2026-04-13 | TTS-KEY-WRITE: 本地 .env 写入 VOLCENGINE_API_KEY + VOLCENGINE_SECRET_KEY，R1 完全解决 (6/6)，.env.example 补全字段 |
| 2026-04-16 | TASK-MUSIC-SEARCH-PY: music-prompt skill search.py 创建 (scripts/ + chmod +x)，5/5 验收 PASS |
| 2026-04-14 | TASK-ARCHIVE-LINES: archive_team_chat.sh 新增 --max-lines/--keep 行数模式，4/4 验收 PASS |
| 2026-04-15 | TASK-HARNESS-V2 Phase 3: PreCommit hook 更新 + push(87aeaa4+ea0edb1) + VPS rsync+rebuild + 4/4 PASS |
| 2026-04-14 | TASK-HE-DEVOPS-2: TEAM_CHAT 归档脚本创建 + 首次执行 (36079→2343行, 4个月份归档文件) |
| 2026-04-14 | TASK-HE-DEVOPS-1: Hook 基础设施升级 (pyright + tsc + PreCommit + PrePush) |
| 2026-04-09 | 阿里云 MySQL ALTER TABLE project_chapters 8 列 TEXT→LONGTEXT (RB-1 配套 DDL) |
| 2026-04-07 | MERGE-FIX push (pull Ben 4dcccc0 → 303cb34+2277ee7+69ebc02) + VPS 部署 (rsync + api rebuild) |
| 2026-04-05 | VPS API Key 验证: 核心 4/6 已填入且容器内生效，R1 风险标记基本解决 |
| 2026-04-04 | WIRE + REORDER-FIX push (066ef46+853a755+a55bb07+708e362) + VPS 部署 (api + frontend rebuild) |
| 2026-04-01 | UPLOADER-ENV-FIX push (f292bee+ceb2ba5) + VPS frontend rebuild |
| 2026-04-01 | REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX push (2520fc5+029841a+d7eb28c) + VPS 部署 (SCP + Docker rebuild api+frontend) |
| 2026-03-30 | 大纲生成全链路 push (56aa22b+c37d392) + Ben 融合 merge (8b5c36a) + VPS 部署 (rsync + Docker rebuild + API Key 填入) |
| 2026-03-29 | REPAIR-V2 + PERSISTENT-LOG push (3 commits: 79d63f8+df1f44d+77ef5f9), d54087e→77ef5f9 |
| 2026-03-29 | 6 TASK push (6 commits: 3975901→0ed98de), faf594f→0ed98de — E2E 联调通过 |
| 2026-03-27 | TASK-SHARED-DB: .env→阿里云 MySQL + 6 列 ALTER TABLE + /health OK + Docker MySQL 停 |
| 2026-03-26 | Phase 1+2 push (4 commits: 673a907+1bbfebf+408ae6a+dc6ef0d), 40ca049→dc6ef0d |
| 2026-03-24 | LLM-FIX push (2 commits: 376d6b7 + a0b3598), 3d27445→a0b3598 — Stage 1 E2E 通过 |
| 2026-03-24 | ENVVAR-FIX push (2 commits: 4fdf1ea + 226e0bc), 41ae0d5→226e0bc |
| 2026-03-24 | MySQL 搭建 (Docker mysql:8.0, 11 tables) + Stage 1 push (4 commits: 5dec834+33f4725+e063b23+ef4acca) |
| 2026-03-24 | 完整 push (2 commits: 7b973fc + da291e0), e4ada3e→da291e0 — register fix + Resonance + skills + coordinator |
| 2026-03-24 | Git pull Ben commit e4ada3e (MySQL user flows, 29 files) + TEAM_CHAT 冲突解决 |
| 2026-03-23 | Frontend review fixes + text-gen hint push (2 commits: a2f61f0 + afeae40), 866ea71→afeae40 |
| 2026-03-22 | Frontend Batch 3+4 push (3 commits: 5f55e57 + d37b4e5 + 8ab7057), 8d51108→8ab7057 |
| 2026-03-22 | Frontend Batch 1A+1B+2 push (3 commits: 336a646 + 955f45d + 9c29aa6) |
| 2026-03-20 | git pull Ben 首次 push (20641ac, 25 files) — 双团队正式运作 |
| 2026-03-19 | PUSH-DUAL-TEAM (59 files) + BRANCH-PROTECTION (设置→移除) + 文件重组 push (43 files) |
| 2026-03-18 | 安全加固: CORS restrict + log sanitizer (1 commit push + VPS api rebuild) |
| 2026-03-17 | TASK-DEPLOY-CLEANUP: 2 commits push + VPS api rebuild (REWRITER-CLEANUP + OB-1/2/3/4) |
| 2026-03-16 | TASK-DEPLOY-R8B: 3 commits push + VPS api+frontend rebuild (N13+IMG-SAFETY+BRAND+LOGO) |
| 2026-03-14 | TASK-DEPLOY-R8: 3 commits push + VPS api rebuild (T-A~T-K + OB-1) |
| 2026-03-10 | TASK-DEPLOY-UPDATE: 3 commits push + VPS frontend/api rebuild |
| 2026-03-06 | TASK-DEPLOY-EXEC Step 1-4 全部完成 |
| 2026-03-05 | TASK-DEPLOY-PREP Step 3 完成 + PM 二次审核 PASS |
| 2026-03-05 | TASK-GIT-COMMIT-3 全部完成 + push |
