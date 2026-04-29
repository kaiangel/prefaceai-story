"""
Seedream 4.0 vs NB2 POC 独立对比脚本（TASK-SEEDREAM-POC）

严格隔离:
- 不 import 任何 app/ 生产代码
- 不修改任何生产文件
- 只读 R8 历史数据 + 调火山方舟 Seedream 4.0 API
- 产物全部归档到 test_output/manualtest/seedream_vs_nb2_2026-04-24/

Founder 5 项决策:
1. 走火山方舟 ark.cn-beijing.volces.com（API 凭证: ARK_API_KEY）
2. 10 shots（R8 shot_01~10）
3. 评估: 中文文字 / 角色一致性 / 场景一致性 / 成本+速度
4. 参考图只传 fullbody（不传 portrait）
5. 严格隔离，不污染生产代码

Phase 4 更新 (2026-04-24):
- 新增 build_text_overlay_instruction() — 简化复写 image_generator.py:47 的 build_native_text_prompt()
  逻辑，把 R8 原 chinese_text 注入进 Seedream prompt，不依赖 app/ 任何模块
- Founder 要求：务必所有必要文字都渲染（thought/narration/dialogue 全要出）
- 文字内容和 NB2 一样（用 R8 原 chinese_text，不改字不改词）

参考文档:
- https://www.volcengine.com/docs/82379/1541523（图片生成 API）
- https://developer.volcengine.com/articles/7551036025242386495（Seedream 4.0 多图融合）
- Model ID: doubao-seedream-4-0-250828
- Endpoint: POST https://ark.cn-beijing.volces.com/api/v3/images/generations
- Auth: Authorization: Bearer $ARK_API_KEY
- image 参数: string | string[]，支持 URL 或 base64 data URI
- 最多 14 张参考图
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import certifi
from dotenv import load_dotenv


# ============ SSL + Env ============
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
R8_BASE = REPO_ROOT / "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614"
OUT_BASE = REPO_ROOT / "test_output/manualtest/seedream_vs_nb2_2026-04-24"

SEEDREAM_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
SEEDREAM_MODEL = "doubao-seedream-5-0-260128"
API_KEY = os.getenv("ARK_API_KEY", "").strip()

# 2:3 portrait, 2K - 匹配项目 DEC-010 抖音宽高比标准
# SIZE_MAP['2K:2:3'] = '1664x2496'（来自 Seedream MCP client 源码）
SEEDREAM_SIZE = "1664x2496"


# ============ Text Overlay Instruction Builder ============
# 简化复写 app/services/image_generator.py:47 build_native_text_prompt()
# 核心要求：不 import app/，只保留把中文字塞进 prompt 的核心逻辑
# 简化（不做）：speaker→char_id 映射、off_screen 判断、characters_in_scene 过滤

def _strip_speaker_label(text: str) -> str:
    """去除说话者标签，只保留台词内容。
    例: '阿朗：「爸爸！今天圩日」' → '爸爸！今天圩日'
    例: '（这孩子，脚下从不知道轻重。）' → '这孩子，脚下从不知道轻重。'
    """
    if not text:
        return text
    # 去除外层括号（thought/内心）
    t = text.strip()
    if t.startswith("（") and t.endswith("）"):
        t = t[1:-1].strip()
    # 去除说话者前缀 "XXX：「...」" → 「...」→ ...
    if "：「" in t or ":「" in t:
        sep = "：「" if "：「" in t else ":「"
        parts = t.split(sep, 1)
        if len(parts) == 2:
            content = parts[1]
            if content.endswith("」"):
                content = content[:-1]
            t = content
    # 去除"内心："前缀
    if t.startswith("内心："):
        t = t[3:]
    elif t.startswith("内心:"):
        t = t[3:]
    return t.strip()


def _infer_subtype(text: str) -> str:
    """从文本内容推断子类型（dialogue / thought / narration）。"""
    t = text.strip()
    # 括号包裹 → thought
    if t.startswith("（") and t.endswith("）"):
        return "thought"
    # 内心标注 → thought
    if "内心：" in t or "内心:" in t:
        return "thought"
    # 说话者：「台词」格式 → dialogue
    if "：「" in t or ":「" in t:
        return "dialogue"
    # 默认 narration
    return "narration"


def build_text_overlay_instruction(text_overlay: dict) -> str:
    """
    Phase 4: 简化复写 image_generator.py:47 build_native_text_prompt()。
    根据 text_overlay dict 生成 TEXT OVERLAY REQUIREMENT 指令块，注入 Seedream prompt。

    Args:
        text_overlay: shot['text_overlay'] — 包含 text_type / chinese_text / speaker_position 字段

    Returns:
        TEXT OVERLAY REQUIREMENT 指令字符串（多条用双换行拼接）。无文字时返回空字符串。

    覆盖范围（10 shots 的 text_type 分布）:
        - thought: shot_04/06/10（括号包裹内心独白，单条字符串）
        - dialogue: shot_01/02/05/09（单条或 || 分隔多条 / list 多条）
        - dialogue_with_thought: shot_03/07/08（混合 list，包含 dialogue + thought 子项）
        - narration: 本次 10 shots 无，但代码覆盖备用
    """
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    blocks: list[str] = []

    # ---- thought ----
    if text_type == "thought":
        # chinese_text 通常是单条字符串，形如 "（内心独白...）"
        if isinstance(chinese_text, list):
            texts = chinese_text
        else:
            texts = [chinese_text]
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

    # ---- narration ----
    elif text_type == "narration":
        if isinstance(chinese_text, list):
            texts = chinese_text
        else:
            texts = [chinese_text]
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

    # ---- dialogue ----
    elif text_type == "dialogue":
        # chinese_text 可以是单条字符串（|| 分隔多条）或 list
        if isinstance(chinese_text, list):
            texts = chinese_text
        elif isinstance(chinese_text, str):
            # 处理 || 分隔的多条对话
            texts = [t.strip() for t in chinese_text.split("||") if t.strip()]
        else:
            texts = [chinese_text]

        for i, txt in enumerate(texts):
            if isinstance(txt, dict):
                txt = txt.get("text", "")
            clean = _strip_speaker_label(txt)
            if not clean:
                continue
            bubble_label = f"({i + 1})" if len(texts) > 1 else ""
            blocks.append(
                f"Add Chinese speech bubble{bubble_label} in the scene with text '{clean}'. "
                f"Bubble style: clean white speech bubble with dark outline. "
                f"Position: near {position} side of the image.\n"
                f"CRITICAL: The Chinese text '{clean}' MUST be visible and legible in the speech bubble."
            )

    # ---- dialogue_with_thought / narration_with_thought / mixed types ----
    elif text_type in (
        "dialogue_with_thought",
        "narration_with_thought",
        "narration_with_dialogue",
        "dialogue_with_narration",
    ):
        if isinstance(chinese_text, list):
            texts = chinese_text
        else:
            texts = [chinese_text]

        for i, item in enumerate(texts):
            # 结构化格式: {"type": "dialogue|thought|narration", "text": "..."}
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

            if sub_type == "thought":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT{idx_label} - Inner monologue:\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered.\n"
                    f"CRITICAL: The Chinese text MUST be visible and legible in the final image."
                )
            elif sub_type == "narration":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT{idx_label} - Narration:\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered.\n"
                    f"CRITICAL: The Chinese text MUST be visible and legible in the final image."
                )
            else:  # dialogue
                blocks.append(
                    f"Add Chinese speech bubble{idx_label} in the scene with text '{clean}'. "
                    f"Bubble style: clean white speech bubble with dark outline. "
                    f"Position: near {position} side of the image.\n"
                    f"CRITICAL: The Chinese text '{clean}' MUST be visible and legible."
                )

    return "\n\n".join(blocks)


# ============ Text Presence Detection ============
def _detect_text_presence(img_path: Path) -> dict:
    """
    简单文字存在性检测：基于图像局部区域的 edge density / 像素方差分析。
    不依赖 pytesseract OCR，只用 PIL。

    策略：检查图像底部和顶部各 20% 的区域的像素标准差是否明显高于纯色区域。
    文字区域（黑底白字）通常有较高的局部对比度。

    Returns:
        dict with keys: has_text (bool), confidence (float 0-1), method (str)
    """
    try:
        from PIL import Image, ImageFilter
        import math

        img = Image.open(img_path).convert("L")  # 灰度
        w, h = img.size

        # 检查底部 20% 和顶部 20% 区域（文字覆盖条通常在这里）
        regions = {
            "bottom_20pct": img.crop((0, int(h * 0.80), w, h)),
            "top_20pct": img.crop((0, 0, w, int(h * 0.20))),
        }

        region_stats = {}
        for name, region in regions.items():
            pixels = list(region.getdata())
            n = len(pixels)
            if n == 0:
                continue
            mean = sum(pixels) / n
            variance = sum((p - mean) ** 2 for p in pixels) / n
            std = math.sqrt(variance)
            # 黑底白字区域：mean 偏低（暗），std 偏高（对比强）
            # 纯色背景：std 接近 0
            region_stats[name] = {"mean": round(mean, 1), "std": round(std, 1)}

        # 启发式：如果任一区域 std > 40，认为有文字
        max_std = max((s["std"] for s in region_stats.values()), default=0)
        has_text = max_std > 40
        confidence = min(max_std / 80, 1.0)  # 80 std 为满信心

        return {
            "has_text": has_text,
            "confidence": round(confidence, 2),
            "max_std": max_std,
            "region_stats": region_stats,
            "method": "edge_std_heuristic",
        }
    except Exception as e:
        return {"has_text": None, "error": str(e), "method": "failed"}


# ============ Helpers ============
def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _file_to_data_uri(path: Path, max_dim: int | None = None) -> str:
    """Convert local PNG to base64 data URI (Seedream image 参数支持).

    若 max_dim 指定，先降采样使最长边不超过该值（节省 payload 带宽）。
    """
    if max_dim is None:
        with path.open("rb") as f:
            raw = f.read()
    else:
        from io import BytesIO

        from PIL import Image

        img = Image.open(path)
        w, h = img.size
        longest = max(w, h)
        if longest > max_dim:
            scale = max_dim / longest
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:image/png;base64,{b64}"


# Payload 阈值：超过则降采样到 1024 px（Founder 指示的 edge case 处理）
PAYLOAD_DOWNSAMPLE_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10 MB


def _load_storyboard_shots_1_to_10() -> list[dict]:
    sb = _load_json(R8_BASE / "4_storyboard.json")
    shots = sb.get("shots", [])[:10]
    if len(shots) < 10:
        raise RuntimeError(f"R8 storyboard only has {len(shots)} shots, need 10")
    return shots


def _load_scene_to_location() -> dict[int, str]:
    """map scene_id -> location_id (from 3_screenplay.json)."""
    sp = _load_json(R8_BASE / "3_screenplay.json")
    return {s["scene_id"]: s.get("location_id", "") for s in sp.get("scenes", [])}


def _get_refs_for_shot(
    shot: dict,
    scene_to_loc: dict[int, str],
) -> tuple[list[Path], dict]:
    """
    根据 shot 返回要传入的参考图路径列表（fullbody only + 场景 anchor）。

    返回 (ref_paths, meta)。meta 含 selection 详情供日志用。
    """
    chars = (shot.get("character_direction") or {}).get("characters_visible") or []
    scene_id = shot.get("scene_id")
    location_id = scene_to_loc.get(scene_id, "")

    ref_paths: list[Path] = []
    meta: dict = {"characters": [], "scenes": [], "missing": []}

    # 1) 角色 fullbody（不传 portrait）
    for char_id in chars:
        # char_001 -> char_001_fullbody.png
        fb_path = R8_BASE / "character_refs" / f"{char_id}_fullbody.png"
        if fb_path.exists():
            ref_paths.append(fb_path)
            meta["characters"].append(fb_path.name)
        else:
            meta["missing"].append(fb_path.name)

    # 2) 场景 anchor（interior + exterior，如存在）
    if location_id:
        for suffix in ("interior", "exterior"):
            sp = R8_BASE / "scene_refs" / f"{location_id}_{suffix}_anchor.png"
            if sp.exists():
                ref_paths.append(sp)
                meta["scenes"].append(sp.name)

    return ref_paths, meta


# ============ Seedream API call ============
def _build_payload(prompt: str, ref_paths: list[Path], max_dim: int | None = None) -> tuple[dict, bytes]:
    """构建 payload。若 max_dim 指定则降采样参考图。"""
    ref_images = [_file_to_data_uri(p, max_dim=max_dim) for p in ref_paths]
    payload: dict = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "size": SEEDREAM_SIZE,
        "response_format": "b64_json",
        "watermark": False,
        "sequential_image_generation": "disabled",
    }
    if ref_images:
        payload["image"] = ref_images if len(ref_images) > 1 else ref_images[0]
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return payload, body


def call_seedream(prompt: str, ref_paths: list[Path], timeout_sec: int = 180) -> tuple[bytes | None, dict]:
    """
    调 Seedream 4.0 API。返回 (image_bytes, meta)。失败时 image_bytes=None, meta['error'] 有值。

    Edge-case 处理 (Founder 2026-04-24 指示):
    - payload 过大（>10MB）→ 降采样 fullbody 到 1024px 再重试
    - QPS 429 / 限流 → 指数退避 sleep 重试（最多 3 次）
    - 其它错误 → continue 不中断
    """
    if not API_KEY:
        return None, {"error": "ARK_API_KEY not set in .env", "success": False}

    meta: dict = {
        "success": False,
        "model": SEEDREAM_MODEL,
        "size": SEEDREAM_SIZE,
        "ref_count": len(ref_paths),
        "ref_files": [p.name for p in ref_paths],
        "prompt_chars": len(prompt),
        "attempts": [],
    }

    # 初次尝试：原图；如果 body 过大，直接降采样到 1024
    _, body = _build_payload(prompt, ref_paths, max_dim=None)
    max_dim_used: int | None = None
    if len(body) > PAYLOAD_DOWNSAMPLE_THRESHOLD_BYTES:
        max_dim_used = 1024
        _, body = _build_payload(prompt, ref_paths, max_dim=max_dim_used)
        meta["downsampled_to_px"] = max_dim_used
    meta["payload_size_bytes"] = len(body)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    max_retries = 3
    data: dict | None = None
    final_latency = 0.0

    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(SEEDREAM_ENDPOINT, data=body, headers=headers, method="POST")
        start = time.monotonic()
        attempt_info: dict = {"attempt": attempt, "payload_size_bytes": len(body)}
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw = resp.read()
                final_latency = round(time.monotonic() - start, 2)
                attempt_info["latency_sec"] = final_latency
                attempt_info["http_status"] = resp.status
                data = json.loads(raw.decode("utf-8"))
                meta["attempts"].append(attempt_info)
                break
        except urllib.error.HTTPError as e:
            final_latency = round(time.monotonic() - start, 2)
            attempt_info["latency_sec"] = final_latency
            attempt_info["http_status"] = e.code
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                err_body = ""
            attempt_info["error"] = f"HTTPError {e.code}: {err_body[:500]}"
            meta["attempts"].append(attempt_info)

            # payload too large → 降采样再试
            if e.code in (413, 400) and "too large" in err_body.lower() and max_dim_used != 512:
                next_dim = 1024 if max_dim_used is None else 512
                _, body = _build_payload(prompt, ref_paths, max_dim=next_dim)
                max_dim_used = next_dim
                meta["downsampled_to_px"] = next_dim
                meta["payload_size_bytes"] = len(body)
                print(f"  ⚠️  payload too large, downsampled to {next_dim}px, retrying...")
                continue
            # 429 / 5xx → 指数退避
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                backoff = 2 ** attempt + 1  # 3, 5, 9 sec
                print(f"  ⚠️  HTTP {e.code} rate-limit/server error, sleeping {backoff}s then retry {attempt + 1}/{max_retries}")
                time.sleep(backoff)
                continue
            # 不可恢复
            meta["latency_sec"] = final_latency
            meta["http_status"] = e.code
            meta["error"] = attempt_info["error"]
            return None, meta
        except Exception as e:
            final_latency = round(time.monotonic() - start, 2)
            attempt_info["latency_sec"] = final_latency
            attempt_info["error"] = f"{type(e).__name__}: {e}"
            meta["attempts"].append(attempt_info)
            if attempt < max_retries:
                backoff = 2 ** attempt
                print(f"  ⚠️  {type(e).__name__}, sleeping {backoff}s then retry {attempt + 1}/{max_retries}")
                time.sleep(backoff)
                continue
            meta["latency_sec"] = final_latency
            meta["error"] = attempt_info["error"]
            meta["traceback"] = traceback.format_exc()[:2000]
            return None, meta

    meta["latency_sec"] = final_latency
    meta["http_status"] = 200
    if data is None:
        meta["error"] = "All retries exhausted, no response"
        return None, meta

    # 响应解析
    meta["raw_response_keys"] = list(data.keys())
    if data.get("error"):
        meta["error"] = f"API error: {data['error']}"
        return None, meta

    data_list = data.get("data", [])
    if not data_list:
        meta["error"] = f"Empty data array in response: {str(data)[:500]}"
        return None, meta

    first = data_list[0]
    meta["response_size"] = first.get("size")
    meta["usage"] = data.get("usage")  # 若 API 返回 token / cost 信息

    # b64_json 优先
    if "b64_json" in first and first["b64_json"]:
        img_bytes = base64.b64decode(first["b64_json"])
        meta["response_format"] = "b64_json"
    elif "url" in first and first["url"]:
        img_url = first["url"]
        meta["response_format"] = "url"
        meta["image_url"] = img_url
        # 下载
        try:
            with urllib.request.urlopen(img_url, timeout=60) as r:
                img_bytes = r.read()
        except Exception as e:
            meta["error"] = f"Failed to download image URL: {e}"
            return None, meta
    else:
        meta["error"] = f"Response has neither b64_json nor url: {first}"
        return None, meta

    meta["success"] = True
    meta["image_size_bytes"] = len(img_bytes)
    return img_bytes, meta


# ============ comparison.html ============
# shot_04 原 prompt（来自 R8 storyboard）和 sanitized prompt（火山方舟内容审查替换后）
# 保留 Phase 3a 的 ⚠️ 标记，不因 Phase 4 重跑而丢失
SHOT04_ORIGINAL_PROMPT_FRAGMENT = (
    "High-angle medium shot looking down at an <span class=\"highlight-diff\">elderly man</span> walking last "
    "along a winding gravel mountain path in early autumn morning mist."
)
SHOT04_SANITIZED_PROMPT_FRAGMENT = (
    "High-angle medium shot looking down at an <span class=\"highlight-diff\">older man</span> walking last "
    "along a winding gravel mountain path in early autumn morning mist."
)


def render_comparison_html(shots_data: list[dict], out_path: Path) -> None:
    rows = []
    for entry in shots_data:
        sid = entry["shot_id"]
        prompt_preview = (entry.get("image_prompt") or "")[:300].replace("<", "&lt;")
        text_overlay = entry.get("text_overlay", {})
        chinese_text_raw = text_overlay.get("chinese_text") or []
        if isinstance(chinese_text_raw, str):
            chinese_text_raw = [chinese_text_raw]
        text_preview = "<br>".join(
            (t if isinstance(t, str) else str(t)).replace("<", "&lt;") for t in chinese_text_raw
        )
        text_type = text_overlay.get("text_type", "")

        latency = entry.get("latency_sec", "-")
        status = entry.get("status", "")

        seedream_label = "Seedream 5.0-lite (Phase 4, 含文字指令)"
        if sid == 4:
            seedream_label = "Seedream 5.0-lite ⚠️ sanitized prompt"

        seedream_cell = (
            f'<img src="seedream/shot_{sid:02d}.png" alt="seedream shot {sid}">'
            if entry.get("seedream_ok")
            else f'<div class="error">FAILED<br>{(entry.get("error") or "")[:200]}</div>'
        )
        nb2_cell = (
            f'<img src="nb2_baseline/shot_{sid:02d}.png" alt="nb2 baseline shot {sid}">'
            if entry.get("nb2_ok")
            else '<div class="error">NB2 baseline missing</div>'
        )

        chars = entry.get("characters", [])
        scenes = entry.get("scenes", [])
        ref_summary = f'chars: {", ".join(chars) or "-"}<br>scenes: {", ".join(scenes) or "-"}'

        # shot_04 special markup — Phase 3a ⚠️ 标记 (preserved in Phase 4 re-run)
        shot04_badge = ""
        shot04_prompt_compare = ""
        if sid == 4:
            shot04_badge = (
                '<div class="sanitized-badge">&#9888;&#65039; Prompt Sanitized — '
                '火山方舟内容审查拦截，Seedream 实际用的 prompt 与 NB2 baseline 不同</div>'
            )
            shot04_prompt_compare = f"""
      <div class="prompt-comparison">
        <div class="prompt-box prompt-box-original">
          <div class="prompt-box-label">原 prompt（NB2 baseline 用的 / R8 storyboard 原文）</div>
          {SHOT04_ORIGINAL_PROMPT_FRAGMENT} ... carrying a <span class="highlight-diff">faint but legible furrow of quiet worry</span>, lips pressed together in suppressed thought.
        </div>
        <div class="prompt-box prompt-box-sanitized">
          <div class="prompt-box-label">Sanitized prompt（Seedream 实际送入 API 的）</div>
          {SHOT04_SANITIZED_PROMPT_FRAGMENT} ... carrying a <span class="highlight-diff">sense of quiet contemplation</span>, lips pressed together in suppressed thought.
          <br><br><small style="color:#999;">&#9432; 拦截原因: 火山方舟 InputTextSensitiveContentDetected — "elderly" + "worry" 触发内容审查。Agent 将 "elderly man" → "older man"，"faint but legible furrow of quiet worry" → "sense of quiet contemplation" 后通过。</small>
        </div>
      </div>"""

        rows.append(
            f"""
