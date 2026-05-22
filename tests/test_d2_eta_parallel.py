"""
test_d2_eta_parallel.py — D2 ETA 并行加速修复验收测试

BUG-T13-ETA-OVERESTIMATE (2026-05-12):
- 旧算法：image_generation = 18 shots × ~60s 串行 = ~1080s（老基线）
- 新算法：image_generation = 18 shots × 60s / max_concurrent=3 = 360s（并行加速）
- 参考图阶段（image_preparation）保持串行不变

Round 2 (2026-05-13) — RISK-T14-4: 验证 dynamic 真生效（不是 dead code）
- actual_shot_count=18, max_concurrent=3 → image_generation=360s
- actual_shot_count=26, max_concurrent=3 → image_generation=520s（动态算，比 18 shots 多）
- actual_shot_count=18, max_concurrent=1 → image_generation=1080s（无并行）

测试方法:
- 直接从 pipeline_orchestrator.py 源文件提取 STAGE_DURATIONS / build_stage_durations /
  estimate_remaining（仅这 3 项不依赖外部 SDK），用 exec() 在隔离 namespace 中运行。
- 避开 pydantic_settings / google-genai 等 SDK 不在测试环境的问题。
- 与 test_wave6_full_regression.py 的静态分析方式互补：本文件做实际数值验证。
"""

import logging
import os
import sys

# 确保 project root 在 sys.path 上
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

_ORCHESTRATOR_PATH = os.path.join(PROJECT_ROOT, "app", "services", "pipeline_orchestrator.py")


def _load_eta_functions():
    """
    从 pipeline_orchestrator.py 源码中提取 STAGE_DURATIONS / build_stage_durations /
    estimate_remaining 并在隔离 namespace 中执行，绕过不可用的 SDK 依赖。

    这 3 个符号在文件顶部（L62-L174），早于任何 app.* import，纯 Python 实现。
    """
    with open(_ORCHESTRATOR_PATH) as f:
        content = f.read()

    start_marker = "STAGE_DURATIONS = {"
    end_marker = "class PipelineCostLimitExceeded"

    start_idx = content.index(start_marker)
    end_idx = content.index(end_marker)
    source_snippet = content[start_idx:end_idx]

    ns = {"logger": logging.getLogger("test_eta")}
    exec(compile(source_snippet, _ORCHESTRATOR_PATH, "exec"), ns)
    return ns


_eta_ns = _load_eta_functions()
STAGE_DURATIONS = _eta_ns["STAGE_DURATIONS"]
build_stage_durations = _eta_ns["build_stage_durations"]
estimate_remaining = _eta_ns["estimate_remaining"]


# ===========================================================================
# Original D2 tests (BUG-T13-ETA-OVERESTIMATE, 2026-05-12)
# ===========================================================================

def test_image_generation_eta_reflects_parallel():
    """
    D2 — BUG-T13-ETA-OVERESTIMATE: image_generation ETA 必须反映 max_concurrent=3 并行加速

    18 shots × 60s / max_concurrent=3 = 360s
    不是 18 shots × 60s = 1080s（串行老基线）
    """
    image_gen_seconds = STAGE_DURATIONS["image_generation"]

    # 验收标准：接近 18×60/3 = 360s（允许 ±20% 浮动）
    expected = 360  # 18 shots × 60s / max_concurrent=3
    serial_baseline = 18 * 60  # = 1080s（不并行时的估算）

    assert image_gen_seconds != serial_baseline, (
        f"image_generation ETA 仍是串行基线 {serial_baseline}s，"
        f"应该除以 max_concurrent=3，期望接近 {expected}s。"
        f"BUG-T13-ETA-OVERESTIMATE 未修复。"
    )

    assert image_gen_seconds <= serial_baseline / 2, (
        f"image_generation ETA={image_gen_seconds}s 仍过高（应 <= {serial_baseline // 2}s）。"
        f"期望接近 {expected}s（18 shots × 60s / 3）。"
    )

    assert image_gen_seconds > 0, "image_generation ETA 不能为 0"

    print(f"[D2 PASS] image_generation ETA={image_gen_seconds}s (期望接近 {expected}s, 串行基线={serial_baseline}s)")


