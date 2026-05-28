# Deploy Parity Check SOP — 部署前 11 维度强制 checklist

> **来源**: DEC-055 Canonical Dev/Prod Parity (5/28 test30 4 处 P0 哑雷连环触发后系统性根治)
> **规则**: 任何部署前 DevOps **必须**逐条跑通, **一条不过不准上**。PM 审查时也用此 SOP cross-check。
> **背景**: 5/28 test30 暴露 PM 之前 dev/prod parity 只盯 DB 栈 (DEC-054), 漏了 .env keys / Nginx 反代 / 静态文件 serving 等 10 维度, 用户测试时连环踩雷。**永不再犯**。

---

## 部署前 checklist (按维度顺序, ⏱ 总 15-30 min)

### 维度 D — `.env` keys 完整性 ✅

**(最关键, 4 处哑雷里 3 处都在这里)**

```bash
# 1. 列出本地 .env 全部 keys (不打印 value)
grep -E '^[A-Z][A-Z_0-9]*=' .env | cut -d= -f1 | sort > /tmp/local_keys.txt

# 2. ssh VPS, 列 .env.production 全部 keys
ssh -p 58913 trader@107.148.1.199 \
  "grep -E '^[A-Z][A-Z_0-9]*=' /opt/xuhua-story/.env.production | cut -d= -f1 | sort" \
  > /tmp/vps_keys.txt

# 3. 看本地有 VPS 没 (必须 0 diff, 否则 P0 阻塞部署)
diff /tmp/local_keys.txt /tmp/vps_keys.txt
# 期望: 仅有 ops-only 显式化 keys 差异 (AUDIO_STORAGE_PATH / IMAGE_GENERATION_TIMEOUT 等 config 有默认值的)
# 任何 API key / SKIP_ flag / IMAGE_GEN_PROVIDER / PROMPT_FORMAT 缺失 → 立即 append + force-recreate
```

**Boolean 关键 flag 单独 verify (防 SKIP=true 漏)**:
```bash
ssh -p 58913 trader@107.148.1.199 \
  "grep -E '^(SKIP_|MOCK_|TEXT_ONLY|DISABLE_)' /opt/xuhua-story/.env.production"
# 期望: SKIP_IMAGE_GENERATION=false (或不存在)
# 任何 =true 立即追问"是否真的要 skip"
```

**容器 runtime env 实证**:
```bash
ssh -p 58913 trader@107.148.1.199 \
  "docker exec docker-api-1 python3 -c \"
from app.config import settings
keys = ['ANTHROPIC_API_KEY','GEMINI_API_KEY','ARK_API_KEY','OPENAI_API_KEY','MUREKA_API_KEY',
        'VOLCENGINE_API_KEY','VOLCENGINE_ACCESS_KEY','VOLCENGINE_SECRET_KEY','DATABASE_URL']
for k in keys:
    v = getattr(settings, k, '')
    assert v, f'{k} MISSING'
    print(f'{k}: len={len(v)}')
print('SKIP_IMAGE_GENERATION:', settings.SKIP_IMAGE_GENERATION)
print('IMAGE_GEN_PROVIDER:', settings.IMAGE_GEN_PROVIDER)
print('PROMPT_FORMAT:', settings.PROMPT_FORMAT)
\""
# 期望: 全部 OK, SKIP=False, PROVIDER=seedream, FORMAT=b_prime
```

---

### 维度 E — Nginx / 反向代理完整性 ✅

**对照 FastAPI mount 路径**:
```bash
# 1. 列出代码中所有 FastAPI mount
grep -nE 'app\.mount\(' app/main.py
# 期望: app.mount("/static/outputs", StaticFiles(directory=...))

# 2. ssh VPS, 看 Nginx location 块
ssh -p 58913 trader@107.148.1.199 \
  "cat /etc/nginx/sites-enabled/prefaceai-mov | grep -E '^\\s*location' | sort -u"
# 期望: /api/ + /static/ + / + /_next/static/ 全在

# 3. 端到端测试: 每个 mount 路径外部 curl
for path in static/outputs/SOME_PROJECT_UUID/images/shot_01.png; do
  echo "Test /${path}:"
  curl -sI --max-time 10 "https://prefaceai.mov/${path}" | head -3
done
# 期望: HTTP/2 200 + Content-Type 对的格式
```