<div class="row">
  <div class="meta">
    <h3>Shot {sid:02d} <span class="status-{status}">[{status}]</span></h3>
    {shot04_badge}
    <p><b>latency:</b> {latency}s &nbsp; <b>refs:</b> {entry.get("ref_count", 0)}</p>
    <p class="refs">{ref_summary}</p>
    <p class="prompt"><b>prompt:</b> {prompt_preview}...</p>
    <p class="text-overlay"><b>text [{text_type}]:</b><br>{text_preview}</p>
    {shot04_prompt_compare}
  </div>
  <div class="imgs">
    <div class="col">
      <div class="label">{seedream_label}</div>
      {seedream_cell}
    </div>
    <div class="col">
      <div class="label">NB2 (R8 baseline)</div>
      {nb2_cell}
    </div>
  </div>
</div>
"""
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Seedream 5.0-lite vs NB2 — R8 shot_01~10 (Phase 4 重跑)</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 24px; background: #f6f7f9; color: #222; }}
  h1 {{ margin-bottom: 4px; }}
  .row {{ background: white; margin: 16px 0; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .meta {{ font-size: 13px; line-height: 1.5; margin-bottom: 12px; }}
  .meta h3 {{ margin: 0 0 6px 0; }}
  .meta p {{ margin: 4px 0; }}
  .prompt {{ color: #555; }}
  .text-overlay {{ color: #306; background: #fafafa; padding: 6px; border-left: 3px solid #9af; }}
  .refs {{ color: #080; font-size: 12px; }}
  .imgs {{ display: flex; gap: 16px; }}
  .col {{ flex: 1; text-align: center; }}
  .col img {{ max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 4px; }}
  .label {{ font-weight: bold; margin-bottom: 6px; color: #36c; }}
  .error {{ background: #fee; color: #a00; padding: 24px; border: 1px dashed #c00; border-radius: 4px; }}
  .status-success {{ color: #090; }}
  .status-failed {{ color: #c00; }}
  /* shot_04 sanitized prompt warning styles — Phase 3a (preserved in Phase 4) */
  .sanitized-badge {{
    display: inline-block;
    background: #d32f2f;
    color: #fff;
    font-weight: bold;
    font-size: 13px;
    padding: 4px 12px;
    border-radius: 4px;
    margin: 8px 0 10px 0;
  }}
  .prompt-comparison {{
    display: flex;
    gap: 12px;
    margin-top: 8px;
  }}
  .prompt-box {{
    flex: 1;
    padding: 8px 10px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.6;
  }}
  .prompt-box-original {{
    background: #fff8e1;
    border: 1px solid #f9a825;
  }}
  .prompt-box-sanitized {{
    background: #fbe9e7;
    border: 1px solid #e64a19;
  }}
  .prompt-box-label {{
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .prompt-box-original .prompt-box-label {{ color: #e65100; }}
  .prompt-box-sanitized .prompt-box-label {{ color: #b71c1c; }}
  .highlight-diff {{
    background: #ffe082;
    border-radius: 2px;
    padding: 0 2px;
  }}
  .shot04-note {{
    background: #fff3e0;
    border: 1px solid #fb8c00;
    border-radius: 6px;
    padding: 10px 16px;
    margin: 16px 0;
    font-size: 13px;
  }}
</style>
</head>
<body>
<h1>Seedream 5.0-lite vs NB2 — R8 shot_01~10 (Phase 4 重跑，含文字指令)</h1>
<p>
  Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
  Left column = Seedream 5.0-lite (doubao-seedream-5-0-260128, 2K 2:3 1664x2496, fullbody refs + text_overlay 注入, Phase 4)<br>
  Right column = R8 NB2 baseline (Gemini 3.1 Flash Image (NB2), 2:3, 2026-03-16 生成)
</p>
{"".join(rows)}
<div class="shot04-note">
  ⚠️ <b>shot_04 评分说明</b>: shot_04 因内容审查用了 sanitized prompt（"elderly" → "older"，"worry" → "contemplation"），
  不计入公平对比均分。但 Seedream 图本身的中文文字渲染质量仍按原维度打分。
  详见 SEEDREAM_VS_NB2_POC_REPORT.md Phase 3b。
</div>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")


# ============ main ============
def main() -> int:
    print(f"[seedream-poc] output dir: {OUT_BASE}")
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    (OUT_BASE / "seedream").mkdir(exist_ok=True)
    (OUT_BASE / "nb2_baseline").mkdir(exist_ok=True)
    (OUT_BASE / "logs").mkdir(exist_ok=True)

    if not API_KEY:
        print("[seedream-poc] ❌ ARK_API_KEY not found in .env — aborting")
        return 2

    shots = _load_storyboard_shots_1_to_10()
    scene_to_loc = _load_scene_to_location()

    api_logs: list[dict] = []
    shots_data: list[dict] = []
    total_ok = 0
    total_latency = 0.0

    # Per-shot text render status tracking (for README and Founder report)
    # Values: "✅" / "⚠️" / "❌" / "N/A"
    text_render_status: list[dict] = []

    for idx, shot in enumerate(shots, start=1):
        sid = shot["shot_id"]
        image_prompt = shot.get("image_prompt") or ""
        text_overlay = shot.get("text_overlay") or {}
        text_type = text_overlay.get("text_type", "none")
        chinese_text = text_overlay.get("chinese_text", "")
        ref_paths, ref_meta = _get_refs_for_shot(shot, scene_to_loc)

        # --- Phase 4: Build text overlay instruction and inject into prompt ---
        text_instruction = build_text_overlay_instruction(text_overlay)

        # shot_04 sanitize: 火山方舟 InputTextSensitiveContentDetected 拦截 "elderly + worry"
        # Phase 3a 已在 comparison.html 加 ⚠️ 标记，此处保留 sanitize 逻辑
        prompt = image_prompt
        if sid == 4:
            prompt = prompt.replace("elderly man", "older man")
            prompt = prompt.replace("elderly", "older")
            prompt = prompt.replace("faint but legible furrow of quiet worry", "sense of quiet contemplation")
            print(f"  ⚠️  shot_04: sanitized prompt (elderly→older, worry→contemplation) — 保持 Phase 3a 标记")

        # Append text overlay instruction
        if text_instruction:
            prompt = prompt + "\n\n" + text_instruction
            print(f"  📝 text_overlay injected: {text_type} | {str(chinese_text)[:80]}...")
        else:
            print(f"  📝 text_overlay: none (text_type={text_type})")

        print(f"\n[seedream-poc] === shot {sid:02d} ({idx}/10) ===")
        print(f"  refs: {len(ref_paths)} ({ref_meta['characters']} + {ref_meta['scenes']})")
        if ref_meta["missing"]:
            print(f"  ⚠️  missing refs: {ref_meta['missing']}")
        print(f"  prompt length: {len(prompt)} chars")

        # --- First attempt ---
        img_bytes, meta = call_seedream(prompt, ref_paths)
        meta["shot_id"] = sid
        meta["ref_characters"] = ref_meta["characters"]
        meta["ref_scenes"] = ref_meta["scenes"]
        meta["ref_missing"] = ref_meta["missing"]
        meta["text_overlay_injected"] = bool(text_instruction)

        out_img_path = OUT_BASE / "seedream" / f"shot_{sid:02d}.png"

        if img_bytes:
            out_img_path.write_bytes(img_bytes)
            print(f"  ✅ saved {out_img_path.name} ({len(img_bytes)//1024} KB, {meta.get('latency_sec')}s)")

            # --- Text presence detection ---
            text_detect = _detect_text_presence(out_img_path)
            meta["text_detection"] = text_detect
            has_text = text_detect.get("has_text")
            confidence = text_detect.get("confidence", 0)

            # If text_type is not 'none' but no text detected → auto-retry once with stronger instruction
            if text_instruction and has_text is False and confidence < 0.3:
                print(f"  ⚠️  text not detected (std={text_detect.get('max_std', 0):.1f}), retrying with stronger instruction...")
                stronger_prompt = prompt + "\n\nCRITICAL REQUIREMENT: ALL Chinese text specified above MUST appear visibly in the final image. Do not omit any text overlay or speech bubble."
                retry_bytes, retry_meta = call_seedream(stronger_prompt, ref_paths)
                retry_meta["shot_id"] = sid
                retry_meta["is_retry"] = True
                if retry_bytes:
                    out_img_path.write_bytes(retry_bytes)
                    img_bytes = retry_bytes
                    retry_text_detect = _detect_text_presence(out_img_path)
                    retry_meta["text_detection"] = retry_text_detect
                    meta["retry"] = retry_meta
                    meta["retry_text_detection"] = retry_text_detect
                    has_text = retry_text_detect.get("has_text")
                    confidence = retry_text_detect.get("confidence", 0)
                    print(f"  🔄 retry: {'✅ text found' if has_text else '❌ still no text'} (std={retry_text_detect.get('max_std',0):.1f})")
                else:
                    print(f"  ❌ retry also failed: {retry_meta.get('error','')[:200]}")
                    meta["retry"] = retry_meta

            # Determine text render status
            if text_type == "none":
                t_status = "N/A"
                t_symbol = "N/A"
            elif has_text is True and confidence >= 0.5:
                t_status = "✅"
                t_symbol = "✅"
            elif has_text is True and confidence >= 0.2:
                t_status = "⚠️"
                t_symbol = "⚠️"
            else:
                t_status = "❌"
                t_symbol = "❌"

            meta["text_render_status"] = t_status
            total_ok += 1
            total_latency += meta.get("latency_sec", 0)
        else:
            print(f"  ❌ failed: {meta.get('error', 'unknown')[:300]}")
            t_symbol = "❌ (gen failed)"
            meta["text_render_status"] = "❌ (gen failed)"

        # Summarize text render status per shot
        expected_text = ""
        if isinstance(chinese_text, list):
            expected_text = " / ".join(str(x) for x in chinese_text[:2])
        else:
            expected_text = str(chinese_text)[:80]
        text_render_status.append({
            "shot_id": sid,
            "text_type": text_type,
            "expected": expected_text,
            "status": t_symbol,
            "seedream_ok": bool(img_bytes),
        })

        entry = {
            "shot_id": sid,
            "image_prompt": image_prompt,  # original, not sanitized, for HTML display
            "prompt_with_text": prompt,
            "text_overlay": text_overlay,
            "ref_count": len(ref_paths),
            "characters": ref_meta["characters"],
            "scenes": ref_meta["scenes"],
            "latency_sec": meta.get("latency_sec"),
            "status": "success" if meta.get("success") else "failed",
            "error": meta.get("error"),
            "seedream_ok": bool(img_bytes),
            "nb2_ok": False,
        }

        # 复制 NB2 baseline
        nb2_src = R8_BASE / "images" / f"shot_{sid:02d}.png"
        nb2_dst = OUT_BASE / "nb2_baseline" / f"shot_{sid:02d}.png"
        if nb2_src.exists():
            nb2_dst.write_bytes(nb2_src.read_bytes())
            entry["nb2_ok"] = True
        else:
            print(f"  ⚠️  R8 NB2 baseline missing: {nb2_src.name}")

        api_logs.append(meta)
        shots_data.append(entry)

        # 软节流：每 shot 之间 sleep 1 秒，降低 QPS 限流风险
        if idx < len(shots):
            time.sleep(1.0)

    # ==== 写 logs ====
    logs_path = OUT_BASE / "logs" / "seedream_api_logs.json"
    logs_path.write_text(
        json.dumps(
            {
                "run_time": datetime.now().isoformat(),
                "model": SEEDREAM_MODEL,
                "endpoint": SEEDREAM_ENDPOINT,
                "size": SEEDREAM_SIZE,
                "total_shots": len(shots),
                "success_count": total_ok,
                "total_latency_sec": round(total_latency, 2),
                "avg_latency_sec": round(total_latency / max(total_ok, 1), 2),
                "shots": api_logs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[seedream-poc] 📝 API logs: {logs_path}")

    # ==== 写 comparison.html ====
    html_path = OUT_BASE / "comparison.html"
    render_comparison_html(shots_data, html_path)
    print(f"[seedream-poc] 🖼  comparison.html: {html_path}")

    # ==== 写 README.md ====
    # 火山方舟 Seedream 5.0-lite 官方价格：¥0.22/张（PM 研究结论，~$0.030，比 4.0 贵 10%）
    # 按 $0.030/张 估算（2K 输出）
    est_cost_per_img = 0.030
    est_total_cost = total_ok * est_cost_per_img

    # Build per-shot text render status table
    text_status_rows = []
    for ts in text_render_status:
        text_status_rows.append(
            f"| shot_{ts['shot_id']:02d} | {ts['text_type']:<24} | {ts['expected'][:50]:<50} | {ts['status']} |"
        )
    text_status_table = "\n".join(text_status_rows)

    rendered_count = sum(1 for ts in text_render_status if ts["status"] in ("✅", "⚠️"))
    total_text_shots = sum(1 for ts in text_render_status if ts["text_type"] != "none")

    readme = f"""# Seedream 5.0-lite vs NB2 POC — R8 shot_01~10

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Task**: TASK-SEEDREAM-POC（Founder 2026-04-24 决策）
**Phase 4 重跑**: 含 text_overlay 注入（build_text_overlay_instruction）

