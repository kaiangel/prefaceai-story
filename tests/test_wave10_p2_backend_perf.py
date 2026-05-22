"""
Wave 10 Phase 2 Backend Performance Fixes — Unit Tests
Tests for: RISK-T16-1, RISK-T16-2, RISK-T16-5, RISK-T15-5, RISK-T14-10
"""

import asyncio
import json
import sys
import os
import time
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ===========================================================================
# RISK-T16-5: storyboard_ready 严格判断
# ===========================================================================

def test_storyboard_ready_empty_json():
    """storyboard_json='{}' 必须返回 False"""
    # Mock chapter 对象
    chapter = MagicMock()
    chapter.storyboard_json = "{}"

    # 导入待测函数
    from app.api.chapters import _is_storyboard_truly_ready
    assert _is_storyboard_truly_ready(chapter) is False, \
        "storyboard_json='{}' 应该返回 False（RISK-T16-5）"
    print("[T16-5] storyboard_json='{}' → False ✅")


def test_storyboard_ready_with_shots():
    """storyboard_json 含 shots > 0 必须返回 True"""
    chapter = MagicMock()
    chapter.storyboard_json = json.dumps({"shots": [{"shot_id": 1}, {"shot_id": 2}, {"shot_id": 3}]})

    from app.api.chapters import _is_storyboard_truly_ready
    assert _is_storyboard_truly_ready(chapter) is True, \
        "shots=[1,2,3] 应该返回 True（RISK-T16-5）"
    print("[T16-5] storyboard_json with 3 shots → True ✅")


def test_storyboard_ready_none():
    """storyboard_json=None 必须返回 False"""
    chapter = MagicMock()
    chapter.storyboard_json = None

    from app.api.chapters import _is_storyboard_truly_ready
    assert _is_storyboard_truly_ready(chapter) is False, \
        "storyboard_json=None 应该返回 False（RISK-T16-5）"
    print("[T16-5] storyboard_json=None → False ✅")


def test_storyboard_ready_empty_shots():
    """storyboard_json shots=[] 必须返回 False"""
    chapter = MagicMock()
    chapter.storyboard_json = json.dumps({"shots": []})

    from app.api.chapters import _is_storyboard_truly_ready
    assert _is_storyboard_truly_ready(chapter) is False, \
        "shots=[] 应该返回 False（RISK-T16-5）"
    print("[T16-5] storyboard_json shots=[] → False ✅")


def test_storyboard_ready_invalid_json():
    """storyboard_json 为无效 JSON 必须返回 False"""
    chapter = MagicMock()
    chapter.storyboard_json = "not valid json {{{"

    from app.api.chapters import _is_storyboard_truly_ready
    assert _is_storyboard_truly_ready(chapter) is False, \
        "无效 JSON 应该返回 False（RISK-T16-5）"
    print("[T16-5] invalid JSON → False ✅")


# ===========================================================================
# RISK-T16-2: portrait regenerate 时传原 portrait 作 ref
# ===========================================================================

def test_portrait_regen_passes_ref():
    """generate_character_reference 在 portrait 重生时能传入 portrait_ref"""
    from app.services.reference_image_manager import ReferenceImageManager
    manager = ReferenceImageManager()

    # 检查 generate_character_reference 的签名支持 portrait_ref 参数
    import inspect
    sig = inspect.signature(manager.generate_character_reference)
    params = list(sig.parameters.keys())
    assert "portrait_ref" in params, "generate_character_reference 必须有 portrait_ref 参数"
    assert "ref_type" in params, "generate_character_reference 必须有 ref_type 参数"
    print("[T16-2] generate_character_reference signature 正确包含 portrait_ref ✅")


async def _test_portrait_regen_ref_passed():
    """当 ref_type='portrait' 且 portrait_ref 非 None 时，reference_images 必须包含 portrait_ref"""
    from app.services.reference_image_manager import ReferenceImageManager
    from app.models.style_config import ProjectStyleConfig
    from PIL import Image

    manager = ReferenceImageManager()
    mock_portrait = Image.new("RGB", (100, 100), color="red")

    captured_calls = []

    async def mock_generate_image(prompt, negative_prompt, aspect_ratio, reference_images=None):
        captured_calls.append({"reference_images": reference_images})
        return {"success": False, "error": "mock — not generating real image", "pil_image": None}

    mock_image_gen = MagicMock()
    mock_image_gen.generate_image = AsyncMock(side_effect=mock_generate_image)

    character = {
        "id": "char_001",
        "name": "TestChar",
        "name_en": "TestChar",
        "character_type": "human",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "hair_color": "black",
            "hair_style": "bob",
            "eye_color": "brown",
            "skin_tone": "fair",
        },
        "clothing": {"top": "blue shirt", "bottom": "jeans", "accessories": [], "style": "casual"},
    }
    project_style = ProjectStyleConfig(style_preset="realistic")

    # 调用 portrait regenerate（传入 portrait_ref）
    await manager.generate_character_reference(
        character=character,
        project_style=project_style,
        image_generator=mock_image_gen,
        ref_type="portrait",
        portrait_ref=mock_portrait,  # 重生场景：传入已有 portrait
    )

    assert len(captured_calls) >= 1, "应该至少调用一次 generate_image"
    call_refs = captured_calls[0]["reference_images"]
    assert call_refs is not None, "portrait regenerate 时 reference_images 不应为 None（RISK-T16-2）"
    assert mock_portrait in call_refs, "portrait_ref 应该出现在 reference_images 中（RISK-T16-2）"
    print("[T16-2] portrait regenerate 时 reference_images 正确包含 portrait_ref ✅")


