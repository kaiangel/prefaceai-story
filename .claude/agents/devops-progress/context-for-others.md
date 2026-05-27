# DevOps Agent - 给其他 Agent 的上下文

> 其他 Agent 查看其文件了解 DevOps 的工作状态和部署要求
> **最后更新**: 2026-05-27 17:20（P0 SQLAlchemy 2.0.50 升级 commit 8cabaec + VPS rebuild 部署 + ping bug 实证消失）

---

## 🔴 P0 修复已部署 (2026-05-27 17:20) — VPS 登录/工作台 500 ping bug 已根治

- **commit `8cabaec`**: SQLAlchemy `2.0.36→2.0.50`(修 #13306 do_ping/async ping 签名 bug) + asyncmy `0.2.10→0.2.11`(parity+#86 bugfix) + pymysql `>=1.1.0→==1.1.2`(精确 pin 防 1.2.0)
- **P0 实证**: 修复前 VPS 近 30min **120 次** `ping() missing 1 required positional argument: 'reconnect'` TypeError → 修复后全程 **0**。/api/projects/ 从间歇 500 → 稳定 401
- VPS 容器内 pip show 坐实: SQLAlchemy **2.0.50** / asyncmy **0.2.11** / PyMySQL **1.1.2**
- VPS 旧 pymysql 确认 = **1.2.0**(被 `pymysql>=1.1.0` 无上界拉到 5/19 新发版, = 分裂源根因)

### 🚨 Canonical DB 栈 (本地 + VPS + 测试三处必须镜像, 消除 dev/prod 分裂)
```
sqlalchemy == 2.0.50   # 修 #13306 ping bug
asyncmy    == 0.2.11   # 统一 async 驱动 + #86 bugfix
pymysql    == 1.1.2    # 精确 pin sync 驱动(alembic), 防 1.2.0 ping bug
DATABASE_URL scheme = mysql+asyncmy
engine = pool_pre_ping=True + pool_recycle=600 + pool_size=10 + max_overflow=20
Python = 3.11.x
```
**给所有 Agent**: 本地若仍跑 aiomysql + .env scheme=aiomysql = 分裂源, 永远测不出 VPS 的 asyncmy+pymysql1.2.0 ping bug。本地对齐由 PM 执行(切 asyncmy + .env scheme + reinstall + 重启不带 --reload)。

---

## 历史状态速览（2026-05-27 15:45 BGM 部署 + VPS fresh 重启）

**✅ GitHub + VPS 均已更新**:
- VPS 代码 = #8 BGM 路径B (d067916) + P0 SA2.0.50 (8cabaec)
- BGM 改动: app/services/story_music_extractor.py (_detect_chinese_cultural universal 中式文化信号 + character_type 19type 就近映射不默认 human + setting_period 字段名修复), 纯后端 prompt 逻辑, [frontend-impact: no]
- **容器内实证**: docker exec grep _detect_chinese_cultural = 2 处, BGM 代码真上线
- frontend 未动(保留旧版 Up), 无 DB 迁移(BGM 不碰 schema)
- docker-compose.yml 仍无 mysql service (83a576b 已删, 防误启本地库, 共享DB铁律)

**.gitignore 安全修复 (commit 81b5d25)**: 加 `team-members-bp/` + `logs/` + `storyrefs/` + `*.log.*`。防 BP/简历/日志误入库。GitHub + VPS 双重核实均无泄露。

**部署 verify (全通过)**:
- api(healthy) + frontend(Up) + redis(healthy)
- /health healthy + 外部 /api/health 200 + 主页 200
- #5c: alembic 006(head) + projects 3 列 EXISTS (aspect_ratio/raw_outline_json/confirmed_outline_json)
- db_retry middleware: main.py L75 add_middleware (非死代码)
- layout.tsx 新版: 外部 HTML 含 proxy-init + PROXY_VERSION

**给 Backend 注意**: VPS database.py pool_recycle 已 1800→600s (Wave13 #5d), db_retry 中间件已 wire (transient/packet 重试)。

**给 Frontend 注意**: VPS frontend 已含 #4A/#4B 守卫 + #5 404 分级 + #6 reroll 异步 + #9 vitest 基建。package-lock 已更新 (vitest devDep)。

**VPS 上一稳定版本 (回滚点)**: d4541c4 (Wave 12: style_enforcer + adjust异步 + sub-progress + 前端)

**5/25 VPS 第 4 次部署（TASK-WAVE12-DEPLOY-VPS）**:
- rsync 3 个目录: app/services/ + app/api/ + frontend/src/ — md5 5/5 一致
- Docker rebuild api (sha256:052228cb) + frontend (sha256:a95369a8) --no-cache
- force-recreate api + frontend
- DB 3 列确认: projects.aspect_ratio + raw_outline_json + confirmed_outline_json = EXISTS
- 全 verify 通过: /api/health 200 + 主页 200 + 容器 api(healthy) + Wave12 代码(anti-anime/adjust-jobs/adjust_job_manager) ✅

**生产性能基线 (2026-05-25 实测, 关键)**:
- VPS 内网 MySQL round-trip (TCP connect): 42-65ms, avg 51ms
- VPS 内网 SELECT 1 实测: 41.8-42.1ms, avg 41.9ms (极稳定)
- 本地公网 MySQL (测试环境): 333-684ms (TEST28实测)
- **改善比: 333ms → 42ms = 8x 改善** (内网 vs 公网)
- 判断: P2-1 hydrate 在生产仍慢 (5 并发 × 42ms/query + 多次query = 可测量延迟), 但已比本地公网大幅改善。Backend 聚合端点 (#3 ②) 仍有价值 (减并发 round-trip)

**#5d MySQL idle 观察**: Wave13 已把 pool_recycle 1800s→600s (10min, 赶在云端 idle-timeout 前重建), pool_pre_ping=True 已在 VPS。已部署生效。

**VPS 部署历史**:
- 第 1 次 (2026-05-22 ~19:45): Wave 8 初次部署 (f9987b0)
- 第 2 次 (2026-05-22 19:50): Wave 9+9.1+Tester (→ c570c2d, PM 代 Docker rebuild)
- 第 3 次 (2026-05-24): Wave 10+11 (→ 648b81c)
- 第 4 次 (2026-05-25): Wave 12 (→ d4541c4, DevOps 全程自执行)
- 第 5 次 (2026-05-26): Wave 13 + test29 (→ ec7b1b6 运行代码, 含 #4 db_retry + pool_recycle 600s) + .gitignore 安全修复 (81b5d25)

---

## VPS 部署清单（Layer 1 完成后执行）

**执行顺序**:

1. **Push GitHub 先于 VPS**（铁律，不分批）
   ```bash
   git push origin main   # 必须先完成
   ```

2. **rsync 本地代码 → VPS**（Ben 协议，不 git pull）
   ```bash
   rsync -avz -e "ssh -p 58913" app/ trader@107.148.1.199:/opt/xuhua-story/app/
   rsync -avz -e "ssh -p 58913" frontend/src/ trader@107.148.1.199:/opt/xuhua-story/frontend/src/
   ```
   **trailing slash 陷阱**: `rsync app/` 目标也要 `/opt/xuhua-story/app/`（含子目录 `app/`），否则平铺到根（2026-04-15 踩坑）

3. **Alembic 006 迁移（VPS 容器内）**
   ```bash
   docker compose exec api alembic upgrade head
   # 期望: 006_add_scene_references_t21_new7 applied
   # 验证: SHOW COLUMNS FROM projects LIKE 'scene_references_confirmed'
   ```
   本地已执行成功。Alembic 006 有幂等兜底（1060 Duplicate column → skip），VPS 重跑安全。

4. **Docker rebuild + force-recreate**
   ```bash
   docker compose build --no-cache api       # Dockerfile.api COPY app/ 是 bake-in，必须 rebuild
   docker compose build --no-cache frontend  # 如有前端改动
   docker compose up -d --force-recreate api frontend
   ```

5. **健康检查**
   ```bash
   docker compose exec api curl http://localhost:8000/health   # 容器内正确路径
   # 外部 /api/health 200 正常（Nginx 反向代理）
   # 外部 /health 直接访问可能 404（正常，Nginx 路由）
   ```

**监控/告警（R4）**: Wave R4 long-tail，不在 Layer 1 范围。

---

## 5-02 MySQL 连接中断故障全记录 (2026-05-02) — 关键基础设施知识

**全员注意 — 阿里云 ECS 安全组 SAS 自管机制 + 修复模式**

### 故障概要

5-01 → 5-02 跨日后本地 backend 启动失败，`OperationalError (2013, Lost connection to MySQL server during query)`。DevOps 经过 V1+V2 两轮诊断，均未锁定真根因（V1 认为瞬时网络问题；V2 认为 server 端 mysqld 故障）。最终由 PM（借助 ttsrecap 项目 agent 的 server 端自查）+ Founder 截图证实真根因：**阿里云 ECS 安全组 SAS 自管**。

### 真根因

ECS 绑定了 SAS（安全管家）自动创建的安全组 `Sas_Malicious_Ip_Security_Group` (sg-uf668b0d3r5ohyphxywo)，该安全组限定 MySQL(3306) source 仅允许 self-IP `101.132.69.232/32`（ECS 本机自连）。

- 外部 IP（包括本地 Astrill 出口 `140.99.222.167`、VPS `107.148.1.199`）全部被 **silent drop**
- 表现：`nc -zv 3306` ✅（TCP SYN-ACK 内核层通过）但 `recv(4) 0 bytes`（MySQL 握手包被安全组吞掉）
- 这是**应用层过滤**，不是 mysqld 崩溃，不是网络层不通

### 修复模式（重要！下次再遇到不要走弯路）

**正确做法**：ECS 安全组新增 allow 规则，**不要编辑 SAS 自管的已有规则**（SAS 会定期覆盖）
1. 阿里云控制台 → ECS → 安全组 → 找到 `Sas_Malicious_Ip_Security_Group`
2. 入方向 → 添加安全组规则
3. 协议: TCP，端口: 3306，授权对象: 需要访问的 IP/32，优先级: 1（高于 SAS 默认规则）
4. 提交后立即生效（秒通）

**本次修复**：Founder 加白 `140.99.222.167/32`（Astrill 出口 IP）→ MySQL(3306) 优先级 1。提交后秒通。

### 对所有 Agent 的影响

- **MySQL 现在可用** (2026-05-02 15:30 后)：本地 backend 已恢复正常，`/health` 200，aiomysql 真连接 + 15 tables
- **VPS docker-api-1**：同样不受影响（VPS IP 107.148.1.199 不在白名单，但 VPS 容器的 DB 操作是通过 ECS 内网地址还是公网地址待确认）
- **如果未来再遇到 `nc 3306 ✅` 但 `mysql -h 连不上 ❌`**：优先排查 ECS 安全组，不是 mysqld 故障

### DevOps V1+V2 诊断质量反思（给 PM 参考）

**V1 失误**：认为"VPS docker-api-1 健康 = MySQL 本身没问题，是瞬时网络，重试通常 OK"。实际上 /health 是假阳性（硬编码不测 DB）。V1 方向基本正确（重启），但对持续失败的可能性估计不足。

**V2 失误**：看到"两个不同 IP（本地 + VPS）都失败"就排除了白名单，推断为 server 端 mysqld 故障。这个推断跳步了——SAS 安全组 source 是 self-IP，本地和 VPS 都不是 self-IP，所以都被拦截，"两个 IP 都失败"恰恰是白名单问题的特征，不是排除。

**改进：标准客户端 4 步自查（DevOps 未来诊断 DB 连接问题前必做）**：

| 步骤 | 命令 | 判断 |
|------|------|------|
| 1 | `ping 101.132.69.232` | ICMP — 网络层可达性 |
| 2 | `nc -zv 101.132.69.232 3306` | TCP — 端口层可达性 |
| 3 | `mysql -u xxx -p -h 101.132.69.232` | 应用层 — MySQL 握手是否到达 |
| 4 | `traceroute 101.132.69.232` | 路径追踪 — drop 发生在哪一跳 |

**信号解读**：
- `nc ✅` + `mysql ❌` = 应用层 filter（安全组/防火墙），不是 mysqld 崩溃
- `nc ✅` + `recv(4) 0 bytes` = 中性（可能是 mysqld 崩溃，也可能是 silent drop）— 需要 server 端自连验证才能区分
- 如果 `server 端 mysql 自连 ✅` + `外部 recv(4) 0 bytes` = 100% 安全组/防火墙 silent drop，不是 mysqld 问题

---

## TASK-KEY-ROTATE-GEMINI 完成 (2026-05-01 00:09) — Gemini API Key 轮换

**全员注意 — 旧 Gemini API key 即将被 Founder 在 Google Cloud Console 撤销**:

- 旧 key `AIzaSyCX***[redacted-key-Apr29-old]` → 新 key `AIzaSyBm***[redacted-key-Apr29-new]`
- 本地 `.env:2`：✅ 新 key 1 处 / 旧 key 0 处
- VPS `/opt/xuhua-story/.env.production`：✅ 新 key 1 处 / 旧 key 0 处
- 本地 backend PID **71921**（重启时间 2026-05-01 00:08，无 --reload）/ VPS `docker-api-1` Recreated
- 真 LLM 验证：本地 + VPS 都用 `gemini-2.5-flash` 调通，AUTH=PASS，无 401/403
- HTTPS prefaceai.mov/api/health：200 ✅

**给 @backend / @ai-ml / @tester**:
- 新 key 已在本地 + VPS 全链路生效，可继续日常开发/测试
- 如有任何 Gemini 调用 401/403/quota 异常，**立即** SendMessage 报 PM
- 备份 `.env.backup-keyrotate-20260501`（本地 + VPS 两端）保留至少 48 hr 后再清理

**给 @pm**:
- 已 SendMessage 提醒：Founder 必须立即去 Google Cloud Console 撤销旧 key（Founder 已明确授权"立即 revoke 不需要观察期"）
- 任何环境变量变更（包括 ANTHROPIC_API_KEY / OPENAI_API_KEY 等其他 key 未来轮换）都按本次 10 步流程：备份 → 替换 → 重启 → 真 LLM 验证 → 通知 Founder revoke 旧 key

---

## Wave 5.3 完成 (2026-04-30) — alembic CLI 工程化

**全员注意 — alembic 正式工程化，以后 schema 改动可走标准流程**:

- `alembic.ini` 已建（项目根），`sqlalchemy.url` 留空由 env.py 读取
- `alembic/env.py` 已建，同步 pymysql driver，`target_metadata = Base.metadata`
- `requirements.txt` 加 `alembic>=1.13.0` + `pymysql>=1.1.0`
- `docker/Dockerfile.api` 加 `COPY alembic.ini` + `COPY alembic/`
- 本地 `alembic current` = `002_r7_2_favorite_share (head)` ✅
- VPS 容器 `alembic current` = `002_r7_2_favorite_share (head)` ✅
- commits: `c30982f` + `26ff792` push main

**以后 schema 变更标准流程（@backend 注意）**:
```bash
# 1. 修改 app/models/*.py
# 2. 生成迁移文件
alembic revision --autogenerate -m "describe_change"
# 3. 检查生成的 versions/xxx.py
# 4. 本地执行
alembic upgrade head
# 5. VPS（DevOps 负责）
docker compose exec api alembic upgrade head
```

**不再需要手写 Python/aiomysql DDL 脚本来迁移**。

---

## Wave 5.2 完成 (2026-04-30) — Wave 5.1 全批修复 + DB migration 002 上生产

**全员注意 — Wave 5.1 (D.13/D.14/D.16/D.17/D.18/T-1/T-2/O-1/O-2/R7-2) 已部署到生产 VPS**:

- commit `84e5861` (feat Wave 5.1: 33 files, +1728/-143) + `2d9eb58` (ops OPS-3: Dockerfile PYTHONUNBUFFERED)
- push range: `ec471a6..2d9eb58`
- rsync app/ + frontend/src/ + frontend/src/app/s/ + docker/Dockerfile.api → VPS
- docker compose build --no-cache api + frontend + force-recreate
- api StartedAt: `2026-04-30T02:49:17Z`
- /health: `{"status":"healthy"}` ✅
- PYTHONUNBUFFERED=1: ✅

**DB Schema 变更（002_r7_2_favorite_share 已执行）**:
- `projects.is_favorite`: BOOLEAN nullable ADD COLUMN ✅
- `share_tokens`: 表存在 ✅
- `share_pv_logs`: 表存在 ✅
- 方式: Python/aiomysql 直接 DDL（阿里云共享 MySQL，本地+VPS 共用同一 DB）

**本地状态**:
- backend PID: **10711**（nohup uvicorn 无 --reload，Wave 5.1 代码）
- frontend PID: **11608**（npm start，20 routes 0 errors）
- 日志: `/tmp/backend_w52.log`

**后端新增端点（@frontend / @tester 注意）**:
- `POST /api/projects/{uuid}/toggle-favorite` — 点赞/取消点赞
- `POST /api/share/create` — 创建分享 token
- `GET /api/share/{token}/view` — 公开分享页数据

**前端新增路由（@frontend / @tester 注意）**:
- `/s/[token]` — 公开分享页面（无需登录）
- `frontend/src/hooks/useStageLock.ts` — 生成中阶段锁定 hook

---

## TASK-T6-FIXBATCH Wave 4 完成 (2026-04-29) — Wave 1.1+1.2+2+2.5+3.5 全部上生产

**全员注意 — T6 修复批次已全部部署到生产 VPS**:

- commit `84a2d35` push range `434c2f0..84a2d35` (84 files, +18818/-1069)
- rsync app/ + frontend/src/ + [projectUuid]/ + package.json → VPS
- docker compose build api + frontend + force-recreate
- api StartedAt: `2026-04-29T08:02:18Z`
- /health: `{"status":"healthy"}` ✅

**后端改动上线（@backend / @tester 注意）**:
- `pipeline_orchestrator.py`: stage label 重构 + ETA + aspect_ratio 穿透 + ARCH-1 批量写
- `job_manager.py`: mark_completed stage='completed' + aspect_ratio
- `projects.py`: adjust_character() 触发 portrait 重生 + regenerate-portrait 端点
- `chapters.py`: /status 接入 estimate_remaining() ETA
- `character_prompt_builder.py`: isinstance(dict) 防御（R7-3 修复）
- `schemas/project.py`: cover_image_url + shot_count + mood + ISO 时区
- `seedream_generator.py` (新): Seedream 生图服务（7 种比例）

**前端改动上线（@frontend 注意）**:
- `[projectUuid]/[stage]/page.tsx` (新): dynamic route
- `url.ts` + `createUrl.ts` (新): toAbsoluteUrl 共享工具
- StageD: toAbsoluteUrl 修复 404（R7-12）
- StageC: portrait_url fetch + 完成态 + carousel fix
- StageE: outline.summary
- StoryCard + AuthContext: 读新 Dashboard 字段

**生产 T8 验证 PASS**:
- UUID: `a3966a40-6d27-42c0-a7cf-109729e453e7`（"牵手走过的街"，1:1 画幅，16 shots NB2 真生图）
- D.15 PASS（1:1→1024x1024 正方形，不再 hardcoded 2:3）
- R7-1 PASS（cover_image_url + shot_count=16 在 /api/projects/ 返回）
- R7-3 PASS（adjust portrait mtime 变化验证）
- UX-16 PASS（/create/{uuid}/preview HTTP 200）

**当前 VPS 状态**:
- SKIP_IMAGE_GENERATION: True（验证完恢复，节省成本）
- 3 容器: api(healthy) + frontend(up) + redis(healthy)

---

## TASK-VPS-SKIP-IMAGE 完成 (2026-04-24 13:32) — VPS api 已配置 SKIP_IMAGE_GENERATION=true

**全员注意 — VPS 生产环境 Stage 5 图像生成已切换为 SKIP（R8 mock 图）模式**:

- `.env.production` 追加 `SKIP_IMAGE_GENERATION=true`（幂等写入）
- `docker compose up -d --force-recreate api` → docker-api-1 重建
- 容器内 `settings.SKIP_IMAGE_GENERATION = True` 已验证
- api StartedAt: `2026-04-24T05:30:37.588742043Z`
- `/health` = `{"status":"healthy"}` ✅

**影响面**（对 @backend / @frontend / @tester 说明）:
- VPS 生产环境 pipeline Stage 5 不再调用 NB2（Gemini 3.1 Flash Image），改用 R8 数据目录的 mock 图
- 避免每次测试 ~$2 的 NB2 图像生成成本
- 本地 .env 已有 `SKIP_IMAGE_GENERATION=true`，两端一致
- **不改代码、不 push、不改 DB、不动 frontend/redis**

**Bash 权限**: ✅ 可用

---

## TASK-BUG-FIX-BATCH-1 Route D 完成 (2026-04-23 17:10) — VPS 已同步

**全员注意 — 18 bug 修复 (Route B + Route C) + output volume 新增 已上生产**:

- commit `3fa2a73` "fix: Pipeline UX/BGM/SKIP bugs + FE StrictMode completedRef race" (20 files, +1050/-77)
- commit `6518563` "fix(docker): add output_data volume mount for /app/output" (1 file, +2)
- push range: `928a621..6518563`
- rsync app/ (main.py + job_manager.py + pipeline_orchestrator.py) + frontend/src/ (StageC.tsx + CreateContext.tsx) + docker/ (docker-compose.yml)
- VPS `docker compose build api` + `docker compose build frontend` (20 routes, 0 errors)
- `docker compose up -d --force-recreate api frontend` → `docker_output_data` 新 volume 创建
- api StartedAt: `2026-04-23T09:01:10Z`
- 外部: https://prefaceai.mov 200 + /api/health 200

**影响面（对 @tester / @frontend / @backend 说明）**:

**后端改动** (Route B):
- `job_manager.py`: checkpoint_callback isinstance 守卫 — `bgm_url`/`bgm_meta_version` 等 String 列不再被 json.dumps 双重引号包裹
- `pipeline_orchestrator.py`: SKIP_IMAGE_GENERATION 模式现在复制 R8 参考图到 `output/{uuid}/images/`，写 image_url 回 storyboard.shots，重新 checkpoint storyboard_json，前端预览页可正确加载图片
- `pipeline_orchestrator.py`: Stage 6 BGM 现在 checkpoint credits_used
- `app/main.py`: 新增 `/static/outputs` StaticFiles mount → `./output/`（容器内 `/app/output`，已由 `docker_output_data` volume 持久化）

**前端改动** (Route C):
- `StageC.tsx`: FE-5 completedRef 在 shot-gen effect 入口重置，完成触发条件扩展（status===completed OR progress>=100），提取 finalizeAndGoToPreview 带 console 时间戳
- `StageC.tsx`: FE-1 STAGE_LABEL map，resolvePhaseTitle 分层 fallback
- `StageC.tsx`: FE-3 progress 直接信任后端值，不再 Math.max-clamp
- `CreateContext.tsx`: FE-2 UPDATE_GENERATION_PROGRESS reducer 用 full-list .some() dedup，防重复 timeline 条目

**docker volume 新增**:
- 旧: api 仅挂 `storage_data:/app/storage` + `sqlite_data:/app/data`
- 新: 加 `output_data:/app/output`（持久化 pipeline 产物，StaticFiles 依赖此目录）
- VPS Docker 已创建 `docker_output_data` named volume

**Bash 权限**: ✅ 可用

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确
- ✅ 未碰 .env / DB schema / redis
- ✅ 未在 VPS 上 git pull
- ✅ build + force-recreate

---

## TASK-LOCAL-BACKEND-HUNG 完成 (2026-04-23 15:05) — 本地 backend 已恢复

**全员注意 — 本地 backend 已干净重启**:

- **PID**: 21995（nohup uvicorn，无 --reload）
- **日志**: `storage/logs/uvicorn_nohup.log`
- **启动时间**: 2026-04-23 15:04:24 Application startup complete
- **/health**: `{"status":"healthy"}` ✅
- **auth 端点**: POST /api/auth/login 返回 `{"detail":"邮箱或密码错误"}` ✅（不再超时）

**根因（给所有 Agent 备忘）**:
- `uvicorn --reload` + 阿里云远程 MySQL 高延迟 → reload 期间旧 worker startup 事务未提交被 kill → 新 worker DESCRIBE 等 metadata lock → 死锁
- 触发 reload 的文件：今日 TASK-P0P1-LOGGING-FIX 改动（image_generator.py / chapters.py / pipeline_orchestrator.py）的 mtime 变化

**下次避坑**:
- 本地 backend **不要用 --reload 模式**，用 `nohup uvicorn ... &`（无 --reload）
- 如果必须热重载：改代码后手动 kill + 重启，不要依赖 inotify 自动 reload
- DEBUG=true 在 .env 里，但 CLI 不传 --reload，两者相互独立

**其他**:
- MySQL SHOW PROCESSLIST: 无本机 zombie 连接（kill 后连接池随进程退出，干净）
- VPS 连接（107.148.1.199: 5 条 Sleep）正常，是 VPS api 容器的连接池

---

## TASK-P0P1-DEPLOY 完成 (2026-04-23 14:35) — VPS 已同步

**全员注意 — Ben utf8mb4 patch + P0P1 logging fix 已一并上生产**:

- git pull --rebase 融合 Ben commit `4725e9e` "fix: ensure charset=utf8mb4 is always set in database URL"
- commit `d154ce1` "fix(logging): P0P1 exception logging + docker log rotate" (12 files, +1088/-377)
- push origin main: `4725e9e..d154ce1`
- rsync `app/` → VPS (4 代码文件: database.py / api/chapters.py / services/image_generator.py / services/pipeline_orchestrator.py)
- rsync `docker/` → VPS (docker-compose.yml logging 配置)
- VPS `docker compose build api` + `up -d --force-recreate api`
- 容器 StartedAt: `2026-04-23T06:31:38Z`

**影响面**（对 @backend / @tester / @frontend 说明）:
- 9 个 chapters.py GET 端点现在有 try/except，500 响应会含 `{"detail":"服务异常: {type}: {msg[:200]}"}`
- 3 个 BackgroundTasks（generate_images / regenerate_single_image / generate_audio_and_align）现在异常会写 `chapter.status='failed' + error_message=traceback[:10000]`（行为变化：failed 任务可见）
- `regenerate_single_image_task` 现在会写 `SceneImage(error_message=..., is_active=True)` 让 GET /images 看到失败记录
- `image_generator.py` 65 处 print 全部转 logger（logger.info/warning/error），对前端/API 无影响，只是日志可搜索
- pipeline_orchestrator.py L1074 裸 except 改 `except Exception as e: logger.exception`（保留原吞异常行为）
- VPS docker log rotate: `max-size=50m, max-file=5`（最多 250MB），Ben 排查 500 不再丢 traceback

**6 项验证 PASS**:
| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | {"status":"healthy"} ✅ |
| logging config | max-size 50m max-file 5 | map[max-file:5 max-size:50m] ✅ |
| logger count in image_generator | ≥ 60 | 65 ✅ |
| Ben utf8mb4 patch | _db_url + if "charset=" not in | ✅ |
| StartedAt | 2026-04-23 | 2026-04-23T06:31:38Z ✅ |
| bare except in pipeline_orchestrator | 0 | 0 ✅ |
| bonus: print count in image_generator | 0 | 0 ✅ |

**Bash 权限**: ✅ 本次可用（一轮通过，无被拒）

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确（`app/` → `/opt/xuhua-story/app/`）
- ✅ 未碰 .env / DB schema / frontend / redis
- ✅ 未在 VPS 上 git pull
- ✅ build + force-recreate（compose 配置变了必须 recreate）

**补充说明**: PM 任务 Step 5 只写 `up -d --force-recreate`，但由于 Dockerfile.api `COPY app/ ./app/` 是 baked-in（非 volume mount），**必须先 `docker compose build api`** 才能把新代码打进 image。首次 up -d 后发现旧代码仍在容器内，补做 build 后验证才全部通过。

---

## TASK-P0P1-LOGGING-FIX 完成 (2026-04-23 11:30) — 已部署（上面块）

**全员注意 — docker-compose.yml api 服务已加 logging 配置，等待下一轮统一部署**:

- 文件: `docker/docker-compose.yml`，api 服务 healthcheck 块之后新增 5 行 logging 配置
- 配置: `driver: json-file`, `max-size: 50m`, `max-file: 5`（最多 250MB 日志保留，5 个文件轮转）
- 效果: 下次 api 容器重建后，VPS `docker logs docker-api-1` 将保留更长历史，Ben 排查 500 错误不再丢 traceback
- YAML 语法验证: `docker compose config --no-interpolate` 返回码 0，无错误
- **此改动已就绪，等待 @backend 完成当前代码改动后 PM 统一安排 rsync + Docker rebuild 部署**
- 其他服务（redis / worker / frontend / mysql）未改动

---

## TASK-DEPLOY-LLM-SAMPLING 完成 (2026-04-23 10:55)

**全员注意 — 今日 LLM sampling 改动已同步到生产 VPS**:

- commit `cb5e395` "chore: unify LLM sampling params (temperature + max_tokens)" 已 push origin main
- 覆盖两个任务: TASK-LLM-TEMP-AUDIT-FIX (15 处 temperature 显式化 + sync max_tokens 8192→16384) + TASK-8631-UNIFY (13 处 8631→16384, 5 files)
- rsync `app/` → VPS `/opt/xuhua-story/app/`（8 代码文件: api/utils.py + services/ 下 7 个）
- VPS docker compose build api + force-recreate api
- 4/4 验证 PASS: /health healthy + character_designer 16384×2 + shot_validator temperature=0.2 + StartedAt 刷新到 2026-04-23 + app/ 下 8631 零命中
- 容器 StartedAt: `2026-04-23T02:52:27Z`（从 2026-04-21T10:05:10Z 刷新）
- **无前端 / redis / DB / env 改动**

**影响面**（对 @backend / @ai-ml / @tester 说明）:
- 对齐/验证/OCR/视觉分析的 Claude + Gemini 调用：temperature=0.2（稳定性提升）
- Stage 3 剧本 + Stage 4 分镜：主备模型都 temperature=0.8（显式化，主备一致）
- sync Claude `messages.create` max_tokens=16384（防长故事截断）
- 所有 LLM token 上限统一 16384，不再有 8631 遗留（character_designer / alignment_service / story_outline_generator L196 / storyboard_director / screenplay_writer 全量覆盖）

**Bash 权限**: ✅ 本次恢复正常（上次 2026-04-21 Mureka 部署二次被拒，PM 代执行）

---

## TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 VPS 部署完成 (2026-04-21)

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

## 历史状态（5/18 快照）

状态: ✅ **TASK-T20-FIXBATCH-2 T18-I IncompleteRead 监控 Dashboard 完成** (2026-05-18)

### T18-I 新增 DevOps 工具（2026-05-18）

**IncompleteRead 监控脚本**:
- `scripts/monitor_incompleteread.py` — 解析 backend.log，统计 Seedream 下载 IncompleteRead 频率
- `scripts/monitor.yaml` — 告警阈值配置（4 个参数，唯一调参入口）
- `docs/MONITORING_INCOMPLETEREAD.md` — 完整部署 + 使用 + VPS cron 部署方案

**基线数据**（test18, 2026-05-18）:
- 每故事约 8 次 IncompleteRead，全部 1 次 retry 成功，成功率 100%
- WARN 阈值: 每小时 >= 20 次；CRITICAL 阈值: 每小时 Retry 耗尽 >= 3 次

**如何使用**:
```bash
# 立即查看当前状态
python3 scripts/monitor_incompleteread.py --log logs/backend.log
# 调阈值只需改 scripts/monitor.yaml
```

---

## 上次状态速览

状态: ✅ **TASK-WAVE9-P2-DEVOPS-FRONTEND-IMPACT-HOOK 完成** (2026-05-13, Wave 9 Phase 2)

### Wave 9 新增 DevOps 工具

**pre-commit hook (DEC-030 Ben 方案 B)**:
- `scripts/pre-commit-frontend-impact.sh` — 核心 hook，检测 6 个契约高风险文件
- `scripts/install_pre_commit_hook.sh` — 一键安装脚本
- `docs/CONTRACT_HOOK.md` — 使用文档
- `.git/hooks/pre-commit` — symlink 已安装

**对 @backend / @ai-ml 的影响**:
- 改以下文件 commit 时，必须在 commit message 加 `[frontend-impact: yes/no]` label
- 受影响文件: `app/api/projects.py`, `app/api/chapters.py`, `app/services/pipeline_orchestrator.py`, `app/services/job_manager.py`, `app/models/project.py`, `app/schemas/project.py`
- 安装 hook: `bash scripts/install_pre_commit_hook.sh`
- 临时跳过: `git commit --no-verify`（强烈不建议）

最新 commit（Wave 9 前）: `6518563` (fix(docker): add output_data volume mount, 1 file)
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
最新 commit: 6518563 fix(docker): add output_data volume mount for /app/output (1 file)
前一 commit: 3fa2a73 fix: Pipeline UX/BGM/SKIP bugs + FE StrictMode completedRef race (20 files)
```

---

## 环境状态

| 环境 | 状态 | 最近更新 |
|------|------|----------|
| dev | 🟢 运行中（本地开发） | 2026-03-19 |
| staging | ⚪ 未部署 | - |
| prod | ✅ **安全加固已部署**（等待 API Key） | 2026-03-18 |
| git | ✅ 双团队文件已推送（两人直接 push main） | 2026-03-19 |