## 运行摘要

| 指标 | 值 |
|------|---|
| 总 shots | 10 |
| Seedream 成功 | {total_ok}/10 |
| 总 API 延迟 | {round(total_latency, 1)}s |
| 平均每张 | {round(total_latency / max(total_ok, 1), 2)}s |
| 估算总成本 | ~¥{round(total_ok * 0.22, 2)} (~${round(est_total_cost, 3)}) (¥0.22/张 × {total_ok}) |
| 文字渲染 shots | {rendered_count}/{total_text_shots} 有文字（启发式检测，Founder 肉眼确认为准）|

## Shot 文字渲染状态（Phase 4 验收）

> ✅ = 启发式检测到文字区域（std > 40）| ⚠️ = 弱信号（std 20-40）| ❌ = 未检测到 | N/A = 无文字要求
> 最终以 Founder 肉眼确认为准，text-only agent 视觉能力有限

| Shot | text_type | expected chinese_text | rendered |
|------|-----------|-----------------------|----------|
{text_status_table}

> ⚠️ shot_04 备注：prompt 已 sanitize（"elderly" → "older", "worry" → "contemplation"），火山方舟内容审查要求。

## API 调用配置

- **Endpoint**: `POST {SEEDREAM_ENDPOINT}`
- **Model**: `{SEEDREAM_MODEL}`（Seedream 5.0-lite，2026-01-28 build）
- **Auth**: `Authorization: Bearer $ARK_API_KEY`
- **Size**: `{SEEDREAM_SIZE}`（2K, 2:3 portrait 抖音适配）
- **Response format**: `b64_json`（无 URL 过期风险）
- **Watermark**: `false`
- **sequential_image_generation**: `disabled`

