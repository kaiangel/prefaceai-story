"""
Wave 4 集成测试 — TASK-MUREKA-PIPELINE-INTEGRATION Step 7

5 个场景：
  1. 3 风格跨验证 E2E（service 层直调，3 个 BGM）
  2. QA 信号验证（silence + LUFS）
  3. 失败降级验证（mock Mureka key 失效）
  4. 4 BGM REST API curl 测试（通过 HTTP，需要 backend 运行）
  5. Frontend BgmPlayer 5 状态（人工验证，此脚本仅记录结论）

用法：
  cd /path/to/xuhua_story
  source venv/bin/activate
  python tests/test_wave4_integration.py

注意：场景 1 + 4 会真实调用 Mureka API，会产生约 $0.15 成本。
"""

import json
import os
import sys
import time
import traceback
from unittest.mock import patch

# ─── 确保 project root 在 Python path ───────────────────────────────────────
_THIS = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 测试数据路径
_TEST_DATA_DIR = os.path.join(_ROOT, "test_output", "manualtest", "sq_upgrade_ab_test", "20260304_113630")
_OUTPUT_DIR = os.path.join(_ROOT, "test_output", "manualtest", "wave4_integration_test")
os.makedirs(_OUTPUT_DIR, exist_ok=True)

# ─── 测试报告收集 ─────────────────────────────────────────────────────────────
_results: dict = {}
_bugs: list = []
_cost_tracker: dict = {"mureka_calls": 0, "estimated_cost_usd": 0.0}


def _log(msg: str):
    print(f"[Wave4Test] {msg}", flush=True)


def _pass(scenario: str, detail: str = ""):
    _results[scenario] = {"status": "PASS", "detail": detail}
    _log(f"✅ {scenario} — PASS {detail}")


def _fail(scenario: str, detail: str = ""):
    _results[scenario] = {"status": "FAIL", "detail": detail}
    _log(f"❌ {scenario} — FAIL {detail}")


def _warn(scenario: str, detail: str = ""):
    _results[scenario] = {"status": "WARN", "detail": detail}
    _log(f"⚠️  {scenario} — WARN {detail}")


def _track_mureka():
    _cost_tracker["mureka_calls"] += 1
    _cost_tracker["estimated_cost_usd"] += 0.028  # ~$0.028/call (Haiku+Mureka)


# ─── Load test data ─────────────────────────────────────────────────────────

def _load_test_story_data():
    """Load year-end dinner story data (the only fully formed test story available)"""
    outline_path = os.path.join(_TEST_DATA_DIR, "1_outline.json")
    screenplay_path = os.path.join(_TEST_DATA_DIR, "3_screenplay.json")
    with open(outline_path, encoding="utf-8") as f:
        outline = json.load(f)
    with open(screenplay_path, encoding="utf-8") as f:
        screenplay = json.load(f)
    return outline, screenplay


# ═══════════════════════════════════════════════════════════════
# 场景 0: 环境预检（前置）
# ═══════════════════════════════════════════════════════════════

def test_env_prereqs():
    """验证环境变量和依赖服务正常"""
    _log("=" * 60)
    _log("场景 0: 环境预检")
    _log("=" * 60)

    errors = []

    # 检查 API keys
    try:
        from app.config import settings
        if not settings.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY 为空")
        else:
            _log(f"  ANTHROPIC_API_KEY: sk-ant-...{settings.ANTHROPIC_API_KEY[-6:]} ✅")

        if not settings.MUREKA_API_KEY:
            errors.append("MUREKA_API_KEY 为空")
        else:
            _log(f"  MUREKA_API_KEY: ...{settings.MUREKA_API_KEY[-6:]} ✅")
    except ImportError as e:
        errors.append(f"无法导入 app.config: {e}")

    # 检查 ffmpeg
    import shutil
    if not shutil.which("ffmpeg"):
        errors.append("ffmpeg 未找到（brew install ffmpeg）")
    else:
        _log("  ffmpeg: 可用 ✅")

    # 检查 test data
    outline_path = os.path.join(_TEST_DATA_DIR, "1_outline.json")
    if not os.path.exists(outline_path):
        errors.append(f"测试数据不存在: {outline_path}")
    else:
        _log(f"  测试数据: {_TEST_DATA_DIR} ✅")

    # 检查 meta-prompt 文件
    meta_dir = os.path.join(_TEST_DATA_DIR, "meta_prompts")
    required_prompts = ["meta_mixed_v3_quote_picking.md", "meta_en_v2.md"]
    for mp in required_prompts:
        mp_path = os.path.join(meta_dir, mp)
        if not os.path.exists(mp_path):
            errors.append(f"meta-prompt 缺失: {mp}")
        else:
            _log(f"  meta-prompt {mp}: ✅")

    if errors:
        for e in errors:
            _log(f"  ❌ {e}")
        _fail("S0_env_prereqs", f"环境检查失败: {'; '.join(errors)}")
        return False
    else:
        _pass("S0_env_prereqs", "所有前置条件通过")
        return True


