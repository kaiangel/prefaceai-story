"""Add BGM fields to project_chapters table

Revision ID: 001_add_bgm_fields
Revises:
Create Date: 2026-04-18

Wave 2 Pipeline Integration — 为 chapters 表新增 BGM 相关字段：
  - bgm_url        VARCHAR(500)     BGM 文件 URL / 本地路径
  - bgm_volume     FLOAT DEFAULT 1.0  用户调节的音量系数
  - bgm_meta_version VARCHAR(50)    使用的 meta-prompt 版本（"mixed" / "en"）
  - credits_used   INT DEFAULT 0     本次 BGM 生成消耗积分（mock）

注意：PM 负责运行此脚本，Backend 不自行执行。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_bgm_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加 BGM 字段到 project_chapters 表"""
    op.add_column(
        'project_chapters',
        sa.Column('bgm_url', sa.String(500), nullable=True)
    )
    op.add_column(
        'project_chapters',
        sa.Column('bgm_volume', sa.Float(), nullable=True, server_default='1.0')
    )
    op.add_column(
        'project_chapters',
        sa.Column('bgm_meta_version', sa.String(50), nullable=True)
    )
    op.add_column(
        'project_chapters',
        sa.Column('credits_used', sa.Integer(), nullable=True, server_default='0')
    )


def downgrade() -> None:
    """回滚：删除 BGM 字段"""
    op.drop_column('project_chapters', 'credits_used')
    op.drop_column('project_chapters', 'bgm_meta_version')
    op.drop_column('project_chapters', 'bgm_volume')
    op.drop_column('project_chapters', 'bgm_url')