## Phase 4 改动说明

- 新增 `build_text_overlay_instruction(text_overlay)` 函数（简化复写 `image_generator.py:47`）
- 每个 shot 的 prompt = `image_prompt` + `\\n\\n` + text_overlay 指令
- 所有文字内容来自 R8 原 chinese_text（不改字不改词）
- 文字存在性检测：PIL 灰度 edge std 启发式（底/顶各 20% 区域，std > 40 认定有文字）
- 自动重试：若首轮未检测到文字，加强指令后重试 1 次（每 shot 最多 2 次 API 调用）
- shot_04 保留 Phase 3a 的 sanitize 处理 + comparison.html ⚠️ 标记

## 参考图策略（Founder 决策 4）

- **只传 fullbody**，不传 portrait
- 角色参考图: `char_NNN_fullbody.png`
- 场景参考图: `<location_id>_interior_anchor.png` + `<location_id>_exterior_anchor.png`
- **多角色参考图机制**: 通过 `image` 参数传 **字符串数组**（base64 data URI），即：
  ```json
  {{
    "image": ["data:image/png;base64,...", "data:image/png;base64,...", ...]
  }}
  ```
  单张时降级为 string。最多支持 14 张。

## 产物结构

```
seedream_vs_nb2_2026-04-24/
├── seedream/              # Seedream 5.0-lite 新生图（{total_ok} 张，Phase 4 重跑，含文字指令）
│   └── shot_01.png ... shot_10.png
├── nb2_baseline/          # R8 NB2 历史图（复制，10 张）
│   └── shot_01.png ... shot_10.png
├── logs/
│   └── seedream_api_logs.json   # 每 shot 的 latency / size / error / text_detection
├── comparison.html        # 左 Seedream（Phase 4）/ 右 NB2 横向对比，shot_04 ⚠️ 标记保留
└── README.md              # 本文件
```

