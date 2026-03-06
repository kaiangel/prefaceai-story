# Docker Compose 部署方案

> **创建时间**: 2026-03-05
> **最后更新**: 2026-03-05（Step 3: PM 审查反馈 R1/R2/R6 + Nginx HTTPS 更新）
> **作者**: DevOps Agent
> **状态**: Step 3 更新完成，待 PM 二次审核
> **前置文档**: `.team-brain/knowledge/VPS_DEPLOYMENT_ENVIRONMENT.md`

---

## 1. 架构总览

```
                         Internet
                            │
                      ┌─────┴─────┐
                      │ Cloudflare│  ← HTTPS 终止 + CDN + DDoS 防护
                      │  Proxy    │     SSL 模式: Full (Strict)
                      └─────┬─────┘
                            │ HTTPS (port 443, Origin Certificate)
                     ┌──────┴──────┐
                     │   Nginx     │  ← VPS 上已有，新增 prefaceai.mov 站点
                     │  (宿主机)   │     443 SSL + 80→443 重定向
                     └──┬─────┬───┘
                        │     │
            ┌───────────┘     └───────────┐
            │                             │
    ┌───────┴────────┐           ┌────────┴────────┐
    │  frontend:3000 │           │   api:8000      │
    │  (Next.js 14)  │           │  (FastAPI)      │
    │  Docker 容器    │           │  Docker 容器     │
    └────────────────┘           └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │  redis:6379     │
                                 │  (Broker)       │
                                 │  Docker 容器     │
                                 └────────┬────────┘
                                          │
                                 ┌────────┴────────┐
                                 │  worker         │
                                 │  (Celery)       │
                                 │  Docker 容器     │
                                 └─────────────────┘

    旧站（不动）:
    ├── :5000 Flask (prefaceai.net API, supervisor 管理)
    └── /var/www/prefaceai/dist/ (prefaceai.net 前端)
    └── /opt/momentum-trading/ (量化交易系统)
```

**端口规划**:

| 端口 | 服务 | 来源 | 说明 |
|------|------|------|------|
| 80 | Nginx | 宿主机（已有） | HTTP → 301 重定向到 HTTPS |
| 443 | Nginx | 宿主机（已有） | HTTPS — prefaceai.mov (Origin Cert) + prefaceai.net (旧站) |
| 3000 | Next.js | Docker 容器 → 宿主机映射 | 仅 localhost 暴露 |
| 8000 | FastAPI | Docker 容器 → 宿主机映射 | 仅 localhost 暴露 |
| 6379 | Redis | Docker 内部网络 | 不对宿主机暴露 |
| 5000 | Flask 旧站 | 宿主机（不动） | prefaceai.net |
| 58913 | SSH | 宿主机（不动） | 管理入口 |

---

## 2. Docker Compose 配置草案

### docker-compose.yml

```yaml
services:
  # ─── Redis (Celery Broker + 缓存) ───
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - xuhua_net
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # ─── FastAPI 后端 ───
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    env_file:
      - .env.production
    volumes:
      - storage_data:/app/storage
      - sqlite_data:/app/data
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - xuhua_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  # ─── Celery Worker (异步任务) ───
  # 初始部署不启动（代码中 Celery 不存在），D2-D4 完成后用 --profile celery 启用
  worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    restart: unless-stopped
    profiles: ["celery"]
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    env_file:
      - .env.production
    volumes:
      - storage_data:/app/storage
      - sqlite_data:/app/data
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - xuhua_net

  # ─── Next.js 前端 ───
  frontend:
    build:
      context: ./frontend
      dockerfile: ../docker/Dockerfile.frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=https://prefaceai.mov/api
    networks:
      - xuhua_net

volumes:
  redis_data:
  storage_data:     # 图像 + 音频生成产物
  sqlite_data:      # SQLite 数据库文件

networks:
  xuhua_net:
    driver: bridge
```

**设计决策说明**:
- `127.0.0.1:8000:8000` — 仅绑定 localhost，外部流量必须经 Nginx 反代，不可直接访问
- Redis 不暴露端口到宿主机 — 仅 Docker 内部网络通信
- `storage_data` 和 `sqlite_data` 用 named volumes — 容器重建不丢数据
- api 和 worker 共用同一 image — 只是启动命令不同
- worker 加 `profiles: ["celery"]` — 初始 `docker compose up` 不启动（代码无 Celery），待 D2-D4 完成后用 `docker compose --profile celery up -d` 启用
- 移除 `version: "3.8"` — Compose V2 不再需要，保留会触发 deprecation warning

