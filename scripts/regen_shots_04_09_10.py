"""
Phase 4-supplementary: Regen shots 04, 09, 10 with Chinese text overlay.

One-off script. Does NOT import app/. Copies helper code from test_seedream_vs_nb2.py.
Overwrites seedream/shot_04.png, shot_09.png, shot_10.png.
Appends 3 Phase 4-supplementary records to logs/seedream_api_logs.json.
Updates README.md text render table.
Updates comparison.html (regenerates with full 10-shot data).

Constraints:
- shot_04: sanitize image_prompt (elderly->older, worry->contemplation)
- shot_04 chinese_text (R8 原文): （老伴昨夜又咳了半宿，不知那秋梨膏管不管用。）
- shot_09 chinese_text: 阿朗：「再来一下！再来！」
- shot_10 chinese_text: （一、二、三……怎么数来数去只有三个人？阿朗呢——阿朗在哪里？）
"""
from __future__ import annotations

import base64
import json
import math
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

ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
R8_BASE = REPO_ROOT / "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614"
OUT_BASE = REPO_ROOT / "test_output/manualtest/seedream_vs_nb2_2026-04-24"

SEEDREAM_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
SEEDREAM_MODEL = "doubao-seedream-5-0-260128"
API_KEY = os.getenv("ARK_API_KEY", "").strip()
SEEDREAM_SIZE = "1664x2496"

PAYLOAD_DOWNSAMPLE_THRESHOLD_BYTES = 10 * 1024 * 1024


# ============ Exact shot data (from R8 storyboard + PM task spec) ============
SHOTS_TO_REGEN = [
    {
        "shot_id": 4,
        "scene_id": 1,
        "location_id": "mountain_path_morning",
        "chars_visible": ["char_001"],
        "image_prompt": (
            "High-angle medium shot looking down at an elderly man walking last along a winding gravel "
            "mountain path in early autumn morning mist. EXACTLY 1 character visible. char_001 wears a "
            "loose-fit faded muted sage-green mandarin-collar linen shirt with small cloth buttons, long "
            "sleeves rolled once to mid-forearm, and straight-cut slate gray linen trousers lightly creased "
            "at the knees. Even viewed from above, his sage-green linen shirt remains clearly identifiable. "
            "He walks with measured unhurried steps, his right arm looped through the handle of a small "
            "round bamboo basket lined with plain brown paper, the basket resting against his hip. His head "
            "is tilted slightly upward, eyes directed ahead down the path — gaze tracking the distant smaller "
            "figures of his family walking ahead in the mist — his brow carrying a faint but legible furrow "
            "of quiet worry, lips pressed together in suppressed thought. Rough gravel and dry grass fill the "
            "near foreground. The foggy path stretches ahead with blurred family silhouettes in the far "
            "mid-distance."
        ),
        "sanitize": True,  # elderly->older, worry->contemplation
        "text_overlay": {
            "text_type": "thought",
            "chinese_text": "（老伴昨夜又咳了半宿，不知那秋梨膏管不管用。）",
            "speaker_position": "bottom",
        },
    },
    {
        "shot_id": 9,
        "scene_id": 2,
        "location_id": "blacksmith_shop",
        "chars_visible": ["char_004"],
        "image_prompt": (
            "Close-up, eye level, left-third composition. Ah-Lang's face (char_004) — a young boy in an "
            "amber-orange rabbit-motif T-shirt — caught in the instant of maximum spark-flash. His entire "
            "face is lit in brilliant molten gold from the right, every detail of his expression illuminated: "
            "he has jerked his head back half an inch in a startled recoil, chin tucking, eyes squeezing shut "
            "for a split second — but already his body is surging forward again, leaning back in toward the "
            "bamboo fence. His lips have lost the fight: the corners pull wide and upward into an "
            "uncontrollable grin, cheeks round and high, the joy entirely involuntary and impossible to "
            "suppress. His small hands remain locked on the bamboo rails at the bottom of frame. In the "
            "background soft-focus upper right, the largest golden spark-bloom spreads like an exploding star "
            "against the deep orange furnace mouth. A single bamboo rail blurs across the bottom edge. The "
            "rest of the frame falls into warm amber shadow, the spark-light being the sole key source."
        ),
        "sanitize": False,
        "text_overlay": {
            "text_type": "dialogue",
            "chinese_text": ["阿朗：「再来一下！再来！」"],
            "speaker_position": "left",
        },
    },
    {
        "shot_id": 10,
        "scene_id": 3,
        "location_id": "stone_bridge",
        "chars_visible": ["char_003"],
        "image_prompt": (
            "Low-angle medium shot of a woman standing frozen at the center of an ancient mossy stone bridge "
            "in early autumn mountain fog. EXACTLY 1 character in this scene. She wears a soft golden harvest "
            "yellow cotton blouse with short flutter sleeves and a calf-length off-white A-line skirt with "
            "faint muted terracotta floral print, the hem catching faint morning breeze. Her body has turned "
            "half-around mid-step, her left foot still pointed forward while her torso twists back sharply — "
            "caught in the act of a sudden, alarmed head-count. Her eyes are wide and scanning frantically to "
            "her left and right behind her, pupils darting as her gaze sweeps the empty bridge in search of a "
            "missing figure. Her lips are slightly parted, her pale face drained of colour. Her right hand "
            "grips the short woven straw tote bag handle so tightly her knuckles show white. A blurred mossy "
            "stone railing anchors the near-left foreground; cold pale fog swallows the far bridge end behind "
            "her. Soft cool morning light. Mood: quiet dread breaking open."
        ),
        "sanitize": False,
        "text_overlay": {
            "text_type": "thought",
            "chinese_text": "（一、二、三……怎么数来数去只有三个人？阿朗呢——阿朗在哪里？）",
            "speaker_position": "bottom",
        },
    },
]


