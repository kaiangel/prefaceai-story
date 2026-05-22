"""
client_log.py — Browser client-side console log receiver

A2-backend (TASK-CLIENT-LOG-PIPE, 2026-05-12):
- 接收 POST /api/_client_log，将 browser console error/warn/onerror/unhandledrejection 等写入 logs/client.log
- 不需要 auth（开发监控用，匿名 OK）
- 返回 {"ok": true}

Coordinator/Agent 监控方式:
    tail -F logs/client.log | grep -E 'error|warn|Exception'
"""

import json
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Request

logger = logging.getLogger("xuhua")

router = APIRouter(prefix="/api", tags=["monitoring"])

# 日志文件路径（相对项目根目录）
CLIENT_LOG_PATH = "logs/client.log"


@router.post("/_client_log")
async def client_log(request: Request) -> dict:
    """
    接收 browser client-side console log，追加到 logs/client.log

    Body 格式（任意字段，宽松接收）:
    {
        "level": "error" | "warn" | "log",
        "ts": "2026-05-12T16:30:00.000Z",
        "args": ["message", "detail"],
        "url": "http://localhost:3000/create/xxx/preview",
        "source": "app/layout.tsx",    # 可选
        "line": 42,                    # 可选
        "col": 7,                      # 可选
        "stack": "Error: ...\n  at ...",  # 可选
    }

    Returns:
        {"ok": true}
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # 追加写入 logs/client.log（每行一条 JSON）
    try:
        # 确保 logs 目录存在
        os.makedirs(os.path.dirname(CLIENT_LOG_PATH), exist_ok=True)

        # 补充服务器侧时间戳（以防客户端 ts 不准）
        log_entry = {
            "server_ts": datetime.utcnow().isoformat() + "Z",
            **payload,
        }

        with open(CLIENT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # 同步打印到 backend logger（便于 uvicorn stdout 看到）
        level = payload.get("level", "log")
        args = payload.get("args", [])
        url = payload.get("url", "")
        args_str = " ".join(str(a) for a in args) if args else ""
        logger.info(f"[ClientLog] [{level.upper()}] {args_str[:200]} | url={url}")

    except Exception as e:
        logger.warning(f"[ClientLog] ⚠️ 写入 logs/client.log 失败: {e}")

    return {"ok": True}
