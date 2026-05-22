# IncompleteRead 监控系统 — 部署与使用手册

> **状态**: 已创建（本地脚本阶段，暂不自动部署到 VPS）
> **创建日期**: 2026-05-18
> **对应 RISK**: RISK-T18-I P3

---

## 1. 背景

Seedream 下载图片偶发 `IncompleteRead` 网络抖动。Pipeline 内部已有 retry 机制，不阻断生成流程。

**test18 实测基线**（2026-05-18）：
- 每次故事生成：~8 次 IncompleteRead
- 全部 1 次 retry 成功，0 次耗尽失败
- Retry 成功率：**100%**
- 每小时频率（3 并发故事）：估计 ~16 次/hr（正常）

监控目标：频率**突增**时（网络质量恶化、Seedream 服务波动）及时知道。

---

## 2. 文件清单

| 文件 | 说明 |
|------|------|
| `scripts/monitor_incompleteread.py` | 核心监控脚本 |
| `scripts/monitor.yaml` | 告警阈值配置文件（唯一需要修改的地方） |
| `docs/MONITORING_INCOMPLETEREAD.md` | 本文档 |

---

## 3. 快速使用

### 3.1 本地运行

```bash
# 基础用法（读默认路径 logs/backend.log，分析最近 24 小时）
python3 scripts/monitor_incompleteread.py

# 指定日志路径（适用任何环境）
python3 scripts/monitor_incompleteread.py --log /path/to/backend.log

# 生成 HTML 报告
python3 scripts/monitor_incompleteread.py --log logs/backend.log --report-dir logs/monitor_reports

# 只分析最近 1 小时（适合 cron 静默告警）
python3 scripts/monitor_incompleteread.py --hours 1 --quiet
```

### 3.2 查看 Dashboard

终端运行后直接看输出。输出示例：

```
=================================================================
  序话Story — Seedream IncompleteRead 监控 Dashboard
  生成时间: 2026-05-18 20:35:49  |  窗口: 最近 24 小时
=================================================================

【总览】
  IncompleteRead 触发总次数 : 8
  Retry 后成功次数           : 8
  Retry 耗尽失败次数         : 0
  Retry 成功率               : 100.0%

【最近 1 小时】
  IncompleteRead 次数 : 0  
  Retry 耗尽失败次数  : 0

【告警状态】
  [OK] 所有指标在阈值以内，无需处理

【每小时趋势（IncompleteRead 次数）】
  2026-05-18 17:00  ##############################  8
=================================================================
```

### 3.3 退出码（适合 cron 集成）

| 退出码 | 含义 |
|--------|------|
| `0` | 所有指标正常 |
| `1` | WARN：最近 1h IncompleteRead >= 阈值 |
| `2` | CRITICAL：最近 1h Retry 耗尽失败 >= 阈值 |

---

## 4. 调整告警阈值

**只需修改 `scripts/monitor.yaml`，立即生效，无需重启任何服务。**

```yaml
# 每小时 IncompleteRead 次数 → WARN（默认: 20）
warn_hourly_count: 20

# 每小时 retry 耗尽失败次数 → CRITICAL（默认: 3）
critical_hourly_exhausted: 3

# 单故事 IncompleteRead 次数（参考，不产生告警，默认: 15）
warn_per_story: 15

# 分析窗口小时数（0=全量，默认: 24）
analysis_window_hours: 24
```

**阈值调整指南**：
- **流量增加后**（多用户并发）：按比例上调 `warn_hourly_count`
- **Seedream 服务质量下降**：临时降低 `critical_hourly_exhausted` 到 1，更敏感触发
- **长期生产环境**：收集 1-2 周基线后，将 `warn_hourly_count` 设为 日均峰值 × 1.5

**环境变量方式（不想改文件时）**：
```bash
export MONITOR_WARN_HOURLY_COUNT=30
export MONITOR_CRITICAL_HOURLY_EXHAUSTED=5
python3 scripts/monitor_incompleteread.py
```

---

## 5. 部署到 VPS（Founder 决定是否部署）

### 5.1 rsync 同步脚本

```bash
# 从本地同步到 VPS（遵循 Ben 铁律：rsync 不 git pull）
rsync -avz -e "ssh -p 58913" \
    scripts/monitor_incompleteread.py \
    scripts/monitor.yaml \
    trader@107.148.1.199:/opt/xuhua-story/scripts/

rsync -avz -e "ssh -p 58913" \
    docs/MONITORING_INCOMPLETEREAD.md \
    trader@107.148.1.199:/opt/xuhua-story/docs/
```

