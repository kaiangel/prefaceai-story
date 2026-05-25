"""In-memory job registry for async character adjust / regenerate-portrait.

Wave 12 P2-1 (2026-05-24): `/characters/{char_id}/adjust` 原本同步阻塞 ~90s
(LLM 重写 + portrait 重生 + fullbody 重生 串行)，前端 fetch 死等转圈、超时重试。
本模块把这类「短命 UI 重绘操作」的瞬态状态放进进程内注册表，让端点立即返回
job_id，前端轮询 job 状态。

为什么用 in-memory 而不是 DB 表:
  - adjust 是短命 (~90s) 操作；角色数据变更 (portrait_url / fullbody_url / outline /
    characters_json) 仍由原有逻辑写 DB 持久化 —— 本 job 只跟踪 status/progress/result
    这类瞬态信息。
  - 新建 DB 表 = Alembic migration = backend_Ben 的 DB/架构领域 + 跨团队协调，对一个
    90s 的 UI 操作过重。
  - 单 uvicorn worker (docker/Dockerfile.api 无 --workers)，与现有 start-generation 的
    asyncio.create_task 后台任务同进程假设一致。
  - 进程重启时未完成的 job 丢失 → 用户重新点一次即可 (角色当前状态已在 DB)。

设计:
  - 模块级单例 dict + asyncio.Lock 保护并发读写。
  - job_id 用 uuid4。
  - 旧 job 用 TTL (默认 1h) 惰性清理，避免无限增长。
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional
from uuid import uuid4


# job 生命周期状态
JOB_STATUS_PENDING = "pending"        # 已创建，后台任务尚未真正开始
JOB_STATUS_PROCESSING = "processing"  # 后台任务运行中
JOB_STATUS_COMPLETED = "completed"    # 成功完成
JOB_STATUS_FAILED = "failed"          # 失败 (LLM fallback 全失败 / portrait 重生失败等)

# 完成/失败的 job 保留多久后惰性清理 (秒)
_JOB_TTL_SECONDS = 3600


class AdjustJobManager:
    """进程内 adjust/regenerate-portrait 任务注册表 (单例)。"""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_job(
        self,
        *,
        project_uuid: str,
        char_id: str,
        kind: str,  # "adjust" | "regenerate_portrait"
        user_id: int,
    ) -> str:
        """创建一个新 job，返回 job_id (uuid)。状态 = pending。"""
        job_id = str(uuid4())
        now = time.time()
        async with self._lock:
            self._prune_locked(now)
            self._jobs[job_id] = {
                "job_id": job_id,
                "project_uuid": project_uuid,
                "char_id": char_id,
                "kind": kind,
                "user_id": user_id,
                "status": JOB_STATUS_PENDING,
                "progress": 0,
                "stage_message": "已加入队列，等待开始...",
                "result": None,          # 成功时填 {character, portrait_url, fullbody_url, ...}
                "error": None,           # 失败时填友好错误信息
                "created_at": now,
                "updated_at": now,
            }
        return job_id

    async def update(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        stage_message: Optional[str] = None,
        result: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """更新 job 字段。job 不存在则静默忽略 (非阻塞)。"""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            if status is not None:
                job["status"] = status
            if progress is not None:
                # 单调递增 guard：进度不回退 (避免 UI 跳变)
                job["progress"] = max(int(progress), int(job.get("progress", 0)))
            if stage_message is not None:
                job["stage_message"] = stage_message
            if result is not None:
                job["result"] = result
            if error is not None:
                job["error"] = error
            job["updated_at"] = time.time()

    async def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        """读取 job 快照 (浅拷贝)。不存在返 None。"""
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return dict(job)

    def _prune_locked(self, now: float) -> None:
        """惰性清理过期 (完成/失败且超过 TTL) 的 job。必须在持锁状态下调用。"""
        if not self._jobs:
            return
        expired = [
            jid
            for jid, j in self._jobs.items()
            if j["status"] in (JOB_STATUS_COMPLETED, JOB_STATUS_FAILED)
            and (now - j["updated_at"]) > _JOB_TTL_SECONDS
        ]
        for jid in expired:
            self._jobs.pop(jid, None)


# 模块级单例 — 整个进程共享同一注册表
adjust_job_manager = AdjustJobManager()