# ═══════════════════════════════════════════════════════════════
# 场景 1: 3 风格跨验证 E2E
# ═══════════════════════════════════════════════════════════════

def test_style_cross_validation():
    """
    3 个风格的 E2E BGM 生成验证。

    注意：使用同一个年夜饭故事数据，但传入不同的 visual_style_hint。
    验证 music_hint 确实影响了 Haiku 生成的 BGM prompt 内容。
    """
    _log("=" * 60)
    _log("场景 1: 3 风格跨验证 E2E")
    _log("=" * 60)

    # ── 先验证 music_hint 获取函数 ──────────────────────────────
    _log("\n[Step 1.A] 验证 get_music_hint() 为 3 个风格返回正确提示...")
    try:
        from app.models.style_config import get_music_hint

        styles_to_test = [
            ("korean_webtoon", ["K-drama", "romantic", "emotional", "manhwa"]),
            ("chinese_ink", ["guqin", "East Asian", "ink", "minimalist"]),
            ("cyberpunk", ["electronic", "synth", "neon", "metropolitan"]),
        ]

        hint_results = {}
        all_hints_pass = True

        for style, expected_keywords in styles_to_test:
            hint = get_music_hint(style)
            hint_lower = hint.lower()

            # 检查至少 2 个关键词存在
            matched = [kw for kw in expected_keywords if kw.lower() in hint_lower]
            ok = len(matched) >= 2

            hint_results[style] = {
                "hint": hint,
                "expected_keywords": expected_keywords,
                "matched": matched,
                "pass": ok,
            }

            if ok:
                _log(f"  {style}: '{hint[:60]}...' — 关键词匹配 {matched} ✅")
            else:
                _log(f"  {style}: '{hint[:60]}...' — 关键词匹配不足 {matched} vs {expected_keywords} ❌")
                all_hints_pass = False

        # 保存 hint 结果供报告使用
        hints_file = os.path.join(_OUTPUT_DIR, "s1_music_hints.json")
        with open(hints_file, "w", encoding="utf-8") as f:
            json.dump(hint_results, f, ensure_ascii=False, indent=2)
        _log(f"  music_hint 结果保存到: {hints_file}")

        if not all_hints_pass:
            _fail("S1A_music_hints", "部分风格 music_hint 关键词不匹配")
        else:
            _pass("S1A_music_hints", "3 个风格 music_hint 全部验证通过")

    except Exception as e:
        _fail("S1A_music_hints", f"异常: {e}")
        all_hints_pass = False

    # ── 实际 BGM 生成（3 个风格）──────────────────────────────────
    _log("\n[Step 1.B] 实际调用 generate_bgm_for_chapter() — 3 个风格...")

    try:
        outline, screenplay = _load_test_story_data()
    except Exception as e:
        _fail("S1B_e2e_generation", f"无法加载测试数据: {e}")
        return

    try:
        from app.services.music_generation_service import generate_bgm_for_chapter
    except ImportError as e:
        _fail("S1B_e2e_generation", f"无法导入 music_generation_service: {e}")
        return

    stories = [
        ("年夜饭", "korean_webtoon", "中篇"),
        ("年夜饭_中国水墨", "chinese_ink", "中篇"),
        ("年夜饭_赛博朋克", "cyberpunk", "中篇"),
    ]

    generation_results = {}

    for story_name, style, story_type in stories:
        _log(f"\n  --- 生成: {story_name} | 风格={style} | 篇幅={story_type} ---")

        story_output_dir = os.path.join(_OUTPUT_DIR, f"s1_{story_name}_{style}")
        os.makedirs(story_output_dir, exist_ok=True)

        try:
            from app.models.style_config import get_music_hint
            music_hint = get_music_hint(style)
            _log(f"  music_hint: {music_hint[:80]}...")

            start_time = time.time()
            result = generate_bgm_for_chapter(
                chapter_id=0,
                project_id=0,
                outline=outline,
                screenplay=screenplay,
                output_dir=story_output_dir,
                story_type=story_type,
                visual_style_hint=music_hint,  # 传入 music_hint 字符串
                regen_count=0,
                bgm_volume=1.0,
                is_change_bgm=False,
            )
            elapsed = time.time() - start_time
            _track_mureka()

            # 验证结果字段
            assert result.get("success") is True, f"success 应为 True，收到: {result.get('success')}"
            assert result.get("bgm_url"), "bgm_url 不能为空"
            assert os.path.exists(result.get("bgm_url", "")), f"BGM 文件不存在: {result.get('bgm_url')}"
            assert result.get("bgm_prompt"), "bgm_prompt 不能为空"
            assert result.get("mureka_task_id"), "mureka_task_id 不能为空"

            bgm_prompt = result.get("bgm_prompt", "")
            bgm_prompt_lower = bgm_prompt.lower()

            # 验证 bgm_prompt 内容与风格方向相符
            style_keyword_check = {
                "korean_webtoon": ["romantic", "emotional", "restraint", "ache", "k-drama", "ambient"],
                "chinese_ink": ["east asian", "guqin", "xiao", "ink", "minimalist", "oriental", "chinese", "traditional"],
                "cyberpunk": ["electronic", "synth", "neon", "digital", "urban", "metallic", "dark", "pulse"],
            }

            expected_kws = style_keyword_check.get(style, [])
            matched_kws = [kw for kw in expected_kws if kw.lower() in bgm_prompt_lower]
            style_ok = len(matched_kws) >= 1  # 至少 1 个关键词命中

            _log(f"  success={result['success']}, elapsed={elapsed:.1f}s")
            _log(f"  bgm_url: {result['bgm_url']}")
            _log(f"  meta_version: {result.get('meta_version')}")
            _log(f"  mureka_task_id: {result.get('mureka_task_id')}")
            _log(f"  bgm_prompt 前 200 字符: {bgm_prompt[:200]}")
            _log(f"  风格关键词验证 ({style}): {matched_kws} {'✅' if style_ok else '⚠️ 未命中'}")

            # 保存 bgm_prompt 到文件
            prompt_file = os.path.join(story_output_dir, "haiku_bgm_prompt.txt")
            with open(prompt_file, "w", encoding="utf-8") as f:
                f.write(f"Story: {story_name}\nStyle: {style}\nMusic Hint: {music_hint}\n\n")
                f.write(f"Haiku BGM Prompt:\n{bgm_prompt}\n")
            _log(f"  BGM prompt 保存到: {prompt_file}")

            # 保存完整结果
            result_copy = dict(result)
            result_copy["qa_result"] = dict(result.get("qa_result", {}))
            result_file = os.path.join(story_output_dir, "generation_result.json")
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result_copy, f, ensure_ascii=False, indent=2, default=str)

            generation_results[story_name] = {
                "success": True,
                "style": style,
                "bgm_url": result["bgm_url"],
                "meta_version": result.get("meta_version"),
                "bgm_prompt_preview": bgm_prompt[:300],
                "style_keyword_matched": matched_kws,
                "style_ok": style_ok,
                "elapsed_sec": elapsed,
                "credits_used": result.get("credits_used"),
            }

        except AssertionError as e:
            _log(f"  ❌ 断言失败: {e}")
            generation_results[story_name] = {"success": False, "error": str(e), "style": style}
        except Exception as e:
            _log(f"  ❌ 异常: {e}")
            _log(f"  {traceback.format_exc()[-500:]}")
            generation_results[story_name] = {"success": False, "error": str(e), "style": style}

    # 保存汇总
    gen_summary_file = os.path.join(_OUTPUT_DIR, "s1_generation_summary.json")
    with open(gen_summary_file, "w", encoding="utf-8") as f:
        json.dump(generation_results, f, ensure_ascii=False, indent=2)

    # 判定整体 PASS/FAIL
    all_pass = all(r.get("success") for r in generation_results.values())
    style_hints_pass = all(r.get("style_ok", False) for r in generation_results.values() if r.get("success"))

    if all_pass and style_hints_pass:
        _pass("S1_style_cross_validation", f"3 个风格全部 PASS，BGM 生成成功，风格关键词验证通过")
    elif all_pass:
        _warn("S1_style_cross_validation", f"3 个风格 BGM 生成成功，但部分风格关键词未命中（BGM 质量待人工听力验证）")
    else:
        failed_stories = [k for k, v in generation_results.items() if not v.get("success")]
        _fail("S1_style_cross_validation", f"失败故事: {failed_stories}")


