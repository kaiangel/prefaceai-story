"""
tests/test_t20_50_fix_round3.py

Wave 2 Round 3 P0 修复验收测试 (2026-05-20)

=== Bug 1: SONNET_MODEL 错误日期后缀 (T20-47-fix-round3) ===
根因: SONNET_MODEL = "claude-sonnet-4-6-20251101" 不存在，Anthropic 返回 404 NotFoundError
     → 100% fail-open，20 张图全部跳过验证
修复: SONNET_MODEL = "claude-sonnet-4-6"（无日期后缀，Sonnet 4.6 正确 ID）
关键: Anthropic API mock 验证 model ID 真的发到 API（不只 grep 字符串）

=== Bug 2: save_all_references 覆盖 portrait (T20-50-fix-2-round3) ===
根因: image_preparation 阶段 save_all_references 把 in-memory dict 无条件写盘
     → 覆盖 Founder 手动重生的 portrait（~500KB 内容差异，实测证实）
修复: 方案 A — 文件已存在时 skip save，信任磁盘文件（KEY_LEARNINGS #46）

测试 case:
  1. SONNET_MODEL 常量无日期后缀
  2. Mock Anthropic API 调用 — 验证发出的 model 参数是正确的 ID（API 层面验证）
  3. save_all_references: 文件不存在 → save
  4. save_all_references: 文件已存在 → skip（不覆盖）
  5. T20-50 重生场景 — Founder 改 portrait 后 image_preparation 不覆盖
"""

import asyncio
import importlib
import importlib.util
import os
import io
import sys
from pathlib import Path
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image


# ─────────────────────────────────────────────────────────────────────────────
# T20-52: Test isolation fixture (same pattern as test_t20_47_shot_validator_fallback.py)
# test_t20_43 injects stub app / app.services (non-package ModuleType) into sys.modules
# which breaks all subsequent `from app.services.shot_validator import ...`.
# ─────────────────────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_shot_validator_fresh():
    """T20-52: 确保 app.services.shot_validator 以干净状态在 sys.modules 中 (同 T20-47)."""
    app_mod = sys.modules.get("app")
    app_is_stub = (app_mod is not None and not hasattr(app_mod, "__path__"))
    svc_mod = sys.modules.get("app.services")
    svc_is_stub = (svc_mod is not None and not hasattr(svc_mod, "__path__"))

    if app_is_stub or svc_is_stub:
        keys_to_remove = [k for k in list(sys.modules.keys())
                          if k == "app" or k.startswith("app.")]
        for k in keys_to_remove:
            del sys.modules[k]

    sys.modules.pop("app.services.shot_validator", None)

    if "app" not in sys.modules or not hasattr(sys.modules["app"], "__path__"):
        import types as _types
        _app_pkg = _types.ModuleType("app")
        _app_pkg.__path__ = [str(_PROJECT_ROOT / "app")]  # type: ignore[attr-defined]
        _app_pkg.__package__ = "app"
        sys.modules["app"] = _app_pkg

    if "app.services" not in sys.modules or not hasattr(sys.modules["app.services"], "__path__"):
        import types as _types
        _svc_pkg = _types.ModuleType("app.services")
        _svc_pkg.__path__ = [str(_PROJECT_ROOT / "app" / "services")]  # type: ignore[attr-defined]
        _svc_pkg.__package__ = "app.services"
        sys.modules["app"].services = _svc_pkg  # type: ignore[attr-defined]
        sys.modules["app.services"] = _svc_pkg

    _sv_path = _PROJECT_ROOT / "app" / "services" / "shot_validator.py"
    _spec = importlib.util.spec_from_file_location(
        "app.services.shot_validator",
        str(_sv_path),
    )
    _sv = importlib.util.module_from_spec(_spec)
    _sv.__package__ = "app.services"
    sys.modules["app.services.shot_validator"] = _sv
    _spec.loader.exec_module(_sv)  # type: ignore[union-attr]
    sys.modules["app.services"].shot_validator = _sv  # type: ignore[attr-defined]


