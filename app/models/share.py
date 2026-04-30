"""R7-2: Share token and PV log models"""

from datetime import datetime
from uuid import uuid4
import secrets

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func

from app.database import Base


class ShareToken(Base):
    """
    分享链接 token 表 (R7-2)

    每个 project 可生成一个（或多个）分享 token。
    Token 永久有效（Founder 决策 Wave 5.1）。
    """

    __tablename__ = "share_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))

    # 关联项目（uuid，不是 int id，避免 JOIN，保持无状态）
    project_uuid = Column(String(36), nullable=False, index=True)

    # 分享 token — URL-safe 随机字符串（16 字节 = 22 base64url chars）
    token = Column(String(64), unique=True, nullable=False,
                   default=lambda: secrets.token_urlsafe(16))

    # PV 统计（冗余计数，快速读取）
    view_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class SharePvLog(Base):
    """
    分享页 PV 日志表 (R7-2)

    每次公开页访问记一条。ip_hash 做隐私脱敏（SHA-256 前 16 hex chars）。
    """

    __tablename__ = "share_pv_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联 ShareToken.token（字符串，避免 FK 依赖）
    share_token = Column(String(64), nullable=False, index=True)

    viewed_at = Column(DateTime, default=datetime.utcnow)

    # 隐私脱敏：SHA-256(ip)[:16] hex chars（32 chars max，仅用于去重统计，不还原原始 IP）
    ip_hash = Column(String(32), nullable=True)