---

## 3. Dockerfile 草案

### docker/Dockerfile.api

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 系统依赖（Pillow 编译 + FFmpeg + curl for healthcheck）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg62-turbo-dev \
    libpng-dev \
    libfreetype6-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir celery[redis] redis

# 中文字体（TextOverlay 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 应用代码
COPY app/ ./app/
COPY docs/ ./docs/

# 默认启动命令（API 服务）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**说明**:
- 基于 `python:3.11-slim`（解决 VPS 系统 Python 3.8 太旧的问题）
- 安装 `fonts-noto-cjk`（TextOverlayService 需要中文字体渲染）
- FFmpeg 打包进镜像（Phase 4.5 视频合成需要）
- `celery[redis]` 和 `redis` 额外安装（当前 requirements.txt 没有）
- worker 容器复用此镜像，仅覆盖 CMD

### docker/Dockerfile.frontend

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# 需要在 next.config.mjs 中添加 output: 'standalone'
ENV NEXT_PUBLIC_API_URL=https://prefaceai.mov/api
RUN npm run build

# --- 生产阶段 ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# standalone 模式仅需这些文件
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

**说明**:
- 多阶段构建，生产镜像极小
- 需要前端代码改动: `next.config.mjs` 添加 `output: 'standalone'`（见依赖清单）
- `NEXT_PUBLIC_API_URL` 构建时注入，指向 `https://prefaceai.mov/api`

---

## 4. Nginx 配置草案

### /etc/nginx/sites-enabled/prefaceai-mov

```nginx
# HTTP → HTTPS 重定向
server {
    listen 80;
    server_name prefaceai.mov www.prefaceai.mov;
    return 301 https://$host$request_uri;
}

# HTTPS 主站（Cloudflare Full Strict + Origin Certificate）
server {
    listen 443 ssl http2;
    server_name prefaceai.mov www.prefaceai.mov;

    # Cloudflare Origin Certificate
    ssl_certificate /etc/ssl/prefaceai-mov/prefaceai-mov-origin.pem;
    ssl_certificate_key /etc/ssl/prefaceai-mov/prefaceai-mov-origin.key;

    # SSL 优化
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL_MOV:10m;
    ssl_session_timeout 10m;

    # Cloudflare 真实 IP 还原
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    set_real_ip_from 162.158.0.0/15;
    set_real_ip_from 104.16.0.0/13;
    set_real_ip_from 104.24.0.0/14;
    set_real_ip_from 172.64.0.0/13;
    set_real_ip_from 131.0.72.0/22;
    real_ip_header CF-Connecting-IP;

    # 安全头
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;

    # API 路由 → FastAPI 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 图像生成可能耗时较长
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        # 上传大小（图片上传）
        client_max_body_size 50m;
    }

    # 其他所有路由 → Next.js 前端
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Next.js 静态资源缓存
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 日志
    access_log /var/log/nginx/prefaceai-mov.access.log;
    error_log /var/log/nginx/prefaceai-mov.error.log;
}
```

**设计决策说明**:
- **443 + SSL + Origin Certificate**：Cloudflare SSL 设为 Full (Strict)，源站必须支持 HTTPS，使用 Cloudflare Origin Certificate
- **80 → 301 HTTPS**：HTTP 仅做重定向，所有实际流量走 HTTPS
- **ssl_session_cache 命名 `SSL_MOV`**：避免与旧站 prefaceai.net 的 `SSL:10m` 冲突
- **HSTS**：`max-age=63072000`（2年），与旧站 prefaceai.net 配置一致
- **`/api/` → :8000**：统一入口，前端通过 `/api/` 前缀访问后端
- **`/` → :3000**：所有非 API 路由交给 Next.js
- **proxy_read_timeout 300s**：图像生成单次可能耗时 2-3 分钟
- 与现有 `prefaceai.net` 配置互不干扰（不同 server_name）

---

## 5. 环境变量管理

### .env.production（VPS 上创建，不入版本控制）

