"""Wave 13 #5d: DBConnectionRetryMiddleware 行为验证。

验证防副作用约束 (代码可证):
  1. 只重试 transient connection 错误 (2013/2003/ETIMEDOUT 等), 不重试业务错误
  2. 只重试幂等 GET/HEAD, 绝不重试 POST/PUT/PATCH/DELETE (防重复写)
  3. 最多重试 1 次
  4. 不掩盖真错误 (非 transient 立即抛 / 重试后仍失败抛)
"""

import errno

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import InternalError, OperationalError, ProgrammingError

from app.middleware.db_retry import (
    DBConnectionRetryMiddleware,
    _is_transient_connection_error,
    _IDEMPOTENT_METHODS,
    _MAX_RETRIES,
)


class _FakeOrig(Exception):
    pass


def _make_2013() -> OperationalError:
    """模拟 MySQL 2013 Lost connection (idle 后第 1 次操作命中死连接)。"""
    return OperationalError(
        "SELECT 1", {}, _FakeOrig('(2013, "Lost connection to MySQL server during query")')
    )


def _make_packet_sequence() -> InternalError:
    """模拟 Wave 13 #4: 并发新建连接, MySQL 认证握手响应包序号错位。

    真实形态是 pymysql.err.InternalError 被 SQLAlchemy 包成 sqlalchemy.exc.InternalError
    (DBAPIError 子类), orig 消息 = "Packet sequence number wrong - got N expected M"。
    """
    return InternalError(
        "SELECT 1", {}, _FakeOrig("Packet sequence number wrong - got 0 expected 1")
    )


# ---------------------------------------------------------------------------
# 1. 纯检测逻辑 (transient 识别)
# ---------------------------------------------------------------------------

def test_transient_detect_2013():
    assert _is_transient_connection_error(_make_2013()) is True


def test_transient_detect_os_etimedout():
    assert _is_transient_connection_error(OSError(errno.ETIMEDOUT, "timed out")) is True


def test_transient_detect_connection_invalidated():
    e = _make_2013()
    e.connection_invalidated = True
    assert _is_transient_connection_error(e) is True


def test_transient_detect_packet_sequence():
    """Wave 13 #4: packet sequence 握手腐败 (InternalError) 应判 transient。"""
    assert _is_transient_connection_error(_make_packet_sequence()) is True


def test_transient_detect_packet_sequence_case_insensitive():
    """消息大小写不敏感: 全小写 / 大写混合都应命中。"""
    lower = InternalError("SELECT 1", {}, _FakeOrig("packet sequence number wrong - got 2 expected 3"))
    assert _is_transient_connection_error(lower) is True
    upper = InternalError("SELECT 1", {}, _FakeOrig("PACKET SEQUENCE NUMBER WRONG - GOT 2 EXPECTED 3"))
    assert _is_transient_connection_error(upper) is True


def test_transient_detect_packet_sequence_via_cause():
    """packet sequence 作为 __cause__ 深埋时仍识别 (走完整异常链)。"""
    outer = ValueError("middleware wrap")
    outer.__cause__ = _make_packet_sequence()
    assert _is_transient_connection_error(outer) is True


def test_business_valueerror_not_transient():
    assert _is_transient_connection_error(ValueError("角色不存在")) is False


def test_internalerror_without_packet_phrase_not_transient():
    """精度边界: InternalError 但不含 packet sequence / 那几个码 → 不重试 (不误伤)。

    防止 isinstance(InternalError, DBAPIError) 命中后被泛化重试任意 InternalError。
    """
    e = InternalError("SELECT 1", {}, _FakeOrig("(1364, \"Field 'x' doesn't have a default value\")"))
    assert _is_transient_connection_error(e) is False


def test_business_message_with_packet_word_not_transient():
    """精度边界: 业务错误消息里恰好含 'packet' 单词但非握手腐败短语 → 不误伤。"""
    e = ValueError("invalid network packet count in user upload")
    assert _is_transient_connection_error(e) is False


