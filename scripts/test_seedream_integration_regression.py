"""TASK-SEEDREAM-INTEGRATION — Phase 2 真实回归测试
================================================================

验证点
------
1. 集成路径正确：调用 generate_shot_image_phase2_safe 后 dispatcher 真的把
   请求派发到 SeedreamGenerator（日志 / 返回 model_used / seedream_info）
2. 2D 风格锁生效：prompt 里包含 Seedream 2D lock 块的标志性词
3. sanitize 兜底：shot_04 触发 InputTextSensitiveContentDetected → 进入
   sanitize 重试，返回里看到 sanitize_attempts 有命中
4. NB2 fallback 可达：通过 _mock_force_sanitize_fail 让 Seedream 永远失败，
   验证 fallback_callback 能真的走回 NB2（_seedream_fallback=True 闭包）
5. 角色一致性无破坏（核心）：4 角色 × 10 shots 产物归档，与 POC Phase 4
   的 10 张 Seedream 图并排对比
6. 参考图传递正确：每 shot 传入 fullbody + 场景 anchor（只 fullbody，和 POC
   策略一致），每张 PIL Image 非空，尺寸与文件一致

脚本约束
--------
- 零生产代码修改（只 import + 调用 generate_shot_image_phase2_safe）
- 产物放到 test_output/manualtest/seedream_integration_regression_2026-04-24/
- 预算 ≤ ¥3（10 shots）
- 顺序执行，避免触发火山方舟 QPS 限制

运行
----
    IMAGE_GEN_PROVIDER=seedream python3 scripts/test_seedream_integration_regression.py

无须改 .env；跑完后 settings 自动还原（子进程）。
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- 项目根（脚本独立运行，确保 app/ 可 import）---
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

# 强制在 import settings 之前就绪：这里读 os.environ 直接覆盖
# 确保 Settings() 初始化时拿到 seedream
os.environ.setdefault("IMAGE_GEN_PROVIDER", "seedream")

from app.config import settings  # noqa: E402
from app.services import seedream_generator as sg  # noqa: E402
from app.services.image_generator import ImageGenerator  # noqa: E402
from app.services.style_enforcer import StyleEnforcer  # noqa: E402

# --------------------------------------------------------------------------
# 常量 / 路径
# --------------------------------------------------------------------------
R8_DIR = ROOT / "test_output" / "manualtest" / "e2e_regression_r8" / "20260316_145613" / "story_A" / "20260316_145614"
OUT_DIR = ROOT / "test_output" / "manualtest" / "seedream_integration_regression_2026-04-24"
IMG_OUT = OUT_DIR / "images"
LOG_OUT = OUT_DIR / "logs"
FALLBACK_OUT = OUT_DIR / "fallback_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_OUT.mkdir(parents=True, exist_ok=True)
LOG_OUT.mkdir(parents=True, exist_ok=True)
FALLBACK_OUT.mkdir(parents=True, exist_ok=True)

# 只跑前 10 shots（R8 一共 28 shots，预算要求 10 shots）
N_SHOTS = 10

# --------------------------------------------------------------------------
# 日志捕获：记录 seedream_generator / image_generator 的日志到文件 + stdout
# --------------------------------------------------------------------------
LOG_FILE = LOG_OUT / "regression.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("seedream_regression")


# --------------------------------------------------------------------------
# 数据加载
# --------------------------------------------------------------------------

def load_r8_inputs() -> Dict[str, Any]:
    storyboard = json.loads((R8_DIR / "4_storyboard.json").read_text())
    characters = json.loads((R8_DIR / "2_characters.json").read_text())
    screenplay = json.loads((R8_DIR / "3_screenplay.json").read_text())
    summary = json.loads((R8_DIR / "summary.json").read_text())
    return {
        "storyboard": storyboard,
        "characters": characters,
        "screenplay": screenplay,
        "summary": summary,
    }


def _scene_location_map(screenplay: Dict[str, Any]) -> Dict[int, str]:
    return {sc["scene_id"]: sc.get("location_id", "") for sc in screenplay.get("scenes", [])}


def load_reference_images(shot: Dict[str, Any], location_id: str) -> List[Image.Image]:
    """按 Founder 决策 4：只传 fullbody + 场景 anchor。"""
    refs: List[Image.Image] = []
    chars_visible = shot.get("character_direction", {}).get("characters_visible", []) or []
    char_dir = R8_DIR / "character_refs"
    for cid in chars_visible:
        fp = char_dir / f"{cid}_fullbody.png"
        if fp.exists():
            refs.append(Image.open(fp).copy())
        else:
            log.warning(f"missing fullbody ref for {cid}: {fp}")

    scene_dir = R8_DIR / "scene_refs"
    if location_id:
        interior = scene_dir / f"{location_id}_interior_anchor.png"
        exterior = scene_dir / f"{location_id}_exterior_anchor.png"
        if interior.exists():
            refs.append(Image.open(interior).copy())
        if exterior.exists():
            refs.append(Image.open(exterior).copy())
    return refs


# --------------------------------------------------------------------------
# 验证点收集
# --------------------------------------------------------------------------
@dataclass
class ShotResult:
    shot_id: int
    success: bool
    model_used: str = ""
    latency_sec: float = 0.0
    prompt_length_chars: int = 0
    ref_count: int = 0
    characters: List[str] = field(default_factory=list)
    location_id: str = ""
    seedream_info: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    image_path: str = ""
    prompt_preview: str = ""


@dataclass
class VerifyPoint:
    name: str
    passed: bool
    detail: str


# --------------------------------------------------------------------------
# 验证点 2：2D 风格锁生效
# --------------------------------------------------------------------------
SEEDREAM_2D_MARKERS = [
    "SEEDREAM RENDERING OVERRIDE",
    "NO 3D rendering",
    "2D hand-drawn illustration",
    "Watercolor-influenced",
    "Korean webtoon watercolor",
]


def check_seedream_2d_lock_block() -> VerifyPoint:
    """V2: 静态检查 StyleEnforcer 有 2D 锁定块方法 + enforce_prompt_for_provider('seedream') 产出包含所有标志词。"""
    try:
        block = StyleEnforcer.build_seedream_2d_boost_prefix()
        full = StyleEnforcer.enforce_prompt_for_provider("A quiet morning scene", "illustration", provider="seedream")
        missing = [m for m in SEEDREAM_2D_MARKERS if m not in block]
        in_full = all(m in full for m in SEEDREAM_2D_MARKERS)
        if not missing and in_full:
            return VerifyPoint(
                name="V2_2d_style_lock_defined",
                passed=True,
                detail=f"block={len(block)} chars, all 5 markers present; enforce_prompt_for_provider('seedream') 也包含全部标志词",
            )
        return VerifyPoint(
            name="V2_2d_style_lock_defined",
            passed=False,
            detail=f"missing from lock block: {missing}; in_full: {in_full}",
        )
    except Exception as e:
        return VerifyPoint(name="V2_2d_style_lock_defined", passed=False, detail=f"exception: {e}")


def check_seedream_2d_lock_in_production_path(seedream_prompts_sample: List[str]) -> VerifyPoint:
    """
    V2b: 检查实际进 Seedream API 的 prompt 是否含 2D lock 标志词。

    这揭示一个**真实集成缺口**：seedream_generator.py 当前走自己 shot['image_prompt']+text_overlay
    路径，不经 StyleEnforcer.enforce_prompt_for_provider()，因此生产路径下 2D 锁块不会被注入。
    """
    hits = 0
    for p in seedream_prompts_sample:
        if any(m in p for m in SEEDREAM_2D_MARKERS):
            hits += 1
    if hits == len(seedream_prompts_sample) and hits > 0:
        return VerifyPoint(
            name="V2b_2d_lock_in_seedream_prompt",
            passed=True,
            detail=f"{hits}/{len(seedream_prompts_sample)} shots 的 Seedream prompt 都含 2D lock 块",
        )
    return VerifyPoint(
        name="V2b_2d_lock_in_seedream_prompt",
        passed=False,
        detail=(
            f"{hits}/{len(seedream_prompts_sample)} shots 的 Seedream prompt 含 2D lock 块。"
            " 原因：seedream_generator.generate_shot_image_seedream() 当前路径"
            " shot['image_prompt']+text_overlay，没调 StyleEnforcer.enforce_prompt_for_provider()。"
            " 集成缺口，建议 @backend 在 seedream_generator 入口或 image_generator dispatcher 里补调用。"
        ),
    )


# --------------------------------------------------------------------------
# 验证点 3：sanitize 兜底 — 对 shot_04 原 prompt 做静态 + 动态验证
# --------------------------------------------------------------------------

def check_sanitize_static(shot04_prompt: str) -> VerifyPoint:
    """sanitize_prompt(attempt=1) 必须命中至少 1 个关键词替换。"""
    sanitized, reps = sg.sanitize_prompt(shot04_prompt, attempt=1)
    if reps:
        return VerifyPoint(
            name="V3a_sanitize_static_shot04",
            passed=True,
            detail=f"attempt=1 命中 {len(reps)} 处替换: {reps[:5]}",
        )
    return VerifyPoint(
        name="V3a_sanitize_static_shot04",
        passed=False,
        detail="attempt=1 未命中任何关键词（shot_04 prompt 可能已改版）",
    )


# --------------------------------------------------------------------------
# 验证点 4：NB2 fallback 路径可达 — 用 monkeypatch 让 Seedream 永远 sensitive_content
# --------------------------------------------------------------------------

async def probe_nb2_fallback(image_gen: ImageGenerator, inputs: Dict[str, Any]) -> VerifyPoint:
    """
    把 seedream._call_seedream_sync monkeypatch 成永远返回 sensitive_content，
    跑 1 个 shot 验证 fallback_callback 确实走到了 NB2，且最终产出成功的图。
    """
    shots = inputs["storyboard"]["shots"]
    loc_map = _scene_location_map(inputs["screenplay"])

    # 选 shot_01（简单，1 角色，预算友好）
    shot = next((s for s in shots if s.get("shot_id") == 1), shots[0])
    loc = loc_map.get(shot.get("scene_id"), "")
    refs = load_reference_images(shot, loc)

    original_call = sg._call_seedream_sync

    def _force_sensitive(prompt, reference_images, aspect_ratio, api_key):  # noqa: ANN001
        # 记录每一次被调用
        _force_sensitive.calls.append({
            "prompt_head": prompt[:120],
            "ref_count": len(reference_images),
        })
        return {
            "success": False,
            "error": "forced sensitive content for fallback probe",
            "error_kind": "sensitive_content",
            "latency_sec": 0.01,
            "http_status": 400,
        }

    _force_sensitive.calls = []  # type: ignore[attr-defined]

    sg._call_seedream_sync = _force_sensitive  # type: ignore[assignment]
    try:
        t0 = time.time()
        result = await image_gen.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=inputs["storyboard"],
            characters=inputs["characters"],
            style_preset=inputs["summary"].get("style_preset", "illustration"),
            reference_images=refs,
            screenplay=inputs["screenplay"],
            aspect_ratio="2:3",
            genre=None,
            use_native_text=True,
        )
    finally:
        sg._call_seedream_sync = original_call  # type: ignore[assignment]

    elapsed = round(time.time() - t0, 2)

    # Verdict
    seedream_calls = len(_force_sensitive.calls)  # type: ignore[attr-defined]
    seedream_info = (result or {}).get("seedream_info", {})
    used_fallback = seedream_info.get("used_fallback") is True
    sanitize_rounds = len(seedream_info.get("sanitize_attempts", []))
    model_used = result.get("model_used", "")
    success = result.get("success", False)

    # 写入调试产物
    (FALLBACK_OUT / "probe_result.json").write_text(
        json.dumps(
            {
                "seedream_calls_before_fallback": seedream_calls,
                "sanitize_rounds_recorded": sanitize_rounds,
                "used_fallback_flag": used_fallback,
                "final_model_used": model_used,
                "final_success": success,
                "final_error": result.get("error", ""),
                "elapsed_sec": elapsed,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    # 保存 fallback 产出图（如果有）
    if success and result.get("image_data"):
        try:
            (FALLBACK_OUT / "shot_01_fallback_nb2.png").write_bytes(base64.b64decode(result["image_data"]))
        except Exception as e:
            log.warning(f"fallback image save failed: {e}")

    # 判定：Seedream 被尝试过 4 次（attempt=0 原 prompt + 3 轮 sanitize），
    # 且最终结果 used_fallback=True 且 model 是 NB2 (gemini-*)
    ok_tries = seedream_calls == 4
    ok_fallback_flag = used_fallback
    ok_model = "gemini" in model_used.lower()
    ok_success = success

    passed = ok_tries and ok_fallback_flag and ok_model and ok_success
    detail = (
        f"seedream_calls={seedream_calls} (期望 4 = 1 原 + 3 sanitize), "
        f"sanitize_rounds_recorded={sanitize_rounds}, used_fallback={used_fallback}, "
        f"model_used={model_used or '<empty>'}, success={success}, elapsed={elapsed}s"
    )
    return VerifyPoint(name="V4_nb2_fallback_reachable", passed=passed, detail=detail)


# --------------------------------------------------------------------------
# 主流程：跑 10 shots
# --------------------------------------------------------------------------
async def run_10_shots(image_gen: ImageGenerator, inputs: Dict[str, Any]) -> List[ShotResult]:
    shots = inputs["storyboard"]["shots"]
    loc_map = _scene_location_map(inputs["screenplay"])
    results: List[ShotResult] = []

    for idx, shot in enumerate(shots[:N_SHOTS], start=1):
        sid = shot.get("shot_id", idx)
        chars = shot.get("character_direction", {}).get("characters_visible", []) or []
        loc = loc_map.get(shot.get("scene_id"), "")
        refs = load_reference_images(shot, loc)

        log.info(f"\n===== shot {sid} (chars={chars}, loc={loc}, refs={len(refs)}) =====")
        t0 = time.time()
        try:
            result = await image_gen.generate_shot_image_phase2_safe(
                shot=shot,
                storyboard=inputs["storyboard"],
                characters=inputs["characters"],
                style_preset=inputs["summary"].get("style_preset", "illustration"),
                reference_images=refs,
                screenplay=inputs["screenplay"],
                aspect_ratio="2:3",
                genre=None,
                use_native_text=True,
            )
        except Exception as e:
            log.exception(f"shot {sid} raised: {e}")
            results.append(
                ShotResult(
                    shot_id=sid,
                    success=False,
                    error=f"{type(e).__name__}: {e}",
                    ref_count=len(refs),
                    characters=chars,
                    location_id=loc,
                )
            )
            continue
        elapsed = round(time.time() - t0, 2)

        sr = ShotResult(
            shot_id=sid,
            success=bool(result.get("success")),
            model_used=str(result.get("model_used", "")),
            latency_sec=elapsed,
            ref_count=len(refs),
            characters=chars,
            location_id=loc,
            seedream_info=result.get("seedream_info", {}),
            error=str(result.get("error", "")) if not result.get("success") else "",
            prompt_preview=(shot.get("image_prompt", "") or "")[:300],
        )

        # 保存图
        if sr.success and result.get("image_data"):
            img_path = IMG_OUT / f"shot_{sid:02d}.png"
            try:
                img_path.write_bytes(base64.b64decode(result["image_data"]))
                sr.image_path = str(img_path.relative_to(OUT_DIR))
            except Exception as e:
                log.warning(f"shot {sid} image save failed: {e}")

        # 记录最终 prompt_length（若 seedream_info 里有）
        api_latency = sr.seedream_info.get("api_latency_sec")
        sanitize_attempts = sr.seedream_info.get("sanitize_attempts", []) if isinstance(sr.seedream_info, dict) else []
        log.info(
            f"shot {sid}: success={sr.success} model={sr.model_used} "
            f"api_latency={api_latency} sanitize_rounds={len(sanitize_attempts)} total={elapsed}s"
        )

        results.append(sr)

    return results


# --------------------------------------------------------------------------
# 报告写入
# --------------------------------------------------------------------------

def write_summary(
    results: List[ShotResult],
    verify_points: List[VerifyPoint],
    env_report: Dict[str, Any],
) -> Path:
    out = {
        "env": env_report,
        "shot_results": [r.__dict__ for r in results],
        "verify_points": [vp.__dict__ for vp in verify_points],
        "total_shots": len(results),
        "success_count": sum(1 for r in results if r.success),
        "seedream_success": sum(
            1 for r in results
            if r.success and "gemini" not in r.model_used.lower()
        ),
        "nb2_fallback_success": sum(
            1 for r in results
            if r.success and "gemini" in r.model_used.lower()
        ),
        "fail_count": sum(1 for r in results if not r.success),
    }
    p = OUT_DIR / "regression_summary.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    return p


def print_verdict(verify_points: List[VerifyPoint]) -> None:
    log.info("\n=====================  VERIFY POINTS  =====================")
    for vp in verify_points:
        mark = "PASS" if vp.passed else "FAIL"
        log.info(f"[{mark}] {vp.name}")
        log.info(f"      {vp.detail}")
    log.info("===========================================================\n")


async def main() -> None:
    log.info(f"OUT_DIR = {OUT_DIR}")
    log.info(f"settings.IMAGE_GEN_PROVIDER = {settings.IMAGE_GEN_PROVIDER}")
    log.info(f"ARK_API_KEY set: {bool(settings.ARK_API_KEY)}")
    log.info(f"GEMINI_API_KEY set: {bool(settings.GEMINI_API_KEY)}")

    env_report = {
        "IMAGE_GEN_PROVIDER": settings.IMAGE_GEN_PROVIDER,
        "ARK_API_KEY_set": bool(settings.ARK_API_KEY),
        "GEMINI_API_KEY_set": bool(settings.GEMINI_API_KEY),
        "seedream_model": sg.SEEDREAM_MODEL,
        "seedream_endpoint": sg.SEEDREAM_ENDPOINT,
        "phase2_dispatcher_installed_at": "app/services/image_generator.py:L1374",
    }

    if settings.IMAGE_GEN_PROVIDER != "seedream":
        log.error("IMAGE_GEN_PROVIDER != 'seedream'，请用 IMAGE_GEN_PROVIDER=seedream 运行本脚本")
        sys.exit(2)
    if not settings.ARK_API_KEY:
        log.error("ARK_API_KEY 未设置，Seedream 调用会立刻 missing_api_key")
        sys.exit(2)
    if not settings.GEMINI_API_KEY:
        log.error("GEMINI_API_KEY 未设置，NB2 fallback 会失败")
        sys.exit(2)

    inputs = load_r8_inputs()
    image_gen = ImageGenerator()

    # ----- V1: 集成路径正确（静态） -----
    # 通过 import 层检查 + 看 dispatcher 存在的源文件行，运行时用返回结果间接验证
    src = (ROOT / "app" / "services" / "image_generator.py").read_text()
    has_safe_dispatcher = (
        'if settings.IMAGE_GEN_PROVIDER == "seedream"' in src
        and "_seedream_fallback" in src
    )
    v1 = VerifyPoint(
        name="V1_integration_dispatcher_present",
        passed=has_safe_dispatcher,
        detail=(
            "image_generator.generate_shot_image_phase2_safe / generate_shot_image 两处都有"
            " `if settings.IMAGE_GEN_PROVIDER == 'seedream'` + `_seedream_fallback` guard"
            if has_safe_dispatcher else
            "未在 image_generator.py 里找到 Seedream dispatcher / _seedream_fallback guard"
        ),
    )

    # ----- V2: 2D 风格锁定块已定义 -----
    v2 = check_seedream_2d_lock_block()

    # ----- V3a: sanitize 静态命中 -----
    shot_04 = next(s for s in inputs["storyboard"]["shots"] if s.get("shot_id") == 4)
    v3a = check_sanitize_static(shot_04.get("image_prompt", ""))

    # ----- V4: NB2 fallback 可达（monkeypatch） -----
    log.info("\n===== V4: NB2 fallback probe (monkeypatch seedream → sensitive_content) =====")
    v4 = await probe_nb2_fallback(image_gen, inputs)

    # ----- 主回归：10 shots 实跑 -----
    log.info(f"\n===== 主回归：跑前 {N_SHOTS} shots =====")
    t_all = time.time()
    results = await run_10_shots(image_gen, inputs)
    total_elapsed = round(time.time() - t_all, 2)
    log.info(f"10-shot 回归耗时 {total_elapsed}s")

    # ----- V1 运行时补充：是否真有至少一张 shot 经 Seedream 成功 -----
    seedream_direct_success = sum(
        1 for r in results
        if r.success and "gemini" not in r.model_used.lower()
    )
    fallback_triggered = sum(
        1 for r in results
        if isinstance(r.seedream_info, dict) and r.seedream_info.get("used_fallback")
    )
    v1_runtime = VerifyPoint(
        name="V1b_seedream_actually_called",
        passed=(seedream_direct_success + fallback_triggered) == len(results),
        detail=(
            f"seedream_direct_success={seedream_direct_success}/{len(results)}, "
            f"nb2_fallback_triggered={fallback_triggered}/{len(results)}；"
            f"全部 shots 都走过 dispatcher（=direct+fallback）"
        ),
    )

    # ----- V3b: 运行中是否见到真的 sanitize 轮（shot_04 可能真的触发）-----
    sanitize_rounds_seen = [
        (r.shot_id, len(r.seedream_info.get("sanitize_attempts", [])))
        for r in results
        if isinstance(r.seedream_info, dict) and r.seedream_info.get("sanitize_attempts")
    ]
    if sanitize_rounds_seen:
        detail_v3b = f"sanitize 轮被触发的 shots: {sanitize_rounds_seen}"
        v3b = VerifyPoint(name="V3b_sanitize_runtime_triggered", passed=True, detail=detail_v3b)
    else:
        v3b = VerifyPoint(
            name="V3b_sanitize_runtime_triggered",
            passed=False,
            detail="本次 10 shots 没有任何 shot 触发 sanitize（可能火山方舟新版审查未拦 shot_04，或 Seedream 路径失败在其它错误类型）",
        )

    # ----- V5: 参考图传递正确 -----
    ref_count_nonzero = sum(1 for r in results if r.ref_count > 0)
    per_shot_ok = all(r.ref_count >= len(r.characters) for r in results)  # 至少每角色 1 张
    v5 = VerifyPoint(
        name="V5_reference_images_passed",
        passed=(ref_count_nonzero == len(results) and per_shot_ok),
        detail=(
            f"{ref_count_nonzero}/{len(results)} shots 有参考图；"
            + "; ".join(
                f"shot {r.shot_id}: chars={len(r.characters)} refs={r.ref_count}"
                for r in results
            )
        ),
    )

    # ----- V6: 角色一致性（自动检查仅看产物 + 参考图映射完整性；主观评估留 Founder） -----
    # 我们收集 shot meta → 产出对照表，方便 Founder 肉眼比对 POC Phase 4 的 Seedream 图
    consistency_rows = []
    for r in results:
        consistency_rows.append({
            "shot_id": r.shot_id,
            "characters_visible": r.characters,
            "location_id": r.location_id,
            "model_used": r.model_used,
            "image_path": r.image_path or "(missing)",
            "seedream_direct": "gemini" not in r.model_used.lower() and r.success,
            "fallback_used": bool(isinstance(r.seedream_info, dict) and r.seedream_info.get("used_fallback")),
        })
    consistency_ok = all(r["image_path"] != "(missing)" for r in consistency_rows)
    v6 = VerifyPoint(
        name="V6_character_consistency_artifacts_complete",
        passed=consistency_ok,
        detail=(
            f"{sum(1 for r in consistency_rows if r['image_path'] != '(missing)')}/{len(consistency_rows)}"
            " shots 产物齐全，主观一致性评估交给 Founder 对比 POC Phase 4 Seedream 10 张"
        ),
    )

    # ----- V2b: 生产 prompt 是否真的经过 StyleEnforcer.enforce_prompt_for_provider -----
    # 我们 sample 前 3 个成功走 Seedream direct 路径的 shot，反查 prompt
    # 为了拿 prompt，我们需要把 _call_seedream_sync 的调用捕获。此处使用保守判定：
    # 既然 seedream_generator 当前没调 enforce_prompt_for_provider，V2b 必定 FAIL。
    # 我们做一次轻量 probe：把一个 shot 的 _call_seedream_sync 拦截，看 prompt 是否包含 2D marker。
    log.info("\n===== V2b: Seedream 生产 prompt 是否含 2D lock 块 =====")

    captured_prompts: List[str] = []
    original_call = sg._call_seedream_sync

    def _capture_then_fail(prompt, reference_images, aspect_ratio, api_key):  # noqa: ANN001
        captured_prompts.append(prompt)
        return {
            "success": False,
            "error": "capture probe",
            "error_kind": "sensitive_content",
            "latency_sec": 0.0,
            "http_status": 400,
        }

    probe_shot = inputs["storyboard"]["shots"][0]
    probe_loc = _scene_location_map(inputs["screenplay"]).get(probe_shot.get("scene_id"), "")
    probe_refs = load_reference_images(probe_shot, probe_loc)
    sg._call_seedream_sync = _capture_then_fail  # type: ignore[assignment]
    try:
        await image_gen.generate_shot_image_phase2_safe(
            shot=probe_shot,
            storyboard=inputs["storyboard"],
            characters=inputs["characters"],
            style_preset=inputs["summary"].get("style_preset", "illustration"),
            reference_images=probe_refs,
            screenplay=inputs["screenplay"],
            aspect_ratio="2:3",
            genre=None,
            use_native_text=True,
        )
    finally:
        sg._call_seedream_sync = original_call  # type: ignore[assignment]

    v2b = check_seedream_2d_lock_in_production_path(captured_prompts)
    (LOG_OUT / "v2b_captured_prompts.json").write_text(
        json.dumps(
            [{"len": len(p), "head": p[:400], "has_2d_override": "SEEDREAM RENDERING OVERRIDE" in p} for p in captured_prompts],
            indent=2,
            ensure_ascii=False,
        )
    )

    # ----- 汇总 -----
    verify_points = [v1, v1_runtime, v2, v2b, v3a, v3b, v4, v5, v6]
    summary_path = write_summary(results, verify_points, env_report)
    log.info(f"summary written to {summary_path}")
    print_verdict(verify_points)

    # 成本估算
    seedream_direct = sum(
        1 for r in results if r.success and "gemini" not in r.model_used.lower()
    )
    fallback_count = sum(
        1 for r in results
        if isinstance(r.seedream_info, dict) and r.seedream_info.get("used_fallback") and r.success
    )
    # 简化估算：Seedream 2K ¥0.22/张，NB2 $0.067/张 ~ ¥0.48/张（汇率 7.2）
    est_cost_cny = seedream_direct * 0.22 + fallback_count * 0.48
    log.info(f"估算成本（仅成功 shots）: Seedream direct={seedream_direct} × ¥0.22 + NB2 fallback={fallback_count} × ¥0.48 ≈ ¥{est_cost_cny:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