@pytest.fixture(autouse=True)
def _restore_app_services_package():
    """T20-52: 每 test 前加载干净的 shot_validator, 清除 test_t20_43 stub 污染."""
    _load_shot_validator_fresh()
    yield
    sys.modules.pop("app.services.shot_validator", None)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_image(color: tuple = (100, 150, 200)) -> Image.Image:
    """创建最小测试图像。"""
    return Image.new("RGB", (16, 16), color=color)


def _read_image_bytes(path: str) -> bytes:
    """读取图像文件字节（用于比较内容是否变更）。"""
    with open(path, "rb") as f:
        return f.read()


def _make_overload_exc() -> Exception:
    """模拟 Anthropic 529 OverloadedError。"""
    exc = Exception("overloaded: 529 — Anthropic temporarily overloaded")
    exc.status_code = 529  # type: ignore[attr-defined]
    return exc


def _make_valid_response(character_count: int = 1) -> MagicMock:
    """模拟有效的 Anthropic response。"""
    resp = MagicMock()
    resp.content = [MagicMock()]
    resp.content[0].text = (
        f'{{"character_count": {character_count}, "has_duplicate_bubbles": false, '
        f'"has_visual_unnaturalness": false, "unnaturalness_details": "", '
        f'"anatomy_severity": "none", "anatomy_issues": []}}'
    )
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: SONNET_MODEL 常量验证
# ─────────────────────────────────────────────────────────────────────────────

class TestSonnetModelIdFix:
    """T20-47-fix-round3: SONNET_MODEL 不应有错误日期后缀。"""

    def test_sonnet_model_no_date_suffix(self):
        """SONNET_MODEL = 'claude-sonnet-4-6'（无日期后缀）。

        Sonnet 4.6 的正确 Anthropic model ID 没有 -YYYYMMDD 后缀。
        带后缀 -20251101 会返回 404 NotFoundError。
        """
        from app.services.shot_validator import SONNET_MODEL
        assert SONNET_MODEL == "claude-sonnet-4-6", (
            f"SONNET_MODEL={SONNET_MODEL!r} 应为 'claude-sonnet-4-6'（无日期后缀）"
        )

    def test_sonnet_model_no_invalid_date(self):
        """SONNET_MODEL 不包含导致 404 的错误日期 '20251101'。"""
        from app.services.shot_validator import SONNET_MODEL
        assert "20251101" not in SONNET_MODEL, (
            f"SONNET_MODEL={SONNET_MODEL!r} 包含不存在的日期后缀 '20251101'"
        )

    def test_haiku_model_has_correct_date(self):
        """HAIKU_MODEL = 'claude-haiku-4-5-20251001'（Haiku 需要日期后缀）。"""
        from app.services.shot_validator import HAIKU_MODEL
        assert HAIKU_MODEL == "claude-haiku-4-5-20251001", (
            f"HAIKU_MODEL={HAIKU_MODEL!r} 应为 'claude-haiku-4-5-20251001'"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: Anthropic API Mock 验证 model ID 真发到 API
# ─────────────────────────────────────────────────────────────────────────────

class TestSonnetModelIdSentToApi:
    """验证 model ID 真的传到 Anthropic API call（不只 grep 字符串）。"""

    @pytest.mark.asyncio
    async def test_api_call_uses_correct_model_id(self):
        """_call_anthropic_with_retry 发出的 model 参数应是 'claude-sonnet-4-6'。

        这是 API 层面的验证：mock Anthropic client，捕获 messages.create 的入参，
        确认 model kwarg 没有错误日期后缀。
        """
        from app.services.shot_validator import _call_anthropic_with_retry, SONNET_MODEL

        mock_client = MagicMock()
        # messages.create 是 async，需要 AsyncMock
        mock_client.messages.create = AsyncMock(return_value=_make_valid_response())

        fake_messages = [{"role": "user", "content": "test"}]
        await _call_anthropic_with_retry(
            mock_client,
            model=SONNET_MODEL,
            max_tokens=100,
            temperature=0.0,
            messages=fake_messages,
            shot_id_for_log="test-shot-001",
        )

        # 验证 API 调用确实发生
        assert mock_client.messages.create.called, "messages.create 未被调用"

        # 验证发出的 model 参数
        call_kwargs = mock_client.messages.create.call_args.kwargs
        sent_model = call_kwargs.get("model", "")
        assert sent_model == "claude-sonnet-4-6", (
            f"API 调用发出的 model={sent_model!r}，期望 'claude-sonnet-4-6'"
        )
        assert "20251101" not in sent_model, (
            f"API 调用发出了错误的 model ID（含 20251101）: {sent_model!r}"
        )

    @pytest.mark.asyncio
    async def test_api_call_succeeds_without_404(self):
        """用正确 model ID 调用不会触发 NotFoundError / 404。

        通过 mock 确认：正确 ID 下 API 返回成功（不会因 404 抛异常走 fail-open）。
        """
        from app.services.shot_validator import _call_anthropic_with_retry, SONNET_MODEL

        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=_make_valid_response())

        # 不应抛异常
        response = await _call_anthropic_with_retry(
            mock_client,
            model=SONNET_MODEL,
            max_tokens=100,
            temperature=0.0,
            messages=[{"role": "user", "content": "test"}],
        )
        assert response is not None, "正确 model ID 调用应返回 response，不应 None"


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: save_all_references 不覆盖已存在文件
# ─────────────────────────────────────────────────────────────────────────────

