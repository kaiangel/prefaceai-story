"""Monitoring API — 错误查询 + 成本汇总"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chapter import Chapter
from app.models.api_cost_log import ApiCostLog
from app.api.projects import verify_user

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class RecentErrorItem(BaseModel):
    chapter_id: int
    chapter_uuid: str
    project_id: int
    error_message: Optional[str]
    created_at: datetime


class RecentErrorsResponse(BaseModel):
    errors: List[RecentErrorItem]
    total: int
    hours: int


class CostServiceSummary(BaseModel):
    service: str
    total_cost_usd: float
    call_count: int


class CostSummaryResponse(BaseModel):
    days: int
    total_cost_usd: float
    by_service: List[CostServiceSummary]
    generated_at: datetime


# ─────────────────────────────────────────────
# 3a. 错误查询端点
# ─────────────────────────────────────────────

@router.get("/errors/recent", response_model=RecentErrorsResponse)
async def get_recent_errors(
    hours: int = 24,
    limit: int = 50,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """查询最近的 Pipeline 错误。

    从 project_chapters 表查 status='failed' 且有 error_message 的记录。
    返回 chapter_id, error_message, created_at, project_id。
    """
    if hours < 1 or hours > 720:
        raise HTTPException(status_code=400, detail="hours 范围: 1 ~ 720")
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="limit 范围: 1 ~ 200")

    cutoff = datetime.utcnow() - timedelta(hours=hours)

    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.status == "failed",
            Chapter.error_message.isnot(None),
            Chapter.created_at >= cutoff,
        )
        .order_by(Chapter.created_at.desc())
        .limit(limit)
    )
    chapters = result.scalars().all()

    items = [
        RecentErrorItem(
            chapter_id=c.id,
            chapter_uuid=c.uuid,
            project_id=c.project_id,
            error_message=c.error_message,
            created_at=c.created_at,
        )
        for c in chapters
    ]

    return RecentErrorsResponse(
        errors=items,
        total=len(items),
        hours=hours,
    )


# ─────────────────────────────────────────────
# 3c. 成本查询端点
# ─────────────────────────────────────────────

@router.get("/costs/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    days: int = 7,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """查询最近 N 天的 API 成本汇总，按 service 分组。"""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days 范围: 1 ~ 365")

    cutoff = datetime.utcnow() - timedelta(days=days)

    # 按 service 分组求和
    result = await db.execute(
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

    by_service = [
        CostServiceSummary(
            service=row.service,
            total_cost_usd=round(float(row.total_cost_usd or 0), 6),
            call_count=row.call_count,
        )
        for row in rows
    ]

    total = round(sum(s.total_cost_usd for s in by_service), 6)

    return CostSummaryResponse(
        days=days,
        total_cost_usd=total,
        by_service=by_service,
        generated_at=datetime.utcnow(),
    )
