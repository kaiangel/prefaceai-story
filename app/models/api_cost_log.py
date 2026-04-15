"""API 成本记录模型

用于追踪每次外部 AI API 调用的估算成本。
注意：只定义 SQLAlchemy model，不执行 CREATE TABLE。
建表通过 Alembic migration 或手动 DDL 执行。
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from app.database import Base


class ApiCostLog(Base):
    """api_cost_logs 表 — 记录每次 AI API 调用的估算成本"""

    __tablename__ = "api_cost_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)         # 关联 projects.id（可空，部分调用无项目上下文）
    service = Column(String(50), nullable=False)         # "sonnet" | "gemini_nb2" | "haiku" | "flash_lite"
    model = Column(String(100), nullable=False)          # 具体模型名，如 "claude-sonnet-4-6"
    cost_usd = Column(Float, nullable=False)             # 估算费用 USD
    tokens_input = Column(Integer, nullable=True)        # 输入 token 数
    tokens_output = Column(Integer, nullable=True)       # 输出 token 数
    detail = Column(String(500), nullable=True)          # 上下文说明，如 "Stage 4 scene 3"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
