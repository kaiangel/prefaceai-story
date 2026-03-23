"""Beta application model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Index

from app.database import Base


class BetaApplication(Base):
    __tablename__ = "u_beta_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    source_page = Column(String(100), nullable=False, default="homepage_cta")
    status = Column(String(32), nullable=False, default="pending")
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_beta_applications_created_at", "created_at"),
        Index("idx_beta_applications_status", "status"),
    )
