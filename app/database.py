"""Database connection and session management"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,      # 每次使用前 ping 验证连接存活，断了自动重连
    pool_recycle=1800,        # 30 分钟回收连接，防止 MySQL 服务器关闭长空闲连接
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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_legacy_schema_compatibility)


async def close_db():
    """Close database connections"""
    await engine.dispose()


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
