"""Beta application API."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.beta_application import BetaApplication
from app.schemas.beta_application import BetaApplicationCreate, BetaApplicationResponse

router = APIRouter(prefix="/api/beta-applications", tags=["beta-applications"])


@router.post("/", response_model=BetaApplicationResponse)
async def create_beta_application(
    payload: BetaApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(BetaApplication).where(BetaApplication.email == payload.email.lower())
    )
    record = existing.scalar_one_or_none()

    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if record:
        record.source_page = payload.source_page
        record.ip_address = client_host
        record.user_agent = user_agent
        record.status = "pending"
        db.add(record)
        await db.flush()
        return BetaApplicationResponse(
            success=True,
            application_id=record.id,
            message="你已提交过申请，我们已更新你的内测登记信息。",
        )

    record = BetaApplication(
        email=payload.email.lower(),
        source_page=payload.source_page,
        ip_address=client_host,
        user_agent=user_agent,
    )
    db.add(record)
    await db.flush()

    if not record.id:
        raise HTTPException(status_code=500, detail="内测申请创建失败")

    return BetaApplicationResponse(
        success=True,
        application_id=record.id,
        message="申请成功，邀请码将发送到你的邮箱。",
    )
