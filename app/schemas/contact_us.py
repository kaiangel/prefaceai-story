"""Contact us schemas"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactUsCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str | None = Field(default=None, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)
    source_page: str = Field(default="contact", min_length=1, max_length=100)


class ContactUsResponse(BaseModel):
    success: bool
    submission_id: int
    message: str


class ContactUsDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    subject: str | None
    message: str
    source_page: str
    status: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    updated_at: datetime
