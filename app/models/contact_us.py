"""Contact us model"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from app.database import Base


class ContactUs(Base):
    __tablename__ = "contact_us"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    source_page = Column(String(100), nullable=False, default="contact")
    status = Column(String(32), nullable=False, default="new")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_contact_us_created_at", "created_at"),
        Index("idx_contact_us_email", "email"),
        Index("idx_contact_us_status", "status"),
    )