def test_image_preparation_remains_serial():
    """
    D2 验收: 参考图阶段（image_preparation）保持串行，不应被 max_concurrent 除

    image_preparation 包含 portrait/fullbody 参考图生成（by design 串行，portrait→fullbody 有依赖）
    不应随 max_concurrent 缩短。
    """
    image_prep_seconds = STAGE_DURATIONS.get("image_preparation", 0)

    # image_preparation 应该是合理的串行估算（60s 左右，含参考图 API overhead）
    assert image_prep_seconds > 0, "image_preparation ETA 不能为 0"
    assert image_prep_seconds >= 30, (
        f"image_preparation ETA={image_prep_seconds}s 太短，"
        f"参考图阶段（portrait/fullbody + scene anchors）串行约需 60s+。"
    )

    print(f"[D2 PASS] image_preparation ETA={image_prep_seconds}s (serial by design)")


def test_estimate_remaining_image_generation_stage():
    """
    D2 验收: estimate_remaining("image_generation", 0) 接近 18×60/3 = 360s

    注意：estimate_remaining 包含当前 stage + 后续所有 stage 的总和。
    仅 image_generation 阶段本身应是 360s。
    """
    # 调用时 progress=0（刚进入 image_generation）
    remaining = estimate_remaining("image_generation", stage_progress=0.0)

    # 后续 stages: bgm=120, completed=0 → 总后续 = 120
    subsequent = sum(
        v for k, v in STAGE_DURATIONS.items()
        if list(STAGE_DURATIONS.keys()).index(k) > list(STAGE_DURATIONS.keys()).index("image_generation")
    )

    image_gen_only = STAGE_DURATIONS["image_generation"]

    # estimate_remaining 有 max(remaining, 5) 兜底
    assert remaining >= 5, f"estimate_remaining 不应返回 < 5"
    assert remaining >= image_gen_only, (
        f"estimate_remaining({remaining}s) 不应小于 image_generation 本身 ({image_gen_only}s)"
    )

    # 核心: image_generation 阶段本身（360s）不是串行基线（1080s）
    assert image_gen_only <= 500, (
        f"image_generation={image_gen_only}s 仍然过高（串行基线 18×60=1080s），"
        f"BUG-T13-ETA-OVERESTIMATE 未修复。期望 <= 500s。"
    )

    print(f"[D2 PASS] estimate_remaining('image_generation', 0) = {remaining}s")
    print(f"         image_gen_only={image_gen_only}s, subsequent={subsequent}s")


# ===========================================================================
# Round 2 tests (RISK-T14-4: dynamic ETA 真生效验证, 2026-05-13)
# ===========================================================================

def test_estimate_remaining_dynamic_shot_count_18():
    """
    Round 2 (2026-05-13) — RISK-T14-4: actual_shot_count=18, max_concurrent=3
    build_stage_durations["image_generation"] = 18 × 80 / 3 = 480s (T20-9 改 60→80)
    PM KEY_LEARNINGS: 'signature 加参数 != 参数被传值'，本测试验证 dynamic 真生效。
    """
    # RISK-T20-9 (2026-05-18): per_shot_seconds 60 → 80
    expected_image_gen = int(18 * 80 / 3)   # = 480

    dyn = build_stage_durations(actual_shot_count=18, max_concurrent=3)
    assert dyn["image_generation"] == expected_image_gen, (
        f"build_stage_durations(18, max_concurrent=3)['image_generation'] = {dyn['image_generation']}，"
        f"期望 {expected_image_gen}s"
    )

    remaining = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=18,
        max_concurrent=3,
    )
    assert remaining >= 5, f"estimate_remaining 不应返回 < 5"

    print(f"[D2-Round2 PASS] 18 shots, concurrent=3: image_gen={dyn['image_generation']}s, remaining={remaining}s")