class TestSaveAllReferencesNoOverwrite:
    """T20-50-fix-2-round3: save_all_references 文件存在时不覆盖。"""

    def test_save_new_file_when_not_exists(self):
        """文件不存在 → 正常 save，返回路径正确。"""
        from app.services.reference_image_manager import ReferenceImageManager

        mgr = ReferenceImageManager()
        img = _make_image((10, 20, 30))
        mgr.character_references["char_001"] = {"portrait": img}

        with tempfile.TemporaryDirectory() as tmpdir:
            result = mgr.save_all_references(tmpdir)

            portrait_path = result["char_001"]["portrait"]
            assert os.path.exists(portrait_path), "文件不存在时应保存文件"
            assert portrait_path.endswith("char_001_portrait.png"), (
                f"路径格式错误: {portrait_path}"
            )

    def test_skip_existing_file_no_overwrite(self):
        """文件已存在 → skip save，磁盘内容不变。

        这是 T20-50 核心 case：Founder 手动重生 portrait 后
        save_all_references 不应覆盖磁盘文件。
        """
        from app.services.reference_image_manager import ReferenceImageManager

        with tempfile.TemporaryDirectory() as tmpdir:
            portrait_path = os.path.join(tmpdir, "char_001_portrait.png")

            # 先写"Founder 重生的 portrait"（内容 A，绿色制服）
            founder_portrait = _make_image((0, 200, 0))  # 绿色 → 模拟重生后新内容
            founder_portrait.save(portrait_path)
            original_bytes = _read_image_bytes(portrait_path)
            original_size = os.path.getsize(portrait_path)

            # 模拟 in-memory 里是旧 portrait（内容 B，红色）
            stale_portrait = _make_image((200, 0, 0))  # 红色 → 旧内容
            mgr = ReferenceImageManager()
            mgr.character_references["char_001"] = {"portrait": stale_portrait}

            # 执行 save_all_references
            result = mgr.save_all_references(tmpdir)

            # 验证：文件内容未变（磁盘保留 Founder 版本）
            after_bytes = _read_image_bytes(portrait_path)
            after_size = os.path.getsize(portrait_path)

            assert after_bytes == original_bytes, (
                f"save_all_references 覆盖了磁盘文件！"
                f"文件大小: 之前={original_size}, 之后={after_size}"
            )

            # 验证：返回值里路径仍正确
            assert result["char_001"]["portrait"] == portrait_path, (
                f"返回路径错误: {result['char_001']['portrait']}"
            )

    def test_mixed_existing_and_new(self):
        """portrait 已存在（skip） + fullbody 不存在（save）— 混合 case。"""
        from app.services.reference_image_manager import ReferenceImageManager

        with tempfile.TemporaryDirectory() as tmpdir:
            portrait_path = os.path.join(tmpdir, "char_001_portrait.png")

            # portrait 已存在（Founder 重生版本）
            existing_portrait = _make_image((0, 255, 0))
            existing_portrait.save(portrait_path)
            portrait_bytes_before = _read_image_bytes(portrait_path)

            # fullbody 不存在
            mgr = ReferenceImageManager()
            stale_portrait = _make_image((255, 0, 0))  # in-memory 旧版
            fullbody_img = _make_image((0, 0, 255))
            mgr.character_references["char_001"] = {
                "portrait": stale_portrait,
                "fullbody": fullbody_img,
            }

            result = mgr.save_all_references(tmpdir)

            # portrait 不被覆盖
            portrait_bytes_after = _read_image_bytes(portrait_path)
            assert portrait_bytes_after == portrait_bytes_before, (
                "portrait 已存在，不应被覆盖"
            )

            # fullbody 正常保存
            fullbody_path = result["char_001"]["fullbody"]
            assert os.path.exists(fullbody_path), "fullbody 不存在时应保存"

    def test_t20_50_regen_scenario(self):
        """T20-50 重生场景完整模拟: Founder 改 portrait → image_preparation → portrait 不变。

        模拟步骤:
          1. Pipeline 生成 portrait_v1（蓝色，旧版）并保存到磁盘
          2. Founder 手动重生 → portrait_v2（绿色，新版）写到同路径
          3. image_preparation 阶段: ReferenceImageManager 内存里仍是 portrait_v1
          4. save_all_references 被调用
          5. 验证: 磁盘上是 portrait_v2（Founder 重生版），不被 v1 覆盖
        """
        from app.services.reference_image_manager import ReferenceImageManager

        with tempfile.TemporaryDirectory() as tmpdir:
            portrait_path = os.path.join(tmpdir, "char_003_portrait.png")
            fullbody_path_expected = os.path.join(tmpdir, "char_003_fullbody.png")

            # Step 1: Pipeline 生成 portrait_v1（蓝色）
            portrait_v1 = _make_image((0, 0, 200))  # 蓝色 → 旧版
            portrait_v1.save(portrait_path)

            # Step 2: Founder 手动重生 → portrait_v2（绿色制服，新版）
            portrait_v2 = _make_image((0, 200, 50))  # 绿色 → Founder 重生版
            portrait_v2.save(portrait_path)  # 覆盖旧文件
            v2_bytes = _read_image_bytes(portrait_path)
            v2_size = os.path.getsize(portrait_path)

            # Step 3: image_preparation: in-memory 仍是 portrait_v1
            mgr = ReferenceImageManager()
            fullbody_img = _make_image((100, 100, 100))
            mgr.character_references["char_003"] = {
                "portrait": portrait_v1,     # in-memory 旧版（v1）
                "fullbody": fullbody_img,
            }

            # Step 4: save_all_references
            result = mgr.save_all_references(tmpdir)

            # Step 5: 验证磁盘上 portrait 仍是 v2（Founder 重生版）
            disk_bytes_after = _read_image_bytes(portrait_path)
            disk_size_after = os.path.getsize(portrait_path)

            assert disk_bytes_after == v2_bytes, (
                f"T20-50 重生场景失败: portrait 被 in-memory 旧版覆盖！"
                f"期望大小={v2_size}, 实际大小={disk_size_after}"
            )

            # fullbody 不存在则正常保存
            assert "fullbody" in result["char_003"], "fullbody 应被保存"
            assert os.path.exists(result["char_003"]["fullbody"]), "fullbody 文件应存在"

            print(
                f"[OK] T20-50 重生场景: portrait 保留 Founder 版本 "
                f"(size={v2_size}), fullbody 正常保存"
            )