# ============ Text overlay helpers (copied from test_seedream_vs_nb2.py) ============
def _strip_speaker_label(text: str) -> str:
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
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    blocks: list[str] = []

    if text_type == "thought":
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
            bubble_label = f"({i + 1})" if len(texts) > 1 else ""
            blocks.append(
                f"Add Chinese speech bubble{bubble_label} in the scene with text '{clean}'. "
                f"Bubble style: clean white speech bubble with dark outline. "
                f"Position: near {position} side of the image.\n"
                f"CRITICAL: The Chinese text '{clean}' MUST be visible and legible in the speech bubble."
            )

    return "\n\n".join(blocks)


# ============ Text presence detection ============
def _detect_text_presence(img_path: Path) -> dict:
    try:
        from PIL import Image

        img = Image.open(img_path).convert("L")
        w, h = img.size

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
            region_stats[name] = {"mean": round(mean, 1), "std": round(std, 1)}

        max_std = max((s["std"] for s in region_stats.values()), default=0)
        has_text = max_std > 40
        confidence = min(max_std / 80, 1.0)

        return {
            "has_text": has_text,
            "confidence": round(confidence, 2),
            "max_std": max_std,
            "region_stats": region_stats,
            "method": "edge_std_heuristic",
        }
    except Exception as e:
        return {"has_text": None, "error": str(e), "method": "failed"}


# ============ API helpers ============
def _file_to_data_uri(path: Path, max_dim: int | None = None) -> str:
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


def _build_payload(prompt: str, ref_paths: list[Path], max_dim: int | None = None) -> tuple[dict, bytes]:
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

            if e.code in (413, 400) and "too large" in err_body.lower() and max_dim_used != 512:
                next_dim = 1024 if max_dim_used is None else 512
                _, body = _build_payload(prompt, ref_paths, max_dim=next_dim)
                max_dim_used = next_dim
                meta["downsampled_to_px"] = next_dim
                meta["payload_size_bytes"] = len(body)
                print(f"  payload too large, downsampled to {next_dim}px, retrying...")
                continue
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                backoff = 2 ** attempt + 1
                print(f"  HTTP {e.code} rate-limit/server error, sleeping {backoff}s then retry {attempt + 1}/{max_retries}")
                time.sleep(backoff)
                continue
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
                print(f"  {type(e).__name__}, sleeping {backoff}s then retry {attempt + 1}/{max_retries}")
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
    meta["usage"] = data.get("usage")

    if "b64_json" in first and first["b64_json"]:
        img_bytes = base64.b64decode(first["b64_json"])
        meta["response_format"] = "b64_json"
    elif "url" in first and first["url"]:
        img_url = first["url"]
        meta["response_format"] = "url"
        meta["image_url"] = img_url
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


