"""Invite relationship model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer

from app.database import Base


class InviteRelationship(Base):
    __tablename__ = "u_invite_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invite_code_id = Column(Integer, ForeignKey("u_invite_codes.id"), nullable=False)
    inviter_user_id = Column(Integer, ForeignKey("u_users.id"), nullable=True)
    invitee_user_id = Column(Integer, ForeignKey("u_users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