```bash
# === AI API Keys ===
ANTHROPIC_API_KEY=sk-ant-xxx
GEMINI_API_KEY=AIzaSyxxx
OPENAI_API_KEY=sk-xxx

# === 火山引擎 TTS ===
VOLCENGINE_APP_ID=xxx
VOLCENGINE_ACCESS_KEY=AKLTxxx
VOLCENGINE_RESOURCE_ID=volcano_tts
VOLCENGINE_DEFAULT_VOICE=zh_female_shuangkuaisisi_moon_bigtts

# === 数据库 ===
DATABASE_URL=sqlite+aiosqlite:///./data/xuhua_story.db

# === 服务器 ===
HOST=0.0.0.0
PORT=8000
DEBUG=false

# === 存储 ===
IMAGE_STORAGE_PATH=/app/storage/images
AUDIO_STORAGE_PATH=/app/storage/audio

# === 图像生成 ===
IMAGE_MAX_CONCURRENT=3
IMAGE_GENERATION_TIMEOUT=120

# === 分镜拆分 ===
SHOT_MAX_NARRATION_LENGTH=60
SHOT_TARGET_LENGTH=40
SHOT_MIN_LENGTH=25
TTS_CHARS_PER_SECOND=4.0

# === Celery ===
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

**安全策略**:
- `.env.production` 只在 VPS 上存在，**不入 Git**（.gitignore 已排除 `.env`）
- Docker image 中不包含任何 API Key — 运行时通过 `env_file` 挂载
- 敏感变量绝不通过 `docker-compose.yml` 的 `environment` 字段明文写入

---

## 6. 部署步骤（执行阶段用）

以下步骤在 PM 审核 + Founder 批准后执行，此处仅列出清单。

### Step 1: VPS 系统准备（root 操作）

```bash
# 1.1 创建 Swap（4GB）
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 1.2 安装 Docker + Compose
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
# Docker Compose V2 已包含在 Docker CE 中

# 1.3 将 trader 用户加入 docker 组（免 sudo 操作 Docker）
usermod -aG docker trader

# 1.4 安装 FFmpeg（宿主机备用，容器内也有）
apt-get update && apt-get install -y ffmpeg
```

### Step 2: 项目部署

```bash
# 2.1 克隆代码到 VPS
su - trader
cd /opt
git clone https://github.com/kaiangel/prefaceai-story.git xuhua-story
cd xuhua-story

# 2.2 创建 .env.production（手动填入真实 Key）
cp .env.example .env.production
nano .env.production  # 编辑填入实际值

# 2.3 创建 docker 目录结构
mkdir -p docker

# 2.4 创建 Dockerfile 和 docker-compose.yml
# (将本文档中的草案写入对应文件)

# 2.5 构建 + 启动（不含 worker，因为 Celery 代码尚不存在）
docker compose up -d --build

# 2.6 验证
docker compose ps          # 应看到 3 个容器: api + frontend + redis
docker compose logs api --tail 20
docker compose logs frontend --tail 20
curl http://localhost:8000/health
curl http://localhost:3000
```

### Step 3: SSL 证书部署 + Nginx 配置（root 操作）

```bash
# 3.1 复制 Origin Certificate 到 VPS 标准位置
sudo mkdir -p /etc/ssl/prefaceai-mov
sudo cp docker/ssl/prefaceai-mov-origin.pem /etc/ssl/prefaceai-mov/
sudo cp docker/ssl/prefaceai-mov-origin.key /etc/ssl/prefaceai-mov/
sudo chmod 600 /etc/ssl/prefaceai-mov/prefaceai-mov-origin.key
sudo chmod 644 /etc/ssl/prefaceai-mov/prefaceai-mov-origin.pem

# 3.2 创建 prefaceai.mov 站点配置
sudo nano /etc/nginx/sites-enabled/prefaceai-mov
# (写入本文档中的 Nginx HTTPS 配置)

# 3.3 测试 + 重载
sudo nginx -t
sudo systemctl reload nginx

