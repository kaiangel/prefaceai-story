"""
R7-2: 公开分享页 API

GET /api/share/{token} — 无需 auth，返回分享预览数据（方案 A: 前 3 张 shot 引流注册）
同时写 share_pv_logs 一条 + share_tokens.view_count++
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select, update

from app.database import async_session_maker
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.share import ShareToken, SharePvLog

logger = logging.getLogger("xuhua")

router = APIRouter(prefix="/api/share", tags=["share"])


def _hash_ip(ip: str | None) -> str | None:
    """隐私脱敏：SHA-256(ip)[:32] hex chars（16 bytes = 32 hex），不存原始 IP。"""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()[:32]


@router.get("/{token}")
async def get_share_page(
    token: str,
    request: Request,
):
    """
    R7-2: 公开分享页端点（无需登录）。
    方案 A: 返回前 3 张 shot 引流注册，不返回完整故事。

    Returns:
        {
            "story_title": "...",
            "cover_image_url": "/static/...",
            "preview_shots": [
                {"image_url": "...", "narration": "...", "shot_id": 1},
                ...  # 最多 3 张
            ],
            "is_full_access": false,
            "total_shots": 16
        }
    """
    async with async_session_maker() as db:
        # 1. 查 token
        token_result = await db.execute(
            select(ShareToken).where(ShareToken.token == token)
        )
        token_row = token_result.scalar_one_or_none()
        if token_row is None:
            raise HTTPException(status_code=404, detail="分享链接不存在或已失效")

        # 2. 查 project
        project_result = await db.execute(
            select(Project).where(Project.uuid == token_row.project_uuid)
        )
        project = project_result.scalar_one_or_none()
        if project is None:
            raise HTTPException(status_code=404, detail="分享链接对应的项目不存在")

        # 3. 查 chapter（取第 1 章 storyboard）
        chapter_result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == project.id)
            .order_by(Chapter.chapter_number)
            .limit(1)
        )
        chapter = chapter_result.scalar_one_or_none()

        # 4. 解析 shots
        preview_shots: list[dict] = []
        total_shots = 0
        cover_image_url: str | None = None

        if chapter and chapter.storyboard_json:
            try:
                storyboard = json.loads(chapter.storyboard_json)
                shots_raw = (
                    storyboard if isinstance(storyboard, list)
                    else storyboard.get("shots", [])
                )
                total_shots = len(shots_raw)
                # 方案 A: 只返前 3 张
                for shot in shots_raw[:3]:
                    preview_shots.append({
                        "shot_id": shot.get("shot_id", 0),
                        "image_url": shot.get("image_url"),
                        "narration": shot.get("narration", ""),
                    })
                # cover = shot_01 的 image_url
                if shots_raw and shots_raw[0].get("image_url"):
                    cover_image_url = shots_raw[0]["image_url"]
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        # 5. PV 统计：写 log + view_count++
        ip_raw = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
        # X-Forwarded-For 可能是 "1.2.3.4, 5.6.7.8"，取第一个
        if ip_raw and "," in ip_raw:
            ip_raw = ip_raw.split(",")[0].strip()
        ip_hash = _hash_ip(ip_raw)

        try:
            # 写 PV log
            pv_log = SharePvLog(
                share_token=token,
                viewed_at=datetime.utcnow(),
                ip_hash=ip_hash,
            )
            db.add(pv_log)

            # view_count++
            await db.execute(
                update(ShareToken)
                .where(ShareToken.token == token)
                .values(view_count=ShareToken.view_count + 1)
            )
            await db.commit()
        except Exception as _pv_exc:
            logger.warning(f"[Share] PV 统计写入失败（非阻塞）: {_pv_exc}")
            await db.rollback()

        logger.info(
            f"[Share] GET /{token} project={token_row.project_uuid} "
            f"total_shots={total_shots} preview={len(preview_shots)}"
        )

        return {
            "story_title": project.title or "",
            "cover_image_url": cover_image_url,
            "preview_shots": preview_shots,
            "is_full_access": False,  # 方案 A: 部分 shot 引流注册
            "total_shots": total_shots,
        }
