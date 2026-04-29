"""TASK-SHOT08-DIAGNOSIS — Shot 8 Seedream 卡死根因单独诊断脚本

背景
----
shot_8 在 Phase 3 / Phase 4 / 回归测试三次都在同一位置卡死（4 角色 + 2 场景 = 6 refs，
prompt 2023 字符，payload 估算 12-18MB base64）。

根因假设
--------
A 脚本累积态问题（前 7 shot 跑完后内存/socket/handle 没释放）
  → 单独跑 shot_8 应成功 → 生产 FastAPI 每请求独立调用栈不会卡
B 代码层同步阻塞（base64 编码 6×3MB 图阻塞 main thread / urlopen 在大 payload hang）
  → 单独跑也卡 → 生产会卡，必须修代码
C 火山方舟 API 对超大 payload 直接 reject（API gateway 拒 13-18MB body）
  → 应有 HTTP error，脚本捕获，不会"静默挂"

运行
----
    cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
    source venv/bin/activate
    mkdir -p test_output/manualtest/shot8_diagnosis_2026-04-25
    python scripts/diagnose_shot8_seedream.py 2>&1 | tee test_output/manualtest/shot8_diagnosis_2026-04-25/diagnose.log

产物
----
- test_output/manualtest/shot8_diagnosis_2026-04-25/diagnose.log   完整日志
- test_output/manualtest/shot8_diagnosis_2026-04-25/result.json    结构化结果
- test_output/manualtest/shot8_diagnosis_2026-04-25/shot_08.png    如果成功
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import resource
import signal
import sys
import time
import traceback
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -------------------------------------------------------------------
# 强制 seedream provider（不改 .env，仅此进程生效）
# -------------------------------------------------------------------
os.environ["IMAGE_GEN_PROVIDER"] = "seedream"

from PIL import Image  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.image_generator import ImageGenerator  # noqa: E402

# -------------------------------------------------------------------
# 路径常量
# -------------------------------------------------------------------
R8_DIR = (
    ROOT
    / "test_output"
    / "manualtest"
    / "e2e_regression_r8"
    / "20260316_145613"
    / "story_A"
    / "20260316_145614"
)
OUT_DIR = ROOT / "test_output" / "manualtest" / "shot8_diagnosis_2026-04-25"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HARD_TIMEOUT_SEC = 240  # 超过则 TimeoutError，防真的 hang 死

# -------------------------------------------------------------------
# 日志
# -------------------------------------------------------------------
LOG_PATH = OUT_DIR / "diagnose.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s :: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("shot8_diagnosis")

# -------------------------------------------------------------------
# 内存工具
# -------------------------------------------------------------------

def _rss_mb() -> float:
    """当前进程 RSS（MB）。macOS getrusage 返回字节，Linux 返回 KB。"""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    ru_maxrss = usage.ru_maxrss
    # macOS: bytes；Linux: kilobytes
    if sys.platform == "darwin":
        return round(ru_maxrss / 1024 / 1024, 2)
    else:
        return round(ru_maxrss / 1024, 2)


# 可选 psutil 辅助
try:
    import psutil  # type: ignore
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False


def _psutil_rss_mb() -> Optional[float]:
    if not _PSUTIL_OK:
        return None
    try:
        return round(psutil.Process().memory_info().rss / 1024 / 1024, 2)
    except Exception:
        return None


# -------------------------------------------------------------------
# SIGALRM handler（POSIX only — 用于 hard timeout）
# -------------------------------------------------------------------

class _TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):  # noqa: ANN001
    raise _TimeoutError(f"Hard timeout {HARD_TIMEOUT_SEC}s exceeded")


_SIGALRM_AVAILABLE = hasattr(signal, "SIGALRM")

# -------------------------------------------------------------------
# 数据加载
# -------------------------------------------------------------------

def load_shot8_data() -> Dict[str, Any]:
    log.info("[load_data] 开始加载 R8 storyboard / characters / screenplay / summary")
    t0 = time.time()

    storyboard = json.loads((R8_DIR / "4_storyboard.json").read_text())
    characters = json.loads((R8_DIR / "2_characters.json").read_text())
    screenplay = json.loads((R8_DIR / "3_screenplay.json").read_text())
    summary = json.loads((R8_DIR / "summary.json").read_text())

    # 提取 shot_8
    shot = next((s for s in storyboard["shots"] if s.get("shot_id") == 8), None)
    if shot is None:
        raise RuntimeError("shot_8 not found in 4_storyboard.json")

    # 提取 scene_id → location_id 映射
    loc_map = {sc["scene_id"]: sc.get("location_id", "") for sc in screenplay.get("scenes", [])}
    location_id = loc_map.get(shot.get("scene_id", -1), "")

    elapsed = round(time.time() - t0, 3)
    log.info(f"[load_data] 完成 (shot_id={shot.get('shot_id')}, scene_id={shot.get('scene_id')}, location_id={location_id}, elapsed={elapsed}s)")
    log.info(f"[load_data] image_prompt 长度: {len(shot.get('image_prompt', ''))} chars")
    log.info(f"[load_data] characters_visible: {shot.get('character_direction', {}).get('characters_visible', [])}")

    return {
        "storyboard": storyboard,
        "characters": characters,
        "screenplay": screenplay,
        "summary": summary,
        "shot": shot,
        "location_id": location_id,
        "load_elapsed": elapsed,
    }


def load_reference_images(shot: Dict[str, Any], location_id: str) -> tuple[List[Image.Image], List[str]]:
    """加载参考图（仅 fullbody + 场景 anchor），返回 (images, paths)。"""
    log.info("[build_payload] 开始加载参考图（fullbody + scene anchor）")
    t0 = time.time()

    refs: List[Image.Image] = []
    paths: List[str] = []

    chars_visible = shot.get("character_direction", {}).get("characters_visible", []) or []
    char_dir = R8_DIR / "character_refs"

    for cid in chars_visible:
        fp = char_dir / f"{cid}_fullbody.png"
        if fp.exists():
            img = Image.open(fp).copy()
            refs.append(img)
            paths.append(str(fp))
            log.info(f"  [build_payload] 角色参考图加载: {fp.name} ({img.width}x{img.height}, size={fp.stat().st_size // 1024}KB)")
        else:
            log.warning(f"  [build_payload] ⚠️ 缺失角色参考图: {fp}")

    scene_dir = R8_DIR / "scene_refs"
    if location_id:
        for suffix in ("interior_anchor", "exterior_anchor"):
            fp = scene_dir / f"{location_id}_{suffix}.png"
            if fp.exists():
                img = Image.open(fp).copy()
                refs.append(img)
                paths.append(str(fp))
                log.info(f"  [build_payload] 场景参考图加载: {fp.name} ({img.width}x{img.height}, size={fp.stat().st_size // 1024}KB)")
            else:
                log.warning(f"  [build_payload] ⚠️ 缺失场景参考图: {fp}")

    elapsed = round(time.time() - t0, 3)
    log.info(f"[build_payload] 参考图加载完成: {len(refs)} 张，elapsed={elapsed}s")
    return refs, paths


def estimate_payload_size(references: List[Image.Image]) -> int:
    """估算 base64 encode 后参考图总字节数（不含 JSON 包装）。"""
    total = 0
    for img in references:
        buf = BytesIO()
        to_enc = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        to_enc.save(buf, format="PNG", optimize=True)
        raw_bytes = len(buf.getvalue())
        b64_bytes = (raw_bytes * 4 + 2) // 3  # base64 overhead
        total += b64_bytes
    return total


# -------------------------------------------------------------------
# 主诊断流程
# -------------------------------------------------------------------

async def diagnose() -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "outcome": "unknown",
        "root_cause": "unknown",
        "mem_peak_mb": 0.0,
        "payload_bytes": 0,
        "step_timings_sec": {
            "load_data": 0.0,
            "build_payload": 0.0,
            "encode_refs": 0.0,
            "api_call": 0.0,
            "decode_response": 0.0,
            "save_image": 0.0,
        },
        "total_elapsed_sec": 0.0,
        "http_status": None,
        "exception_type": None,
        "traceback": None,
        "image_path": None,
    }

    wall_start = time.time()
    mem_before = _rss_mb()
    psutil_before = _psutil_rss_mb()

    log.info("=" * 60)
    log.info("TASK-SHOT08-DIAGNOSIS 单 shot 诊断开始")
    log.info(f"  settings.IMAGE_GEN_PROVIDER = {settings.IMAGE_GEN_PROVIDER}")
    log.info(f"  ARK_API_KEY set: {bool(settings.ARK_API_KEY)}")
    log.info(f"  GEMINI_API_KEY set: {bool(settings.GEMINI_API_KEY)}")
    log.info(f"  mem_before RSS = {mem_before} MB (getrusage)")
    if psutil_before is not None:
        log.info(f"  mem_before RSS = {psutil_before} MB (psutil)")
    log.info("=" * 60)

    if settings.IMAGE_GEN_PROVIDER != "seedream":
        log.error("IMAGE_GEN_PROVIDER != 'seedream'，请确认环境变量设置")
        result["outcome"] = "exception"
        result["exception_type"] = "ConfigError"
        result["traceback"] = "IMAGE_GEN_PROVIDER is not 'seedream'"
        return result

    if not settings.ARK_API_KEY:
        log.error("ARK_API_KEY 未设置，Seedream 调用无法进行")
        result["outcome"] = "exception"
        result["exception_type"] = "ConfigError"
        result["traceback"] = "ARK_API_KEY is empty"
        return result

    # ---- Step 1: 加载数据 ----
    t_step = time.time()
    try:
        inputs = load_shot8_data()
    except Exception as e:
        log.exception(f"[load_data] 加载数据失败: {e}")
        result["outcome"] = "exception"
        result["exception_type"] = type(e).__name__
        result["traceback"] = traceback.format_exc()
        result["step_timings_sec"]["load_data"] = round(time.time() - t_step, 3)
        result["total_elapsed_sec"] = round(time.time() - wall_start, 3)
        return result
    result["step_timings_sec"]["load_data"] = round(time.time() - t_step, 3)

    shot = inputs["shot"]
    location_id = inputs["location_id"]
    style_preset = inputs["summary"].get("style_preset", "illustration")

    # ---- Step 2: 构建参考图（含 encode 成本测量）----
    t_step = time.time()
    try:
        refs, ref_paths = load_reference_images(shot, location_id)
    except Exception as e:
        log.exception(f"[build_payload] 参考图加载失败: {e}")
        result["outcome"] = "exception"
        result["exception_type"] = type(e).__name__
        result["traceback"] = traceback.format_exc()
        result["step_timings_sec"]["build_payload"] = round(time.time() - t_step, 3)
        result["total_elapsed_sec"] = round(time.time() - wall_start, 3)
        return result
    result["step_timings_sec"]["build_payload"] = round(time.time() - t_step, 3)

    log.info(f"[build_payload] ref_paths: {[Path(p).name for p in ref_paths]}")

    # ---- Step 3: 估算 payload 大小（encode_refs）----
    t_step = time.time()
    try:
        payload_bytes = estimate_payload_size(refs)
        result["payload_bytes"] = payload_bytes
        log.info(f"[encode_refs] 估算 base64 payload size = {payload_bytes / 1024 / 1024:.2f} MB")
    except Exception as e:
        log.warning(f"[encode_refs] 估算失败（非阻塞）: {e}")
    result["step_timings_sec"]["encode_refs"] = round(time.time() - t_step, 3)

    mem_after_load = _rss_mb()
    psutil_after_load = _psutil_rss_mb()
    log.info(f"[mem] 加载 + 构建参考图后 RSS = {mem_after_load} MB (delta={mem_after_load - mem_before:.2f} MB)")
    if psutil_after_load is not None:
        log.info(f"[mem] 加载 + 构建参考图后 RSS = {psutil_after_load} MB psutil (delta={psutil_after_load - psutil_before:.2f} MB)")

    # ---- Step 4: 调 generate_shot_image_phase2_safe (生产路径) ----
    log.info("[api_call] 开始调用 generate_shot_image_phase2_safe (生产路径)")
    log.info(f"[api_call] shot_id=8, refs={len(refs)}, style={style_preset}")
    log.info(f"[api_call] Hard timeout = {HARD_TIMEOUT_SEC}s")

    image_gen = ImageGenerator()

    t_api = time.time()
    api_result: Optional[Dict[str, Any]] = None
    http_status: Optional[int] = None
    exc_type: Optional[str] = None
    exc_tb: Optional[str] = None

    if _SIGALRM_AVAILABLE:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(HARD_TIMEOUT_SEC)

    try:
        api_result = await image_gen.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=inputs["storyboard"],
            characters=inputs["characters"],
            style_preset=style_preset,
            reference_images=refs,
            screenplay=inputs["screenplay"],
            aspect_ratio="2:3",
            genre=None,
            use_native_text=True,
        )
    except _TimeoutError as e:
        log.error(f"[api_call] ⏰ TIMEOUT: {e}")
        exc_type = "TimeoutError"
        exc_tb = traceback.format_exc()
    except Exception as e:
        log.exception(f"[api_call] 异常: {type(e).__name__}: {e}")
        exc_type = type(e).__name__
        exc_tb = traceback.format_exc()
        # 尝试提取 http_status
        if hasattr(e, "code"):
            http_status = getattr(e, "code", None)
        elif hasattr(e, "status_code"):
            http_status = getattr(e, "status_code", None)
    finally:
        if _SIGALRM_AVAILABLE:
            signal.alarm(0)  # 取消 alarm

    api_elapsed = round(time.time() - t_api, 3)
    result["step_timings_sec"]["api_call"] = api_elapsed
    log.info(f"[api_call] 耗时 {api_elapsed}s")

    mem_after_api = _rss_mb()
    psutil_after_api = _psutil_rss_mb()
    log.info(f"[mem] API 调用后 RSS = {mem_after_api} MB")
    if psutil_after_api is not None:
        log.info(f"[mem] API 调用后 RSS = {psutil_after_api} MB psutil")

    result["mem_peak_mb"] = max(mem_before, mem_after_load, mem_after_api)

    # ---- Step 5: 解码 response ----
    if api_result is not None:
        t_step = time.time()
        try:
            success = api_result.get("success", False)
            log.info(f"[decode_response] success={success}, model_used={api_result.get('model_used', 'N/A')}")
            if not success:
                error_detail = api_result.get("error", "")
                error_kind = api_result.get("error_kind", "")
                log.error(f"[decode_response] 失败: error_kind={error_kind}, error={error_detail[:400]}")
                seedream_info = api_result.get("seedream_info", {})
                if seedream_info:
                    log.info(f"[decode_response] seedream_info: {json.dumps(seedream_info, ensure_ascii=False, indent=2)}")
                # 尝试从 error 中提取 http_status
                if "http_status" in api_result:
                    http_status = api_result["http_status"]
            else:
                log.info(f"[decode_response] ✅ 成功！width={api_result.get('width')}, height={api_result.get('height')}, time={api_result.get('generation_time_seconds')}s")
        except Exception as e:
            log.warning(f"[decode_response] 解析失败（非阻塞）: {e}")
        result["step_timings_sec"]["decode_response"] = round(time.time() - t_step, 3)

    # ---- Step 6: 保存图片（如果成功）----
    if api_result is not None and api_result.get("success") and api_result.get("image_data"):
        t_step = time.time()
        try:
            img_path = OUT_DIR / "shot_08.png"
            img_bytes = base64.b64decode(api_result["image_data"])
            img_path.write_bytes(img_bytes)
            result["image_path"] = str(img_path)
            log.info(f"[save_image] ✅ 图片保存成功: {img_path} ({len(img_bytes) // 1024}KB)")
        except Exception as e:
            log.warning(f"[save_image] 保存失败: {e}")
        result["step_timings_sec"]["save_image"] = round(time.time() - t_step, 3)

    # ---- 综合判定 ----
    total_elapsed = round(time.time() - wall_start, 3)
    result["total_elapsed_sec"] = total_elapsed
    result["http_status"] = http_status
    result["exception_type"] = exc_type
    result["traceback"] = exc_tb

    if exc_type == "TimeoutError":
        result["outcome"] = "timeout"
    elif exc_type is not None:
        result["outcome"] = "exception"
    elif api_result is not None and api_result.get("success"):
        result["outcome"] = "success"
    else:
        result["outcome"] = "exception"

    # ---- 根因推断 ----
    if result["outcome"] == "success":
        result["root_cause"] = "A"
        log.info(
            "[root_cause] 结论 A：单独跑 shot_8 成功。前 7 shot 跑完后的累积态（内存/socket/handle）"
            "导致脚本在第 8 个 shot 时资源耗尽。生产 FastAPI 每次请求独立调用栈，不会重现此问题。"
        )
    elif result["outcome"] == "timeout":
        result["root_cause"] = "B"
        log.error(
            "[root_cause] 结论 B：单独跑 shot_8 也超时。根因是代码层同步阻塞（base64 编码"
            "6×3MB 大图阻塞 main thread，或 urlopen 在 12-18MB payload 挂起）。"
            "生产 FastAPI 会卡，需要修代码。"
        )
    elif result["outcome"] == "exception":
        # 区分 B 和 C
        tb = exc_tb or ""
        err_detail = ""
        if api_result:
            err_detail = str(api_result.get("error", ""))
        if (
            "413" in tb or "413" in err_detail
            or "too large" in (tb + err_detail).lower()
            or "payload" in (tb + err_detail).lower()
            or (http_status is not None and http_status in (400, 413))
        ):
            result["root_cause"] = "C"
            log.error(
                "[root_cause] 结论 C：火山方舟 API 拒绝超大 payload（HTTP 400/413）。"
                "需要在 seedream_generator.py 中增强降采样逻辑，或在 dispatch 前检查 payload size。"
            )
        else:
            result["root_cause"] = "B"
            log.error(
                "[root_cause] 结论 B/unknown：单独跑 shot_8 也失败，但不是 HTTP 400/413。"
                f"exception_type={exc_type}, http_status={http_status}。"
                "可能是代码层阻塞或其他 API 错误。"
            )
    else:
        result["root_cause"] = "unknown"

    log.info(f"[summary] outcome={result['outcome']}, root_cause={result['root_cause']}")
    log.info(f"[summary] mem_peak_mb={result['mem_peak_mb']}")
    log.info(f"[summary] payload_bytes={result['payload_bytes']} ({result['payload_bytes'] / 1024 / 1024:.2f} MB)")
    log.info(f"[summary] total_elapsed_sec={total_elapsed}")
    log.info(f"[summary] step_timings={result['step_timings_sec']}")

    return result


# -------------------------------------------------------------------
# 入口
# -------------------------------------------------------------------

async def main() -> None:
    log.info("=" * 60)
    log.info("TASK-SHOT08-DIAGNOSIS 启动")
    log.info(f"ROOT = {ROOT}")
    log.info(f"OUT_DIR = {OUT_DIR}")
    log.info("=" * 60)

    result = await diagnose()

    result_path = OUT_DIR / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=str)
    )
    log.info(f"result.json 写入: {result_path}")

    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print(f"  outcome     : {result['outcome']}")
    print(f"  root_cause  : {result['root_cause']}")
    print(f"  mem_peak_mb : {result['mem_peak_mb']} MB")
    print(f"  payload_mb  : {result['payload_bytes'] / 1024 / 1024:.2f} MB")
    print(f"  total_sec   : {result['total_elapsed_sec']} s")
    print(f"  image_path  : {result['image_path'] or 'N/A'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
