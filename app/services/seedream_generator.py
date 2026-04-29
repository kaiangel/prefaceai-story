"""
Seedream 5.0-lite Generator (火山方舟国内版)

TASK-SEEDREAM-INTEGRATION — 测试期主力生图模型（成本 55% 低于 NB2）。
MVP 发布时通过 env flag `IMAGE_GEN_PROVIDER=nb2` 切回 NB2。

集成点:
- image_generator.generate_shot_image() / generate_shot_image_phase2() 当
  settings.IMAGE_GEN_PROVIDER == "seedream" 时把调用派发到本模块。
- sanitize 3 次失败后降级到 NB2 补图（保证 Pipeline 不断）。

火山方舟国内版审查严（POC Phase 3/4 实测：10% shots 触发 InputTextSensitiveContentDetected）：
已知拦截词示例: elderly + worry / furrow / suppressed / mist 的组合。

设计要点:
- 参考图策略复用生产 NB2 传入的 reference_images（只传 fullbody + scene anchors），
  不重新生成参考图，不污染现有参考图管道。
- prompt 直接复用 NB2 已构建好的 full_prompt（含 StyleEnforcer / text_overlay 指令 / 风格锁）。
- sanitize 逐级替换（attempt 1/2/3 力度递增），3 轮失败 → fallback_callback 调 NB2 补这一张。
- 不 import app/ 之外的东西；整个模块只依赖 app.config + stdlib + Pillow。
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import ssl
import time
import urllib.error
import urllib.request
from io import BytesIO
from typing import Awaitable, Callable, List, Optional

import certifi
from PIL import Image

from app.config import settings

logger = logging.getLogger("xuhua")


# ---------------------------------------------------------------------------
# 火山方舟国内版端点（Founder 决策 Q4）
# ---------------------------------------------------------------------------
SEEDREAM_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

# Founder 决策 Q2：5.0-lite 先跑（账号已开通 model ID）
SEEDREAM_MODEL = "doubao-seedream-5-0-260128"

# 2:3 portrait, 2K — 匹配项目 DEC-010 抖音宽高比标准
# aspect_ratio "2:3" → size "1664x2496"（来自 POC 实测）
_ASPECT_RATIO_TO_SIZE = {
    "2:3": "1664x2496",
    "3:2": "2496x1664",
    "1:1": "2048x2048",
    "3:4": "1664x2218",  # D.15: 小红书 3:4 — 1664 × (4/3) ≈ 2219, 取 2218 偶数
    "4:3": "2218x1664",  # 横屏 4:3 对称版
    "9:16": "1440x2560",
    "16:9": "2560x1440",
}

# Payload 阈值：超过则降采样参考图到 1024 px
PAYLOAD_DOWNSAMPLE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB

MAX_REFERENCE_IMAGES = 14  # 火山方舟上限
SEEDREAM_MAX_SANITIZE_ATTEMPTS = 3  # Founder 决策 Q3：3 次失败降级 NB2
SEEDREAM_TIMEOUT_SEC = 180
SEEDREAM_HTTP_RETRIES = 3  # Bug 3 fix: 网络层瞬时错误（IncompleteRead/429/5xx）指数退避次数，2→3


# ---------------------------------------------------------------------------
# Sanitize 关键词替换表（POC Phase 3/4 实测拦截词）
# ---------------------------------------------------------------------------
# Attempt 1：保守替换（语义最接近）
SANITIZE_MAP_ATTEMPT_1: dict[str, str] = {
    "elderly man": "older man",
    "elderly woman": "older woman",
    "elderly": "older",
    "furrow of quiet worry": "sense of quiet contemplation",
    "quiet worry": "quiet contemplation",
    "worry": "concern",
    "worried": "concerned",
    "suppressed": "quiet",
    "mist": "fog",
    "misty": "foggy",
}

# Attempt 2：追加更激进的替换
SANITIZE_MAP_ATTEMPT_2: dict[str, str] = {
    "furrow": "expression",
    "furrowed": "thoughtful",
    "grief": "reflection",
    "sorrow": "quietness",
    "anguish": "stillness",
    "suffering": "quiet moment",
    "pain": "stillness",
    "tears": "gentle eyes",
}

# Attempt 3：兜底 — 剥离所有可能触发的情绪强词
SANITIZE_MAP_ATTEMPT_3: dict[str, str] = {
    "dying": "resting",
    "death": "stillness",
    "dead": "still",
    "blood": "mark",
    "bloody": "marked",
    "violent": "intense",
    "violence": "intensity",
    "cry": "gentle expression",
    "crying": "gentle",
}

# 汇总（仅用于 context-for-others 汇报；实际应用时按 attempt 分级）
SANITIZE_KEYWORD_MAP_FULL: dict[str, str] = {
    **SANITIZE_MAP_ATTEMPT_1,
    **SANITIZE_MAP_ATTEMPT_2,
    **SANITIZE_MAP_ATTEMPT_3,
}


# ---------------------------------------------------------------------------
# text_overlay instruction builder（来自 POC 脚本 scripts/test_seedream_vs_nb2.py）
# 简化版：不依赖 app/ 内的 build_native_text_prompt，保持 Seedream 路径独立
# ---------------------------------------------------------------------------

def _strip_speaker_label(text: str) -> str:
    """去除说话者标签/括号，只保留台词内容。"""
    if not text:
        return text
    t = text.strip()
    if t.startswith("（") and t.endswith("）"):
        t = t[1:-1].strip()
    if "：「" in t or ":「" in t:
        sep = "：「" if "：「" in t else ":「"
        parts = t.split(sep, 1)
        if len(parts) == 2:
            content = parts[1]
            if content.endswith("」"):
                content = content[:-1]
            t = content
    if t.startswith("内心："):
        t = t[3:]
    elif t.startswith("内心:"):
        t = t[3:]
    return t.strip()


def _infer_subtype(text: str) -> str:
    t = text.strip()
    if t.startswith("（") and t.endswith("）"):
        return "thought"
    if "内心：" in t or "内心:" in t:
        return "thought"
    if "：「" in t or ":「" in t:
        return "dialogue"
    return "narration"


def build_text_overlay_instruction(text_overlay: dict) -> str:
    """根据 shot['text_overlay'] 生成 Seedream 的 TEXT OVERLAY REQUIREMENT 块。

    返回空字符串表示无需附加文字指令（调用方决定是否把原 prompt 直接发送）。
    """
    if not text_overlay:
        return ""

    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    blocks: List[str] = []

    if text_type == "thought":
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            clean = _strip_speaker_label(txt)
            if clean:
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT:\n"
                    f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
                    f"height approximately 18% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered alignment.\n"
                    f"Inner monologue style: represents character's private thoughts.\n"
                    f"CRITICAL: The Chinese text MUST be visible and legible in the final image."
                )

    elif text_type == "narration":
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            clean = _strip_speaker_label(txt)
            if clean:
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT:\n"
                    f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
                    f"height approximately 18% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered alignment.\n"
                    f"Narrative caption style: objective narration.\n"
                    f"CRITICAL: The Chinese text MUST be visible and legible in the final image."
                )

    elif text_type == "dialogue":
        if isinstance(chinese_text, list):
            texts = chinese_text
        elif isinstance(chinese_text, str):
            texts = [t.strip() for t in chinese_text.split("||") if t.strip()]
        else:
            texts = [chinese_text]
        for i, txt in enumerate(texts):
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            clean = _strip_speaker_label(txt)
            if not clean:
                continue
            label = f"({i + 1})" if len(texts) > 1 else ""
            blocks.append(
                f"Add Chinese speech bubble{label} in the scene with text '{clean}'. "
                f"Bubble style: clean white speech bubble with dark outline. "
                f"Position: near {position} side of the image.\n"
                f"CRITICAL: The Chinese text '{clean}' MUST be visible and legible in the speech bubble."
            )

    elif text_type in (
        "dialogue_with_thought",
        "narration_with_thought",
        "narration_with_dialogue",
        "dialogue_with_narration",
    ):
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for i, item in enumerate(texts):
            if isinstance(item, dict) and "type" in item:
                sub_type = item["type"]
                txt = item.get("text", "")
            else:
                txt = item if isinstance(item, str) else str(item)
                sub_type = _infer_subtype(txt)
            clean = _strip_speaker_label(txt)
            if not clean:
                continue
            idx_label = f" ({i + 1})"
            if sub_type in ("thought", "narration"):
                label = "Inner monologue" if sub_type == "thought" else "Narration"
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT{idx_label} - {label}:\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered.\n"
                    f"CRITICAL: The Chinese text MUST be visible and legible in the final image."
                )
            else:
                blocks.append(
                    f"Add Chinese speech bubble{idx_label} in the scene with text '{clean}'. "
                    f"Bubble style: clean white speech bubble with dark outline. "
                    f"Position: near {position} side of the image.\n"
                    f"CRITICAL: The Chinese text '{clean}' MUST be visible and legible."
                )

    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# sanitize 逐级替换
# ---------------------------------------------------------------------------

def sanitize_prompt(prompt: str, attempt: int = 1) -> tuple[str, list[str]]:
    """按关键词表逐级替换。attempt 1/2/3 表示替换力度递增。

    返回 (sanitized_prompt, replacements_applied)。
    """
    if attempt <= 0:
        return prompt, []
    mapping: dict[str, str] = {}
    if attempt >= 1:
        mapping.update(SANITIZE_MAP_ATTEMPT_1)
    if attempt >= 2:
        mapping.update(SANITIZE_MAP_ATTEMPT_2)
    if attempt >= 3:
        mapping.update(SANITIZE_MAP_ATTEMPT_3)

    replacements: list[str] = []
    sanitized = prompt
    # 按 key 长度倒序替换，避免短词先替换破坏长短语
    for src in sorted(mapping.keys(), key=len, reverse=True):
        if src in sanitized:
            sanitized = sanitized.replace(src, mapping[src])
            replacements.append(f"{src} → {mapping[src]}")
    return sanitized, replacements


# ---------------------------------------------------------------------------
# 参考图 → base64 data URI
# ---------------------------------------------------------------------------

def _pil_to_data_uri(img: Image.Image, max_dim: Optional[int] = None) -> str:
    """PIL Image → base64 data URI。max_dim 指定时先降采样。"""
    to_encode = img
    if max_dim is not None:
        w, h = img.size
        longest = max(w, h)
        if longest > max_dim:
            scale = max_dim / longest
            new_size = (int(w * scale), int(h * scale))
            to_encode = img.resize(new_size, Image.LANCZOS)
    buf = BytesIO()
    if to_encode.mode not in ("RGB", "RGBA"):
        to_encode = to_encode.convert("RGB")
    to_encode.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _build_payload(
    prompt: str,
    reference_images: List[Image.Image],
    aspect_ratio: str,
    max_ref_dim: Optional[int] = None,
) -> tuple[dict, bytes]:
    """构建 Seedream 请求 payload + body bytes。"""
    size = _ASPECT_RATIO_TO_SIZE.get(aspect_ratio, _ASPECT_RATIO_TO_SIZE["2:3"])

    refs = reference_images[:MAX_REFERENCE_IMAGES] if reference_images else []
    ref_uris = [_pil_to_data_uri(img, max_dim=max_ref_dim) for img in refs]

    payload: dict = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
        "watermark": False,
        "sequential_image_generation": "disabled",
    }
    if ref_uris:
        payload["image"] = ref_uris if len(ref_uris) > 1 else ref_uris[0]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return payload, body


# ---------------------------------------------------------------------------
# 内容安全拦截识别
# ---------------------------------------------------------------------------

_SENSITIVE_MARKERS = (
    "InputTextSensitiveContentDetected",
    "sensitive_content",
    "SensitiveContent",
    "content_policy",
    "Content policy",
    "risk_control",
)


def _is_sensitive_content_error(err_body: str) -> bool:
    if not err_body:
        return False
    for marker in _SENSITIVE_MARKERS:
        if marker.lower() in err_body.lower():
            return True
    return False


# ---------------------------------------------------------------------------
# 低层 API 调用（同步 urllib，在 to_thread 里跑）
# ---------------------------------------------------------------------------

def _call_seedream_sync(
    prompt: str,
    reference_images: List[Image.Image],
    aspect_ratio: str,
    api_key: str,
) -> dict:
    """同步调用 Seedream API。返回 {"success","pil_image","error","error_kind","latency_sec",...}。

    error_kind ∈ {"sensitive_content","rate_limit","payload_too_large","network",
                  "api_error","empty_response","missing_api_key"}。
    """
    if not api_key:
        return {"success": False, "error": "ARK_API_KEY not set", "error_kind": "missing_api_key"}

    # SSL context（部分环境下 Python framework 证书链异常）
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()

    _, body = _build_payload(prompt, reference_images, aspect_ratio, max_ref_dim=None)
    max_dim_used: Optional[int] = None
    if len(body) > PAYLOAD_DOWNSAMPLE_THRESHOLD_BYTES:
        max_dim_used = 1024
        _, body = _build_payload(prompt, reference_images, aspect_ratio, max_ref_dim=max_dim_used)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    last_err: dict = {"success": False, "error": "unknown", "error_kind": "api_error"}
    # Bug 3 fix: 追踪每次调用的重试次数，便于监控 IncompleteRead fail rate
    _retry_count: int = 0

    for attempt in range(1, SEEDREAM_HTTP_RETRIES + 2):
        req = urllib.request.Request(SEEDREAM_ENDPOINT, data=body, headers=headers, method="POST")
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=SEEDREAM_TIMEOUT_SEC, context=ctx) as resp:
                raw = resp.read()
                latency = round(time.monotonic() - start, 2)
                data = json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            latency = round(time.monotonic() - start, 2)
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                err_body = ""
            logger.warning(
                f"    [SeedreamGenerator] HTTP {e.code} (attempt {attempt}): {err_body[:300]}"
            )
            if _is_sensitive_content_error(err_body):
                return {
                    "success": False,
                    "error": f"Sensitive content detected: {err_body[:300]}",
                    "error_kind": "sensitive_content",
                    "latency_sec": latency,
                    "http_status": e.code,
                }
            if e.code in (413, 400) and "too large" in err_body.lower() and max_dim_used != 512:
                next_dim = 1024 if max_dim_used is None else 512
                _, body = _build_payload(prompt, reference_images, aspect_ratio, max_ref_dim=next_dim)
                max_dim_used = next_dim
                logger.warning(f"    [SeedreamGenerator] payload too large, downsampled to {next_dim}px")
                continue
            if e.code in (429, 500, 502, 503, 504) and attempt <= SEEDREAM_HTTP_RETRIES:
                backoff = 2 ** attempt + 1
                logger.warning(f"    [SeedreamGenerator] HTTP {e.code}, sleep {backoff}s then retry")
                time.sleep(backoff)
                continue
            last_err = {
                "success": False,
                "error": f"HTTP {e.code}: {err_body[:300]}",
                "error_kind": "rate_limit" if e.code == 429 else "api_error",
                "latency_sec": latency,
                "http_status": e.code,
            }
            return last_err
        except Exception as e:
            latency = round(time.monotonic() - start, 2)
            logger.warning(
                f"    [SeedreamGenerator] {type(e).__name__} (attempt {attempt}): {e}"
            )
            if attempt <= SEEDREAM_HTTP_RETRIES:
                _retry_count += 1
                backoff = 2 ** attempt
                logger.info(
                    f"    [SeedreamGenerator] {type(e).__name__} 重试 #{_retry_count}，sleep {backoff}s"
                )
                time.sleep(backoff)
                continue
            return {
                "success": False,
                "error": f"{type(e).__name__}: {e}",
                "error_kind": "network",
                "latency_sec": latency,
                "retry_count": _retry_count,
            }

        # 解析响应
        if data.get("error"):
            err_str = json.dumps(data["error"], ensure_ascii=False)
            if _is_sensitive_content_error(err_str):
                return {
                    "success": False,
                    "error": f"Sensitive content detected: {err_str[:300]}",
                    "error_kind": "sensitive_content",
                    "latency_sec": latency,
                }
            return {
                "success": False,
                "error": f"API error: {err_str[:300]}",
                "error_kind": "api_error",
                "latency_sec": latency,
            }

        data_list = data.get("data") or []
        if not data_list:
            return {
                "success": False,
                "error": f"Empty data array: {str(data)[:300]}",
                "error_kind": "empty_response",
                "latency_sec": latency,
            }
        first = data_list[0]
        img_bytes: Optional[bytes] = None
        if first.get("b64_json"):
            img_bytes = base64.b64decode(first["b64_json"])
        elif first.get("url"):
            try:
                with urllib.request.urlopen(first["url"], timeout=60, context=ctx) as r:
                    img_bytes = r.read()
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to download image URL: {e}",
                    "error_kind": "network",
                    "latency_sec": latency,
                }
        if not img_bytes:
            return {
                "success": False,
                "error": f"No b64_json or url in response: {first}",
                "error_kind": "empty_response",
                "latency_sec": latency,
            }
        pil_image = Image.open(BytesIO(img_bytes))
        pil_image.load()
        if _retry_count > 0:
            logger.info(
                f"    [SeedreamGenerator] ✅ 下载成功（经历 {_retry_count} 次重试，Bug 3 retry 统计）"
            )
        return {
            "success": True,
            "pil_image": pil_image,
            "image_bytes": img_bytes,
            "latency_sec": latency,
            "size": first.get("size"),
            "usage": data.get("usage"),
            "model_used": SEEDREAM_MODEL,
            "retry_count": _retry_count,  # Bug 3: 重试次数统计
        }

    return last_err


# ---------------------------------------------------------------------------
# 高层入口：generate_shot_image_seedream
# ---------------------------------------------------------------------------

async def generate_shot_image_seedream(
    shot: dict,
    reference_images: Optional[List[Image.Image]] = None,
    aspect_ratio: str = "2:3",
    full_prompt: Optional[str] = None,
    fallback_callback: Optional[Callable[[], Awaitable[dict]]] = None,
    **_kwargs,
) -> dict:
    """Seedream 5.0-lite 主流程。

    Args:
        shot: storyboard shot dict。用于读取 text_overlay 和 image_prompt 作 prompt 源。
        reference_images: 预处理好的 PIL Image 列表（角色 fullbody + 场景 anchor）。
            复用调用方已有的参考图管道，Seedream 不额外请求参考图。
        aspect_ratio: 宽高比字符串（"2:3" 等）。
        full_prompt: 可选。如果调用方已构建好完整 prompt（含 StyleEnforcer + text_overlay），
            直接使用；否则自行拼接 shot['image_prompt'] + build_text_overlay_instruction。
        fallback_callback: async callable，3 次 sanitize 仍失败时调用（通常是 NB2 原生成逻辑）。
            返回 dict 与本函数对齐（含 success / pil_image 等）。
        **_kwargs: 兼容其它调用参数（忽略）。

    Returns:
        dict 与 ImageGenerator.generate_shot_image_phase2 的成功结构兼容：
            success, pil_image, image_data(base64 png), image_format, width, height,
            model_used, generation_time_seconds, shot_id, seedream_info
        失败时 success=False，error + error_kind 描述，并附带 sanitize_attempts 记录。
    """
    api_key = getattr(settings, "ARK_API_KEY", "") or ""
    # 同时兼容环境变量直读（未加到 Settings 的场景）
    if not api_key:
        import os

        api_key = os.getenv("ARK_API_KEY", "").strip()

    shot_id = shot.get("shot_id", "?")
    text_overlay = shot.get("text_overlay", {}) or {}

    if full_prompt:
        base_prompt = full_prompt
    else:
        base_prompt = shot.get("image_prompt", "") or ""
        text_instruction = build_text_overlay_instruction(text_overlay)
        if text_instruction:
            base_prompt = base_prompt + "\n\n" + text_instruction

    if not base_prompt.strip():
        logger.error(f"    [SeedreamGenerator] Shot {shot_id} 没有可用 prompt，跳到 fallback")
        return await _run_fallback(fallback_callback, reason="empty_prompt")

    logger.info(
        f"    [SeedreamGenerator] Shot {shot_id} 开始生成 "
        f"(refs={len(reference_images or [])}, prompt={len(base_prompt)} chars)"
    )

    start = time.time()
    sanitize_attempts: list[dict] = []
    current_prompt = base_prompt

    for attempt in range(0, SEEDREAM_MAX_SANITIZE_ATTEMPTS + 1):
        # attempt=0：原 prompt；attempt 1/2/3：sanitize 力度递增
        if attempt > 0:
            sanitized, replacements = sanitize_prompt(base_prompt, attempt=attempt)
            if sanitized == base_prompt:
                sanitize_attempts.append(
                    {"attempt": attempt, "replacements": [], "note": "no sanitize hit"}
                )
                logger.warning(
                    f"    [SeedreamGenerator] Shot {shot_id} sanitize attempt {attempt} 未命中任何关键词"
                )
            else:
                sanitize_attempts.append(
                    {"attempt": attempt, "replacements": replacements}
                )
                logger.warning(
                    f"    [SeedreamGenerator] Shot {shot_id} sanitize attempt {attempt}: "
                    f"{len(replacements)} replacements"
                )
            current_prompt = sanitized

        result = await asyncio.to_thread(
            _call_seedream_sync,
            current_prompt,
            reference_images or [],
            aspect_ratio,
            api_key,
        )

        if result.get("success"):
            pil_image: Image.Image = result["pil_image"]
            buf = BytesIO()
            pil_image.save(buf, format="PNG")
            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            total_time = round(time.time() - start, 2)
            logger.info(
                f"    [SeedreamGenerator] ✅ Shot {shot_id} 生成成功 "
                f"({pil_image.width}x{pil_image.height}, {total_time}s, sanitize_attempts={attempt})"
            )

            # TASK-PARALLEL-M1 ARCH-4: 写入 api_cost_logs INSERT 路径（Seedream 路径）
            # ARCH-4 round 2: 从 **_kwargs 提取 project_id（由 pipeline_orchestrator 透传）
            # Bug 4 fix: 用 await 代替 ensure_future，避免 event loop 关闭后仍有 pending task
            _db_project_id = _kwargs.get("project_id")
            try:
                from app.services.api_cost_logger import log_api_cost, SEEDREAM_COST_PER_IMAGE
                await log_api_cost(
                    project_id=_db_project_id,
                    stage=f"Stage 5 Shot {shot_id}",
                    model=SEEDREAM_MODEL,
                    cost_usd=SEEDREAM_COST_PER_IMAGE,
                    detail="Seedream generate_shot_image_seedream",
                )
            except Exception as _cost_log_err:
                logger.warning(f"[SeedreamGenerator] api_cost_log 写入失败（非阻塞）: {_cost_log_err}")

            return {
                "success": True,
                "image_data": image_b64,
                "pil_image": pil_image,
                "image_format": "png",
                "width": pil_image.width,
                "height": pil_image.height,
                "model_used": result.get("model_used", SEEDREAM_MODEL),
                "generation_time_seconds": total_time,
                "shot_id": shot_id,
                "seedream_info": {
                    "sanitize_attempts": sanitize_attempts,
                    "api_latency_sec": result.get("latency_sec"),
                    "size": result.get("size"),
                    "usage": result.get("usage"),
                    "http_retry_count": result.get("retry_count", 0),  # Bug 3: IncompleteRead 重试次数
                },
            }

        kind = result.get("error_kind")
        if kind == "missing_api_key":
            logger.error(
                f"    [SeedreamGenerator] Shot {shot_id} ARK_API_KEY 缺失，直接降级 NB2"
            )
            return await _run_fallback(
                fallback_callback,
                reason="missing_api_key",
                sanitize_attempts=sanitize_attempts,
            )

        if kind == "sensitive_content":
            # 继续下一轮 sanitize
            if attempt >= SEEDREAM_MAX_SANITIZE_ATTEMPTS:
                logger.error(
                    f"    [SeedreamGenerator] Shot {shot_id} sanitize {SEEDREAM_MAX_SANITIZE_ATTEMPTS} 次仍拦截，降级 NB2"
                )
                return await _run_fallback(
                    fallback_callback,
                    reason="sanitize_exhausted",
                    sanitize_attempts=sanitize_attempts,
                )
            continue

        # 非敏感内容错误（网络/5xx/格式等）— 直接降级（不消耗 sanitize 轮次）
        logger.error(
            f"    [SeedreamGenerator] Shot {shot_id} 非敏感内容错误（{kind}），降级 NB2: {result.get('error','')[:200]}"
        )
        return await _run_fallback(
            fallback_callback,
            reason=f"seedream_error:{kind}",
            sanitize_attempts=sanitize_attempts,
            upstream_error=result.get("error"),
        )

    # 理论上不会到这
    return await _run_fallback(
        fallback_callback,
        reason="unexpected_exit",
        sanitize_attempts=sanitize_attempts,
    )


async def _run_fallback(
    fallback_callback: Optional[Callable[[], Awaitable[dict]]],
    reason: str,
    sanitize_attempts: Optional[list[dict]] = None,
    upstream_error: Optional[str] = None,
) -> dict:
    """调用 fallback_callback（NB2 原逻辑），并在返回结果里记录 seedream_fallback 信息。"""
    if fallback_callback is None:
        logger.error(
            f"    [SeedreamGenerator] 无 fallback_callback（reason={reason}），返回失败"
        )
        return {
            "success": False,
            "error": f"Seedream failed and no fallback available ({reason})",
            "error_kind": "no_fallback",
            "seedream_info": {
                "sanitize_attempts": sanitize_attempts or [],
                "fallback_reason": reason,
                "upstream_error": upstream_error,
            },
        }
    try:
        fallback_result = await fallback_callback()
    except Exception as e:
        logger.exception(f"    [SeedreamGenerator] fallback_callback 抛异常: {e}")
        return {
            "success": False,
            "error": f"Seedream fallback raised: {e}",
            "error_kind": "fallback_exception",
            "seedream_info": {
                "sanitize_attempts": sanitize_attempts or [],
                "fallback_reason": reason,
                "upstream_error": upstream_error,
            },
        }
    if isinstance(fallback_result, dict):
        fallback_result.setdefault("seedream_info", {})
        fallback_result["seedream_info"].update(
            {
                "sanitize_attempts": sanitize_attempts or [],
                "fallback_reason": reason,
                "upstream_error": upstream_error,
                "used_fallback": True,
            }
        )
    return fallback_result
