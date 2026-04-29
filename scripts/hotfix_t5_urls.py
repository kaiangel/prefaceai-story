#!/usr/bin/env python3
"""
hotfix_t5_urls.py — T5 测试数据热修复脚本 (BE-3 + BE-5)

修复内容：
  - BE-3: 为 4_storyboard.json 中每个 shot 写入 image_url（/static/outputs/{uuid}/images/shot_NN.png）
  - BE-5: 更新 DB chapter.bgm_url 为 HTTP URL（/static/outputs/{uuid}/bgm_chapterN.mp3）

目标项目: project_uuid=283bd407-0e64-43bb-b2eb-8f6b4063c4af

用法：
    cd /path/to/xuhua_story
    source venv/bin/activate
    python scripts/hotfix_t5_urls.py
"""

import asyncio
import json
import logging
import os
import sys

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_UUID = "283bd407-0e64-43bb-b2eb-8f6b4063c4af"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def fix_storyboard_json():
    """BE-3: 为 4_storyboard.json 每个 shot 写入 image_url"""
    storyboard_path = os.path.join(OUTPUT_DIR, PROJECT_UUID, "4_storyboard.json")
    if not os.path.exists(storyboard_path):
        logger.error(f"找不到 storyboard 文件: {storyboard_path}")
        return False

    with open(storyboard_path, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard.get("shots", [])
    updated = 0
    for shot in shots:
        shot_id = shot.get("shot_id")
        if shot_id is None:
            continue
        image_url = f"/static/outputs/{PROJECT_UUID}/images/shot_{shot_id:02d}.png"
        shot["image_url"] = image_url
        updated += 1

    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)

    logger.info(f"[BE-3] ✅ 4_storyboard.json 更新完成: {updated} shots 写入 image_url")
    return True


async def fix_db_bgm_url():
    """BE-5: 更新 DB 中 chapter.bgm_url 为 HTTP URL"""
    try:
        from app.database import async_session_maker
        from sqlalchemy import select
        from app.models.project import Project
        from app.models.chapter import Chapter

        bgm_filename = "bgm_chapter0.mp3"
        bgm_http_url = f"/static/outputs/{PROJECT_UUID}/{bgm_filename}"

        async with async_session_maker() as db:
            # 查 project
            proj_result = await db.execute(
                select(Project).where(Project.uuid == PROJECT_UUID)
            )
            project = proj_result.scalar_one_or_none()
            if not project:
                logger.error(f"[BE-5] 找不到 project: {PROJECT_UUID}")
                return False

            # 查 chapter（取第一个）
            ch_result = await db.execute(
                select(Chapter).where(Chapter.project_id == project.id)
            )
            chapters = ch_result.scalars().all()
            if not chapters:
                logger.error(f"[BE-5] 找不到 chapter for project_id={project.id}")
                return False

            for chapter in chapters:
                old_url = chapter.bgm_url
                chapter.bgm_url = bgm_http_url
                logger.info(
                    f"[BE-5] chapter.id={chapter.id}: "
                    f"bgm_url: {old_url!r} → {bgm_http_url!r}"
                )

            await db.commit()
            logger.info(f"[BE-5] ✅ DB chapter.bgm_url 更新完成")
            return True
    except Exception as e:
        logger.error(f"[BE-5] DB 更新失败: {e}")
        return False


async def fix_storyboard_in_db():
    """BE-3: 将修复后的 storyboard（含 image_url）回写到 DB chapter.storyboard_json"""
    try:
        from app.database import async_session_maker
        from sqlalchemy import select
        from app.models.project import Project
        from app.models.chapter import Chapter

        storyboard_path = os.path.join(OUTPUT_DIR, PROJECT_UUID, "4_storyboard.json")
        with open(storyboard_path, "r", encoding="utf-8") as f:
            storyboard = json.load(f)

        async with async_session_maker() as db:
            proj_result = await db.execute(
                select(Project).where(Project.uuid == PROJECT_UUID)
            )
            project = proj_result.scalar_one_or_none()
            if not project:
                logger.error(f"找不到 project: {PROJECT_UUID}")
                return False

            ch_result = await db.execute(
                select(Chapter).where(Chapter.project_id == project.id)
            )
            chapters = ch_result.scalars().all()
            for chapter in chapters:
                chapter.storyboard_json = json.dumps(storyboard, ensure_ascii=False)
                logger.info(f"[BE-3] chapter.id={chapter.id}: storyboard_json 已更新（含 image_url）")

            await db.commit()
            logger.info(f"[BE-3] ✅ DB storyboard_json 更新完成")
            return True
    except Exception as e:
        logger.error(f"[BE-3] DB storyboard_json 更新失败: {e}")
        return False


async def main():
    logger.info(f"=" * 60)
    logger.info(f"T5 Hot-fix 脚本启动")
    logger.info(f"project_uuid: {PROJECT_UUID}")
    logger.info(f"=" * 60)

    # Step 1: 修复本地 JSON 文件（BE-3）
    ok1 = fix_storyboard_json()

    # Step 2: 回写 DB storyboard_json（BE-3）
    ok2 = await fix_storyboard_in_db()

    # Step 3: 修复 DB bgm_url（BE-5）
    ok3 = await fix_db_bgm_url()

    logger.info(f"\n{'=' * 60}")
    logger.info(f"Hot-fix 完成:")
    logger.info(f"  BE-3 (storyboard JSON 文件):   {'✅' if ok1 else '❌'}")
    logger.info(f"  BE-3 (DB storyboard_json):      {'✅' if ok2 else '❌'}")
    logger.info(f"  BE-5 (DB bgm_url):              {'✅' if ok3 else '❌'}")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