## 使用

```bash
python3 scripts/test_seedream_vs_nb2.py
open test_output/manualtest/seedream_vs_nb2_2026-04-24/comparison.html
```

## 隔离验证

- ✅ 脚本不 import 任何 `app/` 模块
- ✅ 未修改任何生产代码（`git diff app/` 应为空）
- ✅ 只读 R8 历史数据 + .env 凭证
- ✅ 产物全部落在 `test_output/manualtest/` 下
"""
    (OUT_BASE / "README.md").write_text(readme, encoding="utf-8")
    print(f"[seedream-poc] 📄 README.md: {OUT_BASE / 'README.md'}")

    est_cny = round(total_ok * 0.22, 2)
    print(
        f"\n[seedream-poc] DONE — {total_ok}/10 success, "
        f"{round(total_latency, 1)}s total, est ¥{est_cny} (~${round(est_total_cost, 3)})"
    )
    print(f"[seedream-poc] Text render: {rendered_count}/{total_text_shots} shots with detectable text")

    # Print per-shot text status summary
    print("\n[seedream-poc] Text render status per shot:")
    for ts in text_render_status:
        print(f"  shot_{ts['shot_id']:02d} | {ts['text_type']:<24} | {ts['status']}")

    return 0 if total_ok >= 8 else 1


if __name__ == "__main__":
    sys.exit(main())
