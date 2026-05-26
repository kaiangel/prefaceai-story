"""Connection-level retry middleware for transient MySQL disconnects.

Wave 13 #5d (2026-05-25): 5/25 12:13 VPS 实测复现 — 阿里云 MySQL idle 1h+ 后服务端断开
空闲连接, 用户离开看片再回来的【第 1 次操作】拿到死连接 → OperationalError 2013
(Lost connection) → 500。pool_pre_ping 在公网 + ping 本身超时 (Errno60) 场景没完全防住。

本中间件是【最后一道兜底】: 当一次请求因 transient connection 错误失败时, 自动重试 1 次。
重试时 get_db() 会从池里 checkout 一条新连接, pool_pre_ping 会 ping 验证 / pool_recycle 已
主动回收 idle 连接 → 拿到健康连接, 重试成功。

Wave 13 #4 (2026-05-26): test29 实测又复现一类 #5d 漏接的 transient 错误 —— 浏览器 tab
挂起再恢复时突发并发轮询 chapters/N/status, 连接池被迫同时新建多条连接, 每条走 MySQL 认证
握手 (aiomysql/connection.py:844 _request_authentication → :629 _read_packet), 公网+VPN
并发握手被截断 → 认证响应包序号错位 → pymysql.err.InternalError: "Packet sequence number
wrong - got N expected M" → 3 次 500。该 InternalError 虽是 DBAPIError 子类 (isinstance
命中分支 1), 但既无 connection_invalidated 也不含 2013/2006/2003 码 → 旧逻辑判 False 漏接。
修复: 把 "packet sequence number wrong" 这一【连接握手腐败】消息片段纳入 transient 识别
(方案A)。安全性同 #5d: 仅幂等 GET/HEAD 重试 + 限 1 次 + 重试 checkout 干净连接 + 它是连接
握手层错误 (不与业务/SQL 语义错误混淆), test29 已证 2nd attempt 自愈成功。

⚠️ 严格防副作用 (这是关键, 退化会重复写库 / 掩盖真错误):
  1. 只重试 **transient connection 类错误** — OperationalError(2013/2003/2006) / 连接失效 /
     OSError(ETIMEDOUT/ECONNRESET/ECONNREFUSED) / InternalError("packet sequence number
     wrong" 握手腐败, Wave 13 #4)。业务错误 (ValueError / HTTPException / 4xx/5xx 域逻辑 /
     SQL 语法 ProgrammingError) **绝不重试**。
  2. 只重试 **幂等读 (GET / HEAD)** — POST/PUT/PATCH/DELETE 一律不重试 (防重复写)。
  3. 最多重试 **1 次** (_MAX_RETRIES=1)。
  4. **不掩盖真错误** — 非 transient 错误立即原样抛出; 重试后仍失败也原样抛出
     (交给 app.main 的全局 exception handler 转 500)。
"""

from __future__ import annotations

import errno
import logging

from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("xuhua")

# 只重试幂等读方法 (无副作用) — POST/PUT/PATCH/DELETE 绝不重试
_IDEMPOTENT_METHODS = frozenset({"GET", "HEAD"})

# 最多重试 1 次 (限 1 次, 不放大故障)
_MAX_RETRIES = 1

# transient MySQL 错误码 (字符串匹配 orig 错误): 2013 Lost connection /
# 2006 server has gone away / 2003 can't connect
_TRANSIENT_MYSQL_CODES = ("2013", "2006", "2003")

# transient 连接握手腐败消息片段 (Wave 13 #4): 并发新建连接时 MySQL 认证握手响应包序号错位,
# 抛 pymysql.err.InternalError "Packet sequence number wrong - got N expected M"。这是连接
# 握手层错误 (非查询执行、非业务/SQL 语义), 重试 checkout 新连接重做握手即可自愈。
# 小写匹配 (消息大小写可能不一)。刻意保持片段足够具体, 不误伤业务错误。
_TRANSIENT_MESSAGE_FRAGMENTS = ("packet sequence number wrong",)

