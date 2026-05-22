"""T21-NEW-7 DEC-047: Add scene_references_confirmed (projects) + scene_references_json (project_chapters)

Revision ID: 006_add_scene_references_t21_new7
Revises: 005_add_scenes_confirmed
Create Date: 2026-05-21

T21-NEW-7 / DEC-047 (Founder 决方案 D, 2026-05-21 18:25):
Pipeline 引入 Stage 4.5 scene_image_preparation, 让用户审查场景参考图
(mirror character_design 模式). 跟 characters 页面对偶设计:
- 真预览 + 编辑 + 重生 + 60s 倒计时

DB 新加 2 列:
1. projects.scene_references_confirmed (Boolean, default=False)
   - R4-3 闸门: 用户确认场景参考图后由 confirm-scene-references API 置 True
   - 镜像 characters_confirmed / scenes_confirmed 模式
2. project_chapters.scene_references_json (LONGTEXT, nullable=True)
   - Stage 4.5 输出: [{location_id, location_zh, interior_url, exterior_url,
     description_zh, atmosphere, time_of_day, lighting_condition, key_visual_elements}]
   - GET /chapters/{n}/scene-references endpoint 返回此字段

Backfill 策略 (防卡死老数据):
- 已跑完 Stage 5+ 的项目 (project_chapters.storyboard_json 非空 + LENGTH > 100):
  scene_references_confirmed = True (老项目无需再过 R4-3, 直接放行)
- scene_references_json 默认 NULL (老项目无场景参考图数据, GET endpoint 返空列表 + ready=false)

注意: PM 负责运行此脚本 (alembic upgrade head), Backend 不自行执行.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import LONGTEXT


# revision identifiers, used by Alembic.
revision = '006_t21new7_scene_refs'
down_revision = '005_add_scenes_confirmed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PM hotfix (2026-05-21 20:35): 第一次 alembic upgrade 因 revision id 超长 fail,
    # 但部分 ALTER 已 apply, 第二次重跑出 "Duplicate column" 错. 加 idempotent 兜底.
    # 1. projects.scene_references_confirmed (R4-3 闸门)
    try:
        op.add_column(
            'projects',
            sa.Column(
                'scene_references_confirmed',
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    except Exception as e:
        if '1060' in str(e) or 'Duplicate column' in str(e):
            print("[Alembic 006] projects.scene_references_confirmed 已存在, 跳过")
        else:
            raise

    # 2. project_chapters.scene_references_json (Stage 4.5 输出)
    try:
        op.add_column(
            'project_chapters',
            sa.Column(
                'scene_references_json',
                LONGTEXT(),
                nullable=True,
            ),
        )
    except Exception as e:
        if '1060' in str(e) or 'Duplicate column' in str(e):
            print("[Alembic 006] project_chapters.scene_references_json 已存在, 跳过")
        else:
            raise

    # Backfill: 已跑完 Stage 5+ 的老项目直接放行, 防止卡 R4-3
    # 与 005 backfill 同款判断标准 (storyboard_json 非空 + LENGTH > 100 防 "{}" 误判)
    op.execute(
        """
        UPDATE projects p
           SET scene_references_confirmed = TRUE
         WHERE EXISTS (
           SELECT 1 FROM project_chapters c
            WHERE c.project_id = p.id
              AND c.storyboard_json IS NOT NULL
              AND LENGTH(c.storyboard_json) > 100
         )
        """
    )


def downgrade() -> None:
    op.drop_column('project_chapters', 'scene_references_json')
    op.drop_column('projects', 'scene_references_confirmed')