**任何 mount 路径无对应 location 块 → 立即派 DevOps 补 nginx config + reload, 否则 deploy 阻塞**.

---

### 维度 G — 静态文件 mount 链路端到端 ✅

```bash
# 五段链路全 verify
# 1. 后端 app/main.py mount 路径
grep -E 'app.mount' app/main.py
# 2. Pipeline 写文件目录
grep -rnE 'output_dir.*join.*character_refs|output_dir.*join.*images' app/services/pipeline_orchestrator.py | head -3
# 3. Docker volume 挂载
ssh -p 58913 trader@107.148.1.199 \
  "docker inspect docker-api-1 | grep -A2 'output_data\\|/app/output'"
# 4. Nginx proxy_pass
ssh -p 58913 trader@107.148.1.199 \
  "grep -A3 'location /static/' /etc/nginx/sites-enabled/prefaceai-mov"
# 5. 外部 curl HTTP 200
curl -sI 'https://prefaceai.mov/static/outputs/EXISTING_PROJECT_UUID/images/shot_01.png' | head -3
```

---

### 维度 C — DB 栈 (DEC-054 canonical) ✅

```bash
# 容器 pip show 三包版本必须精确
ssh -p 58913 trader@107.148.1.199 \
  "docker exec docker-api-1 pip show sqlalchemy asyncmy pymysql | grep -E 'Name|Version'"
# 期望: SQLAlchemy 2.0.50 + asyncmy 0.2.11 + pymysql 1.1.2 (DEC-054)

# 容器内 settings.DATABASE_URL 实证 asyncmy 驱动 + utf8mb4
ssh -p 58913 trader@107.148.1.199 \
  "docker exec docker-api-1 python3 -c 'from app.config import settings; assert settings.DATABASE_URL.startswith(\"mysql+asyncmy\"); print(settings.DATABASE_URL[:50])'"
```

---

### 维度 B — Python 依赖 (requirements.txt pin) ✅

```bash
# 本地 vs VPS requirements.txt MD5 一致
LOCAL_MD5=$(md5sum requirements.txt 2>/dev/null | awk '{print $1}' || md5 -q requirements.txt)
VPS_MD5=$(ssh -p 58913 trader@107.148.1.199 "md5sum /opt/xuhua-story/requirements.txt" | awk '{print $1}')
echo "Local: $LOCAL_MD5"
echo "VPS:   $VPS_MD5"
# 必须一致, 否则 rsync requirements.txt + 重新 docker build --no-cache
```

---

### 维度 A — 应用代码同步 ✅

```bash
# git HEAD 双侧一致 (本地 commit / VPS 部署的代码)
LOCAL_HEAD=$(git rev-parse --short HEAD)
# VPS 部署后 PM 用 rsync, 无 git history. 容器内代码用 MD5 比对关键文件:
for f in app/api/projects.py app/services/pipeline_orchestrator.py app/services/seedream_generator.py app/main.py; do
  L=$(md5sum "$f" 2>/dev/null | awk '{print $1}' || md5 -q "$f")
  V=$(ssh -p 58913 trader@107.148.1.199 "docker exec docker-api-1 md5sum /app/$f | awk '{print \$1}'")
  echo "$f: L=$L V=$V $([ "$L" = "$V" ] && echo ✅ || echo ❌)"
done
```

---

### 维度 F — Docker 配置 ✅

```bash
# docker-compose.yml volume + ports + healthcheck
ssh -p 58913 trader@107.148.1.199 \
  "cd /opt/xuhua-story/docker && docker compose config | grep -E 'volumes:|ports:|healthcheck:'"

# 三容器状态 healthy + restart policy
ssh -p 58913 trader@107.148.1.199 \
  "docker ps --format '{{.Names}}: {{.Status}}' | grep -E 'docker-api-1|docker-frontend-1|docker-redis-1'"
```

---

### 维度 K — Build-time env (Next.js NEXT_PUBLIC_*) ✅

