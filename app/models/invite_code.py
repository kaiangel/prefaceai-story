"""Invite code model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class InviteCode(Base):
    __tablename__ = "u_invite_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False, unique=True)
    owner_user_id = Column(Integer, ForeignKey("u_users.id"), nullable=True)
    status = Column(String(32), nullable=False, default="active")
    max_uses = Column(Integer, nullable=False, default=1)
    used_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
