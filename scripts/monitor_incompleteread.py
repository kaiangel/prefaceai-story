#!/usr/bin/env python3
"""
IncompleteRead 监控脚本 — 序话Story DevOps

分析 backend.log 中 Seedream 下载的 IncompleteRead 网络抖动频率，
生成文本 dashboard + 告警报告。

用法:
    python3 scripts/monitor_incompleteread.py [--log /path/to/backend.log] [--config /path/to/monitor.yaml]

输出:
    - 终端文本 dashboard
    - 可选：写出 HTML 报告到 --report-dir 目录

作者: DevOps Agent
日期: 2026-05-18
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 默认配置（可被 YAML 文件或环境变量覆盖）
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    # 每小时 IncompleteRead 触发次数告警阈值
    "warn_hourly_count": int(os.environ.get("MONITOR_WARN_HOURLY_COUNT", "20")),
    # 每小时连续重试仍失败次数（达到 max_retries 还失败）告警阈值
    "critical_hourly_exhausted": int(os.environ.get("MONITOR_CRITICAL_HOURLY_EXHAUSTED", "3")),
    # 每故事 IncompleteRead 次数告警阈值（用于单次运行扫描）
    "warn_per_story": int(os.environ.get("MONITOR_WARN_PER_STORY", "15")),
    # 分析窗口小时数（0 = 分析全部日志）
    "analysis_window_hours": int(os.environ.get("MONITOR_ANALYSIS_HOURS", "24")),
}

# ---------------------------------------------------------------------------
# 日志模式
# ---------------------------------------------------------------------------
# 2026-05-18 17:22:06,100 WARNING xuhua [SeedreamGenerator] IncompleteRead (attempt 1): ...
RE_INCOMPLETE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ "
    r"WARNING .* \[SeedreamGenerator\] IncompleteRead \(attempt (\d+)\)"
)

# 2026-05-18 17:22:54,598 INFO xuhua [SeedreamGenerator] ✅ 下载成功（经历 N 次重试，Bug 3 retry 统计）
RE_SUCCESS_RETRY = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ "
    r"INFO .* \[SeedreamGenerator\] ✅ 下载成功（经历 (\d+) 次重试"
)

# 可选：如果存在最终失败日志（耗尽 max_retries 后仍失败）
RE_EXHAUSTED = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ "
    r"ERROR .* \[SeedreamGenerator\] IncompleteRead 重试耗尽"
)


def load_yaml_config(path: str) -> dict:
    """加载 YAML 配置文件（可选依赖，不强制安装 PyYAML）"""
    try:
        import yaml  # type: ignore
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        print("[WARN] PyYAML 未安装，跳过 YAML 配置文件，使用默认值 + 环境变量。", file=sys.stderr)
        return {}
    except FileNotFoundError:
        print(f"[WARN] 配置文件 {path} 不存在，使用默认值。", file=sys.stderr)
        return {}


def parse_log(log_path: str, since: Optional[datetime]) -> dict:
    """
    解析 backend.log，提取 IncompleteRead 相关事件。

    Returns dict:
        events        : list of (timestamp, attempt_num)
        retry_success : list of (timestamp, retry_count)
        exhausted     : list of timestamp
        hourly_count  : {hour_str: count}
        hourly_exhausted : {hour_str: count}
    """
    events = []
    retry_success = []
    exhausted = []
    hourly_count: dict = defaultdict(int)
    hourly_exhausted: dict = defaultdict(int)

    if not os.path.exists(log_path):
        print(f"[ERROR] 日志文件不存在: {log_path}", file=sys.stderr)
        return {
            "events": events,
            "retry_success": retry_success,
            "exhausted": exhausted,
            "hourly_count": hourly_count,
            "hourly_exhausted": hourly_exhausted,
        }

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = RE_INCOMPLETE.match(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if since and ts < since:
                    continue
                attempt = int(m.group(2))
                events.append((ts, attempt))
                hour_key = ts.strftime("%Y-%m-%d %H:00")
                hourly_count[hour_key] += 1
                continue

            m = RE_SUCCESS_RETRY.match(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if since and ts < since:
                    continue
                retry_n = int(m.group(2))
                retry_success.append((ts, retry_n))
                continue

            m = RE_EXHAUSTED.match(line)
            if m:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if since and ts < since:
                    continue
                exhausted.append(ts)
                hour_key = ts.strftime("%Y-%m-%d %H:00")
                hourly_exhausted[hour_key] += 1

    return {
        "events": events,
        "retry_success": retry_success,
        "exhausted": exhausted,
        "hourly_count": dict(hourly_count),
        "hourly_exhausted": dict(hourly_exhausted),
    }


def compute_stats(data: dict) -> dict:
    """计算汇总统计"""
    events = data["events"]
    retry_success = data["retry_success"]
    exhausted = data["exhausted"]

    total_incomplete = len(events)
    total_retry_success = len(retry_success)
    total_exhausted = len(exhausted)

    # 成功率（retry 后成功 / 所有触发）
    if total_incomplete > 0:
        success_rate = total_retry_success / total_incomplete * 100
    else:
        success_rate = 100.0

    # 最近 1 小时
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    last_hour_events = [e for e in events if e[0] >= one_hour_ago]
    last_hour_exhausted = [e for e in exhausted if e >= one_hour_ago]

    # 最近 24 小时趋势（按小时 bucket）
    hourly_count = data["hourly_count"]
    sorted_hours = sorted(hourly_count.keys())

    return {
        "total_incomplete": total_incomplete,
        "total_retry_success": total_retry_success,
        "total_exhausted": total_exhausted,
        "success_rate": success_rate,
        "last_hour_count": len(last_hour_events),
        "last_hour_exhausted": len(last_hour_exhausted),
        "sorted_hours": sorted_hours,
        "hourly_count": hourly_count,
        "hourly_exhausted": data["hourly_exhausted"],
    }


def render_dashboard(stats: dict, cfg: dict, window_label: str) -> str:
    """生成文本 dashboard 字符串"""
    lines = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("=" * 65)
    lines.append("  序话Story — Seedream IncompleteRead 监控 Dashboard")
    lines.append(f"  生成时间: {now_str}  |  窗口: {window_label}")
    lines.append("=" * 65)

    # 总览
    lines.append("")
    lines.append("【总览】")
    lines.append(f"  IncompleteRead 触发总次数 : {stats['total_incomplete']}")
    lines.append(f"  Retry 后成功次数           : {stats['total_retry_success']}")
    lines.append(f"  Retry 耗尽失败次数         : {stats['total_exhausted']}")
    sr = stats["success_rate"]
    lines.append(f"  Retry 成功率               : {sr:.1f}%")

    # 最近 1 小时
    lines.append("")
    lines.append("【最近 1 小时】")
    lhc = stats["last_hour_count"]
    lhe = stats["last_hour_exhausted"]
    warn_h = cfg["warn_hourly_count"]
    crit_h = cfg["critical_hourly_exhausted"]

    lhc_flag = " <-- WARN" if lhc >= warn_h else ""
    lhe_flag = " <-- CRITICAL" if lhe >= crit_h else ""
    lines.append(f"  IncompleteRead 次数 : {lhc}{lhc_flag}")
    lines.append(f"  Retry 耗尽失败次数  : {lhe}{lhe_flag}")

    # 告警状态
    lines.append("")
    lines.append("【告警状态】")
    has_alert = False
    if lhc >= warn_h:
        lines.append(f"  [WARN]     最近 1h IncompleteRead {lhc} 次 >= 阈值 {warn_h}")
        has_alert = True
    if lhe >= crit_h:
        lines.append(f"  [CRITICAL] 最近 1h Retry 耗尽失败 {lhe} 次 >= 阈值 {crit_h}")
        has_alert = True
    if not has_alert:
        lines.append("  [OK] 所有指标在阈值以内，无需处理")

    # 每小时趋势（ASCII 柱状图）
    hourly = stats["hourly_count"]
    sorted_hours = stats["sorted_hours"]
    if sorted_hours:
        lines.append("")
        lines.append("【每小时趋势（IncompleteRead 次数）】")
        max_count = max(hourly.values()) if hourly else 1
        bar_width = 30
        for h in sorted_hours[-24:]:  # 最多显示最近 24 小时
            c = hourly.get(h, 0)
            bar_len = int(c / max(max_count, 1) * bar_width)
            bar = "#" * bar_len
            flag = " *WARN*" if c >= warn_h else ""
            lines.append(f"  {h}  {bar:<{bar_width}}  {c}{flag}")

    # 告警阈值说明
    lines.append("")
    lines.append("【当前告警阈值（可在 scripts/monitor.yaml 或环境变量中修改）】")
    lines.append(f"  WARN  每小时 IncompleteRead   >= {warn_h} 次")
    lines.append(f"  CRIT  每小时 Retry 耗尽失败   >= {crit_h} 次")
    lines.append(f"  WARN  单故事 IncompleteRead   >= {cfg['warn_per_story']} 次")

    lines.append("")
    lines.append("【POST_BETA 建议】")
    lines.append("  现在: 文本 dashboard + cron 定时扫描（当前方案）")
    lines.append("  未来: 集成 Sentry / 阿里云 SLS 实现实时告警推送")
    lines.append("=" * 65)

    return "\n".join(lines)


def write_html_report(dashboard_text: str, report_dir: str) -> str:
    """将文本 dashboard 写成简单 HTML 文件"""
    os.makedirs(report_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    html_path = os.path.join(report_dir, f"incompleteread_{date_str}.html")

    html_body = dashboard_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>IncompleteRead Monitor — {date_str}</title>
  <style>
    body {{ font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }}
    pre {{ white-space: pre-wrap; font-size: 14px; line-height: 1.6; }}
    .warn {{ color: #ffcc00; }}
    .critical {{ color: #ff4444; }}
    .ok {{ color: #44ff88; }}
  </style>
</head>
<body>
<pre>
{html_body}
</pre>
</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def check_exit_code(stats: dict, cfg: dict) -> int:
    """返回退出码：0=OK, 1=WARN, 2=CRITICAL"""
    if stats["last_hour_exhausted"] >= cfg["critical_hourly_exhausted"]:
        return 2
    if stats["last_hour_count"] >= cfg["warn_hourly_count"]:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="序话Story IncompleteRead 监控 dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
环境变量（优先级低于 --config YAML 文件）:
  MONITOR_WARN_HOURLY_COUNT       每小时 WARN 阈值（默认 20）
  MONITOR_CRITICAL_HOURLY_EXHAUSTED  每小时 CRITICAL 阈值（默认 3）
  MONITOR_WARN_PER_STORY          单故事 WARN 阈值（默认 15）
  MONITOR_ANALYSIS_HOURS          分析窗口小时数（0=全量，默认 24）

退出码:
  0  所有指标 OK
  1  触发 WARN
  2  触发 CRITICAL

cron 示例（每小时跑一次，结果写 HTML）:
  0 * * * * /path/to/venv/bin/python3 scripts/monitor_incompleteread.py \\
      --log logs/backend.log --report-dir logs/monitor_reports >> logs/cron_monitor.log 2>&1
""",
    )
    parser.add_argument(
        "--log",
        default="logs/backend.log",
        help="backend.log 路径（默认: logs/backend.log，支持绝对/相对路径）",
    )
    parser.add_argument(
        "--config",
        default="scripts/monitor.yaml",
        help="YAML 配置文件路径（可选，默认: scripts/monitor.yaml）",
    )
    parser.add_argument(
        "--report-dir",
        default="",
        help="HTML 报告输出目录（不填则不生成 HTML）",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=0,
        help="分析最近 N 小时（0=全量，覆盖 config/env 里的 analysis_window_hours）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="只输出告警行，不显示完整 dashboard（适合 cron 静默模式）",
    )
    args = parser.parse_args()

    # 加载配置
    cfg = dict(DEFAULT_CONFIG)
    yaml_cfg = load_yaml_config(args.config)
    cfg.update(yaml_cfg)  # YAML 覆盖默认值

    # 分析窗口
    analysis_hours = args.hours if args.hours > 0 else cfg.get("analysis_window_hours", 24)
    if analysis_hours > 0:
        since = datetime.now() - timedelta(hours=analysis_hours)
        window_label = f"最近 {analysis_hours} 小时"
    else:
        since = None
        window_label = "全量日志"

    # 解析日志
    log_path = args.log
    # 如果是相对路径，基于脚本所在项目根目录
    if not os.path.isabs(log_path):
        project_root = Path(__file__).parent.parent
        log_path = str(project_root / log_path)

    data = parse_log(log_path, since)
    stats = compute_stats(data)

    # 渲染 dashboard
    dashboard = render_dashboard(stats, cfg, window_label)

    if not args.quiet:
        print(dashboard)
    else:
        # quiet 模式：只打印告警行
        lhc = stats["last_hour_count"]
        lhe = stats["last_hour_exhausted"]
        if lhc >= cfg["warn_hourly_count"]:
            print(f"[WARN] 最近 1h IncompleteRead {lhc} 次 >= 阈值 {cfg['warn_hourly_count']}")
        if lhe >= cfg["critical_hourly_exhausted"]:
            print(f"[CRITICAL] 最近 1h Retry 耗尽失败 {lhe} 次 >= 阈值 {cfg['critical_hourly_exhausted']}")

    # 生成 HTML 报告
    if args.report_dir:
        report_dir = args.report_dir
        if not os.path.isabs(report_dir):
            project_root = Path(__file__).parent.parent
            report_dir = str(project_root / report_dir)
        html_path = write_html_report(dashboard, report_dir)
        if not args.quiet:
            print(f"\n[INFO] HTML 报告已写入: {html_path}")

    # 返回退出码（供 cron 告警脚本检测）
    exit_code = check_exit_code(stats, cfg)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