```bash
# Dockerfile.frontend 中 NEXT_PUBLIC_API_URL 必须 build time 注入
grep -E 'NEXT_PUBLIC_' docker/Dockerfile.frontend
# 期望: ENV NEXT_PUBLIC_API_URL=https://prefaceai.mov/api

# 容器内 .next/static 编译后是否含正确 API_URL
# (sample 抽测, 不强制)
```

---

### 维度 H — 服务启动方式 ✅

```bash
# 容器内进程必须是 uvicorn (不带 --reload, 防 metadata lock 死锁)
ssh -p 58913 trader@107.148.1.199 \
  "docker exec docker-api-1 ps aux | grep -E 'uvicorn|node|next' | grep -v grep"
# 期望: uvicorn app.main:app --host 0.0.0.0 --port 8000 (无 --reload)
#       Next.js: next-server (production)
```

---

### 维度 I — 端口 / 网络 ✅

```bash
# host 端口绑定 (127.0.0.1, 防公网直暴露)
ssh -p 58913 trader@107.148.1.199 \
  "ss -tlnp | grep -E ':8000|:3000|:443|:80\b'"
# 期望: 127.0.0.1:8000 (api) / 127.0.0.1:3000 (frontend) / 0.0.0.0:443+80 (nginx)
```

---

### 维度 J — 文件权限 ✅ (低优先级)

```bash
# Docker 容器 root 写 volume, host trader 可读 (755 自动)
ssh -p 58913 trader@107.148.1.199 \
  "ls -la /var/lib/docker/volumes/docker_output_data/_data/ | head -3"
# 期望: root:root 文件, 755 权限, trader (uid≠0) 可读
```

---

## 端到端 smoke test (deploy 后)

```bash
# 1. 健康端点
curl -sI https://prefaceai.mov/api/health | head -1  # 期望 HTTP/2 200
curl -sI https://prefaceai.mov/ | head -1            # 期望 HTTP/2 200

# 2. 静态文件 (用现有项目的 png)
EXISTING_UUID="a3966a40-6d27-42c0-a7cf-109729e453e7"  # VPS 上已知有图的项目
curl -sI "https://prefaceai.mov/static/outputs/${EXISTING_UUID}/images/shot_01.png" | head -3
# 期望: HTTP/2 200 + Content-Type: image/png

# 3. /api/projects 401 (无 auth, 正常)
curl -s -o /dev/null -w '%{http_code}\n' https://prefaceai.mov/api/projects/
# 期望: 401 (不是 500, 不是 404)

# 4. 容器 ping bug 实证 (DEC-054 P0 根治验证)
ssh -p 58913 trader@107.148.1.199 \
  "docker logs --since 5m docker-api-1 2>&1 | grep -c 'ping().*missing.*reconnect'"
# 期望: 0 (修前是 120/30min)
```

---

## 失败处理

任何 checklist 项失败:
1. **立即终止部署** — 不上生产
2. DevOps **明确报告失败项** + 根因
3. 派对应 Agent 修复 (Backend / AI-ML / Frontend / DevOps)
4. **必须从 checklist 第一项重跑** (不要从失败项往后跑, 避免漏依赖)

---

## 历史教训 (这个 SOP 的来源)

| 日期 | 事件 | 教训 |
|---|---|---|
| 2026-05-27 | DEC-054 P0 ping bug — VPS PyMySQL 1.2.0 vs 本地 1.1.2 分裂 | 加 B 维度 requirements pin |
| 2026-05-28 06:20 | SKIP_IMAGE_GENERATION=true 误开 | 加 D 维度 boolean kill switch 单独 verify |
| 2026-05-28 06:45 | ARK_API_KEY 完全缺失 | 加 D 维度 `diff local vs vps keys` + 容器 runtime API key assert |
| 2026-05-28 07:12 | Nginx 缺 location /static/ | 加 E 维度 mount path vs nginx location cross-check + end-to-end smoke test |

---

## 维护

- 每次新发现 dev/prod 哑雷, 在历史教训表加一行 + 对应维度加 check 步骤
- PM 每月或每次大版本部署前重审此 SOP
- DevOps 部署前必须签字确认 11 维度全过 (在 TEAM_CHAT 留一条 "✅ SOP 11 维度全过, 可部署")

---

— PM (Opus 4.7, 2026-05-28)