# 3.4 验证（从外部访问）
curl -I https://prefaceai.mov
```

### Step 4: 验证清单

| 验证项 | 命令 | 预期 |
|--------|------|------|
| Docker 容器状态 | `docker compose ps` | 4 个容器 Up |
| API 健康检查 | `curl localhost:8000/health` | `{"status":"healthy"}` |
| 前端页面 | `curl localhost:3000` | HTML 响应 |
| Redis 连通 | `docker compose exec redis redis-cli ping` | PONG |
| Nginx 代理 | `curl -H "Host: prefaceai.mov" localhost/api/health` | API 响应 |
| 外部访问 | `curl https://prefaceai.mov` | 前端页面 |
| 旧站不受影响 | `curl https://www.prefaceai.net` | 旧站正常 |
| Trading 不受影响 | 检查 momentum-trading 进程 | 运行中 |

---

## 7. 依赖清单（实施前须完成）

### 代码改动（由对应 Agent 完成后 DevOps 才能部署）

| # | 改动 | 负责 Agent | 说明 | 阻塞部署？ |
|---|------|-----------|------|-----------|
| D1 | `frontend/next.config.mjs` 添加 `output: 'standalone'` | Frontend | Docker 优化构建必需 | ✅ 是 |
| D2 | 创建 `app/celery_app.py` Celery 应用定义 | Backend | 当前代码中 Celery 完全不存在 | ⚠️ 可延后 |
| D3 | 创建 Celery 任务文件（图像生成/TTS 异步化） | Backend | 与 D2 配套 | ⚠️ 可延后 |
| D4 | `requirements.txt` 添加 `celery[redis]` + `redis` | Backend | 与 D2 配套 | ⚠️ 可延后 |
| D5 | 前后端联调（API 对接替换 Mock 数据） | Frontend + Backend | 当前前端用 Mock 数据 | ⚠️ 可延后 |
| D6 | `app/main.py` CORS `allow_origins=["*"]` → 限制为 `prefaceai.mov` | Backend | 当前允许所有来源，生产需限制 | ⚠️ 可延后 |

**最小可部署集**：只需 D1 即可完成初始部署（API + 前端 + Redis 就位）。D2-D4（Celery）可在部署后补充——初始阶段图像生成可走同步模式。D5 是产品完整性问题，不阻塞基础设施部署。

### VPS 操作（DevOps 执行）

| # | 操作 | 用户 | 说明 |
|---|------|------|------|
| V1 | 创建 4GB Swap | root | 防止 OOM |
| V2 | 安装 Docker + Compose | root | 容器化基础 |
| V3 | trader 加入 docker 组 | root | 免 sudo 操作 |
| V4 | 克隆代码仓库 | trader | 从 GitHub 拉取 |
| V5 | 创建 .env.production | trader | 手动填入 API Key |
| V6 | 创建 Dockerfile + docker-compose.yml | trader | 根据本方案 |
| V7 | docker compose up | trader | 构建 + 启动 |
| V8 | Nginx 站点配置 | root | prefaceai.mov |
| V9 | 全面验证 | trader | 按 Step 4 验证清单 |

---

## 8. 风险与应对

| 风险 | 等级 | 应对 |
|------|------|------|
| Docker 安装中断已有服务 | 低 | Docker 安装不影响 Nginx/Supervisor/Trading |
| Nginx 配置错误影响旧站 | 中 | 新增独立配置文件，`nginx -t` 必须通过才 reload |
| 内存不足（16GB 跑 4 容器 + 旧服务） | 低 | 创建 4GB Swap + worker concurrency=2 控制 |
| SQLite 并发限制 | 中 | MVP 阶段够用；高并发需迁移 PostgreSQL（记为后续 TODO） |
| ~~Cloudflare SSL 模式不匹配~~ | ~~中~~ | ✅ 已解决 — Full (Strict) + Origin Certificate + Nginx HTTPS 443 |
| 首次构建耗时长 | 低 | Python 依赖 + Pillow 编译 + Node 构建，预计 5-10 分钟 |

---

## 9. 后续演进（不在当前方案范围）

| 阶段 | 内容 | 触发条件 |
|------|------|----------|
| Phase 2 | PostgreSQL 替代 SQLite | 用户量增长 / 并发需求 |
| Phase 2 | CI/CD 流水线（GitHub Actions → 自动部署） | 部署稳定后 |
| Phase 3 | 监控告警（Prometheus + Grafana / Uptime Kuma） | 生产运行后 |
| Phase 3 | 日志聚合（Docker logs → 持久化） | 生产运行后 |
| Phase 4 | 水平扩展（多 worker 节点） | 用户量级增长 |
