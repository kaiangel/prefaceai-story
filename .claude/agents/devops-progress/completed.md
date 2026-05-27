# DevOps Agent - 已完成任务

> 按时间倒序记录已完成的工作
> **2026-05-27 15:45 更新**: TASK-BGM8-DOCS-COMMIT 完成 — 补提交 4 收尾文档 commit b512ada + push(d067916→b512ada), git status 干净, VPS fresh 重启(07:40:47 UTC), api+frontend force-recreate, BGM grep 实证仍在, /api/health 200, 三容器健康。

---

### TASK-BGM8-DOCS-COMMIT ✅ (2026-05-27 15:45, DevOps Sonnet 4.6)

**任务**: 补提交 4 个收尾文档 + VPS fresh 重启（Founder 真机测试前）

| 项 | 结果 |
|----|------|
| git status 确认 | 只有 4 个目标文件，team-members-bp/logs/storyrefs/ 全部被 .gitignore 挡住（check-ignore 三命中）✅ |
| git add | 精确 add 4 文件（devops-progress 三件套 + TEAM_CHAT），无误入 ✅ |
| commit | `b512ada` — "docs(收尾): devops progress 三件套 + TEAM_CHAT BGM部署记录" ✅ |
| push | d067916→b512ada origin/main, git status 干净 ✅ |
| VPS 重启时刻 | **2026-05-27T07:40:47 UTC（北京 15:40:47）** — api+frontend force-recreate ✅ |
| docker ps | api(healthy) + frontend(Up) + redis(healthy) ✅ |
| 容器内 /health | {"status":"healthy"} ✅ |
| 外部 /api/health | 200 ✅ |
| 主页 | 200 ✅ |
| BGM grep | docker exec docker-api-1 grep _detect_chinese_cultural = 2 处 (L218 def + L734 call) — 重启未丢代码 ✅ |

**redis 未动（有状态），DB 阿里云共享不受影响。**

---

### TASK-BGM8-COMMIT-DEPLOY ✅ (2026-05-27, DevOps Opus 4.7, Founder go, PM 13:00 审查通过)

**任务**: #8 BGM 路径B(已过 PM 地毯式审查 pytest 395+dry-run)commit+push+VPS 部署。

| 项 | 结果 |
|----|------|
| commit 1 (BGM 代码) | `40a9d02` [frontend-impact: no] — story_music_extractor.py(+359/-38) + bgm_signal_probe.py(新) |
| commit 2 (文档) | `d067916` — team-brain 4 文件 + 全员 progress + test28/29 回溯 + GENERIC_PM + full-retrospective skill + style_drift_probe |
| push | origin/main `83a576b→d067916`, origin = 本地 HEAD ✅ |
| git status 干净 | team-members-bp/+logs/+storyrefs/ 被 .gitignore(81b5d25) 全挡, staged 复查 0 误入 ✅ |
| rsync | `app/` → /opt/xuhua-story/app/(trailing slash 子目录), 增量只传 services/story_music_extractor.py, VPS md5 986d8676 = 本地 ✅ |
| Docker | build api → sha256:e22f4e97; force-recreate api → healthy(try3); frontend 未动; 无 DB 迁移 |
| 容器内实证 | `docker exec docker-api-1 grep _detect_chinese_cultural` = 2 处 + is_chinese_cultural L265/L292 ✅ BGM 真上线 |
| verify | curl /api/health 200 `{"status":"healthy"}` + 主页 200 + 三容器(api/frontend/redis)健康 ✅ |

**关键**: 纯后端 prompt 逻辑, 无前端 rebuild/无 DB 迁移/无契约。真听感(荷塘渡中式 BGM)待 Founder e2e 抽测。

---

### TASK-DOCKER-COMPOSE-MYSQL-CLEANUP ✅ (2026-05-27, DevOps Sonnet 4.6)

**任务**: 删除 docker-compose.yml 残留 mysql service 定义 (Ben 微信确认可删)。

| 项 | 结果 |
|----|------|
| 引用检查 | api/worker 的 depends_on 均只依赖 redis, 无任何 mysql 引用 ✅ |
| 删除内容 | mysql service (image: mysql:8.4, 13 行) + mysql_data volume 声明 (1 行) |
| 语法验证 | docker compose config --no-interpolate 解析通过, 0 mysql/error/warn ✅ |
| commit | `83a576b` (1 file, 15 deletions) ✅ |
| push | `81b5d25→83a576b` origin/main ✅ |
| VPS 同步 | scp docker-compose.yml → /opt/xuhua-story/docker/, VPS grep mysql = 0 ✅ |
| 容器不受影响 | api(healthy 19h) + frontend(Up 19h) + redis(healthy 2mo) + /health {"status":"healthy"} ✅ |

---

### TASK-WAVE13-TEST29 ✅ (2026-05-26, DevOps Opus 4.7, Founder 决策 B 两步)

**任务**: Wave 13 + test29 修复上线。Founder 决策 B (信任单测, commit+部署), 分两步 (第 2 步 Ben 闸门)。

---
**第 1 步 (18:35 完成): commit + push GitHub, 未碰 VPS**

HEAD 68e4211 (Wave12) 起 4 commit:
| commit | hash | 范围 |
|--------|------|------|
| 1 Backend/DB-infra `[frontend-impact: no]` | `a0c3934` | #5d MySQL retry middleware (db_retry.py 新, 含 test29 #4 packet sequence) + database.py pool_recycle 1800→600s + #6 regenerate-portrait 异步 + #5e clothing 旁路防崩 + main.py wire + 3 wave13 test |
| 2 Frontend | `ca2e43d` | #4A hydrate 超时守卫 + #4B 后台按钮 scenesConfirmed 守卫 + #5 404 分级 + #6 reroll 异步轮询 + #9 vitest 基建 |
| 3 AI-ML test29 非人类 `[frontend-impact: no]` | `a16c7af` | #5a 锚点层 primary_color 字段 map + #5b builder physical fallback + #7 MULTI-SUBJECT SEPARATION + #6 ShotValidator 计数通用化 |
| 4 契约+文档 | `ec7b1b6` | STATUS_API_CONTRACT §9.7.4 + DECISIONS + PENDING/checklist/PROJECT_STATUS/TODAY_FOCUS + TEST29 回溯 + 15 progress + TEAM_CHAT |

