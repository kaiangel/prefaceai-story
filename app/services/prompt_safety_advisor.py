"""
D.17 Prompt Safety Advisor

When a shot image generation is blocked by content safety filters (all sanitize attempts
exhausted), this module uses Claude Haiku 4.5 to analyze the failed prompt and generate
actionable suggestions for the user — telling them which terms likely triggered the filter
and what to change them to.

This replaces the old NB2↔Seedream fallback strategy (D.17 Wave 5.1).
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("xuhua")


async def analyze_safety_failure(
    failed_prompt: str,
    reason: str,
) -> dict:
    """
    Use Claude Haiku 4.5 to analyze why a shot prompt was blocked by content safety.

    Args:
        failed_prompt: The exact prompt that was rejected.
        reason: The error_kind returned by the image generator (e.g. "sanitize_exhausted").

    Returns:
        {
            "suspected_terms": ["7岁小孩", "红肿"],
            "suggested_changes": [
                {"original": "眼眶红肿", "suggestion": "若有所思 / 望向远方"}
            ],
            "user_message": "你的画面文字 'XXX' 大概率因 'YYY' 触发了 AI 安全审查，建议改成 'ZZZ' 后重试。"
        }
        On failure (API unavailable, etc.): returns a generic safe fallback dict.
    """
    from app.config import settings

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("[SafetyAdvisor] ANTHROPIC_API_KEY 未配置，返回通用提示")
        return _generic_advice(failed_prompt)

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        analysis_prompt = f"""You are a content moderation advisor for an AI image generation system.
A user's story prompt was blocked by the image generation safety filter.

Failed prompt (may contain Chinese or English):
<prompt>
{failed_prompt[:2000]}
</prompt>

Rejection reason code: {reason}

Your task: identify which specific terms or phrases most likely triggered the safety filter,
and suggest safer alternatives that preserve the narrative intent.

Respond in JSON exactly like this example (no markdown, no extra keys):
{{
  "suspected_terms": ["specific term 1", "specific term 2"],
  "suggested_changes": [
    {{"original": "term1", "suggestion": "alternative1 / alternative2"}},
    {{"original": "term2", "suggestion": "alternative3"}}
  ],
  "user_message": "你的画面描述中，「<term>」等词大概率触发了 AI 安全审查。建议将「<term>」改为「<suggestion>」后重新生成。"
}}

Rules:
- suspected_terms: 2-4 most likely problematic terms from the prompt
- suggested_changes: one entry per suspected term
- user_message: friendly Chinese explanation, max 100 chars
- If no obvious safety issue, suspected_terms=[], user_message="本画面描述触发了安全审查，请尝试用更温和的方式描述场景"
"""

        message = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": analysis_prompt}],
        )

        content = message.content[0].text.strip()

        # Parse JSON response — RISK-T17-1: 使用 extract_json_from_llm_response 处理 markdown JSON
        from app.services._llm_helpers import extract_json_from_llm_response
        advice = extract_json_from_llm_response(content)
        if advice is None:
            logger.warning(f"[SafetyAdvisor] JSON 解析失败，content[:200]={content[:200]!r}")
            return _generic_advice(failed_prompt)

        # Validate structure
        if not isinstance(advice.get("suspected_terms"), list):
            advice["suspected_terms"] = []
        if not isinstance(advice.get("suggested_changes"), list):
            advice["suggested_changes"] = []
        if not isinstance(advice.get("user_message"), str):
            advice["user_message"] = "本画面描述触发了安全审查，请尝试用更温和的方式描述场景后重新生成。"

        logger.info(
            f"[SafetyAdvisor] 分析完成: {len(advice['suspected_terms'])} 个可疑词，"
            f"reason={reason}"
        )
        return advice

    except Exception as exc:
        logger.warning(f"[SafetyAdvisor] Haiku 分析失败（非阻塞）: {exc}")
        return _generic_advice(failed_prompt)


def _generic_advice(failed_prompt: str) -> dict:
    """Fallback advice when Haiku API is unavailable."""
    return {
        "suspected_terms": [],
        "suggested_changes": [],
        "user_message": "本画面描述触发了 AI 安全审查。请尝试用更温和、中性的方式描述场景后重新生成。",
    }