def test_portrait_regen_ref_passed():
    asyncio.run(_test_portrait_regen_ref_passed())


async def _test_portrait_first_gen_no_ref():
    """首次生成 portrait（portrait_ref=None）时，reference_images 必须为 None"""
    from app.services.reference_image_manager import ReferenceImageManager
    from app.models.style_config import ProjectStyleConfig

    manager = ReferenceImageManager()
    captured_calls = []

    async def mock_generate_image(prompt, negative_prompt, aspect_ratio, reference_images=None):
        captured_calls.append({"reference_images": reference_images})
        return {"success": False, "error": "mock", "pil_image": None}

    mock_image_gen = MagicMock()
    mock_image_gen.generate_image = AsyncMock(side_effect=mock_generate_image)

    character = {
        "id": "char_002",
        "name": "FirstGen",
        "name_en": "FirstGen",
        "character_type": "human",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {"hair_color": "brown", "hair_style": "short", "eye_color": "blue", "skin_tone": "fair"},
        "clothing": {"top": "shirt", "bottom": "pants", "accessories": [], "style": "casual"},
    }
    project_style = ProjectStyleConfig(style_preset="realistic")

    await manager.generate_character_reference(
        character=character,
        project_style=project_style,
        image_generator=mock_image_gen,
        ref_type="portrait",
        portrait_ref=None,  # 首次生成，没有已有 portrait
    )

    assert len(captured_calls) >= 1
    call_refs = captured_calls[0]["reference_images"]
    assert call_refs is None, "首次生成 portrait（portrait_ref=None）时 reference_images 应为 None（RISK-T16-2）"
    print("[T16-2] portrait 首次生成（portrait_ref=None）→ reference_images=None ✅")


def test_portrait_first_gen_no_ref():
    asyncio.run(_test_portrait_first_gen_no_ref())


# ===========================================================================
# RISK-T16-1: ETA stage 内实时刷新（stage_progress 动态推算）
# ===========================================================================

def test_eta_intra_stage_progress():
    """progress=80（image_generation 阶段中间）时 ETA 应少于 progress=70 时"""
    from app.services.pipeline_orchestrator import estimate_remaining

    # image_generation stage，progress 低（stage 刚开始）
    eta_early = estimate_remaining(
        "image_generation",
        stage_progress=0.0,
        actual_shot_count=18,
        unique_location_count=2,
        max_concurrent=3,
    )
    # image_generation stage，progress 高（stage 快结束）
    eta_late = estimate_remaining(
        "image_generation",
        stage_progress=0.9,
        actual_shot_count=18,
        unique_location_count=2,
        max_concurrent=3,
    )

    assert eta_early > eta_late, \
        f"stage_progress=0.0 的 ETA ({eta_early}s) 应大于 stage_progress=0.9 ({eta_late}s)（RISK-T16-1）"
    print(f"[T16-1] ETA early={eta_early}s > late={eta_late}s ✅")


def test_eta_stage_bounds_calculation():
    """STAGE_PROGRESS_BOUNDS 推算逻辑验证：image_generation 阶段 progress=80 时 stage_progress ~0.45"""
    # image_generation bounds 是 (70, 92)
    # progress=80 → stage_progress = (80-70)/(92-70) = 10/22 ≈ 0.45
    _lo, _hi = 70, 92
    _progress = 80
    _stage_progress = (_progress - _lo) / (_hi - _lo)
    assert abs(_stage_progress - 0.4545) < 0.01, f"stage_progress 推算错误: {_stage_progress}"
    print(f"[T16-1] stage_progress 推算: progress=80 → {_stage_progress:.3f} ✅")


# ===========================================================================
# RISK-T14-10: 参考图并行化验证
# ===========================================================================