def test_estimate_remaining_dynamic_shot_count_26():
    """
    Round 2 (2026-05-13) — RISK-T14-4: actual_shot_count=26, max_concurrent=3
    image_generation ETA = 26 × 80 / 3 = 693s (T20-9 改 60→80, 比 18 shots 多)
    验证 dynamic 真起作用：26 shot vs 18 shot 时 ETA 不同。
    """
    # RISK-T20-9 (2026-05-18): per_shot_seconds 60 → 80
    expected_26 = int(26 * 80 / 3)  # = 693

    dyn_26 = build_stage_durations(actual_shot_count=26, max_concurrent=3)
    assert dyn_26["image_generation"] == expected_26, (
        f"build_stage_durations(26, max_concurrent=3)['image_generation'] = {dyn_26['image_generation']}，"
        f"期望 {expected_26}s"
    )

    remaining_18 = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=18,
        max_concurrent=3,
    )
    remaining_26 = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=26,
        max_concurrent=3,
    )

    # 核心 dynamic 验证: 26 shots ETA 必须 > 18 shots ETA
    assert remaining_26 > remaining_18, (
        f"actual_shot_count=26 时 ETA({remaining_26}s) 应该 > actual_shot_count=18 时 ETA({remaining_18}s)。"
        f"Dynamic 算法未生效（dead code）。"
    )

    print(f"[D2-Round2 PASS] 18 shots ETA={remaining_18}s vs 26 shots ETA={remaining_26}s (dynamic confirmed)")
    print(f"                 image_gen_26={dyn_26['image_generation']}s (期望 {expected_26}s)")


def test_estimate_remaining_dynamic_max_concurrent_1():
    """
    Round 2 (2026-05-13) — RISK-T14-4: actual_shot_count=18, max_concurrent=1 (无并行)
    image_generation ETA = 18 × 80 / 1 = 1440s（串行基线, T20-9 改 60→80）
    验证并发参数真起作用：max_concurrent=1 vs 3 时 ETA 相差 3 倍。
    """
    # RISK-T20-9 (2026-05-18): per_shot_seconds 60 → 80
    expected_serial = int(18 * 80 / 1)  # = 1440

    dyn_1 = build_stage_durations(actual_shot_count=18, max_concurrent=1)
    assert dyn_1["image_generation"] == expected_serial, (
        f"build_stage_durations(18, max_concurrent=1)['image_generation'] = {dyn_1['image_generation']}，"
        f"期望 {expected_serial}s (串行基线)"
    )

    remaining_concurrent_3 = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=18,
        max_concurrent=3,
    )
    remaining_concurrent_1 = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=18,
        max_concurrent=1,
    )

    # 核心: max_concurrent=1 时 ETA 应该显著高于 max_concurrent=3
    assert remaining_concurrent_1 > remaining_concurrent_3, (
        f"max_concurrent=1 时 ETA({remaining_concurrent_1}s) 应该 > max_concurrent=3 时 ETA({remaining_concurrent_3}s)。"
        f"max_concurrent 参数未生效（dead code）。"
    )

    print(f"[D2-Round2 PASS] max_concurrent=3: ETA={remaining_concurrent_3}s vs max_concurrent=1: ETA={remaining_concurrent_1}s")
    print(f"                 image_gen_serial={dyn_1['image_generation']}s (期望 {expected_serial}s)")


# ===========================================================================
# Structural tests
# ===========================================================================

def test_all_stage_keys_present():
    """
    验证 STAGE_DURATIONS 包含所有必要的 stage key（不因修改 image_generation 而丢失其他 stage）
    """
    required_keys = [
        "story_generation", "character_design", "character_ready",
        "screenplay", "scenes_ready", "storyboard",
        "image_preparation", "image_generation",
        "bgm", "completed",
    ]

    for key in required_keys:
        assert key in STAGE_DURATIONS, f"STAGE_DURATIONS 缺少 key: {key!r}"

    print(f"[D2 PASS] STAGE_DURATIONS 含 {len(STAGE_DURATIONS)} 个 key，全部覆盖")
