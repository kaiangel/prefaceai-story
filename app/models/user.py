"""User model"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from app.database import Base


class User(Base):
    __tablename__ = "u_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(64), nullable=True, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    plan = Column(String(32), nullable=False, default="pro")
    credits = Column(Integer, nullable=False, default=87)
    invited_by_user_id = Column(Integer, ForeignKey("u_users.id"), nullable=True)
    used_invite_code_id = Column(Integer, ForeignKey("u_invite_codes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
