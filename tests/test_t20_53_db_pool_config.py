"""
tests/test_t20_53_db_pool_config.py

T20-53 验收测试: SQLAlchemy connection pool 配置优化

背景 (SESSION_FULL_BUG_AUDIT_2026-05-20):
  偶发 `pymysql.err.InternalError: Packet sequence number wrong - got 1 expected 2`
  (本 session 5 次). 根因: frontend 高频 poll status + Pipeline 内部 DB query
  并发竞争 connection, SQLAlchemy 默认配置 (pool_size=5, 无 pre_ping, 无 recycle)
  不足以应对高并发场景.

修复 (app/database.py):
  pool_pre_ping=True     — 每次 checkout 前 ping, 检测 stale connection
  pool_recycle=1800      — 30min 主动回收, 防 MySQL wait_timeout RST
  pool_size=10           — 扩大基础池 (原默认 5 → 10)
  max_overflow=20        — overflow 扩大 (原默认 10 → 20)
  pool_timeout=30        — T20-53 新增: checkout 等待超时 30s

测试 case:
  1. engine 含 pool_pre_ping=True
  2. engine 含 pool_recycle=1800 (< MySQL wait_timeout 28800)
  3. engine 含 pool_size=10 (≥ 10)
  4. engine 含 max_overflow=20 (≥ 10)
  5. engine 含 pool_timeout=30
  6. database.py 源码含 pool_pre_ping + pool_recycle + pool_size + max_overflow + pool_timeout
  7. 语法检查: database.py 编译无错误

Author: @backend
Date: 2026-05-20
Owner: TASK-T20-53
"""

import ast
import py_compile
import tempfile
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DB_SOURCE_PATH = _PROJECT_ROOT / "app" / "database.py"


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: 源码关键词静态验证 (不 import engine, 避免真实 DB 连接)
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabasePoolConfigSource:
    """T20-53: app/database.py 源码含必要 pool 配置关键词."""

    def _read_source(self) -> str:
        return _DB_SOURCE_PATH.read_text(encoding="utf-8")

    def test_pool_pre_ping_true_in_source(self):
        """pool_pre_ping=True 必须在 create_async_engine 调用中."""
        source = self._read_source()
        assert "pool_pre_ping=True" in source, (
            "app/database.py 缺少 pool_pre_ping=True — stale connection 无法自动重建"
        )

    def test_pool_recycle_in_source(self):
        """pool_recycle 必须在 create_async_engine 调用中 (值 < MySQL wait_timeout 28800)."""
        source = self._read_source()
        assert "pool_recycle=" in source, (
            "app/database.py 缺少 pool_recycle — 连接不主动回收, 可能被 MySQL RST"
        )

    def _extract_int_param(self, source: str, param_name: str) -> int:
        """从源码中提取 create_async_engine 参数的整数值 (支持行内注释)."""
        import re
        # Match: pool_recycle=1800, or pool_recycle=1800  # comment
        pattern = rf"{re.escape(param_name)}\s*=\s*(\d+)"
        match = re.search(pattern, source)
        if match:
            return int(match.group(1))
        raise ValueError(f"找不到 {param_name}=<int> 赋值")

    def test_pool_recycle_value_less_than_mysql_wait_timeout(self):
        """pool_recycle 值必须 < MySQL wait_timeout (28800s = 8h)."""
        source = self._read_source()
        try:
            val = self._extract_int_param(source, "pool_recycle")
            assert val < 28800, (
                f"pool_recycle={val} 应 < MySQL wait_timeout (28800s); "
                "否则连接可能被服务器 RST 后仍驻留在池中"
            )
            assert val > 0, f"pool_recycle={val} 必须 > 0"
        except ValueError:
            pytest.fail("app/database.py 中找不到 pool_recycle=<int> 赋值")

    def test_pool_size_in_source(self):
        """pool_size 必须在 create_async_engine 调用中."""
        source = self._read_source()
        assert "pool_size=" in source, (
            "app/database.py 缺少 pool_size — 默认 5 对高并发不足"
        )

    def test_pool_size_at_least_10(self):
        """pool_size 值必须 ≥ 10 (原默认 5 不足以应对高并发 Pipeline)."""
        source = self._read_source()
        try:
            val = self._extract_int_param(source, "pool_size")
            assert val >= 10, (
                f"pool_size={val} 应 ≥ 10 — 高并发 Pipeline 需要足够的基础连接数"
            )
        except ValueError:
            pytest.fail("app/database.py 中找不到 pool_size=<int> 赋值")

    def test_max_overflow_in_source(self):
        """max_overflow 必须在 create_async_engine 调用中."""
        source = self._read_source()
        assert "max_overflow=" in source, (
            "app/database.py 缺少 max_overflow — 突发并发时可能 pool 耗尽"
        )

    def test_max_overflow_at_least_10(self):
        """max_overflow 值必须 ≥ 10."""
        source = self._read_source()
        try:
            val = self._extract_int_param(source, "max_overflow")
            assert val >= 10, (
                f"max_overflow={val} 应 ≥ 10 — 突发并发需要足够的 overflow 容量"
            )
        except ValueError:
            pytest.fail("app/database.py 中找不到 max_overflow=<int> 赋值")

    def test_pool_timeout_in_source(self):
        """pool_timeout 必须在 create_async_engine 调用中 (T20-53 新增)."""
        source = self._read_source()
        assert "pool_timeout=" in source, (
            "app/database.py 缺少 pool_timeout — checkout 等待无限阻塞可能导致 request hang"
        )

    def test_pool_timeout_value_reasonable(self):
        """pool_timeout 值应在 10-120 秒之间."""
        source = self._read_source()
        try:
            val = self._extract_int_param(source, "pool_timeout")
            assert 10 <= val <= 120, (
                f"pool_timeout={val} 应在 10-120 秒之间 — 太短容易超时, 太长请求 hang"
            )
        except ValueError:
            pytest.fail("app/database.py 中找不到 pool_timeout=<int> 赋值")


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: 语法检查
# ─────────────────────────────────────────────────────────────────────────────

