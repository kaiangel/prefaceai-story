"""Wave 12 P2-1: adjust API 异步化 — AdjustJobManager 单元测试.

验证进程内 job 注册表的核心契约:
  1. create_job 返回 uuid，初始 status=pending, progress=0
  2. update 单调递增 guard (progress 不回退)
  3. update 完成时写 result
  4. get_job 返回快照 (浅拷贝，外部 mutate 不污染 store)
  5. 不存在的 job → get 返 None, update 静默 no-op
  6. TTL 惰性清理 (完成/失败超时的 job)
  7. 多 job 并发隔离

测试不依赖 DB / 网络 / LLM — 纯内存逻辑。
"""

import asyncio
import time

import pytest

from app.services.adjust_job_manager import (
    AdjustJobManager,
    adjust_job_manager,
    JOB_STATUS_PENDING,
    JOB_STATUS_PROCESSING,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    _JOB_TTL_SECONDS,
)


@pytest.mark.asyncio
async def test_create_job_initial_state():
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="proj-1", char_id="char_002", kind="adjust", user_id=42
    )
    assert isinstance(jid, str) and len(jid) >= 32  # uuid4
    job = await mgr.get_job(jid)
    assert job is not None
    assert job["status"] == JOB_STATUS_PENDING
    assert job["progress"] == 0
    assert job["char_id"] == "char_002"
    assert job["kind"] == "adjust"
    assert job["user_id"] == 42
    assert job["project_uuid"] == "proj-1"
    assert job["result"] is None
    assert job["error"] is None


@pytest.mark.asyncio
async def test_progress_monotonic_guard():
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    await mgr.update(jid, status=JOB_STATUS_PROCESSING, progress=40)
    # 试图回退到 20 — 应保留 40
    await mgr.update(jid, progress=20)
    job = await mgr.get_job(jid)
    assert job["progress"] == 40
    assert job["status"] == JOB_STATUS_PROCESSING
    # 前进到 70 — 允许
    await mgr.update(jid, progress=70)
    job = await mgr.get_job(jid)
    assert job["progress"] == 70


@pytest.mark.asyncio
async def test_complete_with_result():
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    result_payload = {
        "success": True,
        "character": {"id": "char_001", "name": "苏晨"},
        "char_id": "char_001",
        "portrait_url": "/static/x/char_001_portrait.png?v=123",
        "fullbody_url": "/static/x/char_001_fullbody.png?v=123",
        "message": "角色已调整",
    }
    await mgr.update(
        jid,
        status=JOB_STATUS_COMPLETED,
        progress=100,
        stage_message="角色已调整",
        result=result_payload,
    )
    job = await mgr.get_job(jid)
    assert job["status"] == JOB_STATUS_COMPLETED
    assert job["progress"] == 100
    assert job["result"]["portrait_url"].endswith("?v=123")
    assert job["result"]["fullbody_url"].endswith("?v=123")
    assert job["result"]["character"]["name"] == "苏晨"


@pytest.mark.asyncio
async def test_fail_with_error():
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    await mgr.update(
        jid, status=JOB_STATUS_FAILED, error="AI 服务暂时不可用，请稍后再试"
    )
    job = await mgr.get_job(jid)
    assert job["status"] == JOB_STATUS_FAILED
    assert "暂时不可用" in job["error"]
    assert job["result"] is None


@pytest.mark.asyncio
async def test_get_job_snapshot_isolation():
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    await mgr.update(jid, progress=50)
    snap = await mgr.get_job(jid)
    snap["progress"] = -999  # mutate 外部快照
    snap["result"] = {"hacked": True}
    fresh = await mgr.get_job(jid)
    assert fresh["progress"] == 50  # store 未被污染
    assert fresh["result"] is None


@pytest.mark.asyncio
async def test_missing_job_safe():
    mgr = AdjustJobManager()
    assert await mgr.get_job("does-not-exist") is None
    # update 不存在的 job 应静默 no-op (不抛异常)
    await mgr.update("does-not-exist", progress=99, status=JOB_STATUS_COMPLETED)
    assert await mgr.get_job("does-not-exist") is None


