"""R7-2: Add is_favorite to projects + share_tokens + share_pv_logs tables

Revision ID: 002_r7_2_favorite_share
Revises: 001_add_bgm_fields
Create Date: 2026-04-29

Wave 5.1 R7-2 — 三张表变更：
  1. projects  → 加 is_favorite BOOLEAN DEFAULT NULL（兼容老数据，null 视为 False）
  2. share_tokens → 新建（分享 token 表，永久有效）
  3. share_pv_logs → 新建（分享页 PV 日志，IP 脱敏）

注意：PM 负责运行此脚本，Backend 不自行执行（MEMORY.md 铁律）。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_r7_2_favorite_share'
down_revision = '001_add_bgm_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. projects.is_favorite
    op.add_column(
        'projects',
        sa.Column('is_favorite', sa.Boolean(), nullable=True, server_default=None)
    )

    # 2. share_tokens 新表
    op.create_table(
        'share_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('uuid', sa.String(36), nullable=False, unique=True),
        sa.Column('project_uuid', sa.String(36), nullable=False, index=True),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # 3. share_pv_logs 新表
    op.create_table(
        'share_pv_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('share_token', sa.String(64), nullable=False, index=True),
        sa.Column('viewed_at', sa.DateTime(), nullable=True),
        sa.Column('ip_hash', sa.String(32), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('share_pv_logs')
    op.drop_table('share_tokens')
    op.drop_column('projects', 'is_favorite')
