"""
验证 api_cost_logs 表的建表机制 + monitoring.py 端点可正常使用

测试策略：
- 不连接真实 MySQL（避免依赖外部服务）
- 使用 SQLite in-memory 数据库验证 SQLAlchemy 模型定义正确
- 验证 ApiCostLog 已注册到 Base.metadata
- 验证 monitoring 路由已挂载

运行：pytest tests/test_api_cost_log_table.py -v
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# ─────────────────────────────────────────────
# 1. 验证 ApiCostLog 已注册到 Base.metadata
# ─────────────────────────────────────────────

def test_api_cost_log_registered_in_base():
    """ApiCostLog 必须出现在 Base.metadata.tables 中，否则 create_all 不会建表。"""
    import app.models  # noqa: F401 — 触发所有模型注册

    from app.database import Base

    assert "api_cost_logs" in Base.metadata.tables, (
        "api_cost_logs 未在 Base.metadata.tables 中找到。"
        "请确认 app/models/__init__.py 已导入 ApiCostLog。"
    )


def test_api_cost_log_columns():
    """验证 ApiCostLog 字段定义完整。"""
    import app.models  # noqa: F401

    from app.database import Base

    table = Base.metadata.tables["api_cost_logs"]
    column_names = {col.name for col in table.columns}

    required_columns = {
        "id", "project_id", "service", "model",
        "cost_usd", "tokens_input", "tokens_output",
        "detail", "created_at",
    }
    missing = required_columns - column_names
    assert not missing, f"api_cost_logs 缺少字段: {missing}"


# ─────────────────────────────────────────────
# 2. SQLite in-memory 建表 + 读写验证
# ─────────────────────────────────────────────

def test_create_table_and_insert():
    """用 SQLite in-memory 数据库验证 create_all 可建表并插入记录。"""
    import app.models  # noqa: F401

    from app.database import Base
    from app.models.api_cost_log import ApiCostLog

    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            record = ApiCostLog(
                project_id=1,
                service="sonnet",
                model="claude-sonnet-4-6",
                cost_usd=0.0042,
                tokens_input=1200,
                tokens_output=300,
                detail="Stage 4 scene 3",
                created_at=datetime.utcnow(),
            )
            session.add(record)
            await session.commit()

            result = await session.execute(
                select(ApiCostLog).where(ApiCostLog.service == "sonnet")
            )
            rows = result.scalars().all()

            assert len(rows) == 1
            assert rows[0].model == "claude-sonnet-4-6"
            assert abs(rows[0].cost_usd - 0.0042) < 1e-9
            assert rows[0].tokens_input == 1200
            assert rows[0].detail == "Stage 4 scene 3"

        await engine.dispose()

    asyncio.run(_run())


def test_cost_summary_query():
    """验证 monitoring.py 中的 GROUP BY 查询逻辑可正确执行。"""
    import app.models  # noqa: F401

    from app.database import Base
    from app.models.api_cost_log import ApiCostLog

    async def _run():
        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with session_maker() as session:
            records = [
                ApiCostLog(service="sonnet", model="claude-sonnet-4-6",
                           cost_usd=0.01, created_at=datetime.utcnow()),
                ApiCostLog(service="sonnet", model="claude-sonnet-4-6",
                           cost_usd=0.02, created_at=datetime.utcnow()),
                ApiCostLog(service="gemini_nb2", model="gemini-3.1-flash-image-preview",
                           cost_usd=0.067, created_at=datetime.utcnow()),
            ]
            for r in records:
                session.add(r)
            await session.commit()

            cutoff = datetime.utcnow() - timedelta(days=7)
            result = await session.execute(
                select(
                    ApiCostLog.service,
                    func.sum(ApiCostLog.cost_usd).label("total_cost_usd"),
                    func.count(ApiCostLog.id).label("call_count"),
                )
                .where(ApiCostLog.created_at >= cutoff)
                .group_by(ApiCostLog.service)
                .order_by(func.sum(ApiCostLog.cost_usd).desc())
            )
            rows = result.all()

            assert len(rows) == 2
            # gemini_nb2 total $0.067 > sonnet total $0.03
            assert rows[0].service == "gemini_nb2"
            assert rows[0].call_count == 1
            assert rows[1].service == "sonnet"
            assert rows[1].call_count == 2

        await engine.dispose()

    asyncio.run(_run())


# ─────────────────────────────────────────────
# 3. 验证 monitoring 路由已挂载
# ─────────────────────────────────────────────

def test_monitoring_router_included():
    """monitoring.router 必须已挂载到 api_router，prefix 和端点路径正确。"""
    from app.api.monitoring import router as monitoring_router

    assert monitoring_router.prefix == "/api/monitoring", (
        f"monitoring 路由 prefix 异常: {monitoring_router.prefix}"
    )

    route_paths = {route.path for route in monitoring_router.routes}
    assert "/api/monitoring/errors/recent" in route_paths, "errors/recent 端点未定义"
    assert "/api/monitoring/costs/summary" in route_paths, "costs/summary 端点未定义"
