"""
tests/test_t20_50_freshness_removed.py

T20-50 验收测试: Pipeline freshness check 算法完全移除，改为"文件存在即信任"逻辑。

4 个测试 case:
  case 1: portrait 文件存在 → _skip_portrait_local=True, _portrait_seed_local 不为 None
  case 2: portrait 文件不存在 → _skip_portrait_local=False, _portrait_seed_local=None
  case 3: portrait 文件存在但损坏 → 安全 fallback (skip=False, 重新生成)
  case 4: 模拟 Founder 重生场景 — portrait mtime 在 char.updated_at 之前，仍要被信任（旧 bug 重现 case）

真根因 (KEY_LEARNINGS #45 / #46):
  旧 freshness check `_portrait_fresh = mtime > updated_at + 30` 把"刚重生的"判为"陈旧"→
  Pipeline 重新生成覆盖用户重生的 portrait。

修复: 完全去掉 freshness check 算法，改为 "if file exists → skip = True"。
     文件存在即信任，永不基于 mtime/updated_at 二次裁判 (Founder 设计铁律)。
"""

import os
import time
import tempfile
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers: simulate the T20-50 fixed logic (mirrors pipeline_orchestrator.py)
# ---------------------------------------------------------------------------

def _simulate_portrait_skip_logic(portrait_path: str, char: dict) -> tuple[bool, object]:
    """
    Mirrors the T20-50 fixed logic in pipeline_orchestrator.py.

    Returns (skip_portrait, portrait_seed_local):
      - skip_portrait=True means "portrait exists and loaded, skip regeneration"
      - portrait_seed_local is the PIL Image (or None if skip=False)
    """
    _portrait_seed_local = None
    _skip_portrait_local = False

    if os.path.exists(portrait_path):
        try:
            from PIL import Image as _PilImage
            _portrait_seed_local = _PilImage.open(portrait_path).convert("RGB")
            _skip_portrait_local = True
        except Exception:
            _portrait_seed_local = None
            _skip_portrait_local = False

    return _skip_portrait_local, _portrait_seed_local


def _simulate_old_freshness_check(portrait_path: str, char: dict) -> tuple[bool, object]:
    """
    Mirrors the OLD (BUGGY) freshness check logic that was removed.
    Used in case 4 to demonstrate that the old algorithm would have failed.

    Returns (skip_portrait, portrait_seed_local) using OLD logic.
    """
    from datetime import datetime

    _portrait_seed_local = None
    _skip_portrait_local = False

    if os.path.exists(portrait_path):
        try:
            _portrait_mtime = os.path.getmtime(portrait_path)
            _char_updated_at_str = char.get("updated_at")
            _portrait_fresh = True
            if _char_updated_at_str:
                _char_dt = datetime.fromisoformat(_char_updated_at_str.replace("Z", "+00:00"))
                _char_ts = _char_dt.timestamp()
                _portrait_fresh = _portrait_mtime > (_char_ts + 30)  # BUG line
            if _portrait_fresh:
                from PIL import Image as _PilImage
                _portrait_seed_local = _PilImage.open(portrait_path).convert("RGB")
                _skip_portrait_local = True
        except Exception:
            _portrait_seed_local = None
            _skip_portrait_local = False

    return _skip_portrait_local, _portrait_seed_local


# ---------------------------------------------------------------------------
# Helper: create a valid 1x1 PNG test file
# ---------------------------------------------------------------------------

def _make_test_portrait(path: str) -> None:
    """Create a minimal valid PNG at the given path."""
    img = Image.new("RGB", (10, 10), color=(128, 64, 192))
    img.save(path, format="PNG")


# ---------------------------------------------------------------------------
# case 1: portrait 文件存在 → skip=True, seed not None
# ---------------------------------------------------------------------------

def test_case1_portrait_exists_skip_true(tmp_path):
    """
    T20-50 case 1: portrait 文件存在时 → _skip_portrait_local=True, _portrait_seed_local 不为 None

    固定结果: Pipeline 跳过 portrait 重生，直接用现有文件。
    """
    portrait_path = str(tmp_path / "char_001_portrait.png")
    _make_test_portrait(portrait_path)

    char = {"id": "char_001", "name": "陈婶", "updated_at": "2026-05-20T15:46:00Z"}

    skip, seed = _simulate_portrait_skip_logic(portrait_path, char)

    assert skip is True, "portrait 存在时 _skip_portrait_local 应为 True"
    assert seed is not None, "portrait 存在时 _portrait_seed_local 不应为 None"
    assert hasattr(seed, "size"), "_portrait_seed_local 应是 PIL Image (有 .size 属性)"