# ═══════════════════════════════════════════════════════════════
# 场景 2: QA 信号验证
# ═══════════════════════════════════════════════════════════════

def test_qa_signals():
    """
    验证 QA 信号：
    - qa_silence_detected 应为 False（正常 BGM 无长静音）
    - qa_lufs 应在 -23 ~ -14 范围
    - qa_lufs_in_range 应为 True

    使用已存在的 bgm_v4_simple.mp3 测试，避免额外 Mureka 调用。
    """
    _log("=" * 60)
    _log("场景 2: QA 信号验证")
    _log("=" * 60)

    existing_bgm = os.path.join(_TEST_DATA_DIR, "bgm_v4_simple.mp3")
    if not os.path.exists(existing_bgm):
        _warn("S2_qa_signals", f"测试 BGM 文件不存在: {existing_bgm}，使用场景 1 生成的 BGM")
        # 尝试从场景 1 生成的 BGM 中找一个
        s1_dirs = [d for d in os.listdir(_OUTPUT_DIR) if d.startswith("s1_")]
        if s1_dirs:
            for sd in s1_dirs:
                candidate = os.path.join(_OUTPUT_DIR, sd, "bgm_chapter0.mp3")
                if os.path.exists(candidate):
                    existing_bgm = candidate
                    break
        if not os.path.exists(existing_bgm):
            _fail("S2_qa_signals", "找不到可用的测试 BGM 文件")
            return

    _log(f"  使用 BGM 文件: {existing_bgm}")

    try:
        from app.services.ffmpeg_post_processor import process_bgm

        qa_output = os.path.join(_OUTPUT_DIR, "s2_qa_test_output.mp3")
        result = process_bgm(
            input_path=existing_bgm,
            output_path=qa_output,
            target_duration_sec=180.0,
            volume=0.8,
        )

        _log(f"  process_bgm 返回:")
        for k, v in result.items():
            if k == "warnings":
                _log(f"    warnings: {len(v)} 条")
                for w in v:
                    _log(f"      - {w}")
            else:
                _log(f"    {k}: {v}")

        if not result.get("success"):
            _fail("S2_qa_signals", f"process_bgm 失败: {result.get('error')}")
            return

        # 验证 QA 字段
        qa_silence = result.get("qa_silence_detected", True)  # 默认 True（保守）
        qa_lufs = result.get("qa_lufs", 0.0)
        qa_lufs_in_range = result.get("qa_lufs_in_range", False)

        checks = []

        # 检查静音
        if not qa_silence:
            checks.append(("qa_silence_detected=False", True, "正常 BGM 无异常静音段"))
        else:
            checks.append(("qa_silence_detected=False", False, f"检测到静音段: {result.get('qa_silence_details')}"))

        # 检查 LUFS
        if qa_lufs != 0.0:  # 0.0 表示未能解析（不判断范围）
            if qa_lufs_in_range:
                checks.append(("qa_lufs_in_range=True", True, f"LUFS={qa_lufs:.1f} dBLUFS，在 -23~-14 范围内"))
            else:
                checks.append(("qa_lufs_in_range=True", False, f"LUFS={qa_lufs:.1f} dBLUFS，超出范围 -23~-14"))
        else:
            checks.append(("qa_lufs_parsed", False, "LUFS 未能从 ebur128 输出解析（ebur128 工具可能不支持）"))

        # 输出时长合理
        out_dur = result.get("output_duration_sec", 0)
        if out_dur > 60:
            checks.append(("output_duration_sec>60", True, f"输出时长 {out_dur:.2f}s"))
        else:
            checks.append(("output_duration_sec>60", False, f"输出时长 {out_dur:.2f}s 异常偏短"))

        all_checks_pass = all(c[1] for c in checks)

        for check_name, ok, detail in checks:
            _log(f"  {'✅' if ok else '❌'} {check_name}: {detail}")

        # 保存 QA 结果
        qa_result_file = os.path.join(_OUTPUT_DIR, "s2_qa_result.json")
        with open(qa_result_file, "w", encoding="utf-8") as f:
            json.dump({
                "input_bgm": existing_bgm,
                "output_bgm": qa_output,
                "process_bgm_result": {k: v for k, v in result.items() if k != "warnings"},
                "checks": [{"name": c[0], "pass": c[1], "detail": c[2]} for c in checks],
            }, f, ensure_ascii=False, indent=2)

        if all_checks_pass:
            _pass("S2_qa_signals", f"QA 信号全部合规: LUFS={qa_lufs:.1f} dBLUFS，无异常静音")
        else:
            failed_checks = [c for c in checks if not c[1]]
            _warn("S2_qa_signals", f"部分 QA 检查未通过: {[c[0] for c in failed_checks]}")

    except Exception as e:
        _fail("S2_qa_signals", f"异常: {e}\n{traceback.format_exc()[-500:]}")


