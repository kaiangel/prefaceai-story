"""Wave 13 #6: regenerate-portrait 异步化契约验证。

regenerate-portrait 镜像 adjust 的 job 模式 (Wave 12 已 e2e 验证):
  - 端点改 202 + job_id (不再同步阻塞 ~60s 转圈)
  - 复用 adjust_job_manager (kind="regenerate_portrait")
  - 复用同一轮询端点 GET /characters/adjust-jobs/{job_id}
  - 后台 worker 用独立 session, 全 fallback 保留 (B57 fullbody + 非阻塞兜底)

本测试验证可单元化的契约部分 (不打真 DB/网络/LLM):
  1. 端点已注册为 202 POST
  2. 后台执行体 + core worker 函数存在
  3. regenerate_portrait kind 的 job 生命周期 (pending→processing→completed/failed)
  4. 失败时 job 标 failed + 友好 error (前端可见)
"""

import pytest

from app.api import projects
from app.services.adjust_job_manager import (
    AdjustJobManager,
    JOB_STATUS_PENDING,
    JOB_STATUS_PROCESSING,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
)


def test_endpoint_is_202_post():
    """regenerate-portrait 必须是 202 (异步), 不再 200 (同步阻塞)。"""
    route = next(
        r for r in projects.router.routes
        if getattr(r, "path", "").endswith("/regenerate-portrait")
    )
    assert route.status_code == 202
    assert route.methods == {"POST"}


def test_background_worker_functions_exist():
    """异步化所需的后台执行体 + core worker 已定义。"""
    assert callable(projects._run_regenerate_portrait_in_background)
    assert callable(projects._regenerate_portrait_core)
    # 复用 adjust 的内部失败异常类型 (统一翻译为 job.error)
    assert issubclass(projects._AdjustJobFailed, Exception)


@pytest.mark.asyncio
async def test_regenerate_job_lifecycle_completed():
    """regenerate_portrait kind 的 job: pending → processing → completed + result。"""
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="proj-1", char_id="char_001",
        kind="regenerate_portrait", user_id=7,
    )
    job = await mgr.get_job(jid)
    assert job["status"] == JOB_STATUS_PENDING
    assert job["kind"] == "regenerate_portrait"

    await mgr.update(jid, status=JOB_STATUS_PROCESSING, progress=20,
                     stage_message="正在重新绘制肖像...")
    await mgr.update(jid, progress=70, stage_message="肖像完成，正在重新绘制全身图...")
    await mgr.update(
        jid,
        status=JOB_STATUS_COMPLETED,
        progress=100,
        stage_message="肖像已重新生成",
        result={
            "success": True,
            "char_id": "char_001",
            "portrait_url": "/static/x/char_001_portrait.png?v=111",
            "fullbody_url": "/static/x/char_001_fullbody.png?v=111",
            "message": "肖像和全身图已重新生成",
        },
    )
    job = await mgr.get_job(jid)
    assert job["status"] == JOB_STATUS_COMPLETED
    assert job["progress"] == 100
    assert job["result"]["portrait_url"].endswith("?v=111")
    assert job["result"]["fullbody_url"].endswith("?v=111")


@pytest.mark.asyncio
async def test_regenerate_job_failed_friendly_error():
    """失败 (如生图全失败) → job 标 failed + 友好 error (前端能看到, 不静默崩)。"""
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_002",
        kind="regenerate_portrait", user_id=1,
    )
    await mgr.update(
        jid, status=JOB_STATUS_FAILED,
        error="肖像重生成失败: 图像生成服务暂时不可用",
        stage_message="肖像重生成失败",
    )
    job = await mgr.get_job(jid)
    assert job["status"] == JOB_STATUS_FAILED
    assert "肖像重生成失败" in job["error"]
    assert job["result"] is None
