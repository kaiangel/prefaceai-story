"""B58: Add scenes_confirmed to projects table (Wave 6 — BUG-SCENES-CONFIRM-MISSING)

Revision ID: 005_add_scenes_confirmed
Revises: 004_add_partial_failure_to_jobs
Create Date: 2026-05-11

B58 / Wave 6: Scenes 确认环节后端补齐
前端 ScenePreview 完整存在（StageC.tsx + scene-preview sub-phase + /scenes URL），
但后端长期断裂：
  - 无 POST /confirm-scenes 端点
  - 无 projects.scenes_confirmed DB 字段
  - Pipeline Stage 3 完成后不 pause，直接进 Stage 4

本迁移加 projects.scenes_confirmed 列（默认 False），由：
  - app/models/project.py 暴露
  - app/schemas/project.py.ProjectDetail 序列化
  - app/api/projects.py POST /confirm-scenes 端点写入
  - pipeline_orchestrator R4-2 wait loop 轮询

Backfill 策略（防卡死老数据）：
  已跑完 Stage 4 的项目（chapters.storyboard_json 非空，长度 > 100）
  直接 scenes_confirmed=True，否则 False。

注意：PM 负责运行此脚本（alembic upgrade head），Backend 不自行执行。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_scenes_confirmed'
down_revision = '004_add_partial_failure_to_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # B58: projects.scenes_confirmed — 用户在 /scenes 页面确认场景后由 confirm-scenes API 置 True
    op.add_column(
        'projects',
        sa.Column(
            'scenes_confirmed',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Backfill: 已跑完 Stage 4 的老项目（chapters.storyboard_json 非空）直接设 True，防止卡住
    # 用 LENGTH > 100 避免空 JSON "{}" 误判（typical storyboard JSON > 数 KB）
    op.execute(
        """
        UPDATE projects p
           SET scenes_confirmed = TRUE
         WHERE EXISTS (
           SELECT 1 FROM project_chapters c
            WHERE c.project_id = p.id
              AND c.storyboard_json IS NOT NULL
              AND LENGTH(c.storyboard_json) > 100
         )
        """
    )


def downgrade() -> None:
    op.drop_column('projects', 'scenes_confirmed')