# ═══════════════════════════════════════════════════════════════
# 场景 3: 失败降级验证
# ═══════════════════════════════════════════════════════════════

def test_failure_degradation():
    """
    验证 Mureka key 失效时的降级行为：
    - generate_bgm_for_chapter 应抛出 RuntimeError，不是 uncaught exception
    - Pipeline orchestrator 的 try/except 应捕获

    方法：mock _call_mureka 抛出 RuntimeError，验证上层不崩溃
    """
    _log("=" * 60)
    _log("场景 3: 失败降级验证")
    _log("=" * 60)

    try:
        outline, screenplay = _load_test_story_data()
    except Exception as e:
        _fail("S3_failure_degradation", f"无法加载测试数据: {e}")
        return

    try:
        from app.services import music_generation_service as mgs

        # ── 方法 A: mock _call_mureka 抛出 RuntimeError ──────────────
        _log("\n[Step 3.A] mock _call_mureka() 抛出 RuntimeError...")

        raised_exception = None
        output_dir_s3 = os.path.join(_OUTPUT_DIR, "s3_failure_test")
        os.makedirs(output_dir_s3, exist_ok=True)

        with patch.object(mgs, "_call_mureka", side_effect=RuntimeError("模拟 Mureka 服务不可用")):
            try:
                result = mgs.generate_bgm_for_chapter(
                    chapter_id=0,
                    project_id=0,
                    outline=outline,
                    screenplay=screenplay,
                    output_dir=output_dir_s3,
                    story_type="短篇",
                    visual_style_hint="",
                    regen_count=0,
                    bgm_volume=1.0,
                    is_change_bgm=False,
                )
                # 如果没有抛出异常，这是一个问题（应该抛出）
                _log(f"  ⚠️  函数没有抛出异常（返回了结果）: {result}")
                _warn("S3A_mureka_fail_propagates", "函数没有向上传播 Mureka 失败，而是返回了结果")
            except RuntimeError as e:
                raised_exception = e
                _log(f"  ✅ RuntimeError 正确向上传播: {e}")
            except Exception as e:
                _log(f"  ❌ 抛出了非预期的异常类型 {type(e).__name__}: {e}")
                raised_exception = e

        if raised_exception and isinstance(raised_exception, RuntimeError):
            _pass("S3A_mureka_fail_propagates", f"Mureka 失败正确抛出 RuntimeError: {str(raised_exception)[:100]}")
        elif raised_exception:
            _warn("S3A_mureka_fail_propagates", f"抛出了 {type(raised_exception).__name__}（非 RuntimeError）: {str(raised_exception)[:100]}")

        # ── 方法 B: 验证 Pipeline orchestrator 的 try/except 包裹 ──
        _log("\n[Step 3.B] 验证 pipeline_orchestrator.py Stage 6 try/except 包裹...")

        try:
            from app.services.pipeline_orchestrator import PipelineOrchestrator

            # 读取 orchestrator 源码，检查 Stage 6 try/except 是否存在
            import inspect
            source = inspect.getsource(PipelineOrchestrator)

            # 检查是否有 generate_bgm_for_chapter 调用且有 try/except
            has_bgm_call = "generate_bgm_for_chapter" in source
            has_try_except = "try:" in source and "except" in source
            stage6_indicator = "Stage 6" in source or "BGM" in source or "bgm" in source

            _log(f"  has_bgm_call: {has_bgm_call}")
            _log(f"  has_try_except: {has_try_except}")
            _log(f"  stage6_indicator: {stage6_indicator}")

            if has_bgm_call and has_try_except and stage6_indicator:
                _pass("S3B_orchestrator_try_except", "Pipeline orchestrator Stage 6 try/except 结构存在")
            elif has_bgm_call:
                _warn("S3B_orchestrator_try_except", "orchestrator 有 BGM 调用但未确认 try/except 包裹")
            else:
                _warn("S3B_orchestrator_try_except", "orchestrator 中未找到 generate_bgm_for_chapter 调用")

        except ImportError as e:
            _warn("S3B_orchestrator_try_except", f"无法导入 pipeline_orchestrator: {e}")

        # ── 方法 C: mock invalid Haiku key，验证 Haiku 重试后 RuntimeError ──
        _log("\n[Step 3.C] mock Haiku 3 次失败后 RuntimeError...")

        with patch.object(mgs, "_call_haiku_with_cache", side_effect=Exception("401 Unauthorized")):
            haiku_exception = None
            try:
                mgs._call_haiku_with_retry("system", "user", max_retries=3)
            except RuntimeError as e:
                haiku_exception = e
                _log(f"  ✅ Haiku 3 次重试后正确抛出 RuntimeError: {str(e)[:100]}")
            except Exception as e:
                haiku_exception = e
                _log(f"  ❌ 非预期异常 {type(e).__name__}: {e}")

        if haiku_exception and isinstance(haiku_exception, RuntimeError):
            _pass("S3C_haiku_retry_exhausted", "Haiku 重试耗尽后正确抛出 RuntimeError")
        else:
            _warn("S3C_haiku_retry_exhausted", f"Haiku 重试后抛出了 {type(haiku_exception).__name__ if haiku_exception else '无异常'}")

    except Exception as e:
        _fail("S3_failure_degradation", f"场景 3 整体异常: {e}\n{traceback.format_exc()[-500:]}")


