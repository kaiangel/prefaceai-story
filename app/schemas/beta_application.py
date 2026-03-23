"""Beta application schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class BetaApplicationCreate(BaseModel):
    email: EmailStr
    source_page: str = Field(default="homepage_cta", min_length=1, max_length=100)


class BetaApplicationResponse(BaseModel):
    success: bool
    application_id: int
    message: str


class BetaApplicationDetail(BaseModel):
    id: int
    email: EmailStr
    source_page: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