def get_ref_paths(shot_info: dict) -> tuple[list[Path], dict]:
    chars = shot_info["chars_visible"]
    location_id = shot_info["location_id"]

    ref_paths: list[Path] = []
    meta: dict = {"characters": [], "scenes": [], "missing": []}

    for char_id in chars:
        fb_path = R8_BASE / "character_refs" / f"{char_id}_fullbody.png"
        if fb_path.exists():
            ref_paths.append(fb_path)
            meta["characters"].append(fb_path.name)
        else:
            meta["missing"].append(fb_path.name)

    if location_id:
        for suffix in ("interior", "exterior"):
            sp = R8_BASE / "scene_refs" / f"{location_id}_{suffix}_anchor.png"
            if sp.exists():
                ref_paths.append(sp)
                meta["scenes"].append(sp.name)

    return ref_paths, meta


def main() -> int:
    print(f"[regen-supp] Phase 4-supplementary: regenerating shots 04, 09, 10")
    print(f"[regen-supp] output dir: {OUT_BASE}")

    if not API_KEY:
        print("[regen-supp] ARK_API_KEY not found in .env — aborting")
        return 2

    new_logs: list[dict] = []
    results: list[dict] = []
    total_latency = 0.0
    total_ok = 0
    run_time = datetime.now()

    # Count consecutive shot_04 censorship blocks
    shot04_censor_count = 0

    for shot_info in SHOTS_TO_REGEN:
        sid = shot_info["shot_id"]
        print(f"\n[regen-supp] === shot_{sid:02d} ===")

        image_prompt = shot_info["image_prompt"]
        text_overlay = shot_info["text_overlay"]
        sanitize = shot_info.get("sanitize", False)
        ref_paths, ref_meta = get_ref_paths(shot_info)

        # Build prompt
        prompt = image_prompt
        if sanitize:
            prompt = prompt.replace("elderly man", "older man")
            prompt = prompt.replace("elderly", "older")
            prompt = prompt.replace("faint but legible furrow of quiet worry", "sense of quiet contemplation")
            print(f"  shot_04: sanitized prompt (elderly->older, worry->contemplation)")

        text_instruction = build_text_overlay_instruction(text_overlay)
        if text_instruction:
            prompt = prompt + "\n\n" + text_instruction
            chinese_text = text_overlay.get("chinese_text", "")
            print(f"  text_overlay injected: {text_overlay['text_type']} | {str(chinese_text)[:80]}")
        else:
            print(f"  text_overlay: none")

        print(f"  refs: {len(ref_paths)} ({ref_meta['characters']} + {ref_meta['scenes']})")
        print(f"  prompt length: {len(prompt)} chars")

        # First attempt
        img_bytes, meta = call_seedream(prompt, ref_paths)
        meta["shot_id"] = sid
        meta["phase"] = "4-supplementary"
        meta["ref_characters"] = ref_meta["characters"]
        meta["ref_scenes"] = ref_meta["scenes"]
        meta["ref_missing"] = ref_meta["missing"]
        meta["text_overlay_injected"] = bool(text_instruction)
        if sanitize:
            meta["sanitized"] = True

        out_img_path = OUT_BASE / "seedream" / f"shot_{sid:02d}.png"

        # Handle shot_04 censorship check
        if sid == 4 and not meta.get("success"):
            err = meta.get("error", "")
            if "Sensitive" in err or "sensitive" in err or "InputText" in err:
                shot04_censor_count += 1
                print(f"  shot_04 fire censorship block #{shot04_censor_count}")
                if shot04_censor_count >= 2:
                    print("  STOP: 2 consecutive censorship blocks on shot_04 — PM must be notified")
                    results.append({
                        "shot_id": sid,
                        "status": "❌ (2x censored)",
                        "text_status": "❌ (gen failed)",
                        "latency_sec": meta.get("latency_sec", 0),
                    })
                    new_logs.append(meta)
                    continue

        has_text = None
        confidence = 0.0
        text_detect = {}

        if img_bytes:
            out_img_path.write_bytes(img_bytes)
            print(f"  saved {out_img_path.name} ({len(img_bytes)//1024} KB, {meta.get('latency_sec')}s)")

            text_detect = _detect_text_presence(out_img_path)
            meta["text_detection"] = text_detect
            has_text = text_detect.get("has_text")
            confidence = text_detect.get("confidence", 0)

            print(f"  text detection: has_text={has_text}, std={text_detect.get('max_std', 0):.1f}, confidence={confidence:.2f}")

            # Auto-retry if no text detected
            if text_instruction and has_text is False and confidence < 0.3:
                print(f"  text not detected, retrying with CRITICAL emphasis...")
                stronger_prompt = (
                    prompt
                    + "\n\nCRITICAL REQUIREMENT: ALL Chinese text specified above MUST appear visibly in the final image. "
                    "Do not omit any text overlay or speech bubble. The Chinese characters must be clearly readable."
                )
                retry_bytes, retry_meta = call_seedream(stronger_prompt, ref_paths)
                retry_meta["shot_id"] = sid
                retry_meta["is_retry"] = True
                retry_meta["phase"] = "4-supplementary-retry"

                if retry_bytes:
                    out_img_path.write_bytes(retry_bytes)
                    img_bytes = retry_bytes
                    retry_text_detect = _detect_text_presence(out_img_path)
                    retry_meta["text_detection"] = retry_text_detect
                    meta["retry"] = retry_meta
                    meta["retry_text_detection"] = retry_text_detect
                    has_text = retry_text_detect.get("has_text")
                    confidence = retry_text_detect.get("confidence", 0)
                    total_latency += retry_meta.get("latency_sec", 0)
                    print(f"  retry: {'text found' if has_text else 'still no text'} (std={retry_text_detect.get('max_std',0):.1f})")
                else:
                    print(f"  retry also failed: {retry_meta.get('error','')[:200]}")
                    meta["retry"] = retry_meta

        # Determine text render status
        text_type = text_overlay.get("text_type", "none")
        if text_type == "none":
            t_symbol = "N/A"
        elif has_text is True and confidence >= 0.5:
            t_symbol = "✅"
        elif has_text is True and confidence >= 0.2:
            t_symbol = "⚠️"
        else:
            t_symbol = "❌"

        meta["text_render_status"] = t_symbol

        if img_bytes:
            total_ok += 1
            total_latency += meta.get("latency_sec", 0)
            print(f"  text render status: {t_symbol}")
        else:
            print(f"  FAILED: {meta.get('error', '')[:300]}")
            t_symbol = "❌ (gen failed)"

        results.append({
            "shot_id": sid,
            "status": "✅" if img_bytes else "❌",
            "text_status": t_symbol,
            "latency_sec": meta.get("latency_sec", 0),
            "file_size_kb": len(img_bytes) // 1024 if img_bytes else 0,
        })
        new_logs.append(meta)

        if sid != SHOTS_TO_REGEN[-1]["shot_id"]:
            time.sleep(1.0)

    # ===== Update logs/seedream_api_logs.json (append supplementary records) =====
    logs_path = OUT_BASE / "logs" / "seedream_api_logs.json"
    existing_logs = {}
    if logs_path.exists():
        try:
            existing_logs = json.loads(logs_path.read_text(encoding="utf-8"))
        except Exception:
            existing_logs = {}

    existing_shots = existing_logs.get("shots", [])

    # Replace existing records for shot_id 4/9/10 with new ones, keep others
    new_shot_ids = {lg["shot_id"] for lg in new_logs}
    kept_shots = [s for s in existing_shots if s.get("shot_id") not in new_shot_ids]

    # Tag existing shots with original phase marker if not already tagged
    for s in kept_shots:
        if "phase" not in s:
            s["phase"] = "4"

    merged_shots = kept_shots + new_logs

    total_success = sum(1 for s in merged_shots if s.get("success"))
    total_lat = sum(s.get("latency_sec", 0) for s in merged_shots if s.get("success"))

    updated_logs = {
        "run_time": existing_logs.get("run_time", run_time.isoformat()),
        "supplementary_run_time": run_time.isoformat(),
        "model": SEEDREAM_MODEL,
        "endpoint": SEEDREAM_ENDPOINT,
        "size": SEEDREAM_SIZE,
        "total_shots": 10,
        "success_count": total_success,
        "total_latency_sec": round(total_lat, 2),
        "avg_latency_sec": round(total_lat / max(total_success, 1), 2),
        "notes": existing_logs.get("notes", []) + [
            f"Phase 4-supplementary: shots 04/09/10 rerun at {run_time.strftime('%H:%M')} "
            f"to add Chinese text overlay. {total_ok}/3 succeeded."
        ],
        "shots": merged_shots,
    }

    logs_path.write_text(json.dumps(updated_logs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[regen-supp] logs updated: {logs_path}")

    # ===== Update README.md =====
    # Build a minimal updated text render status table for all 10 shots
    # We need the existing per-shot text render status from the existing logs
    shot_text_status: dict[int, str] = {}
    for s in merged_shots:
        sid_val = s.get("shot_id")
        if sid_val:
            shot_text_status[sid_val] = s.get("text_render_status", "?")

    # Known text_type per shot from R8 storyboard (for README table)
    text_types_by_shot = {
        1: "dialogue",
        2: "dialogue",
        3: "dialogue_with_thought",
        4: "thought",
        5: "dialogue",
        6: "thought",
        7: "dialogue_with_thought",
        8: "dialogue_with_thought",
        9: "dialogue",
        10: "thought",
    }

    known_expected: dict[int, str] = {
        1: "阿朗：「爸爸！今天圩日」",
        2: "阿朗：「要去，要去！」",
        3: "（mixed dialogue + thought）",
        4: "老伴昨夜又咳了半宿，不知那秋梨膏管不管用。",
        5: "阿朗：「买这个！这个！」",
        6: "（这孩子，脚下从不知道轻重。）",
        7: "（mixed dialogue + thought）",
        8: "（mixed dialogue + thought）",
        9: "阿朗：「再来一下！再来！」",
        10: "一、二、三……怎么数来数去只有三个人？阿朗呢——阿朗在哪里？",
    }

    text_status_rows = []
    for i in range(1, 11):
        tt = text_types_by_shot.get(i, "?")
        exp = known_expected.get(i, "")[:50]
        st = shot_text_status.get(i, "?")
        text_status_rows.append(
            f"| shot_{i:02d} | {tt:<24} | {exp:<50} | {st} |"
        )

    rendered_count = sum(1 for v in shot_text_status.values() if v in ("✅", "⚠️"))
    total_text_shots = sum(1 for tt in text_types_by_shot.values() if tt != "none")

    supp_ok = sum(1 for r in results if r["status"] == "✅")
    supp_latency = round(sum(r.get("latency_sec", 0) for r in results), 1)
    supp_cost_cny = round(supp_ok * 0.22, 2)

    readme = f"""# Seedream 5.0-lite vs NB2 POC — R8 shot_01~10

**Date**: {run_time.strftime("%Y-%m-%d %H:%M")} (Phase 4-supplementary update)
**Task**: TASK-SEEDREAM-POC（Founder 2026-04-24 决策）
**Phase 4 重跑**: 含 text_overlay 注入（build_text_overlay_instruction）
**Phase 4-supplementary**: shots 04/09/10 补跑（{run_time.strftime("%H:%M")}）

## 运行摘要

| 指标 | 值 |
|------|---|
| 总 shots | 10 |
| Seedream 成功 | {total_success}/10 |
| Phase 4-supplementary shots | {supp_ok}/3 (shots 04/09/10) |
| 补跑总延迟 | {supp_latency}s |
| 补跑估算成本 | ~¥{supp_cost_cny} ({supp_ok} × ¥0.22/张) |
| 文字渲染 shots | {rendered_count}/{total_text_shots} 有文字（启发式检测，Founder 肉眼确认为准）|

## Shot 文字渲染状态（Phase 4 + 4-supplementary 最终）

> ✅ = 启发式检测到文字区域（std > 40）| ⚠️ = 弱信号（std 20-40）| ❌ = 未检测到 | N/A = 无文字要求
> 最终以 Founder 肉眼确认为准

| Shot | text_type | expected chinese_text | rendered |
|------|-----------|-----------------------|----------|
{chr(10).join(text_status_rows)}

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

## Phase 4-supplementary 说明（{run_time.strftime("%Y-%m-%d %H:%M")}）

- shots 04/09/10 在 Phase 4 主跑中未生成含中文字版本，本次补跑
- shot_04: sanitized + thought text overlay（老伴昨夜又咳了半宿）
- shot_09: dialogue text overlay（阿朗：「再来一下！再来！」）
- shot_10: thought text overlay（一、二、三……怎么数来数去只有三个人？）
- 所有中文原文照抄 R8，不翻译不改字

## 参考图策略（Founder 决策 4）

- **只传 fullbody**，不传 portrait
- 角色参考图: `char_NNN_fullbody.png`
- 场景参考图: `<location_id>_interior_anchor.png` + `<location_id>_exterior_anchor.png`

## 产物结构

```
seedream_vs_nb2_2026-04-24/
├── seedream/              # Seedream 5.0-lite 新生图（10 张，Phase 4+supplementary）
│   └── shot_01.png ... shot_10.png
├── nb2_baseline/          # R8 NB2 历史图（复制，10 张）
│   └── shot_01.png ... shot_10.png
├── logs/
│   └── seedream_api_logs.json   # 每 shot 的 latency / size / error / text_detection
├── comparison.html        # 左 Seedream / 右 NB2 横向对比，shot_04 ⚠️ 标记保留
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
    print(f"[regen-supp] README.md updated: {OUT_BASE / 'README.md'}")

    # ===== Update comparison.html =====
    # Read existing log to rebuild full 10-shot HTML
    # We'll build shots_data for render_comparison_html compatible format
    # using the merged logs
    shots_data_for_html = []
    for s in sorted(merged_shots, key=lambda x: x.get("shot_id", 0)):
        sid_val = s.get("shot_id")
        if not sid_val or sid_val > 10:
            continue
        # Load original text_overlay from merged log (we stored it in meta)
        # Find the matching SHOTS_TO_REGEN entry if available
        shot_spec = next((x for x in SHOTS_TO_REGEN if x["shot_id"] == sid_val), None)
        if shot_spec:
            text_overlay = shot_spec["text_overlay"]
            image_prompt = shot_spec["image_prompt"]
        else:
            # Try to reconstruct from log info — text_overlay not stored in original Phase 4 logs
            # Use minimal placeholders
            text_overlay = {}
            image_prompt = ""

        nb2_src = R8_BASE / "images" / f"shot_{sid_val:02d}.png"
        nb2_dst = OUT_BASE / "nb2_baseline" / f"shot_{sid_val:02d}.png"
        nb2_ok = nb2_dst.exists()

        shots_data_for_html.append({
            "shot_id": sid_val,
            "image_prompt": image_prompt,
            "text_overlay": text_overlay,
            "ref_count": s.get("ref_count", 0),
            "characters": s.get("ref_characters", []),
            "scenes": s.get("ref_scenes", []),
            "latency_sec": s.get("latency_sec", "-"),
            "status": "success" if s.get("success") else "failed",
            "error": s.get("error"),
            "seedream_ok": s.get("success", False),
            "nb2_ok": nb2_ok,
        })

    # Import render function from main script and regenerate
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_seedream_vs_nb2",
            REPO_ROOT / "scripts" / "test_seedream_vs_nb2.py"
        )
        mod = importlib.util.load_from_spec(spec)
        spec.loader.exec_module(mod)
        html_path = OUT_BASE / "comparison.html"
        mod.render_comparison_html(shots_data_for_html, html_path)
        print(f"[regen-supp] comparison.html updated: {html_path}")
    except Exception as e:
        print(f"[regen-supp] comparison.html update failed: {e} — skipping")

    # ===== Final summary =====
    print(f"\n[regen-supp] === DONE ===")
    print(f"Shots regenerated: {supp_ok}/3")
    print(f"Total latency: {supp_latency}s")
    print(f"Estimated cost: ~¥{supp_cost_cny} (~${round(supp_ok * 0.030, 3)})")
    print(f"\nPer-shot results:")
    for r in results:
        print(f"  shot_{r['shot_id']:02d}: gen={r['status']} | text={r['text_status']} | {r.get('latency_sec',0):.1f}s | {r.get('file_size_kb',0)}KB")

    print(f"\n10-shot text render summary:")
    for i in range(1, 11):
        tt = text_types_by_shot.get(i, "?")
        st = shot_text_status.get(i, "?")
        print(f"  shot_{i:02d} | {tt:<24} | {st}")

    return 0 if supp_ok >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
