"""Contact us API"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.contact_us import ContactUs
from app.schemas.contact_us import (
    ContactUsCreate,
    ContactUsResponse,
)

router = APIRouter(prefix="/api/contact-us", tags=["contact-us"])


@router.post("/", response_model=ContactUsResponse)
async def create_contact_us(
    payload: ContactUsCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    submission = ContactUs(
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        subject=payload.subject.strip() if payload.subject else None,
        message=payload.message.strip(),
        source_page=payload.source_page.strip(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(submission)
    await db.flush()

    return ContactUsResponse(
        success=True,
        submission_id=submission.id,
        message="消息已提交，我们会尽快联系你。",
    )
