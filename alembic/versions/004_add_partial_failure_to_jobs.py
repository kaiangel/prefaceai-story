"""B46: Add failed_shot_count and partial_failure to chapter_generation_jobs

Revision ID: 004_add_partial_failure_to_jobs
Revises: 003_add_user_selected_mood
Create Date: 2026-05-11

B46: Stage 5 Shot 生成时即使部分失败（content_safety_failure 等），job.status 仍标 'completed'。
为让 frontend 感知部分失败，加两列：
  - failed_shot_count: 失败 shot 数量（0 表示全部成功）
  - partial_failure: 布尔值（failed_shot_count > 0 时为 True）

frontend 用 failed_shot_count > 0 检测 partial failure，
不破坏现有 status='completed' 逻辑（前端现有分支判断不受影响）。

注意：PM 负责运行此脚本（alembic upgrade head），Backend 不自行执行。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_partial_failure_to_jobs'
down_revision = '003_add_user_selected_mood'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # B46: chapter_generation_jobs 加 partial_failure 字段
    op.add_column(
        'chapter_generation_jobs',
        sa.Column('failed_shot_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'chapter_generation_jobs',
        sa.Column('partial_failure', sa.Boolean(), nullable=False, server_default=sa.false())
    )


def downgrade() -> None:
    op.drop_column('chapter_generation_jobs', 'partial_failure')
    op.drop_column('chapter_generation_jobs', 'failed_shot_count')