def test_sql_programming_error_not_transient():
    """SQL 语法错误 (1064) 不是 transient — 绝不能重试。"""
    e = ProgrammingError("bad sql", {}, _FakeOrig("(1064, syntax error)"))
    assert _is_transient_connection_error(e) is False


def test_generic_oserror_not_transient():
    assert _is_transient_connection_error(OSError(errno.ENOENT, "no file")) is False


def test_chained_transient_via_cause():
    """transient 作为 __cause__ 时仍识别为可重试 (根因是死连接)。"""
    outer = ValueError("wrap")
    outer.__cause__ = _make_2013()
    assert _is_transient_connection_error(outer) is True


def test_retry_limited_to_one():
    assert _MAX_RETRIES == 1


def test_only_idempotent_methods_eligible():
    assert _IDEMPOTENT_METHODS == frozenset({"GET", "HEAD"})


# ---------------------------------------------------------------------------
# 2. 端到端中间件行为 (用最小 FastAPI app)
# ---------------------------------------------------------------------------

def _build_app(handler_factory):
    app = FastAPI()
    app.add_middleware(DBConnectionRetryMiddleware)

    state = {"calls": 0}

    @app.get("/probe")
    async def probe():
        state["calls"] += 1
        return handler_factory(state)

    @app.post("/probe")
    async def probe_post():
        state["calls"] += 1
        return handler_factory(state)

    return app, state


def test_get_retries_once_then_succeeds():
    """GET 第 1 次 transient 失败 → 自动重试 → 第 2 次成功。共调用 2 次。"""

    def factory(state):
        if state["calls"] == 1:
            raise _make_2013()
        return {"ok": True}

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/probe")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert state["calls"] == 2  # 1 次失败 + 1 次重试成功


def test_get_transient_persists_gives_up_after_one_retry():
    """GET 一直 transient 失败 → 只重试 1 次 → 共 2 次调用后放弃 (500), 不掩盖。"""

    def factory(state):
        raise _make_2013()

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/probe")
    assert resp.status_code == 500  # 重抛 → 走默认 500
    assert state["calls"] == 2  # 原始 1 次 + 重试 1 次, 不再多重试


def test_get_business_error_not_retried():
    """GET 业务错误 (非 transient) → 不重试, 只调用 1 次。"""

    def factory(state):
        raise ValueError("业务校验失败")

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/probe")
    assert resp.status_code == 500
    assert state["calls"] == 1  # 不重试


def test_post_transient_not_retried():
    """POST 即使 transient 也绝不重试 (防重复写) → 只调用 1 次。"""

    def factory(state):
        raise _make_2013()

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/probe")
    assert resp.status_code == 500
    assert state["calls"] == 1  # 写操作不重试


def test_get_success_no_retry_no_overhead():
    """GET 正常成功 → 只调用 1 次, 无额外开销。"""

    def factory(state):
        return {"ok": True}

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/probe")
    assert resp.status_code == 200
    assert state["calls"] == 1


def test_get_packet_sequence_retries_once_then_succeeds():
    """Wave 13 #4: GET 第 1 次 packet sequence 握手腐败 → 重试 → 第 2 次成功 (自愈)。"""

    def factory(state):
        if state["calls"] == 1:
            raise _make_packet_sequence()
        return {"ok": True}

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/probe")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    assert state["calls"] == 2  # 握手腐败 1 次 + 重新 checkout 干净连接成功


def test_post_packet_sequence_not_retried():
    """Wave 13 #4: POST 即使 packet sequence 也绝不重试 (防重复写) → 只调用 1 次。"""

    def factory(state):
        raise _make_packet_sequence()

    app, state = _build_app(factory)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/probe")
    assert resp.status_code == 500
    assert state["calls"] == 1  # 写操作不重试, 即使是 transient 握手错误