class TestDatabaseSyntax:
    """T20-53: app/database.py 语法正确."""

    def test_database_py_compiles(self):
        """app/database.py 无语法错误."""
        with tempfile.NamedTemporaryFile(suffix=".pyc", delete=True) as tf:
            try:
                py_compile.compile(str(_DB_SOURCE_PATH), cfile=tf.name, doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"app/database.py 语法错误: {e}")

    def test_database_py_ast_parses(self):
        """app/database.py AST 可解析."""
        source = _DB_SOURCE_PATH.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
            assert tree is not None
        except SyntaxError as e:
            pytest.fail(f"app/database.py AST 解析失败: {e}")

    def test_create_async_engine_call_exists(self):
        """create_async_engine 调用存在于 database.py."""
        source = _DB_SOURCE_PATH.read_text(encoding="utf-8")
        assert "create_async_engine(" in source, (
            "app/database.py 中缺少 create_async_engine() 调用"
        )

    def test_all_pool_configs_in_engine_call(self):
        """所有 5 个 pool 参数都在 create_async_engine 调用块内."""
        source = _DB_SOURCE_PATH.read_text(encoding="utf-8")
        # Find the engine = create_async_engine(...) block
        start_idx = source.find("engine = create_async_engine(")
        assert start_idx != -1, "找不到 engine = create_async_engine( 块"

        # Find closing paren (simple heuristic: find next standalone ")")
        end_idx = source.find("\n)", start_idx)
        assert end_idx != -1, "找不到 engine = create_async_engine() 的结束括号"

        engine_block = source[start_idx:end_idx + 2]
        for param in ["pool_pre_ping", "pool_recycle", "pool_size", "max_overflow", "pool_timeout"]:
            assert param in engine_block, (
                f"create_async_engine 调用块缺少参数 {param!r}\n"
                f"当前 engine 块:\n{engine_block}"
            )
