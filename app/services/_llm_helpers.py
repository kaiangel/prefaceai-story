"""
_llm_helpers.py — 跨服务共用的 LLM 响应处理工具函数

B59-hotfix (2026-05-12): 新增 extract_json_from_llm_response()
解决 LLM 输出 ```json...``` 但未闭合 ``` 时 regex 匹配失败的问题
（13443 字符长输出被 max_tokens 截断，结尾 ``` 缺失）
"""

import json
import re
from typing import Optional


def extract_json_from_llm_response(content: str) -> Optional[dict]:
    """
    通用 LLM JSON 提取，强 markdown 容错（未闭合 ``` 也能 work）

    策略优先级：
    1. 强制剥离 markdown 代码块标记后直接 json.loads（处理未闭合 ``` 情形）
    2. 完整 ```json...``` 正则匹配（fallback，处理已闭合但前后有其他文字的情形）
    3. 直接解析整个 content（LLM 直接输出裸 JSON 时）
    4. 找第一个 { 和最后一个 } 提取（LLM 在 JSON 前后输出了说明文字时）

    Args:
        content: LLM 原始响应文本

    Returns:
        解析成功的 dict，或 None（所有策略均失败）
    """
    if not content:
        return None

    # ── 策略 1: 强制剥离 markdown 代码块标记 ──────────────────────────────
    # B59-hotfix: 解决未闭合 ``` 问题
    # 剥离开头的 ```json 或 ``` (不论结尾 ``` 是否存在)
    cleaned = content.strip()
    cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, count=1)
    # 剥离结尾的 ``` （如有）
    cleaned = re.sub(r'\n?\s*```\s*$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # ── 策略 2: 完整 ```json...``` 正则匹配 ────────────────────────────────
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # ── 策略 3: 直接解析整个 content ────────────────────────────────────────
    try:
        result = json.loads(content)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # ── 策略 4: 找 { ... } 边界提取 ─────────────────────────────────────────
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(content[start:end + 1])
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    return None
