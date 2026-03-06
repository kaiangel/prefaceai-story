# VPS 部署环境文档

> **创建时间**: 2026-03-05
> **最后更新**: 2026-03-05
> **维护者**: DevOps Agent
> **用途**: 序话Story 生产部署的目标服务器环境全维度记录

---

## SSH 连接信息

```
IP: 107.148.1.199
SSH 端口: 58913
用户: trader（普通用户，无免密 sudo）/ root（密钥登录 ✅）
密钥: /Users/kaisbabybook/.ssh/id_ed25519（ED25519）
指纹: SHA256:ySk2HcTI+VUAWuXsZ5V/3zv0zmUojzC+WjNl5Pd+zd0

连接命令:
  trader:  ssh -p 58913 -i ~/.ssh/id_ed25519 trader@107.148.1.199
  root:    ssh -p 58913 -i ~/.ssh/id_ed25519 root@107.148.1.199
```

---

## 硬件资源

| 项目 | 配置 | 评估 |
|------|------|------|
| CPU | 8 核 Intel Xeon Skylake (x86_64) | 充足 |
| 内存 | 16 GB（已用 575MB，可用 14GB） | 充足 |
| 磁盘 | 200 GB（已用 6GB，剩余 193GB = 97%） | 非常充裕 |
| Swap | 无 | 需要创建（建议 4GB） |
| 网络 | 公网 IP 107.148.1.199 | 正常 |

---

## 操作系统

| 项目 | 详情 |
|------|------|
| OS | Ubuntu 20.04.6 LTS (Focal Fossa) |
| 内核 | 5.4.0-216-generic |
| 时区 | UTC |
| Uptime | 44 天（截至 2026-03-05） |
| 备注 | 标准支持已于 2025-04 结束，ESM 安全更新延续至 2030 |

---

## 已安装软件

| 软件 | 版本 | 状态 |
|------|------|------|
| Nginx | 1.18.0 | 运行中，3 个站点配置 |
| Git | 2.25.1 | 可用 |
| Supervisor | 4.1.0 | 运行中，管理旧 Flask 进程 |
| Python 3 | **3.8.10** | ⚠️ 需升级到 3.10+（FastAPI + Pydantic v2 要求） |
| pip3 | 25.0.1 | 可用 |
| anthropic SDK | 0.72.0 | 已安装（momentum-trading 依赖） |

### 未安装（序话Story 部署所需）

| 软件 | 用途 | 优先级 |
|------|------|--------|
| Docker + Compose | 容器化部署 | P0 |
| Node.js 20 LTS | Next.js 前端构建 | P0 |
| Redis | Celery 任务队列 | P0 |
| FFmpeg | Phase 4.5 视频合成 | P1（可后装） |

---

## 端口占用

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | Nginx | HTTP |
| 443 | Nginx (SSL) | HTTPS — 旧版 prefaceai.net 站点 |
| 5000 | Flask 后端 | 旧版 prefaceai.net API（supervisor 管理） |
| 58913 | SSH | 自定义端口 |

---

## 现有服务（不可动）

### 1. 旧版 prefaceai.net — Prompt 优化工具（保留运行）

- **前端**: `/var/www/prefaceai/dist/`（静态 SPA）
- **后端**: `/home/www/sumai/mainv2.py`（Flask，supervisor 管理，:5000）
- **SSL 证书**: `/home/www/sumai/cert/prefaceai.net.pem` + `.key`
- **Nginx 配置**:
  - `prefaceai` — `www.prefaceai.net` → 静态文件 + SSL
  - `prefaceai_api` — `api.prefaceai.net` → proxy :5000

### 2. Momentum Trading 系统（保留运行）

- **路径**: `/opt/momentum-trading/`
- **内容**: signal_system_v4.x.py（量化交易信号系统）
- **数据**: signals.db + 日志
- **说明**: 与序话Story 无关，trader 用户的交易系统，短暂中断可接受

---

## 域名 & 网络

| 域名 | 用途 | DNS | 说明 |
|------|------|-----|------|
| `prefaceai.mov` | 序话Story 主域名 | Cloudflare 代理 → VPS | 橙色云朵已开启，HTTPS 由 Cloudflare 处理 |
| `www.prefaceai.mov` | 同上 | Cloudflare 代理 → VPS | 同上 |
| `prefaceai.net` | 旧版 Prompt 优化工具 | 本地 SSL 证书 | 保留不动 |
| `api.prefaceai.net` | 旧版 API | proxy → :5000 | 保留不动 |

**Cloudflare 配置确认**:
- `prefaceai.mov` + `www` A 记录 → 107.148.1.199（通过 Cloudflare 代理）
- Cloudflare 代理模式下，HTTPS 自动处理（Origin Certificate 或 Full/Flexible 模式）
- 其他 CNAME（autodiscover 等）为 Microsoft 365 邮箱配置，不需要动

---

## Coordinator 部署建议（原文摘要）

### 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 API | Python + FastAPI | 异步架构，async/await |
| 前端 | Next.js 14 | 已完成 LP + Create 全流程（18 路由） |
| 任务队列 | Celery + Redis | 图像生成、TTS 等耗时任务异步处理 |
| 外部 API | Gemini（生图）、Claude（文本）、OpenAI Whisper（对齐）、火山引擎（TTS） |
| 图像处理 | Pillow (PIL) | TextOverlay 文字叠加 |
| 视频合成 | FFmpeg（Phase 4.5 待完成） | 暂未上线 |

### 建议的部署架构

```
Nginx (反向代理 + HTTPS via Cloudflare)
├── :3000 → Next.js 前端
├── :8000 → FastAPI 后端
└── Redis → Celery Worker(s)
```

### 所需环境变量

```
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude Sonnet 4.6
GEMINI_API_KEY=AIzaSyxxx           # Gemini (生图+参考图)
OPENAI_API_KEY=sk-xxx              # Whisper
VOLCENGINE_ACCESS_KEY=AKLTxxx      # 火山引擎 TTS
VOLCENGINE_SECRET_KEY=xxx
VOLCENGINE_TTS_APPID=xxx
```

---

## Founder 确认事项（2026-03-05）

| 问题 | Founder 回复 |
|------|-------------|
| 旧版 prefaceai.net 保留？ | ✅ 保留 — 还在运行的 Prompt 优化工具项目 |
| Momentum Trading 保留？ | ✅ 保留 — 短暂中断可接受 |
| root 权限 | ✅ root 密钥登录已验证可用，无需密码 |
| 域名方案 | `prefaceai.mov` 为序话Story 主域名，Cloudflare 代理 → VPS |

---

## 部署注意事项

1. **端口规划**: 旧站占了 :5000，序话Story 后端用 :8000，前端用 :3000，Redis 用 :6379
2. **Nginx 共存**: 新增 `prefaceai.mov` 站点配置，与现有 `prefaceai.net` 配置并存
3. **Python 版本**: 系统 Python 3.8 不动（momentum-trading 依赖），序话Story 通过 Docker 或 pyenv 使用 3.10+
4. **磁盘**: 图像生成输出可能占空间较大，193GB 够用但需监控
5. **Swap**: 务必创建，图像生成和 Celery worker 可能突发内存需求
6. **防火墙**: ufw 未启用，端口暴露需注意安全