# transient OS-level socket 错误 (公网/内网连接被断/超时)
_TRANSIENT_OS_ERRNOS = frozenset(
    {
        errno.ETIMEDOUT,    # 60: connection timed out (Errno60, 实测复现的那个)
        errno.ECONNRESET,   # 54: connection reset by peer
        errno.ECONNREFUSED, # 61: connection refused
        errno.EPIPE,        # 32: broken pipe
    }
)


def _is_transient_connection_error(exc: BaseException) -> bool:
    """判断异常是否是【可安全重试】的 transient connection 错误。

    走完整异常链 (__cause__ / __context__), 任一层命中即视为 transient。
    刻意从严: 只认连接级别错误, 不碰业务/SQL 语义错误, 避免误重试导致重复写或掩盖 bug。
    """
    seen: set[int] = set()
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))

        # 1) SQLAlchemy 连接失效信号 (pool 检测到断连并 invalidate)
        #    InternalError 也是 DBAPIError 子类, 已被此 isinstance 覆盖 (Wave 13 #4 的
        #    packet-sequence 错误即 InternalError, 走下方消息片段匹配)。
        if isinstance(cur, (OperationalError, InterfaceError, DBAPIError)):
            if getattr(cur, "connection_invalidated", False):
                return True
            # orig DBAPI 错误里带 transient MySQL 码 / 连接握手腐败消息片段
            orig = getattr(cur, "orig", None)
            if orig is not None and _matches_transient_signature(str(orig)):
                return True
            if _matches_transient_signature(str(cur)):
                return True

        # 2) OS-level socket 错误 (ping/connect 阶段超时/被断)
        if isinstance(cur, OSError) and cur.errno in _TRANSIENT_OS_ERRNOS:
            return True

        cur = cur.__cause__ or cur.__context__

    return False


def _matches_transient_code(message: str) -> bool:
    return any(code in message for code in _TRANSIENT_MYSQL_CODES)


def _matches_transient_message_fragment(message: str) -> bool:
    """连接握手腐败消息片段匹配 (小写不敏感)。Wave 13 #4 packet sequence。"""
    lowered = message.lower()
    return any(fragment in lowered for fragment in _TRANSIENT_MESSAGE_FRAGMENTS)


def _matches_transient_signature(message: str) -> bool:
    """统一判断: transient MySQL 错误码 或 连接握手腐败消息片段。"""
    return _matches_transient_code(message) or _matches_transient_message_fragment(message)


class DBConnectionRetryMiddleware(BaseHTTPMiddleware):
    """对 transient MySQL connection 错误的幂等 GET 请求自动重试 1 次。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 非幂等方法 (POST/PUT/PATCH/DELETE): 直接放行, 永不重试 (防重复写)
        if request.method not in _IDEMPOTENT_METHODS:
            return await call_next(request)

        attempt = 0
        while True:
            try:
                return await call_next(request)
            except Exception as exc:  # noqa: BLE001 — 需要判定后决定重试或重抛
                # 非 transient connection 错误 → 不掩盖, 原样抛 (交给全局 handler)
                if not _is_transient_connection_error(exc):
                    raise
                # transient 但已用完重试次数 → 原样抛 (不掩盖真断连)
                if attempt >= _MAX_RETRIES:
                    logger.error(
                        f"[DBRetry] #5d: {request.method} {request.url.path} "
                        f"transient connection 错误重试 {attempt} 次后仍失败, 放弃: {exc}"
                    )
                    raise
                attempt += 1
                logger.warning(
                    f"[DBRetry] #5d: {request.method} {request.url.path} 命中 transient "
                    f"connection 错误, 自动重试 ({attempt}/{_MAX_RETRIES}) — 新连接将经 "
                    f"pool_pre_ping 验证。原错误: {exc}"
                )