# ---------------------------------------------------------------------------
# case 2: portrait 文件不存在 → skip=False, seed=None
# ---------------------------------------------------------------------------

def test_case2_portrait_missing_skip_false(tmp_path):
    """
    T20-50 case 2: portrait 文件不存在 → _skip_portrait_local=False, _portrait_seed_local=None

    固定结果: Pipeline 正常生成 portrait（文件不存在才生成，这是唯一生成触发条件）。
    """
    portrait_path = str(tmp_path / "char_002_portrait.png")
    # 不创建文件

    char = {"id": "char_002", "name": "林深", "updated_at": "2026-05-20T15:39:00Z"}

    assert not os.path.exists(portrait_path), "前置条件: 文件不存在"

    skip, seed = _simulate_portrait_skip_logic(portrait_path, char)

    assert skip is False, "portrait 不存在时 _skip_portrait_local 应为 False"
    assert seed is None, "portrait 不存在时 _portrait_seed_local 应为 None"


# ---------------------------------------------------------------------------
# case 3: portrait 文件存在但损坏 → 安全 fallback (skip=False, 重新生成)
# ---------------------------------------------------------------------------

def test_case3_portrait_corrupted_fallback(tmp_path):
    """
    T20-50 case 3: portrait 文件存在但损坏（非合法 PNG）→ 安全 fallback:
      _skip_portrait_local=False (重新生成), _portrait_seed_local=None

    保证损坏文件不会让 Pipeline 崩溃，而是安全退化到重新生成。
    """
    portrait_path = str(tmp_path / "char_003_portrait.png")
    # 写入无效二进制（损坏文件）
    with open(portrait_path, "wb") as f:
        f.write(b"INVALID_NOT_A_PNG_FILE")

    char = {"id": "char_003", "name": "镜中人", "updated_at": "2026-05-20T15:40:00Z"}

    assert os.path.exists(portrait_path), "前置条件: 损坏文件存在"

    skip, seed = _simulate_portrait_skip_logic(portrait_path, char)

    assert skip is False, "损坏文件时 _skip_portrait_local 应为 False（安全 fallback）"
    assert seed is None, "损坏文件时 _portrait_seed_local 应为 None（安全 fallback）"


# ---------------------------------------------------------------------------
# case 4: Founder 重生场景 — mtime <= updated_at (旧 bug 重现对比)
# ---------------------------------------------------------------------------

def test_case4_founder_regen_scenario_old_bug_vs_new_fix(tmp_path):
    """
    T20-50 case 4: Founder 重生陈婶 portrait 的真实场景重现。

    场景:
      - T₀ 时刻: RegeneratePortrait 端点 B57 生成新 portrait (mtime=T₀)
      - T₀ 时刻: 同步更新 DB char.updated_at=T₀ (同一时刻)
      - 所以: portrait_mtime == updated_at (T₀ == T₀)

    旧 bug 逻辑 (已移除):
      _portrait_fresh = T₀ > T₀ + 30  → False → 算"陈旧" → Pipeline 覆盖重生
      → 用户重生白做 (test20 陈婶事故)

    新逻辑 (T20-50 修复):
      if file exists → skip=True
      → 信任用户操作，直接复用

    本 case 验证:
      1. 旧逻辑在 mtime == updated_at 时确实失败 (skip=False) — 记录历史 bug
      2. 新逻辑在同场景下成功 (skip=True) — 验证修复
    """
    portrait_path = str(tmp_path / "char_003_portrait.png")
    _make_test_portrait(portrait_path)

    # 获取文件的实际 mtime (代表 RegeneratePortrait 完成的时刻 T₀)
    file_mtime = os.path.getmtime(portrait_path)

    # char.updated_at = 同一时刻 T₀ (RegeneratePortrait 同时更新 DB)
    from datetime import datetime, timezone
    updated_at_dt = datetime.fromtimestamp(file_mtime, tz=timezone.utc)
    updated_at_str = updated_at_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    char = {
        "id": "char_003",
        "name": "陈婶",
        "updated_at": updated_at_str,  # T₀ (同 mtime)
    }

    # --- 验证旧 bug: mtime == updated_at 时旧逻辑 skip=False (BUG)
    old_skip, old_seed = _simulate_old_freshness_check(portrait_path, char)
    assert old_skip is False, (
        f"旧 bug 验证: mtime={file_mtime} == updated_at={file_mtime}, "
        f"旧算法要求 mtime > updated_at+30 → False → skip=False (用户重生被覆盖)"
    )
    assert old_seed is None, "旧 bug 验证: skip=False 时 seed 应为 None"

    # --- 验证新修复: 文件存在即信任，skip=True
    new_skip, new_seed = _simulate_portrait_skip_logic(portrait_path, char)
    assert new_skip is True, (
        f"T20-50 修复验证: 文件存在即信任，skip=True (不管 mtime vs updated_at 关系)"
    )
    assert new_seed is not None, "T20-50 修复验证: skip=True 时 seed 不应为 None"

    # 额外确认: updated_at 字段有没有都不影响新逻辑
    char_no_updated_at = {"id": "char_003", "name": "陈婶"}
    skip_no_ts, seed_no_ts = _simulate_portrait_skip_logic(portrait_path, char_no_updated_at)
    assert skip_no_ts is True, "即使 char 没有 updated_at 字段，文件存在也应 skip=True"
    assert seed_no_ts is not None