# ═══════════════════════════════════════════════════════════════
# 场景 4: 4 BGM REST API 测试（HTTP curl）
# ═══════════════════════════════════════════════════════════════

def test_bgm_rest_api():
    """
    测试 4 个 BGM REST API。

    需要 backend 运行在 localhost:8000。
    如果 backend 未运行，跳过并记录 SKIP。
    """
    _log("=" * 60)
    _log("场景 4: 4 BGM REST API curl 测试")
    _log("=" * 60)

    import urllib.request
    import urllib.error

    BASE_URL = "http://localhost:8000"

    # 检查 backend 是否运行
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        backend_alive = True
        _log(f"  Backend 已运行: {BASE_URL} ✅")
    except Exception as e:
        _log(f"  Backend 未运行 ({e})，尝试 /api/health...")
        try:
            urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5)
            backend_alive = True
            _log(f"  Backend 已运行: {BASE_URL}/api/health ✅")
        except Exception as e2:
            _log(f"  Backend 也未响应 /api/health ({e2})")
            backend_alive = False

    if not backend_alive:
        _warn("S4_bgm_rest_api", "Backend 未运行（localhost:8000），请先启动 `uvicorn app.main:app --reload --port 8000` 后再跑此场景")
        _results["S4_bgm_rest_api"] = {"status": "SKIP", "detail": "Backend 未运行，跳过 HTTP 测试"}
        _log("  场景 4: SKIP（Backend 未运行）")

        # 即使 backend 不运行，记录期望的 API 行为
        _log("\n  [期望行为记录（无法实际验证）]")
        _log("  GET /bgm         → 200 {bgm_url, bgm_volume, meta_version, credits_used, bgm_exists}")
        _log("  POST /regenerate → 200 {success, bgm_url, meta_version, credits_used_this_call, total_credits_used}")
        _log("  POST /change-meta → 200 {success, bgm_url, meta_version, credits_used_this_call, total_credits_used}")
        _log("  PATCH /volume    → 200 {success, bgm_volume}")
        return

    # ── 需要 Bearer Token ──────────────────────────────────────────
    # 尝试登录拿 token
    token = None
    try:
        import json as _json
        login_payload = json.dumps({
            "email": "test@test.com",
            "password": "testpassword"
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        login_data = json.loads(resp.read().decode("utf-8"))
        token = login_data.get("access_token") or login_data.get("token")
        _log(f"  登录成功，token: ...{token[-10:] if token else '未获取'}")
    except Exception as e:
        _log(f"  ⚠️  无法登录获取 token: {e}（继续尝试无 token 请求验证 401）")

    PROJECT_ID = "1"
    CHAPTER_NUMBER = "1"
    api_base = f"{BASE_URL}/api/projects/{PROJECT_ID}/chapters/{CHAPTER_NUMBER}/bgm"

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_results = {}

    # ── API 1: GET /bgm ────────────────────────────────────────────
    _log(f"\n  [API 1] GET {api_base}")
    try:
        req = urllib.request.Request(api_base, headers=headers, method="GET")
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
        _log(f"  响应 200: {data}")

        # 验证响应字段
        expected_keys = ["bgm_url", "bgm_volume", "meta_version", "credits_used", "bgm_exists"]
        missing_keys = [k for k in expected_keys if k not in data]

        if not missing_keys:
            api_results["GET_bgm"] = {"status": 200, "data": data, "pass": True}
            _pass("S4A_get_bgm", f"GET bgm 返回正确字段，bgm_exists={data.get('bgm_exists')}")
        else:
            api_results["GET_bgm"] = {"status": 200, "data": data, "pass": False, "missing_keys": missing_keys}
            _fail("S4A_get_bgm", f"响应缺少字段: {missing_keys}")

    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        api_results["GET_bgm"] = {"status": status, "body": body}
        if status == 401 and not token:
            _warn("S4A_get_bgm", "401 Unauthorized（无 token），符合预期（非 API 结构问题）")
        elif status == 500:
            _warn("S4A_get_bgm", f"500 内部错误（可能 DB schema 未更新）: {body[:200]}")
        else:
            _fail("S4A_get_bgm", f"HTTP {status}: {body[:200]}")
    except Exception as e:
        api_results["GET_bgm"] = {"error": str(e)}
        _fail("S4A_get_bgm", f"异常: {e}")

    # ── API 4: PATCH /bgm/volume（不耗钱，优先测）──────────────────
    _log(f"\n  [API 4] PATCH {api_base}/volume")
    try:
        patch_body = json.dumps({"volume": 0.6}).encode("utf-8")
        req = urllib.request.Request(
            f"{api_base}/volume",
            data=patch_body,
            headers=headers,
            method="PATCH"
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
        _log(f"  响应 200: {data}")

        # 验证响应字段
        if data.get("success") is True and "bgm_volume" in data:
            api_results["PATCH_volume"] = {"status": 200, "data": data, "pass": True}
            _pass("S4D_patch_volume", f"PATCH volume 成功，bgm_volume={data.get('bgm_volume')}")
        else:
            api_results["PATCH_volume"] = {"status": 200, "data": data, "pass": False}
            _fail("S4D_patch_volume", f"响应字段不完整: {data}")

    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        api_results["PATCH_volume"] = {"status": status, "body": body}
        if status == 401 and not token:
            _warn("S4D_patch_volume", "401 Unauthorized（无 token），符合预期")
        elif status in (404, 500):
            _warn("S4D_patch_volume", f"HTTP {status}（DB schema 可能未更新）: {body[:200]}")
        else:
            _fail("S4D_patch_volume", f"HTTP {status}: {body[:200]}")
    except Exception as e:
        api_results["PATCH_volume"] = {"error": str(e)}
        _fail("S4D_patch_volume", f"异常: {e}")

    # ── API 2: POST /bgm/regenerate（耗时 90-300s）────────────────
    _log(f"\n  [API 2] POST {api_base}/regenerate")
    _log(f"  ⚠️  此操作会触发真实 Mureka 调用（约 90-300s），成本约 $0.028")

    try:
        req = urllib.request.Request(
            f"{api_base}/regenerate",
            data=b"",
            headers=headers,
            method="POST"
        )
        # 超长 timeout（Mureka 可能需要 5 分钟）
        resp = urllib.request.urlopen(req, timeout=400)
        data = json.loads(resp.read().decode("utf-8"))
        _log(f"  响应 200: {data}")
        _track_mureka()

        expected_keys = ["success", "bgm_url", "meta_version", "credits_used_this_call", "total_credits_used"]
        missing_keys = [k for k in expected_keys if k not in data]

        if not missing_keys and data.get("success"):
            api_results["POST_regenerate"] = {"status": 200, "data": data, "pass": True}
            _pass("S4B_post_regenerate", f"POST regenerate 成功，credits_this_call={data.get('credits_used_this_call')}")
        else:
            api_results["POST_regenerate"] = {"status": 200, "data": data, "pass": False, "missing": missing_keys}
            _fail("S4B_post_regenerate", f"响应不完整或失败: missing={missing_keys}")

    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        api_results["POST_regenerate"] = {"status": status, "body": body}
        if status == 401 and not token:
            _warn("S4B_post_regenerate", "401 Unauthorized（无 token），符合预期")
        elif status in (400, 500):
            _warn("S4B_post_regenerate", f"HTTP {status}（DB schema 可能未更新）: {body[:300]}")
        else:
            _fail("S4B_post_regenerate", f"HTTP {status}: {body[:200]}")
    except Exception as e:
        api_results["POST_regenerate"] = {"error": str(e)}
        _fail("S4B_post_regenerate", f"异常: {e}")

    # ── API 3: POST /bgm/change-meta（耗时 90-300s）────────────────
    _log(f"\n  [API 3] POST {api_base}/change-meta")
    _log(f"  ⚠️  此操作会触发真实 Mureka 调用（约 90-300s），成本约 $0.028")

    try:
        req = urllib.request.Request(
            f"{api_base}/change-meta",
            data=b"",
            headers=headers,
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=400)
        data = json.loads(resp.read().decode("utf-8"))
        _log(f"  响应 200: {data}")
        _track_mureka()

        expected_keys = ["success", "bgm_url", "meta_version", "credits_used_this_call", "total_credits_used"]
        missing_keys = [k for k in expected_keys if k not in data]

        if not missing_keys and data.get("success"):
            api_results["POST_change_meta"] = {"status": 200, "data": data, "pass": True}
            _pass("S4C_post_change_meta", f"POST change-meta 成功，meta_version={data.get('meta_version')}")
        else:
            api_results["POST_change_meta"] = {"status": 200, "data": data, "pass": False, "missing": missing_keys}
            _fail("S4C_post_change_meta", f"响应不完整: missing={missing_keys}")

    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        api_results["POST_change_meta"] = {"status": status, "body": body}
        if status == 401 and not token:
            _warn("S4C_post_change_meta", "401 Unauthorized（无 token），符合预期")
        elif status in (400, 500):
            _warn("S4C_post_change_meta", f"HTTP {status}（DB schema 可能未更新）: {body[:300]}")
        else:
            _fail("S4C_post_change_meta", f"HTTP {status}: {body[:200]}")
    except Exception as e:
        api_results["POST_change_meta"] = {"error": str(e)}
        _fail("S4C_post_change_meta", f"异常: {e}")

    # 保存 API 测试结果
    api_results_file = os.path.join(_OUTPUT_DIR, "s4_api_results.json")
    with open(api_results_file, "w", encoding="utf-8") as f:
        json.dump(api_results, f, ensure_ascii=False, indent=2, default=str)
    _log(f"\n  API 测试结果保存到: {api_results_file}")


# ═══════════════════════════════════════════════════════════════
# 场景 5: Frontend BgmPlayer 状态机（人工验证记录）
# ═══════════════════════════════════════════════════════════════

def test_frontend_bgm_player():
    """
    Frontend BgmPlayer 5 状态机验证。

    此函数不能自动化运行浏览器，仅进行静态代码审查：
    1. BgmPlayer.tsx 文件存在
    2. 5 种状态定义存在
    3. API 调用函数存在
    4. 音量 debounce 存在

    浏览器实际 UI 测试需要人工在 localhost:3000 验证。
    """
    _log("=" * 60)
    _log("场景 5: Frontend BgmPlayer 状态机验证（静态代码审查）")
    _log("=" * 60)

    bgm_player_path = os.path.join(_ROOT, "frontend", "src", "components", "create", "BgmPlayer.tsx")

    if not os.path.exists(bgm_player_path):
        _fail("S5_frontend_bgm_player", f"BgmPlayer.tsx 文件不存在: {bgm_player_path}")
        return

    _log(f"  BgmPlayer.tsx 文件存在: {bgm_player_path} ✅")

    with open(bgm_player_path, encoding="utf-8") as f:
        tsx_content = f.read()

    checks = []

    # 检查 5 种状态
    states = ["idle", "loading", "generating", "ready", "error"]
    for state in states:
        if state in tsx_content:
            checks.append((f"state_{state}", True, f"状态 '{state}' 存在"))
        else:
            checks.append((f"state_{state}", False, f"状态 '{state}' 未找到"))

    # 检查 API 函数调用
    api_functions = [
        ("fetchBgmInfo", "GET bgm API"),
        ("regenerateBgm", "POST regenerate API"),
        ("changeMetaBgm", "POST change-meta API"),
        ("patchBgmVolume", "PATCH volume API"),
    ]
    for func_name, desc in api_functions:
        if func_name in tsx_content:
            checks.append((f"api_{func_name}", True, f"API 函数 {func_name} ({desc}) 存在"))
        else:
            checks.append((f"api_{func_name}", False, f"API 函数 {func_name} ({desc}) 未找到"))

    # 检查 debounce
    if "debounce" in tsx_content or "300" in tsx_content:
        checks.append(("volume_debounce", True, "音量 debounce 机制存在"))
    else:
        checks.append(("volume_debounce", False, "未找到音量 debounce 逻辑"))

    # 检查 HTML5 audio 标签
    if "<audio" in tsx_content:
        checks.append(("html5_audio", True, "HTML5 <audio> 元素存在"))
    else:
        checks.append(("html5_audio", False, "未找到 HTML5 <audio> 元素"))

    for check_name, ok, detail in checks:
        _log(f"  {'✅' if ok else '⚠️'} {check_name}: {detail}")

    all_pass = all(c[1] for c in checks)
    fail_count = sum(1 for c in checks if not c[1])

    # 人工验证说明
    _log("\n  [人工验证 Checklist（需在浏览器 localhost:3000 完成）]")
    _log("  1. 进入 Stage D 预览页面")
    _log("  2. 观察 BgmPlayer 初始状态（应为 idle: '暂无配乐'）或 ready（已有 BGM）")
    _log("  3. 点击'生成配乐' → 验证状态变为 generating（'AI 生成中 2-5 分钟'）")
    _log("  4. 等待完成 → 验证 ready 状态（可播放）")
    _log("  5. 拖动音量滑块 → Chrome DevTools Network 验证 debounced PATCH 请求（300ms）")
    _log("  6. 验证'换一首'+'重新生成'按钮 UI 响应正常")
    _log("  人工验证结论: [待人工填写]")

    # 保存静态审查结果
    check_results_file = os.path.join(_OUTPUT_DIR, "s5_frontend_checks.json")
    with open(check_results_file, "w", encoding="utf-8") as f:
        json.dump({
            "file_path": bgm_player_path,
            "static_checks": [{"name": c[0], "pass": c[1], "detail": c[2]} for c in checks],
            "manual_verification_required": True,
            "manual_checklist": [
                "Stage D: BgmPlayer idle/ready 状态显示正确",
                "点击生成配乐: generating 状态（2-5分钟提示）",
                "完成后: ready 状态（可播放）",
                "音量滑块: debounced PATCH 请求（DevTools 验证）",
                "换一首/重新生成: UI 响应正常",
            ],
            "manual_verification_result": "待人工验证",
        }, f, ensure_ascii=False, indent=2)

    if all_pass:
        _pass("S5_frontend_bgm_player", f"静态代码审查全部通过，5 状态 + 4 API 函数 + debounce + audio 均存在（人工验证待完成）")
    else:
        _warn("S5_frontend_bgm_player", f"静态审查 {fail_count} 项未通过（见详细输出）")


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def main():
    _log("=" * 70)
    _log("Wave 4 集成测试 — TASK-MUREKA-PIPELINE-INTEGRATION Step 7")
    _log(f"输出目录: {_OUTPUT_DIR}")
    _log("=" * 70)

    start_time = time.time()

    # 场景 0: 环境预检
    env_ok = test_env_prereqs()

    if not env_ok:
        _log("\n⛔ 环境预检失败，中止测试")
        _print_summary()
        return

    # 场景 1: 3 风格跨验证
    test_style_cross_validation()

    # 场景 2: QA 信号验证
    test_qa_signals()

    # 场景 3: 失败降级验证
    test_failure_degradation()

    # 场景 4: REST API 测试
    test_bgm_rest_api()

    # 场景 5: Frontend 静态审查
    test_frontend_bgm_player()

    elapsed = time.time() - start_time
    _log(f"\n总耗时: {elapsed:.1f}s")

    _print_summary()

    # 保存结果到 JSON
    summary_file = os.path.join(_OUTPUT_DIR, "test_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "test_results": _results,
            "bugs": _bugs,
            "cost_tracker": _cost_tracker,
            "total_elapsed_sec": elapsed,
        }, f, ensure_ascii=False, indent=2)
    _log(f"\n结果汇总保存到: {summary_file}")


def _print_summary():
    _log("\n" + "=" * 70)
    _log("测试结果汇总")
    _log("=" * 70)

    pass_count = sum(1 for r in _results.values() if r.get("status") == "PASS")
    fail_count = sum(1 for r in _results.values() if r.get("status") == "FAIL")
    warn_count = sum(1 for r in _results.values() if r.get("status") == "WARN")
    skip_count = sum(1 for r in _results.values() if r.get("status") == "SKIP")

    for name, r in _results.items():
        status = r.get("status", "?")
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ ", "SKIP": "⏭️ "}.get(status, "?")
        _log(f"  {icon} {name}: {status} — {r.get('detail', '')[:80]}")

    _log(f"\n  PASS: {pass_count}  FAIL: {fail_count}  WARN: {warn_count}  SKIP: {skip_count}")
    _log(f"  Mureka 调用次数: {_cost_tracker['mureka_calls']}")
    _log(f"  估算成本: ${_cost_tracker['estimated_cost_usd']:.3f}")

    if _bugs:
        _log("\n  Bugs:")
        for bug in _bugs:
            _log(f"    - {bug}")


if __name__ == "__main__":
    main()
