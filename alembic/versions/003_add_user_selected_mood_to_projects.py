"""B33: Add user_selected_mood to projects table

Revision ID: 003_add_user_selected_mood
Revises: 002_r7_2_favorite_share
Create Date: 2026-05-09

B33: 用户在 Stage A（项目创建时）选择的情绪基调，注入 Stage 1 LLM prompt。
优先级最高：project.user_selected_mood > confirmed_outline.user_selected_mood > outline.visual_tone.overall_mood

注意：PM 负责运行此脚本，Backend 不自行执行（MEMORY.md 铁律）。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_user_selected_mood'
down_revision = '002_r7_2_favorite_share'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # projects.user_selected_mood — Stage A 用户选择的情绪基调
    op.add_column(
        'projects',
        sa.Column('user_selected_mood', sa.String(32), nullable=True, server_default=None)
    )


def downgrade() -> None:
    op.drop_column('projects', 'user_selected_mood')
