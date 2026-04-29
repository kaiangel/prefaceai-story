"""
API 成本记录服务 (ARCH-4 修复)

TASK-PARALLEL-M1 Q5: 解决 api_cost_logs 表 0 行 / 0 INSERT 问题。
让 PipelineCostTracker 的 $10 熔断从"空头支票"变成真实依据。

调用点:
- image_generator.py NB2 路径: 每次 generate_shot_image_phase2 成功后
- seedream_generator.py Seedream 路径: 每次 _call_seedream_sync 成功后

成本定价:
- NB2 (gemini-3.1-flash-image-preview): $0.067/张 (官方定价，docs/API_COST_CALCULATION.md)
- Seedream 5.0-lite (doubao-seedream-5-0-260128): ¥0.22/张 ≈ $0.030/张 (1 USD = 7.2 RMB)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("xuhua")

# 定价常量（对齐 docs/API_COST_CALCULATION.md）
NB2_COST_PER_IMAGE: float = 0.067          # $0.067/张 (官方定价)
SEEDREAM_COST_PER_IMAGE: float = 0.030     # ¥0.22/张 ÷ 7.2 RMB/USD ≈ $0.030/张


async def log_api_cost(
    project_id: Optional[int],
    stage: str,
    model: str,
    cost_usd: float,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    detail: str = "",
) -> None:
    """
    异步写入一条 api_cost_logs 记录。

    Args:
        project_id: 项目 ID（可空，部分调用无项目上下文）
        stage: 调用阶段，如 "Stage 5 Shot 3"
        model: 具体模型名，如 "gemini-3.1-flash-image-preview"
        cost_usd: 估算费用（美元）
        input_tokens: 输入 token 数（可选）
        output_tokens: 输出 token 数（可选）
        detail: 上下文说明，如 "Shot 3 (gemini_nb2)"

    Returns:
        None（失败时记录 warning，不抛异常，不阻塞 Pipeline）
    """
    try:
        from app.database import async_session_maker
        from app.models.api_cost_log import ApiCostLog

        record = ApiCostLog(
            project_id=project_id,
            service=_model_to_service(model),
            model=model,
            cost_usd=cost_usd,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            detail=(f"{stage} — {detail}".strip(" —") if detail else stage)[:500],
            created_at=datetime.utcnow(),
        )
        async with async_session_maker() as session:
            session.add(record)
            await session.commit()

        logger.info(
            f"[ApiCostLogger] ✅ 成本记录写入: "
            f"model={model}, cost=${cost_usd:.4f}, "
            f"stage={stage}, project_id={project_id}"
        )
    except Exception as e:
        # 成本记录失败不阻塞 Pipeline，只记录 warning
        logger.warning(
            f"[ApiCostLogger] ⚠️ 成本记录写入失败（非阻塞）: "
            f"model={model}, cost=${cost_usd:.4f}, error={type(e).__name__}: {e}"
        )


def _model_to_service(model: str) -> str:
    """将模型名映射到 service 标识（对齐 monitoring.py 查询 key）。"""
    m = model.lower()
    if "gemini-3.1-flash-image" in m or "nb2" in m:
        return "gemini_nb2"
    if "seedream" in m or "doubao" in m:
        return "seedream"
    if "claude-haiku" in m or "haiku" in m:
        return "haiku"
    if "claude-sonnet" in m or "sonnet" in m:
        return "sonnet"
    if "gemini" in m and "flash" in m:
        return "flash_lite"
    return "unknown"