# ---------------------------------------------------------------------------
# 额外: 验证 pipeline_orchestrator.py 代码层面没有旧算法残留
# ---------------------------------------------------------------------------

def test_no_freshness_check_code_in_orchestrator():
    """
    验证 pipeline_orchestrator.py 中不再存在旧 freshness check 算法代码。

    检查项:
      - 没有 `_portrait_fresh` 变量定义
      - 没有 `_char_ts + 30` 表达式
      - 没有 `_portrait_mtime > (_char_ts` 逻辑
    """
    orchestrator_path = os.path.join(
        os.path.dirname(__file__),
        "..", "app", "services", "pipeline_orchestrator.py"
    )
    orchestrator_path = os.path.normpath(orchestrator_path)

    assert os.path.exists(orchestrator_path), f"pipeline_orchestrator.py 不存在: {orchestrator_path}"

    with open(orchestrator_path, "r", encoding="utf-8") as f:
        source = f.read()

    # 旧 bug 的核心变量名不应出现（除了注释）
    lines = source.splitlines()

    def lines_with_code(pattern: str) -> list[str]:
        """返回含 pattern 的非注释行（不以 # 开头）"""
        result = []
        for line in lines:
            stripped = line.strip()
            if pattern in stripped and not stripped.startswith("#"):
                result.append(line)
        return result

    # 1. `_portrait_fresh =` 赋值语句不应存在（只在注释里可以提到）
    portrait_fresh_code_lines = lines_with_code("_portrait_fresh =")
    assert len(portrait_fresh_code_lines) == 0, (
        f"旧 freshness check 变量 `_portrait_fresh =` 仍存在于代码行:\n"
        + "\n".join(portrait_fresh_code_lines)
    )

    # 2. `_char_ts + 30` 不应存在（旧 bug 的核心 +30 buffer）
    char_ts_30_lines = lines_with_code("_char_ts + 30")
    assert len(char_ts_30_lines) == 0, (
        f"旧 bug `_char_ts + 30` 仍存在于代码行:\n" + "\n".join(char_ts_30_lines)
    )

    # 3. `_portrait_mtime >` 比较逻辑不应存在
    mtime_compare_lines = lines_with_code("_portrait_mtime >")
    assert len(mtime_compare_lines) == 0, (
        f"旧 freshness check mtime 比较 `_portrait_mtime >` 仍存在:\n"
        + "\n".join(mtime_compare_lines)
    )

    # 4. 新修复标识应存在
    assert "T20-50" in source, "新修复标识 T20-50 应在 pipeline_orchestrator.py 中"
    assert "KEY_LEARNINGS #46" in source, "KEY_LEARNINGS #46 注释应在 pipeline_orchestrator.py 中"
    assert "信任用户操作" in source, "新逻辑的中文标识 '信任用户操作' 应存在"