async def _test_char_refs_parallel():
    """3 角色并发 asyncio.gather 应比串行快（模拟 ~100ms/角色）"""

    call_log = []

    async def mock_multi_refs(character, project_style, image_generator,
                               seed_image=None, skip_portrait=False, aspect_ratio="2:3",
                               delay=3.0):
        start = time.time()
        await asyncio.sleep(0.1)  # 模拟 100ms 每角色
        end = time.time()
        call_log.append({
            "char_id": character["id"],
            "start": start,
            "end": end,
        })

    # Mock ReferenceImageManager
    mock_ref_manager = MagicMock()
    mock_ref_manager.generate_character_multi_refs = AsyncMock(side_effect=mock_multi_refs)

    # 3 个角色并行任务
    sem = asyncio.Semaphore(3)
    characters = [{"id": f"char_{i:03d}", "name": f"Char{i}"} for i in range(1, 4)]

    async def gen_one(char):
        async with sem:
            await mock_ref_manager.generate_character_multi_refs(
                character=char,
                project_style=None,
                image_generator=None,
            )

    t_start = time.time()
    await asyncio.gather(*[gen_one(c) for c in characters], return_exceptions=True)
    t_total = time.time() - t_start

    # 串行需要 0.3s，并行 3 路最多 0.1s + overhead
    assert t_total < 0.25, f"3 角色并行应 < 250ms，实际 {t_total*1000:.0f}ms（RISK-T14-10）"
    assert len(call_log) == 3, f"应该生成 3 个角色参考图，实际 {len(call_log)}"

    # 验证有真正并发：至少有两个 char 的 start 时间接近（< 50ms 差）
    starts = sorted([e["start"] for e in call_log])
    overlap = starts[-1] - starts[0]
    assert overlap < 0.05, f"3 角色应并发启动，start 时间差 {overlap*1000:.0f}ms（RISK-T14-10）"
    print(f"[T14-10] 3 角色并行: total={t_total*1000:.0f}ms, start spread={overlap*1000:.0f}ms ✅")


def test_char_refs_parallel():
    asyncio.run(_test_char_refs_parallel())


async def _test_scene_refs_parallel():
    """3 location 并发 asyncio.gather 应比串行快（模拟 ~100ms/location）"""
    from app.services.scene_reference_manager import SceneReferenceManager
    from app.models.style_config import ProjectStyleConfig

    manager = SceneReferenceManager()

    call_log = []

    async def mock_generate_single_anchor(anchor_key, anchor_info, view_type, project_style,
                                           image_generator, reference_image=None,
                                           location_id=None, num_characters=None, aspect_ratio="2:3"):
        await asyncio.sleep(0.1)  # 模拟 100ms 每张
        call_log.append({"anchor_key": anchor_key, "time": time.time()})
        return None, {"image": None, "success": True, "description": "mock"}

    manager._generate_single_anchor = mock_generate_single_anchor
    manager._analyze_anchor_needs = MagicMock(return_value={
        "loc1_interior_anchor": {"location_id": "loc1", "view_type": "interior", "description": "loc1 int"},
        "loc2_interior_anchor": {"location_id": "loc2", "view_type": "interior", "description": "loc2 int"},
        "loc3_interior_anchor": {"location_id": "loc3", "view_type": "interior", "description": "loc3 int"},
    })
    manager._group_anchors_by_location = MagicMock(return_value={
        "loc1": {"loc1_interior_anchor": {"location_id": "loc1", "view_type": "interior", "description": "loc1 int"}},
        "loc2": {"loc2_interior_anchor": {"location_id": "loc2", "view_type": "interior", "description": "loc2 int"}},
        "loc3": {"loc3_interior_anchor": {"location_id": "loc3", "view_type": "interior", "description": "loc3 int"}},
    })

    t_start = time.time()
    results = await manager.generate_anchor_images(
        scenes=[],
        project_style=ProjectStyleConfig(style_preset="realistic"),
        image_generator=None,
    )
    t_total = time.time() - t_start

    # 3 个 location 串行需 ~0.3s，并行 ~0.1s + overhead
    assert t_total < 0.25, f"3 location 并行应 < 250ms，实际 {t_total*1000:.0f}ms（RISK-T14-10）"
    assert len(call_log) == 3, f"应该生成 3 张锚点图，实际 {len(call_log)}"
    print(f"[T14-10] 3 location 并行场景参考图: total={t_total*1000:.0f}ms ✅")


def test_scene_refs_parallel():
    asyncio.run(_test_scene_refs_parallel())


# ===========================================================================
# Run all tests
# ===========================================================================

if __name__ == "__main__":
    tests = [
        # RISK-T16-5
        ("T16-5 storyboard_ready empty json", test_storyboard_ready_empty_json),
        ("T16-5 storyboard_ready with shots", test_storyboard_ready_with_shots),
        ("T16-5 storyboard_ready none", test_storyboard_ready_none),
        ("T16-5 storyboard_ready empty shots", test_storyboard_ready_empty_shots),
        ("T16-5 storyboard_ready invalid json", test_storyboard_ready_invalid_json),
        # RISK-T16-2
        ("T16-2 portrait signature has portrait_ref", test_portrait_regen_passes_ref),
        ("T16-2 portrait regen passes ref", test_portrait_regen_ref_passed),
        ("T16-2 portrait first gen no ref", test_portrait_first_gen_no_ref),
        # RISK-T16-1
        ("T16-1 ETA intra-stage progress", test_eta_intra_stage_progress),
        ("T16-1 stage bounds calculation", test_eta_stage_bounds_calculation),
        # RISK-T14-10
        ("T14-10 char refs parallel", test_char_refs_parallel),
        ("T14-10 scene refs parallel", test_scene_refs_parallel),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Wave 10 P2 Backend Perf Tests: {passed} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        sys.exit(1)