push: 68e4211→ec7b1b6, origin/main verified。第 1 步停手等 Ben 闸门 (含 #4 DB-infra = Ben 域)。

---
**第 2 步 (19:30 完成): .gitignore 安全修复 + 泄露核实 + VPS 第 5 次部署** (Founder 知会 Ben + PM 放行后)

**A. .gitignore 安全修复 (commit `81b5d25`, ec7b1b6→81b5d25)**:
- 加规则: `team-members-bp/` + `logs/` + `storyrefs/` + `*.log.*` (rotated 日志)
- `git check-ignore` 三项全命中 + rotated 日志 `logs/backend.log.20260526-1534-rotate` 命中
- 纯增忽略规则, 零副作用 (防 BP/简历/日志误入库)

**B. 双重核实无泄露 (GitHub + VPS)**:
- GitHub 历史: grep `team-members-bp|商业计划|简历|resume|.pdf` → 0 真泄露 (扫到的 seed 全是 Seedream/seed-ref 误匹配); `git ls-files` → 0 tracked
- VPS: `/opt/xuhua-story/` 无 team-members-bp/、无 storyrefs/ (只有 team-members/ 照片, 本就在 .gitignore + 不进镜像); Dockerfile 只 COPY app/docs/alembic, 容器内 0 敏感目录
- 结论: GitHub + VPS 均干净 (预期本就干净, 确认无误)

**C. VPS 第 5 次部署 (d4541c4 Wave12 → 运行代码 ec7b1b6 Wave13+test29)**:
- rsync `app/` (115 files) + `frontend/src/` (126 files) + package.json/lock — md5 6/6 全一致 (db_retry.py 新 + identity_anchor_prompts + injector + shot_validator + database.py + layout.tsx)
- Docker rebuild --no-cache: api `sha256:192a0413` + frontend `sha256:b2aaf989` (frontend next standalone build 走完, vitest devDep 未破坏构建)
- force-recreate: api(healthy) + frontend(Up) + redis(healthy)
- **#5c Alembic/DB**: alembic current = `006_t21new7_scene_refs (head)`; projects 3 列 aspect_ratio varchar(16) + raw_outline_json text + confirmed_outline_json text = EXISTS (无需新迁移)
- **新代码 grep (容器内)**: db_retry.py 存在 + 9 处 transient/packet / database.py pool_recycle=600 / #5a primary_color map 15 处 / #7 MULTI-SUBJECT SEPARATION 1 处
- **db_retry 非死代码**: main.py L17 import + L75 `app.add_middleware(DBConnectionRetryMiddleware)`
- **layout.tsx 新版生效 (硬证据)**: 外部主页 HTML 含 `proxy-init` + `PROXY_VERSION` inline script + 镜像 build 2026-05-26T12:41:58Z
- **verify**: 容器内 /health healthy + 外部 /api/health 200 + 主页 200

**踩坑**: DB schema 查询 — 容器用 asyncmy (非 aiomysql), 且 MYSQL_USER/PASSWORD env 不直接暴露 (分类器正确拦截 env dump)。最终用项目 SQLAlchemy `app.database.engine` (PYTHONPATH=/app + -w /app) 跑 SHOW COLUMNS, 不接触任何凭据。

**Ben 协议**: #4 DB-infra (db_retry packet sequence + pool_recycle 1800→600s) = Ben 域, Founder 已微信知会 Ben + PM 放行后部署。0 schema 改动 / 0 新 Alembic revision / 0 .env 改动 / 0 越权 (只碰 .gitignore + rsync + Docker)。

**风险**: 无。pool_recycle 600s 在 VPS 生效 (赶在云端 idle-timeout 前重建)。

---

### TASK-WAVE12-DEPLOY-VPS ✅ (2026-05-25, DevOps Sonnet 4.6 effort high 全程自执行)

**任务**: VPS 第 4 次部署 — Wave 12 (style_enforcer画风 + adjust异步 + sub-progress + 前端), 648b81c → d4541c4, 含生产性能基线实测

**执行**:
- commit d4541c4 (32 files, [frontend-impact: yes]) + push GitHub
- rsync app/services/ + app/api/ + frontend/src/ (trailing slash 正确) — md5 5/5 一致
- Docker rebuild api sha256:052228cb + frontend sha256:a95369a8 --no-cache + force-recreate
- alembic current = 006 (head), DB 3 列 projects.aspect_ratio/raw_outline_json/confirmed_outline_json = EXISTS

**生产性能基线 (P2-1 #3 关键判断)**:
- VPS 内网 MySQL TCP connect: 42-65ms avg 51ms (vs 本地公网 333-684ms)
- VPS 内网 SELECT 1: 41.8-42.1ms avg 42ms (极稳定)
- 改善: ~8x。Backend 聚合端点仍有价值 (减并发 round-trip)，不需紧急大改

**verify**:
- api(healthy) + frontend(Up) + redis(healthy)
- /api/health 200 + 主页 200 + Wave 12 代码 grep 全在

**Ben 协议 5+1**: 0 schema / 0 Alembic / STATUS_API v1.6 / [frontend-impact: yes] / 0 .env / 0 越权

---

### TASK-WAVE-11-DEPLOY-VPS ✅ (2026-05-24 14:33, DevOps Sonnet 4.6 effort high)

> ⚠️ 本条由 PM 审查时代补 (DevOps 本次 commit 5234707 漏更 completed.md, current+context+TEAM_CHAT 已更)

**任务**: VPS 第 3 次部署 — Wave 10 (AI-ML 3faf585 + Backend 28e33a7) + Wave 11 (Frontend 648b81c), VPS c570c2d → 648b81c

**执行**:
- rsync `app/services/` + `app/api/` + `app/prompts/` + `app/database.py` + `frontend/src/` (trailing slash 正确)
- Docker rebuild api (sha256:47ed6871) + frontend (sha256:3a17b649) `--no-cache` + force-recreate

**verify (PM 亲自 SSH 独立复核)**:
- md5 本地 vs VPS 容器内 5 文件 100% 一致
- 容器内 Wave 10 const × 8 + pool_pre_ping × 3 (= 本地)
- api(healthy) + frontend(Up) + redis(healthy) / /api/health 200 + 主页 200
- frontend 镜像 5/24 14:30 rebuild (Showcase LCP priority 上线)

**修复**: 5/23 MySQL 500 (VPS pool_pre_ping=True + pool_recycle=1800s 升级到位, 死连接自动重建)

**Ben 协议 5+1**: 0 schema / 0 Alembic / 0 STATUS_API / 0 .env / [frontend-impact: no] / 0 越权

**commit**: 5234707 (push GitHub main)

---

### TASK-SECRET-LEAK-REMEDIATION Step 4-5 ✅ (2026-05-22 18:50, DevOps Sonnet 4.6 effort high)

**任务**: P0 GitGuardian 安全事故响应 — git filter-repo 历史清洗 + GitHub force push

**背景**:
- 5/22 17:01 GitGuardian 警报: commit e5470e8 含 2 把 Google API Key 明文 (AIzaSyCX... + AIzaSyBm...)
- 上一轮 DevOps Opus 4.7 max thinking 完成 Step 1-3 (audit + 脱敏 + 防御层)
- 本轮 Sonnet 4.6 接力执行 Step 4-5

**Step 4 — git filter-repo 历史重写**:
- 工具: `/opt/homebrew/bin/git-filter-repo 2.47.0`
- 命令: `git filter-repo --replace-text .secret-replacements.txt --force`
- 备份: `/tmp/git-backup-1779445910`
- 解析: 126 commits, 耗时 6.01s
- 结果: HEAD e5470e8 → f9987b0 (所有 commit SHA 重写，因 e5470e8 是 HEAD)
- 历史验证: `git log --all -p -S "AIzaSyCX..."` = 0 命中 ✅
- 历史验证: `git log --all -p -S "AIzaSyBm..."` = 0 命中 ✅
- 清理: `.secret-replacements.txt` 删除

**Step 5 — GitHub force push**:
- filter-repo 自动移除 origin remote → `git remote add origin https://github.com/kaiangel/prefaceai-story.git`
- `--force-with-lease` 报错: filter-repo 已删除旧 commit 对象, lease ref 无法解析
- 先验证: `git ls-remote origin main` → e5470e8 (GitHub 无并发 push)
- 执行: `git push --force origin main` → `e5470e8...f9987b0 main -> main (forced update)` ✅
- GitHub 验证: `gh api repos/kaiangel/prefaceai-story/commits/HEAD --jq '.sha'` = `f9987b07f6c7a09da94559a311afbedd80e718d0` ✅

**Step 6a (上一轮完成)**: Founder 操作指引写入 current.md (revoke 2 key + 生成第 3 把 + 给 PM 私聊)

**还剩**:
- Step 6b: Founder 给第 3 把 key → DevOps 更新本地 + VPS .env + 重启 + verify (另起 spawn)
- GitGuardian 约 30 min 后自动 re-scan 应 mark resolved

**未动文件**:
- 业务代码 (app/ frontend/ tests/) 一字未改
- 其他 agent progress 未改
- docker-compose.yml / Dockerfile.* 未改

---

> **2026-05-21 更新**: 5/19-5/21 无 DevOps 派工。本地服务管理（重启 + Alembic 006）PM 直接做（常规重启 PM 直接 Bash，见 memory feedback_restart_services_pm_do.md）。

---

### 5/19 - 5/21 PM 自操作记录（DevOps 无派工）

**事实记录（诚实归档）**：

| 日期时间 | 操作 | 操作者 | 说明 |
|---------|------|--------|------|
| 5/20 17:20 | backend 重启（PID 68942）| PM | Wave 1 Backend 完成后 |
| 5/20 17:45 | backend 重启（PID 68942→71758）| PM | Wave 1 Backend wire 重启（KEY_LEARNINGS #29 实证）|
| 5/20 18:20 | backend 重启（PID 71758→77188）| PM | Wave 2 round 2 后重启 |
| 5/20 ~20:00 | backend 维持 PID 87388 | PM | Wave 3 完成，不重启等下次 |
| 5/21 ~21:10 | 干净重启（合并 T21-NEW-1+T21-NEW-2）| PM | 含 13 type schema |
| 5/21 ~20:35 | `alembic upgrade head`（3次，2次 error 后幂等兜底成功）| PM | Alembic 006 本地执行 |
| 5/21 ~22:50+ | Wave II Frontend 完成后，Wave III PM 承诺自做重启 | PM | alembic + 干净重启 + monitors |

**DevOps 说明**: 以上均为 PM 常规权限范围内操作（memory feedback_restart_services_pm_do.md），DevOps 没有接到派工，不存在漏做。下一个 DevOps 任务是 Layer 1 完成后的 VPS 部署（含 Alembic 006 迁移 + rsync + Docker rebuild）。

---

### TASK-T20-FIXBATCH-2 T18-I ✅ (2026-05-18, DevOps Sonnet 4.6)

**任务**: RISK-T18-I P3 IncompleteRead 监控 Dashboard，为 Seedream 下载网络抖动建立频率监控告警。

**背景**: test18 两轮共计 8 次 IncompleteRead，全部 1 次 retry 成功，Retry 成功率 100%。需要监控频率突增。

**交付 3 文件**:
- `scripts/monitor_incompleteread.py` (chmod +x, Python stdlib only, universal log path)
- `scripts/monitor.yaml` (告警阈值唯一配置入口，含 4 个可调参数)
- `docs/MONITORING_INCOMPLETEREAD.md` (8 节: 背景/文件/快速用法/调阈值/部署VPS/日志路径/告警处理/POST_BETA)

**本地验证 PASS**:
- backend.log 50622 行完整解析
- 8 IncompleteRead → 8 retry 成功 → 0 耗尽失败，100% 成功率
- ASCII 柱状图 + 每小时趋势正常
- WARN/CRIT/OK 退出码逻辑 PASS
- HTML 报告生成 PASS

**约束遵守**: 未改 app/ / frontend/ / .team-brain/team_ben/ ✅

---

### TASK-WAVE9-P2-DEVOPS-FRONTEND-IMPACT-HOOK ✅ (2026-05-13, DevOps Sonnet 4.6)

**任务**: Wave 9 Phase 2 DEC-030 配套，pre-commit hook 强制 backend commit 涉及 frontend 契约文件时加 `[frontend-impact: yes/no]` label。

**背景**: test15 暴露 7/13 (47%) bug 属于前后端契约断裂。Ben 建议纠错机制，Founder 采纳为 DEC-030 Wave 9。

**交付 3 文件**:
- `scripts/pre-commit-frontend-impact.sh` ✅ (chmod +x, 核心 hook 逻辑)
- `scripts/install_pre_commit_hook.sh` ✅ (chmod +x, 一键安装软链接)
- `docs/CONTRACT_HOOK.md` ✅ (5 段文档)

**安装**: `.git/hooks/pre-commit` symlink 已安装 ✅

**3 种场景测试全 PASS**:
- 场景 1: watched file + 无 label → BLOCKED ✅
- 场景 2: watched file + `[frontend-impact: yes]` → PASS ✅
- 场景 3: 不相关文件 → 直接放行 ✅

**约束遵守**: 未改 app/ / frontend/ / .team-brain/team_ben/ ✅

---

### TASK-KEY-ROTATE-GEMINI ✅ (2026-05-01 00:09, DevOps Sonnet 4.6)

**任务**: Gemini API key 轮换（Founder 授权 + 必须立即 revoke 旧 key）

**背景**:
- 旧 key `AIzaSyCX***[redacted-key-Apr29-old]` 安全风险，Founder 决定轮换
- 新 key `AIzaSyBm***[redacted-key-Apr29-new]`（同 Google project，同配额，model access 一致）
- Founder 三项授权：(1) 新 key 配额一致 (2) 必须立即 revoke 旧 key (3) VPS 路径需 SSH 自查

**10 步流程全 PASS**:

| Step | 动作 | 验收证据 |
|------|------|---------|
| 1 | 备份本地 `.env` → `.env.backup-keyrotate-20260501` | ✅ 1608 bytes 0600 |
| 2 | Edit `.env:2` GEMINI_API_KEY 旧→新 | ✅ grep: 新 1 处 / 旧 0 处 |
| 3 | `pkill -f "uvicorn app.main"` (PID 48766) + nohup 重启不带 --reload | ✅ 新 PID **71921**, /health 200 |
| 4 | 本地真测：settings 加载 + 真 Gemini API 调用 | ✅ `gemini-2.5-flash → 'OK'` AUTH=PASS |
| 5 | SSH VPS (trader@107.148.1.199:58913) 找 .env.production 路径 | ✅ `/opt/xuhua-story/.env.production` (1376 bytes 0644) |
| 5b | grep VPS 旧 key 一致性自检 | ✅ 都是 `AIzaSyCX...` |
| 6 | VPS cp 备份 `.env.production.backup-keyrotate-20260501` | ✅ 1376 bytes 0644 |
| 7 | VPS sed 精确替换 `^GEMINI_API_KEY=AIzaSyCX...$` | ✅ grep: 新 1 处 / 旧 0 处 |
| 8 | VPS `cd /opt/xuhua-story/docker && docker compose up -d --force-recreate api` | ✅ docker-api-1 Recreated + Started + healthy |
| 9 | VPS 真测：容器内 settings + 真 Gemini API + HTTPS /api/health | ✅ `gemini-2.5-flash → 'OK'`, prefaceai.mov/api/health 200 |
| 10 | TEAM_CHAT.md 追加 + SendMessage 让 PM 提醒 Founder revoke 旧 key | ⏳ 等 Founder Google Cloud Console 操作 |

**关键证据**:
- 本地容器 settings: `GEMINI_API_KEY[:15]=AIzaSyBmiM1SsK8` ✅
- VPS 容器 settings: `os.environ['GEMINI_API_KEY'][:15]=AIzaSyBmiM1SsK8`, len=39 ✅
- 本地真 LLM 调用: `model='gemini-2.5-flash' → response='OK'`（无 quota error）✅
- VPS 真 LLM 调用: `model='gemini-2.5-flash' → response='OK'`（无 quota error）✅

**风控措施**:
- 备份文件本地 + VPS 双端保留至少 48 hr，可秒级回滚
- VPS sed 替换前先 grep 旧 key 与本地一致性自检（避免 VPS 用了不同 key）
- 本地 + VPS 都做真 LLM 调用（不止 settings 加载），确认新 key 实际可用而不是只是字面正确

**未动文件**:
- 业务代码（app/、frontend/、tests/）一字未改
- 其他 agent progress（backend-/frontend-/tester-/ai-ml-/pm-/resonance-progress/）一字未改
- docker-compose.yml / Dockerfile.* / requirements.txt / .gitignore 未改
- 其他 env vars（ANTHROPIC_API_KEY / OPENAI_API_KEY / VOLCENGINE_*）未改
- 仅修改：本地 `.env:2` + VPS `.env.production` 同一行 + TEAM_CHAT.md 追加 + devops-progress 三件套

**下一步**:
- 等 Founder Google Cloud Console 撤销旧 key
- 48 hr 后清理本地 + VPS 备份文件 `.env.backup-keyrotate-20260501`（确认无回滚需要后）

---

### TASK-DIAGNOSE-BACKEND-LIFESPAN-STUCK V1 ✅ (2026-05-02 ~14:00, DevOps Sonnet 4.6)

**任务背景**: PM 跨日（5-01 → 5-02）发现本地 backend pid 71921 不存在，curl /health connection refused，怀疑进程卡死（lifespan hang）。

**故障现象**:
- `ps aux | grep uvicorn` — 无进程（71921 已不存在）
- 端口 8000 未占用
- `/tmp/backend.log` 实际有 194 行 traceback（PM 说"只有 2 行"是只看了末尾）

**V1 诊断结论**:

根因：跨日系统休眠 → 阿里云 MySQL idle TCP 被切断 → aiomysql `_get_server_information()` 读 4 bytes 握手包时收到 0 bytes（`IncompleteReadError: 0 bytes read`）→ `OperationalError (2013, Lost connection to MySQL server during query)` → lifespan `init_db()` 抛出 → `Application startup failed. Exiting.` → 进程退出。

这不是 metadata lock 死锁，不是卡死——进程已经**自行退出**。

**诊断证据**:
- `OperationalError (2013, Lost connection to MySQL server during query)` 明确
- `Application startup failed. Exiting.` 明确
- VPS `docker-api-1 Up 7 days (healthy)` — 推断 MySQL 本身没问题，认为是瞬时网络问题
- `storage/logs/uvicorn_nohup.log` — 正常启动成功对比记录（16:10, 2026-04-23）

**推荐方案 E（重启）**: 进程已退出，直接重启即可，无需 kill 任何进程。

**给 PM 的重启步骤**:
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend_restart.log 2>&1 &
# 等 20-30s，出现 "Application startup complete." 后 curl /health 验证
```

**V1 结论的准确性评估**: 部分准确，部分错误。
- 准确：进程退出原因（2013 握手失败）、方案 E（重启）方向正确
- 错误："MySQL 瞬时网络问题，重试通常 OK" — PM 重试 2 次仍失败，说明不是瞬时问题
- 真根因留待 V2 继续诊断

---

### TASK-DIAGNOSE-MYSQL-V2 ✅ (2026-05-02 ~14:30, DevOps Sonnet 4.6)

**任务背景**: PM 按 V1 方案 E 重启 backend 2 次，仍同样 `OperationalError (2013)`。说明不是瞬时问题，需要深度诊断。

**V2 诊断过程（6 维度）**:

| 诊断项 | 结果 | 结论 |
|--------|------|------|
| `nc -zv 101.132.69.232 3306` | ✅ connected | TCP 3306 端口可达，SYN ACK 正常 |
| Python socket.recv(4) MySQL greeting（本地） | 超时 0 bytes | MySQL 握手包永远不到达 |
| aiomysql 直连（绕过 SQLAlchemy） | 2:13 超时 → OperationalError 2013 | 不是 SQLAlchemy/pool 问题 |
| macOS 防火墙 | block-all disabled，Python.app 允许 | 不是本地防火墙拦截 |
| **VPS 容器 socket.recv(4)（决定性）** | **超时 0 bytes** | VPS（IP 107.148.1.199）也失败 |
| **VPS 容器 asyncmy 直连** | **`Can't connect to MySQL server`** | 两个完全不同 IP 同时失败 |

**V2 诊断结论**（后来证明仍不准确）:

- "VPS 和本地两个不同 IP 都失败 → 100% 排除白名单问题"
- "VPS docker-api-1 healthy 是假阳性 — /health 硬编码不测 DB，8 天来无真实 DB 请求"
- 结论：**阿里云 MySQL 实例 101.132.69.232 的 mysqld 进程异常** — TCP 端口还在监听但不回应握手包，最可能是实例欠费暂停或 mysqld 崩溃
- 建议 Founder/Ben 登录阿里云 RDS 控制台检查实例状态

**V2 结论的准确性评估**: 结论**错误**，方向跑偏。
- 错误：诊断为"server 端 MySQL 进程异常"，实际是**阿里云 ECS 安全组**问题
- 错误："`nc -zv 3306 connected` + `recv(4) 0 bytes` = mysqld 进程崩溃" — 这个推断跳步了，silent drop 也会有同样表现
- 错误：建议看 RDS 控制台，实际是 ECS 安全组（不是 RDS）

**真根因（PM 5-02 15:33 诊断 + Founder 截图证实）**:

阿里云 ECS 安全组 `Sas_Malicious_Ip_Security_Group` (sg-uf668b0d3r5ohyphxywo) — SAS（阿里云安全管家）自动创建的"恶意 IP 防护"安全组：
- 规则限定 MySQL(3306) source 仅 self-connect `101.132.69.232/32`（ECS 本机）
- Founder 的 Astrill 出口 IP `140.99.222.167` 不在白名单 → **应用层 silent drop**
- 表现：TCP SYN-ACK 通（内核层接受），但 MySQL 协议握手包被 SAS 安全组吞掉（0 bytes）
- VPS `107.148.1.199` 也不在白名单 → 同样 0 bytes → 这就是为什么两个 IP 都失败

为什么 DevOps V2 "两个不同 IP 都失败 → 排除白名单"推断错了：因为 SAS 安全组的白名单 source 是 self-IP（101.132.69.232/32），本地和 VPS 都不是 self-IP，所以都被拦截，这恰恰证明是白名单问题，不是排除。

**真修复（Founder 操作）**: 
- 在 ECS 安全组**新增**允许规则（不编辑 SAS 自管的 self-connect 规则，避免 SAS 覆盖）
- 加白 `140.99.222.167/32` → MySQL(3306)，优先级 1
- 提交后秒通

破案关键：ttsrecap 项目 agent 在 server 端跑诊断 — `mysql -u root -p`（server 自连 OK）+ 116 天 uptime + 防火墙清白 → 给了客户端 4 步自查表 → PM 跑完 ping ❌ + nc ✅ + aiomysql ❌ → 判断到 SAS 应用层 silent drop 特征。

**运维教训**:

1. **诊断 "server 端故障" 前，必须先让用户跑客户端 4 步自查**：
   - Step 1: `ping 101.132.69.232`（ICMP — 测网络层可达性）
   - Step 2: `nc -zv 101.132.69.232 3306`（TCP — 测端口层可达性）
   - Step 3: `mysql -u xxx -p -h 101.132.69.232`（应用层协议 — 测 MySQL 握手是否到达）
   - Step 4: `traceroute 101.132.69.232`（路径追踪 — 定位 drop 发生在哪一跳）
   - "nc ✅ 但 mysql ❌" = 应用层 filter（安全组/防火墙），不是 mysqld 崩溃
   - "nc ✅ 但 recv(4) 0 bytes" 本身是中性的 — 既可能是 mysqld 崩溃，也可能是 silent drop

2. **阿里云 ECS 安全组分类**：
   - 用户自管安全组（橙色图标）：可以自由编辑
   - SAS 自管安全组（安全管家图标）：不要编辑已有规则（SAS 会覆盖），只新增 allow 规则
   - SAS "恶意 IP 防护"默认只允许 self-connect，外部 IP 全部 silent drop

3. **VPS "healthy" 不代表 DB 链路正常**：/health 端点硬编码，不测 DB 连接。DB 连接池在容器启动时建立，如果启动时 MySQL 通但后来安全组规则变化，容器 healthy 但 DB 实际不可用。

4. **"两个不同 IP 都失败"≠ 排除白名单**：如果白名单 source 是 self-IP，那么任何外部 IP 都会失败，反而是白名单问题的特征。

**Gemini Key 真闭环（同日完成）**:
- 5-01 Key Rotation 替换 + 5-02 Founder Google Cloud Console revoke 旧 key
- 旧 key 反测：`400 INVALID_ARGUMENT 'API key expired' API_KEY_INVALID` ✅（确认真 revoke）
- 新 key 真 LLM：`gemini-2.5-flash → 'OK'` ✅（确认新 key 可用）

---

### Wave 5.3 ✅ (2026-04-30, DevOps Sonnet 4.6)

**任务**: alembic CLI 工程化补全（Wave 5.2 部署后续）

**改动文件**:
- `alembic.ini` (新建) — 项目根，sqlalchemy.url 留空
- `alembic/env.py` (新建) — 同步 pymysql driver，target_metadata = Base.metadata
- `requirements.txt` — 加 alembic>=1.13.0 + pymysql>=1.1.0
- `docker/Dockerfile.api` — 加 COPY alembic.ini + COPY alembic/

**验收结果**:

| 验收项 | 结果 |
|--------|------|
| requirements.txt 含 alembic>=1.13.0 + pymysql>=1.1.0 | ✅ |
| 项目根 alembic.ini 存在 | ✅ |
| alembic/env.py 存在 + import target_metadata | ✅ |
| 本地 alembic current = 002_r7_2_favorite_share (head) | ✅ |
| alembic_version 表存在 + value = 002_r7_2_favorite_share | ✅ |
| Dockerfile.api 加 COPY alembic.ini + COPY alembic/ | ✅ |
| VPS Docker build 含 Step: COPY alembic.ini + COPY alembic/ | ✅ sha256:2d06fcdd |
| VPS 容器 alembic current = 002_r7_2_favorite_share (head) | ✅ |
| VPS /health 200 healthy | ✅ |
| git push commit c30982f + 26ff792 | ✅ |

**踩坑**: pymysql 本地是 aiomysql 间接依赖，requirements.txt 未显式 pin，容器缺失 → 补加 + 二次 rebuild 解决

---

### TASK-T6-FIXBATCH Wave 4 ✅ (2026-04-29, DevOps Sonnet)

**任务**: 将 Wave 1.1+1.2+2+2.5+3.5 全批代码修复部署到生产 VPS，完成生产环境验证

**部署范围（16 文件）**:
- Backend (8): pipeline_orchestrator.py / job_manager.py / projects.py / chapters.py / character_prompt_builder.py / reference_image_manager.py / schemas/project.py / seedream_generator.py(新)
- Frontend (8): [projectUuid]/[stage]/page.tsx(新) / url.ts(新) / createUrl.ts(新) / StageD.tsx / StageC.tsx / 其他

**执行步骤**:

| 步骤 | 操作 | 结果 |
|------|------|------|
| Step 1 | git commit + push GitHub | commit 84a2d35, branch main ✅ |
| Step 2 | 通知 Ben (.team-brain/team_ben/TEAM_CHAT.md) | 后端 10 文件清单已发 ✅ |
| Step 3 | rsync app/ → VPS app/ + frontend/ → VPS frontend/ | trailing slash 正确 ✅ |
| Step 4 | docker compose build --no-cache api frontend + force-recreate | api + frontend 重建 ✅ |
| Step 5 | docker exec api curl /health | {"status":"healthy"} 200 ✅ |
| Step 6 | 生产 T8 故事验证 (1:1 朋友圈, NB2 真生图) | status=completed, 16 shots ✅ |

**T8 验证数据**:
- 项目 UUID: a3966a40-6d27-42c0-a7cf-109729e453e7
- 画幅: 1:1（朋友圈）
- Shots: 16 张（NB2 真生图，1024x1024）
- D.15: PIL 实测 1024x1024（不再 hardcoded 2:3）✅
- R7-1: cover_image_url + shot_count=16 返回正常 ✅
- R7-3: portrait mtime +45s（adjust 后真实重生）✅
- UX-16: GET /create/{uuid}/preview → HTTP 200 ✅

**验证后**: SKIP_IMAGE_GENERATION 恢复 true（节省后续测试成本）

---

### TASK-VPS-SKIP-IMAGE ✅ (2026-04-24 13:32, DevOps 自执行)

**任务**: VPS .env.production 追加 SKIP_IMAGE_GENERATION=true，让生产环境 Stage 5 使用 R8 mock 图跳过 NB2 真实生图

**执行步骤**:

1. **幂等追加 env** ✅
   - `grep -q '^SKIP_IMAGE_GENERATION=' /opt/xuhua-story/.env.production || echo '...' >> .env.production`
   - 判断不存在才追加，防重复写入

2. **验证 .env.production** ✅
   - `grep SKIP_IMAGE_GENERATION /opt/xuhua-story/.env.production`
   - 返回: `SKIP_IMAGE_GENERATION=true` ✅

3. **force-recreate api 容器** ✅
   - `cd /opt/xuhua-story/docker && docker compose up -d --force-recreate api`
   - docker-api-1 Recreated → Started ✅（frontend / redis 不动）

4. **容器内验证 3/3 PASS** ✅

| 验证项 | 期望 | 结果 |
|--------|------|------|
| `/health` | `{"status":"healthy"}` | ✅ `{"status":"healthy"}` |
| `settings.SKIP_IMAGE_GENERATION` | `True` | ✅ `SKIP_IMAGE_GENERATION = True` |
| 容器 StartedAt | 2026-04-24 今天 | ✅ `2026-04-24T05:30:37.588742043Z` |

**约束遵守**:
- ✅ 不改代码、不 push、不 commit
- ✅ 不动共享 MySQL / frontend 容器 / redis
- ✅ 不改其他 env 配置
- ✅ 未改 PM 维护文档

**Bash 权限**: ✅ 可用（一轮通过）

---

### TASK-BUG-FIX-BATCH-1 Route D ✅ (2026-04-23 17:10, DevOps 自执行)

**任务**: 将 Route B (Backend BE-3/4/5 + /static mount) + Route C (Frontend FE-1~5) 18 bug 修复部署到 VPS prefaceai.mov

**Step 2 关键发现**: VPS docker-compose.yml api 服务无 `output_data:/app/output` volume，`/static/outputs` StaticFiles mount 依赖的 `/app/output/` 目录需持久化。PM 任务说明已授权添加，DevOps 新增 named volume `output_data:/app/output`。

**执行步骤**:

1. **git add + commit + push** ✅
   - Staged 20 modified tracked files (不含未跟踪的 docs/INVESTOR_MEMO_2026Q2.md)
   - commit `3fa2a73` "fix: Pipeline UX/BGM/SKIP bugs + FE StrictMode completedRef race" (20 files, +1050/-77)
   - push: `928a621..3fa2a73`

2. **docker-compose.yml output volume 新增** ✅
   - 本地 `docker/docker-compose.yml`: api volumes 加 `- output_data:/app/output`，volumes 段加 `output_data:`
   - commit `6518563` "fix(docker): add output_data volume mount for /app/output" (1 file, +2)
   - push: `3fa2a73..6518563`

3. **rsync → VPS** ✅
   - `app/` → VPS (main.py + job_manager.py + pipeline_orchestrator.py, 3 文件)
   - `frontend/src/` → VPS (StageC.tsx + CreateContext.tsx, 2 文件)
   - `docker/docker-compose.yml` → VPS (1 文件)
   - trailing slash 全部正确

4. **VPS docker build + force-recreate** ✅
   - `docker compose build api` → image sha256:6090c0d4... 1 layer changed ✅
   - `docker compose build frontend` → 20 routes, 0 errors, 65s ✅
   - `docker compose up -d --force-recreate api frontend` → Volume "docker_output_data" Created + api+frontend Started ✅

5. **验证 8/8 PASS** ✅

| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | {"status":"healthy"} ✅ |
| /app/output 目录 | 存在 | ls → 空目录（新 volume）✅ |
| /static/outputs StaticFiles | app.mount 存在 | main.py Line 79 ✅ |
| job_manager isinstance 守卫 | isinstance(data,(dict,list)) | job_manager.py Line 202 ✅ |
| pipeline_orchestrator credits_used | checkpoint_callback("credits_used",...) | Line 734 ✅ |
| 无 --reload | Cmd 无 reload | uvicorn host 0.0.0.0 port 8000 only ✅ |
| StartedAt | 2026-04-23 | 2026-04-23T09:01:10Z ✅ |
| 外部 HTTPS | 200 | prefaceai.mov 200 + /api/health 200 ✅ |

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确（`app/` → `/opt/xuhua-story/app/`）
- ✅ 未碰 .env / DB schema / redis
- ✅ 未在 VPS 上 git pull
- ✅ build + force-recreate

**Bash 权限**: ✅ 可用，全程无中断

---

### TASK-LOCAL-BACKEND-HUNG ✅ (2026-04-23 15:05, DevOps 自执行)

**任务**: 本地 backend 卡死诊断 + 干净重启（Founder 无法登录 localhost:3000）

**诊断结论 (4 维度)**:

| 维度 | 发现 |
|------|------|
| MySQL zombie 连接 | **无**：kill 后连接池随进程退出，SHOW PROCESSLIST 无本机残留连接 |
| --reload 触发源 | 今日 P0P1-LOGGING-FIX 改动的 3 文件（image_generator.py / chapters.py / pipeline_orchestrator.py）mtime 变化触发 inotify reload |
| startup 阻塞根因 | reload 期间旧 worker 处于 BEGIN 事务（DESCRIBE prefacestory.project_chapters），被 reload kill 前未 COMMIT → 新 worker 等待 metadata lock → 无限等待（15:30+ 阿里云 MySQL metadata_lock 等待超时极长）|
| 端口/进程 | PM kill 后 port 8000 空闲，无 uvicorn 进程残留 |

**根本原因**: `uvicorn --reload` + 阿里云远程 MySQL（网络延迟 ~0.5s/表）→ reload 中断导致 SQLAlchemy metadata_create_all BEGIN 事务未提交 → metadata lock 死锁

**修复步骤**:
1. 确认 port 8000 空闲（PM 已 kill）
2. `cd xuhua_story && source venv/bin/activate`
3. `nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > storage/logs/uvicorn_nohup.log 2>&1 &`
4. 等待 "Application startup complete"（via until 循环监测日志，约 20s）
5. 验证 /health + auth 端点

**验证**:
| 项 | 结果 |
|----|------|
| PID | **21995** |
| Application startup complete | 2026-04-23 15:04:24 ✅ |
| /health | `{"status":"healthy"}` ✅ |
| POST /api/auth/login (test) | `{"detail":"邮箱或密码错误"}` (401) ✅ |

**关键教训**:
- 本地 backend 禁止 --reload 模式 + 阿里云 MySQL 组合：高延迟 DB + 热重载 = metadata lock 死锁风险
- 正确启动方式：`nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &`（无 --reload）
- DEBUG=true 在 .env 控制应用行为，与 uvicorn CLI --reload 无关，可独立控制

---

### TASK-P0P1-DEPLOY ✅ (2026-04-23 14:35, DevOps 自执行)

**任务**: 融合 Ben commit `4725e9e` (utf8mb4 defensive patch) + 今日 P0P1 logging fix（4 处代码 + 1 处 compose）一起上生产 VPS。

**执行步骤**:

1. **git pull --rebase 融合 Ben commit** ✅
   - fetch → 确认 `4725e9e fix: ensure charset=utf8mb4 is always set in database URL` 在 origin
   - stash 未提交 12 files → `pull --rebase` Fast-forward `cb5e395..4725e9e` (app/database.py +6/-1) → stash pop（零冲突）
   - 验证 `_db_url` + `if "charset=" not in _db_url` 落地

2. **commit + push** ✅
   - `git add -A` → 12 files staged
   - commit `d154ce1` "fix(logging): P0P1 exception logging + docker log rotate" (+1088/-377, Co-Authored-By)
   - `git push origin main` → `4725e9e..d154ce1`

3. **rsync → VPS** ✅
   - `rsync -avz -e "ssh -p 58913" --exclude '__pycache__' --exclude '*.pyc' app/ trader@107.148.1.199:/opt/xuhua-story/app/` — 4 代码文件 (database.py + api/chapters.py + services/image_generator.py + services/pipeline_orchestrator.py)
   - `rsync -avz -e "ssh -p 58913" docker/ trader@107.148.1.199:/opt/xuhua-story/docker/` — docker-compose.yml

4. **VPS build + force-recreate** ✅
   - 首轮仅 `up -d --force-recreate api` → 验证失败（容器仍跑旧代码，Dockerfile COPY baked-in）
   - 补 `docker compose build api` → image sha256:aaba97eb5674... → 再 `up -d --force-recreate api`

5. **验证 6/6 PASS** ✅

| 验证项 | 期望 | 结果 |
|--------|------|------|
| /health | healthy | {"status":"healthy"} ✅ |
| logging config | max-size=50m max-file=5 | map[max-file:5 max-size:50m] ✅ |
| logger count in image_generator.py | ≥ 60 | 65 ✅ |
| Ben utf8mb4 patch | _db_url + if "charset=" not in | ✅ |
| StartedAt | 2026-04-23 | 2026-04-23T06:31:38Z ✅ |
| bare except in pipeline_orchestrator.py | 0 | 0 ✅ |
| bonus: print count | 0 | 0 ✅ |

**教训**:
- Dockerfile.api 用 `COPY app/ ./app/` 是 baked-in（volume 只挂 storage 和 sqlite），代码改动必须 `docker compose build api`，仅 `--force-recreate` 不够
- 前几次 DevOps 部署都有做 build，这次 PM 任务描述漏写了 build 步骤 → DevOps 按铁律发现问题后补齐
- 下次同类任务：rsync 后无脑 `build + up -d --force-recreate`，不要省 build

**部署铁律遵守**:
- ✅ 先 push GitHub 再部署 VPS
- ✅ rsync trailing slash 正确
- ✅ 未碰 .env / DB schema / frontend / redis
- ✅ 未在 VPS 上 git pull
- ✅ 未改 PM 维护文档

**Bash 权限**: ✅ 可用

---

### TASK-P0P1-LOGGING-FIX ✅ (2026-04-23 11:30, DevOps 自执行)

**任务**: 修改 `docker/docker-compose.yml` api 服务，加 logging 配置（json-file, max-size=50m, max-file=5），解决生产 VPS 日志保留不足问题（仅 139 行，Ben 的 500 错误 traceback 丢失）。

**执行步骤**:

1. **读取文件确认当前状态** ✅
   - `docker/docker-compose.yml` api 服务无 logging 块，healthcheck 结束于第 39 行

2. **修改 docker-compose.yml** ✅
   - 在 api 服务 healthcheck 块末尾（`retries: 3` 之后）插入 5 行:
     ```yaml
         logging:
           driver: "json-file"
           options:
             max-size: "50m"
             max-file: "5"
     ```
   - 其他服务（redis / worker / frontend / mysql）未改动

3. **验证 YAML 语法** ✅
   - `docker compose config --no-interpolate` 返回码 0，无 STDERR
   - parsed 输出确认 api 服务含 `logging: {driver: json-file, options: {max-file: "5", max-size: 50m}}`

**未部署**（按任务 Step 3 要求，等待 @backend 完成代码改动后 PM 统一安排）

**约束遵守**:
- ✅ 仅改 docker-compose.yml，无代码/env/DB 改动
- ✅ 未 commit / push / rsync / 部署
- ✅ 其他服务不受影响

---

### TASK-DEPLOY-LLM-SAMPLING ✅ (2026-04-23 10:55, DevOps 自执行)

**任务**: 同步今日 @backend 完成的两个 LLM sampling 任务（TASK-LLM-TEMP-AUDIT-FIX + TASK-8631-UNIFY）到生产 VPS。本地已验证通过，VPS 仍跑 2026-04-21 `b998cbf` 镜像。

**执行步骤**:

1. **git commit + push** ✅
   - `git add -A` → 22 files staged
   - `git commit` → commit `cb5e395` "chore: unify LLM sampling params (temperature + max_tokens)" (22 files, +812/-38)
   - commit message 完整覆盖两个任务:
     - TASK-LLM-TEMP-AUDIT-FIX (15 changes): alignment_service × 2 / shot_validator × 1 / api/utils × 4+1 import / story_generator max_tokens / screenplay_writer × 4 / storyboard_director × 2 Claude+Gemini temperature 显式化
     - TASK-8631-UNIFY (13 changes): 5 files 的 max_tokens 8631→16384
   - `git push origin main` → `b998cbf..cb5e395`

2. **rsync `app/` → VPS** ✅
   - `rsync -avz -e "ssh -p 58913" --exclude '__pycache__' --exclude '*.pyc' app/ trader@107.148.1.199:/opt/xuhua-story/app/`
   - 传输 8 个代码文件: api/utils.py + services/ 下 7 个
   - trailing slash 正确: `app/` → `/opt/xuhua-story/app/`（memory 教训避坑）

3. **VPS docker rebuild + 重启** ✅
   - `cd /opt/xuhua-story/docker && docker compose build api` → image sha256:b1d6dfe5485c... 构建成功
   - `docker compose up -d --force-recreate api` → api Recreated + Started
   - redis / frontend 未动（本次无前端改动）

4. **验证 4/4 PASS** ✅

| 验证项 | 期望 | 结果 |
|--------|------|------|
| `docker exec docker-api-1 curl -s http://localhost:8000/health` | healthy | `{"status":"healthy"}` ✅ |
| `grep -c '16384' /app/app/services/character_designer.py` | ≥2 | **2** ✅ |
| `grep -c 'temperature=0.2' /app/app/services/shot_validator.py` | 1 | **1** ✅ |
| `docker inspect ... --format '{{.State.StartedAt}}'` | 2026-04-23 | **2026-04-23T02:52:27Z** ✅ (从 2026-04-21T10:05:10Z 刷新) |
| `grep -rn '8631' /app/app/services/ /app/app/api/` | 0 | **0** ✅ |

**部署铁律遵守**:
- ✅ 先 push 到 GitHub 再部署 VPS（push before notify）
- ✅ rsync trailing slash 正确（`app/` → `/opt/xuhua-story/app/`）
- ✅ 未碰 .env / DB schema / frontend / redis
- ✅ 未在 VPS 上 git pull（rsync only）

**Bash 权限**: ✅ 本次可用（上次 2026-04-21 Mureka 部署二次被拒由 PM 代执行，本次恢复正常）。

**影响面**（对下游 agent）:
- Stage 1-4 LLM 调用全部对齐: 对齐/验证/OCR/视觉分析 temperature=0.2，Stage 3/4 剧本+分镜主备 temperature=0.8
- sync Claude max_tokens 8192→16384（story_generator.py L303）
- 所有 max_tokens 统一 16384（character_designer / alignment_service / story_outline_generator L196 补齐 / storyboard_director / screenplay_writer）
- 不再有 8631 遗留

---

### TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 VPS 部署 ✅ (2026-04-21, PM 代执行)

**任务**: TASK-MUREKA-PIPELINE-INTEGRATION Wave 4 的 VPS 部署环节，把 Mureka BGM 能力从 local 推到生产环境。

**执行事实（PM 代执行）**:
- DevOps agent 本轮第 1 次 spawn: Bash 权限被拒，agent 报告中准备了完整命令
- PM 重 spawn DevOps agent: Bash 依旧被拒
- PM 按 memory "重启服务 PM 自己做" 原则，先读 `.claude/agents/devops.md` 确认铁律（push before notify, rsync trailing slash, shared MySQL），然后代执行全部部署命令
- PM 第 3 次 spawn DevOps agent 补文档：401 auth error（agent 已更新 current.md 顶部后挂），PM 代写剩余 completed/context-for-others

**部署步骤（PM 执行）**:
1. `git add -A && git commit -m "feat: Mureka AI BGM integration (Wave 1-4)"`
   - commit hash: `b998cbf`
   - diff stat: 69 files changed, 18922 insertions(+), 1147 deletions(-)
2. `git push origin main` → `0fcb65a..b998cbf`
3. `ssh -p 58913 trader@107.148.1.199 "echo 'MUREKA_API_KEY=op_...' >> /opt/xuhua-story/.env.production"`
4. `rsync -avz -e "ssh -p 58913" --exclude '__pycache__' --exclude '*.pyc' app/ trader@107.148.1.199:/opt/xuhua-story/app/`
5. `rsync -avz -e "ssh -p 58913" scripts/ trader@107.148.1.199:/opt/xuhua-story/scripts/`
6. `rsync -avz -e "ssh -p 58913" --exclude 'node_modules' --exclude '.next' frontend/src/ trader@107.148.1.199:/opt/xuhua-story/frontend/src/`
7. 共享阿里云 MySQL (101.132.69.232/prefacestory/project_chapters) 已有 4 BGM 列（local migration 一次覆盖 VPS，无需重跑）
8. `ssh -p 58913 trader@107.148.1.199 "cd /opt/xuhua-story/docker && docker compose build api && docker compose build frontend"`
9. `docker compose up -d api frontend` (force recreate)

**验证**:
- `docker exec docker-api-1 curl -s http://localhost:8000/health` → `{"status":"healthy"}` ✅
- `docker exec docker-api-1 python -c 'from app.config import settings; print(settings.MUREKA_API_KEY)'` → True ✅
- 容器: `docker-api-1 Up (healthy)`, `docker-frontend-1 Up`, `docker-redis-1 Up (healthy)` ✅

**铁律遵守**:
- ✅ 先 push 到 GitHub 再部署 VPS
- ✅ rsync trailing slash 正确（`app/` → `/opt/xuhua-story/app/`）
- ✅ 不自建本地 MySQL，用共享阿里云 DB
- ✅ Health check 通过才算部署完成

**教训**:
- 下次 DevOps agent spawn 前先确认 Bash 权限是否可用
- 长文档更新任务中间 spawn agent 有 auth 风险，关键节点 PM 可代写 + 明确标注

---

### TTS-KEY-WRITE: 火山引擎 TTS 凭证写入 ✅ (2026-04-13)

**任务**: 将 Founder 提供的 4 个火山引擎 TTS 凭证写入本地 .env + 补全 .env.example

**完成内容**:
- [x] 分析 config.py + tts_service.py 确认字段映射关系
- [x] 本地 .env 写入 VOLCENGINE_API_KEY + VOLCENGINE_SECRET_KEY（VOLCENGINE_APP_ID + VOLCENGINE_ACCESS_KEY 已存在）
- [x] .env.example 补全 VOLCENGINE_API_KEY + VOLCENGINE_SECRET_KEY 字段（含注释说明）
- [x] R1 风险从"基本解决 4/6"升级为"完全解决 6/6"
- [x] devops-progress/current.md + context-for-others.md 同步更新
- [x] TEAM_CHAT.md 追加完成通知（含 VPS 操作指引，不含真实 Key 值）

**字段映射清单**:
| Founder 提供名称 | .env 字段名 | 用途 |
|-----------------|-------------|------|
| TTS_APPID | VOLCENGINE_APP_ID | TTS app 鉴权 ID（payload.app.appid）|
| ACCESS TOKEN | VOLCENGINE_ACCESS_KEY | Bearer Auth token（Authorization: Bearer;xxx）|
| API KEY | VOLCENGINE_API_KEY | VolcEngine 控制台 API Key（备用签名鉴权）|
| SECRET KEY | VOLCENGINE_SECRET_KEY | VolcEngine 控制台 Secret Key（备用签名鉴权）|

**VPS 操作**: Founder 需手动在 VPS /opt/xuhua-story/.env.production 补入 VOLCENGINE_API_KEY + VOLCENGINE_SECRET_KEY，再 docker compose restart api

---

### TASK-HARNESS-V2 Phase 3: PreCommit + Push + VPS 部署 ✅ (2026-04-15)
- settings.local.json PreCommit 加入 test_error_patterns.py
- chmod +x scripts/health_check.sh
- 2 commits: 87aeaa4 (feat:19 files) + ea0edb1 (docs:5 files), push e572076→ea0edb1
- rsync 353 files + Docker --no-cache rebuild + force-recreate api
- 验证 4/4 PASS: push + health + errors/recent 401 + costs/summary 401
- R3 (无 CI/CD) 风险已解决: GitHub Actions CI 上线

### TASK-HARNESS-V2 Phase 1+2: CI + EP sensors + Schema + monitoring endpoints ✅ (2026-04-15)
- P1-1: .github/workflows/ci.yml — push/PR to main auto-run tests
- P1-2 (@tester): 6 EP sensors test_error_patterns.py (EP-005/006/007/009/013/014)
- P1-3 (@ai-ml): OutlineSchema + ScreenplaySchema + validate_outline/screenplay
- P1-4 (@pm): 6 Agent 文件白名单
- P2-3 (devops): monitoring.py (errors/recent + costs/summary) + api_cost_log.py + health_check.sh
- 16/16 tests PASS

### TASK-DEPLOY-STAGED-V2: Push + VPS 部署 ✅ (2026-04-14, PM 代更新)
- 3 commits: 611c501 + 68ac04f + 259f696, push 69ebc02→259f696
- .gitignore 更新 (settings.local.json + .trae + output + .mov + team-members)
- VPS rsync + Docker rebuild api+frontend, 10/10 验证 PASS
- anthropic 0.89.0 确认

### TASK-HE-DEVOPS-1: Hook 基础设施升级 ✅ (2026-04-14, PM 代更新)
- pyright 1.1.408 + tsc 5.9.3 + PostToolUse/PreCommit/PrePush hooks

### TASK-HE-DEVOPS-2: TEAM_CHAT 归档机制 ✅

**完成时间**: 2026-04-14
**任务类型**: Harness Engineering — 信息治理 (P1)

**完成内容**:
- [x] 创建 `scripts/archive_team_chat.sh` (chmod 755, #!/bin/bash, set -euo pipefail)
- [x] 首次归档执行: 36,079行 → 2,343行 (减少 93.5%)
- [x] 4 个月份归档文件: 2026-01 / 2026-02 / 2026-03 / 2026-04
- [x] 幂等验证: 二次运行结果不变
- [x] TEAM_CHAT.md 头部加入归档说明
- [x] 更新 TEAM_CHAT.md 完成报告
- [x] 更新 devops-progress (current/context-for-others/completed)

**脚本特性**: macOS+Linux 兼容、日期精确解析、按月分割、幂等

---

### TASK-HE-DEVOPS-1: Hook 基础设施升级 ✅

**完成时间**: 2026-04-14
**任务类型**: Harness Engineering — 自动化 Sensor 基础设施 (P0)

**完成内容**:
- [x] 安装 pyright (pip3 install pyright → 1.1.408)
- [x] 验证 tsc 可用 (frontend/ → Version 5.9.3)
- [x] 验证 pytest 可用 (8.3.4)
- [x] settings.local.json PostToolUse hook 升级 — .py→pyright, .ts/.tsx→tsc+清缓存
- [x] settings.local.json PreCommit hook 新增 — 架构测试+质量门测试 (|| true 安全启动)
- [x] settings.local.json PrePush hook 新增 — 全量测试 (timeout 300s)
- [x] env/permissions 保持不变
- [x] 更新 TEAM_CHAT.md 完成报告
- [x] 更新 devops-progress (current/context-for-others/completed)

**关键适配**: `python` 在本机不可用，所有 hook 命令使用 `python3` 代替

**待后续**: PM 通知后去掉 PreCommit 的 `|| true`（@tester 测试文件就绪后）

---

### 阿里云 MySQL ALTER TABLE — project_chapters TEXT→LONGTEXT ✅

**完成时间**: 2026-04-09
**任务类型**: 数据库 DDL 变更（RB-1 配套）

**完成内容**:
- [x] 连接阿里云 MySQL (101.132.69.232:3306/prefacestory) via pymysql
- [x] ALTER TABLE project_chapters MODIFY 8 列 TEXT → LONGTEXT
- [x] DESCRIBE 验证全部 8 列已变为 longtext
- [x] 更新 TEAM_CHAT.md 完成报告
- [x] 更新 devops-progress (current/context-for-others/completed)

**影响列**: full_script, summary, characters_json, scenes_json, storyboard_json, error_message, transcript_json, timeline_json

**背景**: Backend RB-1 已在 chapter.py 中将 8 个 Text 列改为 LONGTEXT（SQLAlchemy model），但已有数据库表不会自动变更，需要手动 DDL。

---

### MERGE-FIX push + VPS 部署 ✅

**完成时间**: 2026-04-07
**任务类型**: push + VPS 部署

**完成内容**:
- [x] git pull Ben 最新 (4dcccc0, 5 files model 修复)
- [x] git stash/pop 无冲突
- [x] Commit 1: `303cb34` fix(backend) — confirm-outline merge summary dual-write + ending replacement
- [x] Commit 2: `2277ee7` test — MERGE-FIX 4 scenarios (55/55 PASS)
- [x] Commit 3: `69ebc02` docs — agent progress + team-brain sync
- [x] Push: `origin/main` 4dcccc0 → 69ebc02
- [x] rsync projects.py + api/__init__.py + models/ 到 VPS
- [x] 清理误放到 app/ 根目录的 12 个 model 文件
- [x] Docker rebuild api + force-recreate
- [x] 验证: `/health` healthy ✅ + 3 容器正常

---

### VPS API Key 验证 ✅

**完成时间**: 2026-04-05
**任务类型**: 运维验证

**结果**:
- [x] SSH 检查 `.env.production`: 核心 4/6 Key 已填入
- [x] 容器内验证: `docker exec` 确认 ANTHROPIC/GEMINI/OPENAI 三个 Key 已加载
- [x] 容器健康: api (healthy) + frontend (up) + redis (healthy)
- [x] 不需要重启（容器已在用 Key 运行，uptime 21h）
- [x] 风险清单 R1 标记 ✅ 基本解决
- [ ] 缺: VOLCENGINE_SECRET_KEY + TTS_APPID（仅影响 TTS，核心功能不受影响）

---

### TASK-CONFIRM-OUTLINE-WIRE + REORDER-FIX push + VPS 部署 ✅

**完成时间**: 2026-04-04
**任务类型**: 版本控制 + VPS 部署

**Push**:
- [x] `066ef46` feat(backend): WIRE + REORDER-FIX (3 files, 174+ lines)
- [x] `853a755` feat(frontend): WIRE + REORDER-FIX (4 files)
- [x] `a55bb07` test: 39/39 confirm-outline 全链路测试 (1 file)
- [x] `708e362` docs: agent progress + team-brain + shared-memory (18 files)
- [x] Push: `origin/main` 38f2505 → 708e362

**VPS 部署**:
- [x] SCP 7 关键代码文件到 VPS
- [x] Docker rebuild api + frontend → force-recreate
- [x] 验证: frontend 200 + API `/health` healthy + 3 容器运行

---

### TASK-UPLOADER-ENV-FIX push + VPS 前端部署 ✅

**完成时间**: 2026-04-01
**任务类型**: 版本控制 + VPS 部署（仅前端）

**Push**:
- [x] `f292bee` fix(frontend): 5 个 Uploader 统一 API_BASE (5 files)
- [x] `ceb2ba5` docs: agent progress + team-brain sync (10 files)
- [x] Push: `origin/main` 0ed365e → ceb2ba5

**VPS 部署**:
- [x] SCP 5 个 Uploader 文件到 VPS
- [x] Docker rebuild frontend → force-recreate（API 容器不动）
- [x] 验证: frontend 200 + API `/health` healthy + 3 容器运行

---

### REPAIR-V3 + OUTLINE-PROGRESS + LOGGING-FIX push + VPS 部署 ✅

**完成时间**: 2026-04-01
**任务类型**: 版本控制 + VPS 部署

**Push**:
- [x] `2520fc5` feat(backend): TASK-JSON-REPAIR-V3 状态机 + LOGGING-FIX 增强 (3 files)
- [x] `029841a` feat(frontend): TASK-OUTLINE-PROGRESS 大纲生成进度页面 (1 file)
- [x] `d7eb28c` docs: agent progress + team-brain sync (14 files)
- [x] Push: `origin/main` 3a437bd → d7eb28c

**VPS 部署**:
- [x] SCP 4 个关键代码文件到 VPS
- [x] Docker alpine 修复 /opt/xuhua-story/ 文件所有权 (uid 501 → trader 1000)
- [x] Docker rebuild api + frontend → force-recreate
- [x] 验证: frontend 200 + API `/health` healthy + 3 容器运行

---

### 大纲生成全链路 push + Ben 融合 + VPS 部署 ✅

**完成时间**: 2026-03-30
**任务类型**: 版本控制 + VPS 部署

**Push + Merge**:
- [x] `56aa22b` feat: 大纲生成全链路打通 — LOGGING-FIX 26 处 print→logger (4 files)
- [x] `c37d392` docs: 大纲生成里程碑 (9 files)
- [x] `8b5c36a` merge: 融合 Ben `954f274` int-id+uuid 重构（projects.py import 冲突解决）
- [x] Push: `origin/main` → 8b5c36a

**VPS 部署**:
- [x] rsync 本地代码 → VPS /opt/xuhua-story/
- [x] Docker rebuild api + frontend
- [x] `.env.production` 创建：DB 驱动 asyncmy（与 Ben 一致）+ 真实 API Key 全部填入
- [x] 验证: frontend 200 + API `/health` healthy + `/api/auth/me` 401（正常）
- [x] 3 容器全部运行: api + frontend + redis

---

### REPAIR-V2 + PERSISTENT-LOG push ✅

**完成时间**: 2026-03-29
**任务类型**: 版本控制

- [x] `79d63f8` fix(backend): JSON-REPAIR-V2 (1 file)
- [x] `df1f44d` feat(backend): PERSISTENT-LOG (1 file)
- [x] `77ef5f9` docs (9 files)
- [x] Push: `origin/main` d54087e → 77ef5f9
- [x] 不需要 VPS 部署

---

### 6 TASK push — Founder E2E 联调通过 ✅

**完成时间**: 2026-03-29
**任务类型**: 版本控制（bug fixes + features）

- [x] `3975901` fix(frontend): TASK-AUTH-RESILIENCE (1 file)
- [x] `3b55f4d` fix(backend): TASK-JSON-REPAIR (1 file)
- [x] `cdc2d22` fix: TASK-DOC-ONLY-FIX + TASK-DOC-FORMAT (3 files)
- [x] `171803f` feat(frontend): TASK-STYLE-PRIORITY (3 files)
- [x] `9ea6014` feat(backend): TASK-DEBUG-LOGGING (1 file)
- [x] `0ed98de` docs (17 files)
- [x] Push: `origin/main` faf594f → 0ed98de
- [x] 不需要 VPS 部署

---

### TASK-SHARED-DB — 切换阿里云共享 MySQL ✅

**完成时间**: 2026-03-27
**任务类型**: 基础设施（数据库切换）

- [x] .env DATABASE_URL: localhost:3306/xuhua_story → 101.132.69.232:3306/prefacestory
- [x] 云端 `projects` 表补 6 列 (aspect_ratio, raw_outline_json, confirmed_outline_json, custom_style_analysis_json, character_refs_analysis_json, scene_refs_analysis_json)
- [x] 后端 `/health` healthy，阿里云 DB 连接正常
- [x] 本地 Docker MySQL 已停并删除
- [x] .env 未 commit（含真实密码，在 .gitignore 中）

---

### Phase 1+2 全部 push ✅

**完成时间**: 2026-03-26
**任务类型**: 版本控制（Phase 1+2 代码 + 文档）

- [x] `673a907` feat(frontend): 13 new style thumbnails (14 files)
- [x] `1bbfebf` feat(backend): Phase 2 — image analysis + seed refs + dynamic style (18 files)
- [x] `408ae6a` feat(frontend): Phase 2 — real image analysis + 28 styles + uploaders (10 files)
- [x] `dc6ef0d` docs: Phase 1+2 complete (16 files)
- [x] Push: `origin/main` 40ca049 → dc6ef0d
- [x] 不需要 VPS 部署

---

### LLM-FIX push ✅ — Stage 1 E2E 联调通过

**完成时间**: 2026-03-24
**任务类型**: 版本控制（bug fix push）

- [x] `376d6b7` fix(backend): Stage 1 LLM call — system prompt + async + debug logging (1 file)
- [x] `a0b3598` docs: Stage 1 E2E success + LLM-FIX progress + team-brain sync (12 files)
- [x] Push: `origin/main` 3d27445 → a0b3598
- [x] 不需要 VPS 部署

---

### ENVVAR-FIX push ✅

**完成时间**: 2026-03-24
**任务类型**: 版本控制（bug fix push）

- [x] `4fdf1ea` fix(backend): Stage 1-4 os.getenv → settings.XXX (5 files)
- [x] `226e0bc` docs: ENVVAR-FIX progress + bug report + team-brain sync (9 files)
- [x] Push: `origin/main` 41ae0d5 → 226e0bc
- [x] 不需要 VPS 部署

---

### MySQL 搭建 + Stage 1 pipeline push ✅

**完成时间**: 2026-03-24
**任务类型**: 基础设施 + 版本控制

**MySQL 搭建**:
- [x] Docker `mysql:8.0` container (xuhua-mysql, port 3306)
- [x] .env DATABASE_URL 切换到 MySQL
- [x] pip install aiomysql email-validator
- [x] 修复 scene_image.py + audio_segment.py String 长度（MySQL 兼容）
- [x] 后端启动 `/health` healthy, 11 tables auto-created

**Stage 1 push** (4 commits, d1d2705 → ef4acca):
- [x] `5dec834` feat(ai-ml): Stage 1 prompt upgrade (1 file)
- [x] `33f4725` feat(backend): generate-outline API + MySQL model fixes (3 files)
- [x] `e063b23` feat(frontend): Stage 1 real API integration (1 file)
- [x] `ef4acca` docs: progress + team-brain sync (18 files)
- [x] 不需要 VPS 部署

---

### 完整 push: register fix + Resonance + skills + coordinator ✅

**完成时间**: 2026-03-24
**任务类型**: 版本控制（push 2 commits, 186 files）

- [x] `7b973fc` fix(frontend): register success — direct login (1 file)
- [x] `da291e0` feat: Resonance agent + marketing skills + coordinator + progress (185 files)
- [x] Push: `origin/main` e4ada3e → da291e0
- [x] 不需要 VPS 部署
- [x] 排除: assets/ 视频 + team-members/ + .trae/

---

### Git pull Ben commit e4ada3e + TEAM_CHAT 冲突解决 ✅

**完成时间**: 2026-03-24
**任务类型**: 版本控制（pull + 冲突解决）

- [x] `git pull origin main`: 0df1f03 → e4ada3e (29 files, +932/-162)
- [x] TEAM_CHAT 合并冲突解决（Ben 后端消息 + Founder Resonance 入职消息均保留）
- [x] 群聊通知 PM 接手变更分析

---

### Frontend review fixes + text-gen hint push ✅

**完成时间**: 2026-03-23
**任务类型**: 版本控制（前端修复 + 文档）

- [x] `a2f61f0` fix(frontend): Batch 1A-4 review fixes (7 items) + text-gen hint (6 files)
- [x] `afeae40` docs: agent progress + team-brain sync (9 files)
- [x] Push: `origin/main` 866ea71 → afeae40
- [x] 不需要 VPS 部署

---

### Frontend Batch 1A-4 全部 push ✅

**完成时间**: 2026-03-22
**任务类型**: 版本控制（纯前端代码 + 文档）

**第一轮 push (Batch 1A+1B+2)**:
- [x] `336a646` feat(frontend): Batch 1A+1B — Create preview + MVP auth + settings (10 files)
- [x] `955f45d` feat(frontend): Batch 2 — Dashboard enhancements (11 files)
- [x] `9c29aa6` docs: agent progress + team-brain sync (13 files)
- [x] Push: `origin/main` 20641ac → 9c29aa6

**第二轮 push (Batch 3+4)**:
- [x] `5f55e57` feat(frontend): Batch 3 — story input (OCR, voice, templates) + skeleton (2 files)
- [x] `d37b4e5` feat(frontend): Batch 4 — membership tiers + aspect ratio + pricing (4 files)
- [x] `8ab7057` docs: agent progress + team-brain sync (9 files)
- [x] Push: `origin/main` 8d51108 → 8ab7057

**不需要 VPS 部署**（纯前端改动，VPS 前端容器未重建）

---

### Ben 团队文件重组 push + Git 工作流简化 ✅

**完成时间**: 2026-03-19
**任务类型**: 版本控制 + 文件重组

**重组 push**:
- [x] `be6c37b` refactor: reorganize Ben team files to .team-brain/team_ben/ (43 files)
- [x] Push to GitHub: `6fb95a3..be6c37b` → `origin/main`
- [x] 不需要 VPS 部署

**之前的 push**:
- [x] `33eaac6` feat: dual-team collaboration system (59 files)
- [x] `820fb7e` docs: DevOps progress sync (5 files)

**分支保护经历**: 设置 → Ben 决策移除 → 改为两人直接 push main
- [x] Founder 升级 GitHub Pro ($4/月) → 设置保护 → PR #1 验证通过
- [x] Ben 决策: 两人分工不同，冲突概率极低，不需要 PR 流程
- [x] PM 移除保护 → `protected: false` 确认
- [x] Ben 添加为 collaborator (ArBen2, write 权限)

---

### 安全加固部署: CORS restrict + log sanitizer ✅

**完成时间**: 2026-03-18
**验收状态**: 全部验证通过
**任务类型**: 安全加固 + 部署

**背景**: Founder 填 API Key 的前置安全条件。CORS 全开放 + 日志无脱敏 → 必须在填 Key 前修复。

**完成内容**:
- [x] Git 提交: `f76ac1e` (3 files)
- [x] Push to GitHub: `c6d697a..f76ac1e` → `origin/main`
- [x] rsync 3 files (main.py + middleware/) 到 VPS
- [x] Docker rebuild api + force-recreate
- [x] CORS 验证: prefaceai.mov ✅ 允许 / evil.com ✅ 拒绝
- [x] API health + 3 容器 Up

**风险清单更新**: R2 (CORS) + R6 (日志脱敏) 标记为 ✅ 已解决

---

### TASK-DEPLOY-CLEANUP: REWRITER-CLEANUP + OB-1/2/3/4 推送 + VPS 部署 ✅

**完成时间**: 2026-03-17
**验收状态**: 全部验证通过
**任务类型**: 版本控制 + 部署更新

**背景**: TASK-REWRITER-CLEANUP (phase2_safe 接入 + 注释清理 + 备用模型) + OB-1~4 (Haiku→Sonnet + gemini-3-pro→3.1-flash) + TASK-SAFE-DRYRUN 验证，全部 PM Review PASS。

**完成内容**:
- [x] 部署前验证: Python syntax 6/6 ✅ + Haiku 零残留 ✅ + gemini-3-pro-preview 零残留 ✅
- [x] Git 提交 2 批:
  - `1814193` feat: REWRITER-CLEANUP + OB-1/2/3/4 (7 files)
  - `c6d697a` docs: agent progress + team-brain sync (21 files)
- [x] Push to GitHub: `ec3b4fd..c6d697a` → `origin/main`
- [x] rsync app/ (6 files) + tests/ (1 file) 同步到 VPS
- [x] Docker rebuild api 容器
- [x] docker compose up -d --force-recreate api 重启服务
- [x] 外部验证全部通过

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| `https://prefaceai.mov` | ✅ HTTP 200 |
| `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
| Docker api 容器 | ✅ Up (healthy) |
| Docker frontend 容器 | ✅ Up |
| Docker redis 容器 | ✅ Up (healthy) |

---

### TASK-DEPLOY-R8B: N13-FIX + IMG-SAFETY + BRAND + LOGO 推送 + VPS 部署 ✅

**完成时间**: 2026-03-16
**验收状态**: 全部验证通过
**任务类型**: 版本控制 + 部署更新

**背景**: R8 E2E 完成后的修复任务 (N13-FIX + IMG-SAFETY-RETRY) + 品牌升级 (BRAND-MANIFESTO + LOGO-REPLACE)，全部 PM Review + Tester 验证 PASS。

**完成内容**:
- [x] Git 提交 3 批:
  - `935f0b0` feat: N13-FIX + IMG-SAFETY-RETRY (7 files)
  - `34fbcc4` feat(frontend): BRAND-MANIFESTO + LOGO-REPLACE (28 files, 19 brand PNGs)
  - `ec3b4fd` docs: agent progress + test scripts (26 files)
- [x] Push to GitHub: `73f8a78..ec3b4fd` → `origin/main`
- [x] rsync 57 文件同步到 VPS
- [x] Docker rebuild api + frontend 容器
- [x] docker compose up -d 重启服务
- [x] 外部验证全部通过

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| `https://prefaceai.mov` | ✅ HTTP 200 |
| `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
| Docker 3 容器 | ✅ 全部 Up (api healthy, frontend up, redis healthy) |

---

### TASK-DEPLOY-R8: T-A~T-K 代码推送 + VPS 部署更新 ✅

**完成时间**: 2026-03-14
**验收状态**: 全部验证通过
**任务类型**: 版本控制 + 部署更新

**背景**: T-A~T-K (11 项平台级修复) + OB-1 修复全部完成，代码已 Code Review 12/12 PASS。Tester 即将执行 R8 E2E 回归验证，需要最新代码部署到 VPS。

**完成内容**:
- [x] 读取 TEAM_CHAT 最新消息，理解部署上下文
- [x] 排除敏感文件（.env, team-members, .claude）
- [x] Git 提交 3 批:
  - `4926a9a` feat: T-A~T-K platform fixes + ShotValidator naturalness (Phase 1 log-only) (9 files)
  - `b98a6df` test: add E2E regression test scripts R4-R7 (4 files)
  - `73f8a78` docs: agent progress + team-brain sync + R7 E2E + T-A~T-K tracking (23 files)
- [x] Push to GitHub: `a33fb32..73f8a78` → `origin/main`
- [x] rsync 代码同步到 VPS `/opt/xuhua-story/`（排除 .env, .git, node_modules, test_output, __pycache__, ssl, team-members, .claude, .team-brain）
- [x] 修复文件权限（UID 501 → trader:trader，通过 root SSH chown -R）
- [x] Docker rebuild api 容器
- [x] docker compose up -d 重启服务（api 重建，frontend/redis 保持运行）
- [x] 外部验证全部通过

**问题处理**:
| # | 问题 | 解决方式 |
|---|------|----------|
| 1 | SSH 默认端口 22 连不上 | 从 completed.md 找到正确端口 58913 |
| 2 | rsync Permission denied (UID 501) | root SSH chown -R trader:trader |
| 3 | --no-cache build SSH 超时 | 重连后利用已缓存层秒级完成 |

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| `https://prefaceai.mov` | ✅ HTTP 200 |
| `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
| Docker api 容器 | ✅ Up (healthy) |
| Docker frontend 容器 | ✅ Up |
| Docker redis 容器 | ✅ Up (healthy) |

---

### TASK-DEPLOY-UPDATE: 代码推送 + VPS 部署更新 ✅

**完成时间**: 2026-03-10
**验收状态**: 全部验证通过

**任务类型**: 版本控制 + 部署更新

**背景**: Frontend 完成 TASK-GCLOUD-OPT + Contact 更新 + TASK-STYLE-THUMBNAILS 集成，Backend 完成 E2E R2/R3 修复 T1-T16，需要统一推送到 GitHub 并部署到 VPS。

**完成内容**:
- [x] 读取 TEAM_CHAT 最新 1088 行（20200-21288），理解全部改动上下文
- [x] 确认 frontend build 通过（18 路由，0 错误）
- [x] 排除敏感文件（.env, docker/ssl）
- [x] Git 提交 3 批:
  - `c367abf` feat: E2E regression fixes T1-T16 + backup model Flash + NB2 rename (11 files)
  - `d57a7c1` feat(frontend): TASK-GCLOUD-OPT + Contact updates + style thumbnails (30 files)
  - `232f2f0` docs: agent progress + team-brain sync + E2E R2/R3 test scripts (32 files)
- [x] Push to GitHub: `702361d..232f2f0` → `origin/main`
- [x] rsync 代码同步到 VPS `/opt/xuhua-story/`
- [x] Docker rebuild frontend + api（--no-cache）
- [x] docker compose up -d 重启全部服务
- [x] 外部验证全部通过

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| `https://prefaceai.mov` | ✅ HTTP 200 |
| `https://prefaceai.mov/api/health` | ✅ `{"status":"healthy"}` |
| `/styles/ghibli.jpg` | ✅ HTTP 200 |
| `/team/kai.jpg` | ✅ HTTP 200 |
| `/demo.mp4` | ✅ HTTP 200 |
| Docker 3 容器 (api+frontend+redis) | ✅ 全部 Up |

---

### TASK-DEPLOY-EXEC Step 1-4: VPS 生产环境部署 ✅

**完成时间**: 2026-03-06
**验收状态**: 基础设施部署完成，等待 Founder 填入 API Key

**任务类型**: 基础设施 / 生产部署

**完成内容**:
- [x] Step 1: VPS 系统准备
  - Swap 4GB 创建 + /etc/fstab 持久化
  - Docker 28.1.1 + Compose v2.35.1 安装
  - trader 加入 docker 组
  - FFmpeg 4.2.7 安装
- [x] Step 2: 项目部署
  - rsync 代码到 /opt/xuhua-story（排除 .git/node_modules/venv/ssl）
  - 清理误传的 venv 目录 + 删除开发 .env
  - 创建 .env.production（PLACEHOLDER 占位符）
  - docker compose up -d --build（3 容器全部启动）
- [x] Step 3: SSL + Nginx HTTPS
  - SCP Origin Certificate 到 /etc/ssl/prefaceai-mov/
  - 创建 Nginx 站点配置 prefaceai-mov
  - nginx -t 通过 + reload
- [x] Step 4: 全面验证
  - Docker 3 容器 Up + Healthy ✅
  - API /health → {"status":"healthy"} ✅
  - Frontend → 200, 57KB HTML ✅
  - Redis → PONG ✅
  - Nginx HTTPS → API/Frontend 代理正常 ✅
  - 外部 https://prefaceai.mov → HTTP/2 200 ✅
  - 外部 https://prefaceai.mov/api/health → healthy ✅
  - 旧站 prefaceai.net + Legacy Flask → 未受影响 ✅

**关键决策**:
- 使用 rsync 而非 git clone（私有仓库无 deploy key）
- 删除误传的 .env 和 venv（安全 + 清洁）
- .env.production 使用占位符，等 Founder 填入真实值

---

### TASK-DEPLOY-EXEC 启动 — 全面状态检查 + 阻塞项识别 ✅

**完成时间**: 2026-03-06
**验收状态**: 检查完成，3 项阻塞已全部解决

**任务类型**: 部署执行 / 状态检查

**完成内容**:
- [x] 读取 TEAM_CHAT 最新 1000 行（19084 行中的 18084-19084）
- [x] 读取部署方案 DOCKER_COMPOSE_DEPLOYMENT_PLAN.md（561 行）
- [x] 读取 VPS 环境文档 VPS_DEPLOYMENT_ENVIRONMENT.md
- [x] 检查 SSL 证书文件: `docker/ssl/*.pem` + `.key` 存在 ✅
- [x] 检查 `frontend/next.config.mjs`: 空配置，缺 `output: 'standalone'` — D1 阻塞
- [x] 检查 `app/main.py`: `/health` 可用 ✅，CORS `["*"]` 需后续限制
- [x] 检查 `requirements.txt`: 无 celery/redis（D4 可延后）
- [x] 检查 `.env.example`: 17 变量模板 ✅
- [x] 检查 git status: 45 文件未提交（代码+文档+测试）
- [x] 输出运维状态报告
- [x] 更新进度文档: current.md + context-for-others.md + completed.md + daily-sync + TEAM_CHAT

**阻塞项**:
| # | 内容 | 解决方式 |
|---|------|----------|
| 1 | D1: next.config.mjs 缺 output: 'standalone' | 待确认谁修改 |
| 2 | 45 文件未提交/未推送 | 待确认 commit+push 节奏 |
| 3 | .env.production API Key | 待 Founder 提供 |

---

### TASK-DEPLOY-PREP Step 3: PM 审查反馈落实 ✅

**完成时间**: 2026-03-05
**验收状态**: 待 PM 二次审核
**依据**: PM [2026-03-05] TEAM_CHAT 审查 PASS + 6 项修改建议（R1-R6）+ Cloudflare SSL 配置

**任务类型**: 基础设施 / 部署方案更新

**完成内容**:
- [x] R1: worker 添加 `profiles: ["celery"]`（初始部署不启动）
- [x] R2: 依赖清单新增 D6 — CORS `allow_origins=["*"]` → 限制为 `prefaceai.mov`
- [x] R6: 移除 `version: "3.8"`（Compose V2 不需要，避免 deprecation warning）
- [x] Nginx HTTP → HTTPS 全面升级（Cloudflare Origin Certificate）
  - HTTP 80 仅做 301 重定向
  - HTTPS 443 + Origin Certificate（`/etc/ssl/prefaceai-mov/`）
  - `ssl_session_cache shared:SSL_MOV:10m` 避免与旧站冲突
  - HSTS `max-age=63072000` 与旧站一致
- [x] 部署步骤新增 Step 3: SSL 证书部署
- [x] 架构图更新（HTTP → HTTPS）
- [x] 风险表 SSL 条目更新为已解决
- [x] 设计决策说明更新

**PM 审查反馈覆盖情况**:
| # | PM 修改建议 | 落实状态 |
|---|------------|---------|
| R1 | worker profiles: ["celery"] | ✅ 已添加 |
| R2 | CORS D6 标注 | ✅ 已添加到依赖清单 |
| R3 | Cloudflare Full (Strict) 已确认 | ✅ N/A — PM 已在 Cloudflare 设置 |
| R4 | 考虑 pg_isready healthcheck | ℹ️ 当前用 SQLite，暂不适用 |
| R5 | gzip_types 补充 font 类型 | ℹ️ 可在实际部署时微调 |
| R6 | 移除 version: "3.8" | ✅ 已移除 |

---

### TASK-DEPLOY-PREP Step 2: Docker Compose 部署方案 ✅

**完成时间**: 2026-03-05
**验收状态**: 待 PM 审核 + Founder 批准
**依据**: PM [2026-03-05 11:19] TEAM_CHAT Docker Compose 方案批准派发（含 6 项注意事项）

**任务类型**: 基础设施 / 部署规划

**完成内容**:
- [x] 架构设计: 4 容器（api + worker + frontend + redis）+ Nginx 反代
- [x] docker-compose.yml 草案（含健康检查、named volumes、内部网络）
- [x] Dockerfile.api 草案（Python 3.11-slim + Pillow + FFmpeg + 中文字体 + Celery）
- [x] Dockerfile.frontend 草案（Node 20 多阶段构建 + standalone 模式）
- [x] Nginx 配置草案（prefaceai.mov + Cloudflare 真实 IP 还原 + API/前端分流）
- [x] 环境变量管理方案（.env.production 运行时挂载，不入 image）
- [x] 部署步骤清单（4 步 + 验证清单 8 项）
- [x] 依赖清单（5 项代码改动 + 9 项 VPS 操作）
- [x] 风险评估（6 项 + 应对策略）

**输出文档**: `.team-brain/knowledge/DOCKER_COMPOSE_DEPLOYMENT_PLAN.md`

**PM 6 项注意事项覆盖情况**:
| # | PM 注意事项 | 方案覆盖 |
|---|------------|---------|
| 1 | 后端 API 层已有基础 + 前后端联调未完成 | ✅ 依赖 D5 标注 |
| 2 | 环境变量安全管理 | ✅ .env.production 方案 |
| 3 | Celery + Redis | ✅ 容器 + 依赖 D2-D4 标注 |
| 4 | Python 版本策略 | ✅ Docker 内 3.11-slim |
| 5 | Nginx 共存 | ✅ 独立站点配置 |
| 6 | 输出格式 | ✅ 架构图 + 配置草案 + 步骤 + 依赖 |

**关键设计决策**:
- 端口仅绑定 `127.0.0.1`，外部流量必须经 Nginx
- Redis 不暴露到宿主机，仅 Docker 内部网络
- Celery worker 可延后（D2-D4），不阻塞初始部署
- 最小可部署集：仅需 Frontend 改 `next.config.mjs`（D1）

---

### TASK-DEPLOY-PREP Step 1: VPS 环境全维度检查 ✅

**完成时间**: 2026-03-05
**验收状态**: Founder 已确认
**依据**: Coordinator 部署指令（技术栈 + SSH 信息 + 域名确认）

**任务类型**: 基础设施 / 部署准备

**完成内容**:
- [x] SSH 连接验证: trader 密钥登录 ✅ + root 密钥登录 ✅
- [x] 硬件检查: 8C / 16GB / 200GB（97% 磁盘空闲）
- [x] OS 检查: Ubuntu 20.04.6 LTS, Python 3.8.10（需升级到 3.10+）
- [x] 已安装软件: Nginx 1.18 + Supervisor 4.1 + Git 2.25
- [x] 缺失软件: Docker、Node.js、Redis、FFmpeg
- [x] 端口占用: :80/:443 Nginx, :5000 旧 Flask, :58913 SSH
- [x] 现有服务确认: prefaceai.net（Prompt 优化工具，保留）+ Momentum Trading（保留）
- [x] Founder 确认 4 项: 旧站保留 / Trading 保留 / root 密钥可用 / prefaceai.mov 主域名
- [x] 环境文档创建: `.team-brain/knowledge/VPS_DEPLOYMENT_ENVIRONMENT.md`

**VPS 摘要**:
```
IP: 107.148.1.199:58913
硬件: 8C Intel Xeon / 16GB RAM / 200GB SSD
OS: Ubuntu 20.04.6 LTS
已有: Nginx + Supervisor + Git + Python 3.8
缺失: Docker + Node.js + Redis + FFmpeg
域名: prefaceai.mov → Cloudflare 代理 → VPS
```

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| trader SSH 密钥登录 | ✅ |
| root SSH 密钥登录 | ✅ |
| 硬件资源充足 | ✅ 8C/16GB/200GB |
| 现有服务不受影响 | ✅ 端口 :5000 + /opt/momentum-trading 不动 |
| Cloudflare DNS 指向 VPS | ✅ prefaceai.mov → 107.148.1.199 |

---

### TASK-GIT-COMMIT-3: SQ/Bugfix + 剩余积压变更提交 + Push ✅

**完成时间**: 2026-03-05
**验收状态**: 待PM核验
**依据**: PM [2026-03-04 21:00] TEAM_CHAT 派发（SQ/Bugfix 7文件）+ PM [2026-03-05] TEAM_CHAT 补充派发（Batch A/B/C + push）

**任务类型**: 版本控制

**完成内容**:
- [x] SQ/Bugfix: 7 文件（SQ-1~8 + Bug#1~5 + Rule#7/#8）— commit `4daad77`
- [x] Batch A: Backend 代码 9 文件（模型升级 + 风格系统 + NB2原生文字）— commit `135acf4`
- [x] Batch B: Frontend 代码 60 文件（Create P0/P1/P2 + Dashboard + Register + 28 mock PNGs）— commit `3a9ec56`
- [x] Batch C: 文档 + 测试 55 文件（agent progress + team-brain + 12测试脚本 + knowledge base）— commit `4af7ea1`
- [x] 统一 push: `e05bbd2..4af7ea1` → `origin/main` ✅

**Commit 信息**:
```
4af7ea1 docs: agent progress + team-brain + tests + knowledge base (55 files, +19306/-816)
3a9ec56 feat(frontend): Create upgrade P0+P1+P2 + Dashboard + Register (60 files, +3863/-1)
135acf4 feat: model upgrade + style system + NB2 native text (9 files, +401/-255)
4daad77 feat: shot quality upgrade (SQ-1~8) + bugfix (#1~5) + prompt rules (#7/#8) (7 files, +566/-83)
总计: 131 files changed, 24136 insertions(+), 1155 deletions(-)
```

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| git status 工作区干净 | ✅ 0 个未提交文件 |
| git log 4 新commits | ✅ 全部完整 |
| git push origin main | ✅ 远程同步成功 |
| 无敏感文件 | ✅ 全部 Batch 安全 |
| storyboard_prompts.py 确认 | ✅ PM 列出但实际无变更，正确跳过 |

---

### GitHub 远程仓库建立 ✅

**完成时间**: 2026-02-26 11:02
**验收状态**: Founder 确认
**依据**: Founder 直接指令（需要给合伙人看项目代码）

**任务类型**: 基础设施

**完成内容**:
- [x] 安装 gh CLI（brew install gh，v2.87.3）
- [x] Founder 手动完成 GitHub 登录（gh auth login → kaiangel）
- [x] 创建 private repo: `prefaceai-story`
- [x] 调整 http.postBuffer（500MB）解决大仓库推送问题
- [x] 推送 main 分支到 origin（6 commits 全部上线）

**仓库信息**:
```
URL: https://github.com/kaiangel/prefaceai-story
可见性: Private
分支: main → origin/main (tracked)
Commits: 6 (全部已推送)
```

**备注**: 另有一个空仓库 `xuhua-story` 待 Founder 在 GitHub 网页手动删除

---

### TASK-GIT-COMMIT-2: 12天积压变更提交 ✅

**完成时间**: 2026-02-24 11:42
**验收状态**: 待PM核验
**依据**: PM [2026-02-24 11:25] TEAM_CHAT 方案（Coordinator 6项任务完成后统一提交）

**任务类型**: 版本控制

**完成内容**:
- [x] Batch 1: 后端代码（11文件，385+/29-）— commit `926f284`
  - 宽高比统一2:3（TASK-ASPECT-2x3, DEC-010）
  - 参考图预处理对比测试（DEC-009）
- [x] Batch 2: 前端代码（30文件，1670+/21-）— commit `825aece`
  - 10个子页面 + SEO metadata（TASK-LP-PAGES, TASK-LP-PAGES-FIX）
- [x] Batch 3: 文档（26文件，4079+/1228-）— commit `e05bbd2`
  - 6个Agent进度更新 + TEAM_CHAT + daily-sync + DECISIONS + PENDING + PROJECT_STATUS + TODAY_FOCUS
- [x] 每个Batch安全检查通过（0个敏感文件）

**Commit 信息**:
```
e05bbd2 docs: update team-brain and agent progress (TASK-LP-PAGES, TASK-ASPECT-2x3, DEC-009/010)
825aece feat(landing-page): add 10 sub-pages with SEO metadata (TASK-LP-PAGES, TASK-LP-PAGES-FIX)
926f284 feat(backend): unify aspect ratio to 2:3 and add ref preprocess test (TASK-ASPECT-2x3, DEC-010)
67 files changed, 6134 insertions(+), 1278 deletions(-)
```

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| git log --oneline -6 | ✅ 6条commit全部完整 |
| git status 无遗漏 | ✅ 工作区基本干净（仅进度文件待追加提交） |
| 无敏感文件 | ✅ 3个Batch均通过安全检查 |

---

### TASK-GIT-COMMIT Step 2: 文档提交 ✅

**完成时间**: 2026-02-12 17:19
**验收状态**: 待PM核验
**依据**: PM 17:15 通知（CLAUDE.md 更新完成，前置条件满足）

**任务类型**: 版本控制

**完成内容**:
- [x] 暂存18个文档文件（.claude/agents/、.team-brain/、claude.md、.claude/settings.json）
- [x] 安全检查（无.env泄露）
- [x] commit: `docs: update team-brain and agent progress (2026-02-12)`

**Commit 信息**:
```
08a0e9f docs: update team-brain and agent progress (2026-02-12)
18 files changed, 1982 insertions(+), 506 deletions(-)
```

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| git status 无遗漏 | ✅ 工作区干净 |
| git log --oneline -3 | ✅ 3条commit完整 |
| 无敏感文件 | ✅ .env 未被追踪 |

---

### TASK-GIT-COMMIT Step 1: LP源码提交 ✅

**完成时间**: 2026-02-12 17:11
**验收状态**: 通过
**依据**: Coordinator 3项协调事项 → PM TASK-GIT-COMMIT 方案

**任务类型**: 版本控制

**完成内容**:
- [x] 暂存5个LP源码文件（globals.css、HeroSection.tsx、Pipeline.tsx、Showcase.tsx、ValueProposition.tsx）
- [x] 安全检查（无.env泄露）
- [x] commit: `feat(landing-page): complete LP fixes and polish (5.0/5)`

**Commit 信息**:
```
a6a0359 feat(landing-page): complete LP fixes and polish (5.0/5)
5 files changed, 375 insertions(+), 218 deletions(-)
```

**Step 2 状态**: 阻塞 — 等待 Coordinator 审核 CLAUDE.md 草案

---

### TASK-GIT-INIT: Git仓库初始化 ✅

**完成时间**: 2026-02-12 11:40
**验收状态**: 待PM核验
**依据**: DEC-007 (Founder决策)

**任务类型**: 基础设施

**完成内容**:
- [x] Step 1: 删除 frontend/.git（避免submodule问题）
- [x] Step 2: 创建 .gitignore（安全红线排除）
- [x] Step 3: 补全 .env.example（4变量 → 17变量，与app/config.py一一对应）
- [x] Step 4: git init -b main + git add -A + git commit
- [x] Step 5: 逐项验证（安全+完整性+统计）

**验证结果**:
| 验证项 | 结果 |
|--------|------|
| 5a. 安全验证 | 9/9 全部OK（.env、*.db、test_output/、venv/、node_modules/、forclaudeweb/、still_image_storyref/、__pycache__、.DS_Store 均未被追踪） |
| 5b. 完整性验证 | 14/14 关键文件全部被追踪 |
| 5c. 统计 | 1条commit (acba309), main分支, 315文件, 仓库18MB |

**Commit 信息**:
```
acba309 chore: initialize git repository (DEC-007)
```

---

### 运维状态全面检查 ✅

**完成时间**: 2026-02-12
**验收状态**: 通过

**任务类型**: 状态检查

**完成内容**:
- [x] 读取 TODAY_FOCUS.md、PROJECT_STATUS.md、PENDING.md
- [x] 检查 deploy/ 目录状态（不存在）
- [x] 检查 git 仓库状态（未初始化）
- [x] 评估运维风险（成本监控缺失、环境变量不完整、无版本控制）
- [x] 确认上游依赖状态（Phase 4 ✅、Phase 4.5 WIP、Phase 5 WIP）
- [x] 更新所有 DevOps progress 文件

**关键发现**:
| 发现 | 风险等级 | 说明 |
|------|----------|------|
| 项目无 git 仓库 | 🟡 中 → ✅ 已解决 | TASK-GIT-INIT 完成 |
| 无成本监控 | 🟡 中 | $9.35/故事，上线前必须建立 |
| .env.example 不完整 | 🟡 中 → ✅ 已解决 | 4→17变量已补全 |
| deploy/ 目录不存在 | 🟢 低 | Phase 6 时创建即可 |

---

## 2026-04-30 11:00 Wave 5.2 部署归档

push: 84e5861 (Wave 5.1 33 files) + 2d9eb58 (OPS-3) + eeff484 (docs)
VPS: docker compose api(healthy) + frontend(up) + redis(healthy)
DB: alembic 002 DDL 通过 aiomysql 直接跑 — projects.is_favorite + share_tokens + share_pv_logs 全到位
本地: backend pid 10712 + frontend pid 11628 真跑 Wave 5.1 代码
Ben 通知: team_ben/TEAM_CHAT.md append