### 5.2 VPS 上设置 cron

SSH 登录 VPS 后：

```bash
ssh -p 58913 trader@107.148.1.199
crontab -e
```

添加以下 cron job（每小时第 5 分钟运行）：

```cron
# 序话Story IncompleteRead 监控（每小时）
5 * * * * cd /opt/xuhua-story && \
    docker compose exec -T api python3 scripts/monitor_incompleteread.py \
        --log /app/logs/backend.log \
        --config scripts/monitor.yaml \
        --hours 1 \
        --report-dir /app/logs/monitor_reports \
        --quiet >> /opt/xuhua-story/logs/cron_monitor.log 2>&1
```

**注意**：VPS 上的脚本在 Docker 容器内运行（日志在容器内 `/app/logs/backend.log`）。如果脚本直接运行在宿主机，需要指定容器外的日志路径：

```cron
# 如果 backend.log 挂载在宿主机
5 * * * * python3 /opt/xuhua-story/scripts/monitor_incompleteread.py \
    --log /opt/xuhua-story/logs/backend.log \
    --config /opt/xuhua-story/scripts/monitor.yaml \
    --hours 1 --quiet >> /opt/xuhua-story/logs/cron_monitor.log 2>&1
```

### 5.3 查看 VPS 监控报告

```bash
# SSH 登录 VPS
ssh -p 58913 trader@107.148.1.199

# 查看最新 cron 运行日志
tail -50 /opt/xuhua-story/logs/cron_monitor.log

# 手动运行一次查看完整 dashboard
python3 /opt/xuhua-story/scripts/monitor_incompleteread.py \
    --log /opt/xuhua-story/logs/backend.log \
    --hours 24

# 查看 HTML 报告文件列表
ls -la /opt/xuhua-story/logs/monitor_reports/
```

---

## 6. 日志文件位置

| 环境 | 日志路径 |
|------|---------|
| 本地开发 | `logs/backend.log` |
| VPS 容器内 | `/app/logs/backend.log` |
| VPS 宿主机（如有 volume 挂载） | `/opt/xuhua-story/logs/backend.log` |

脚本的 `--log` 参数支持绝对路径和相对路径（相对于项目根目录），**universal，不 hardcode**。

---

## 7. 告警触发时怎么做

### WARN（最近 1h IncompleteRead >= 20 次）

1. SSH 登录 VPS，查看容器日志：
   ```bash
   docker logs --tail 200 docker-api-1 | grep "IncompleteRead"
   ```
2. 检查 Seedream API 状态（是否有维护公告）
3. 如果频率持续升高但 retry 仍成功，暂时忽略（不阻断生成）
4. 如果 retry 成功率下降，考虑临时增大 retry 次数（需 Backend 修改代码）

### CRITICAL（最近 1h Retry 耗尽失败 >= 3 次）

1. 立即检查 VPS 容器日志，找到哪些 shot 生成失败
2. 如果大量 shot 失败导致故事不完整，通知用户重新生成
3. 检查出口网络情况（VPS 到 Seedream API 的连通性）
4. 临时方案：将并发从 3 降到 1 减少并发请求

---

## 8. POST_BETA 升级路径

当前方案是最简实现（dev 阶段够用）。上线后建议按以下路径升级：

| 阶段 | 方案 | 触发条件 |
|------|------|----------|
| 现在（dev） | cron + 文本 dashboard（本方案）| 已实现 |
| Beta 用户 100+ | 集成 Sentry 错误追踪，IncompleteRead 自动上报 | 第一批真实用户 |
| 生产规模 | 阿里云 SLS 日志服务 + 钉钉/飞书告警 | 日生成 50+ 故事 |
| 大规模 | Prometheus exporter + Grafana 看板 | 日生成 500+ 故事 |

**Sentry 集成示例**（POST_BETA，由 Backend 实现）：
```python
# 在 SeedreamGenerator 的 IncompleteRead 重试处加埋点
import sentry_sdk
sentry_sdk.capture_message(
    f"IncompleteRead attempt {attempt}",
    level="warning",
    extras={"bytes_read": ..., "bytes_expected": ...}
)
```

---

*文档维护: @devops | 最后更新: 2026-05-18*
