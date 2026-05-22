"""Database connection and session management"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger("xuhua")

# Ensure charset=utf8mb4 is in the URL regardless of how DATABASE_URL was set
_db_url = settings.DATABASE_URL
if "charset=" not in _db_url:
    _db_url += ("&" if "?" in _db_url else "?") + "charset=utf8mb4"

logger.info(f"[DB] Creating async engine: pool_pre_ping=True, pool_recycle=1800s, pool_size=10, max_overflow=20")

# Create async engine
# A1 — BUG-T13-MYSQL-STALE-CONNECTION + BUG-T13-DB-POOL-EXHAUSTION-CASCADE (2026-05-12)
# pool_pre_ping: 每次 checkout 前 ping，stale connection 自动重建，防止 OperationalError 2013
# pool_recycle: 30min 主动回收，必须 < MySQL wait_timeout (28800s) 且 < 内网 TCP idle timeout (~30-60min)
# pool_size: 扩大基础池（原默认 5 太小，并发生图阶段多请求同时需要连接）
# max_overflow: overflow 扩大（原默认 10），与 pool_size 共同容纳 30 并发请求
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,       # 每次使用前 ping 验证连接存活，断了自动重连
    pool_recycle=1800,         # 30 分钟回收连接，防止 MySQL 服务器关闭长空闲连接
    pool_size=10,              # 扩大池（原默认 5 → 10）
    max_overflow=20,           # overflow 扩大（原默认 10 → 20）
    pool_timeout=30,           # T20-53: checkout 等待超时 30s，避免请求无限阻塞
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    logger.info("[DB] init_db: running create_all and legacy schema compatibility check")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_legacy_schema_compatibility)
    logger.info("[DB] init_db: complete")


async def close_db():
    """Close database connections"""
    logger.info("[DB] close_db: disposing engine connection pool")
    await engine.dispose()
    logger.info("[DB] close_db: engine disposed")


def _ensure_legacy_schema_compatibility(sync_conn):
    """Patch a few old tables so new auth code can run on legacy dev databases."""
    inspector = inspect(sync_conn)

    if "u_users" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("u_users")}
        if "email" not in columns:
            sync_conn.execute(text("ALTER TABLE u_users ADD COLUMN email VARCHAR(255)"))
        if "avatar_url" not in columns:
            sync_conn.execute(text("ALTER TABLE u_users ADD COLUMN avatar_url VARCHAR(500)"))
        if "plan" not in columns:
            sync_conn.execute(text("ALTER TABLE u_users ADD COLUMN plan VARCHAR(32) DEFAULT 'pro'"))
        if "credits" not in columns:
            sync_conn.execute(text("ALTER TABLE u_users ADD COLUMN credits INTEGER DEFAULT 87"))