@pytest.mark.asyncio
async def test_ttl_prune_on_create():
    mgr = AdjustJobManager()
    old_jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    await mgr.update(old_jid, status=JOB_STATUS_COMPLETED, progress=100)
    # 手动把 updated_at 推到 TTL 之前 (模拟过期)
    async with mgr._lock:
        mgr._jobs[old_jid]["updated_at"] = time.time() - _JOB_TTL_SECONDS - 10
    # 创建新 job 触发惰性清理
    new_jid = await mgr.create_job(
        project_uuid="p", char_id="char_002", kind="adjust", user_id=1
    )
    assert await mgr.get_job(old_jid) is None  # 过期已清理
    assert await mgr.get_job(new_jid) is not None  # 新 job 保留


@pytest.mark.asyncio
async def test_ttl_does_not_prune_active_processing_job():
    """processing 状态的 job 即使很老也不能被清理 (只清完成/失败)。"""
    mgr = AdjustJobManager()
    jid = await mgr.create_job(
        project_uuid="p", char_id="char_001", kind="adjust", user_id=1
    )
    await mgr.update(jid, status=JOB_STATUS_PROCESSING, progress=30)
    async with mgr._lock:
        mgr._jobs[jid]["updated_at"] = time.time() - _JOB_TTL_SECONDS - 100
    # 触发清理
    await mgr.create_job(
        project_uuid="p", char_id="char_002", kind="adjust", user_id=1
    )
    assert await mgr.get_job(jid) is not None  # processing 不被清理


@pytest.mark.asyncio
async def test_concurrent_jobs_isolated():
    mgr = AdjustJobManager()
    jids = await asyncio.gather(
        *[
            mgr.create_job(
                project_uuid=f"p{i}", char_id=f"char_{i:03d}", kind="adjust", user_id=i
            )
            for i in range(10)
        ]
    )
    assert len(set(jids)) == 10  # 全部唯一
    # 并发更新各自 job
    await asyncio.gather(
        *[mgr.update(jid, progress=(i + 1) * 10) for i, jid in enumerate(jids)]
    )
    for i, jid in enumerate(jids):
        job = await mgr.get_job(jid)
        assert job["progress"] == (i + 1) * 10
        assert job["char_id"] == f"char_{i:03d}"


@pytest.mark.asyncio
async def test_module_singleton_exists():
    """模块级单例可用 (端点通过它共享状态)。"""
    assert isinstance(adjust_job_manager, AdjustJobManager)
    jid = await adjust_job_manager.create_job(
        project_uuid="p", char_id="char_001", kind="regenerate_portrait", user_id=1
    )
    job = await adjust_job_manager.get_job(jid)
    assert job["kind"] == "regenerate_portrait"


# ===========================================================================
# Wave 12 P2-2: Stage 2 portrait 子步骤进度公式 — 验证 ETA 不再冻结
# ===========================================================================

from app.services.job_manager import (
    calculate_eta_remaining_sec,
    _ETA_STAGE_PROGRESS_BOUNDS,
)


def _portrait_sub_progress(char_index: int, n_chars: int) -> int:
    """复刻 pipeline_orchestrator.py Stage 2 portrait loop 的子进度公式。"""
    return 6 + int((char_index / max(n_chars, 1)) * 4)


@pytest.mark.parametrize("n_chars", [1, 2, 3, 6])
def test_p2_2_portrait_subprogress_within_band(n_chars):
    """每角色子进度必须落在 character_design band (6,10) 内, 且不到 10 (留给 character_ready)。"""
    lo, hi = _ETA_STAGE_PROGRESS_BOUNDS["character_design"]
    assert (lo, hi) == (6, 10)
    prev = -1
    for ci in range(n_chars):
        p = _portrait_sub_progress(ci, n_chars)
        assert lo <= p < hi, f"char {ci}/{n_chars}: progress {p} 越出 band [{lo},{hi})"
        assert p >= prev, "子进度必须非递减"
        prev = p


def test_p2_2_eta_decreases_within_character_design_band():
    """P2-2 根因修复证明: progress 在 character_design band 内递增 → ETA 真递减 (不再冻结)。"""
    eta_at_6 = calculate_eta_remaining_sec("character_design", 6, actual_shot_count=18)
    eta_at_9 = calculate_eta_remaining_sec("character_design", 9, actual_shot_count=18)
    assert eta_at_6 is not None and eta_at_9 is not None
    # 6 个角色画像生成期间, 原本 progress 冻结在 6 → ETA 冻结。
    # 现在 progress 6→9 → ETA 必须减小。
    assert eta_at_9 < eta_at_6, (
        f"ETA 应随 character_design 内 progress 递增而递减: "
        f"eta@6={eta_at_6}s, eta@9={eta_at_9}s"
    )
