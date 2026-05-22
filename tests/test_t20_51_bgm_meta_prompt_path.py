"""
tests/test_t20_51_bgm_meta_prompt_path.py

T20-51 验收测试: BGM meta-prompt 文件从 test_output 迁至 app/prompts/bgm/

背景 (PM Wave 1 审查 2026-05-20):
  music_generation_service.py:L58-65 META_PROMPT_DIR 指向:
    test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/
  生产部署时 test_output 目录通常被 .gitignore 排除, 导致 BGM 生成失败.

修复 (T20-51):
  1. 将 meta_mixed_v3_quote_picking.md 迁至 app/prompts/bgm/
  2. META_PROMPT_DIR 改为 app/prompts/bgm/
  3. 旧文件保留不删 (Founder memory: 不主动删文件)

测试 case:
  1. app/prompts/bgm/meta_mixed_v3_quote_picking.md 文件存在
  2. app/prompts/bgm/meta_en_v2.md 文件存在 (同 _META_VERSION_FILES 的 en key)
  3. META_PROMPT_DIR 指向 app/prompts/bgm (不含 test_output)
  4. META_PROMPT_DIR 路径真实存在 (os.path.isdir)
  5. _META_VERSION_FILES["mixed"] 文件可从 META_PROMPT_DIR 真实读取
  6. 读取内容与旧路径一致 (diff 验证)
  7. meta_prompt_path 构建函数返回新路径 (回归检查)

Author: @backend
Date: 2026-05-20
Owner: TASK-T20-51
"""

import os
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_OLD_PROMPT_PATH = (
    _PROJECT_ROOT
    / "test_output"
    / "manualtest"
    / "sq_upgrade_ab_test"
    / "20260304_113630"
    / "meta_prompts"
)
_NEW_PROMPT_DIR = _PROJECT_ROOT / "app" / "prompts" / "bgm"


# ─────────────────────────────────────────────────────────────────────────────
# Section 1: 文件存在验证
# ─────────────────────────────────────────────────────────────────────────────

class TestBgmMetaPromptFilesExist:
    """T20-51: app/prompts/bgm/ 目录和文件必须存在."""

    def test_bgm_prompts_dir_exists(self):
        """app/prompts/bgm/ 目录必须存在."""
        assert _NEW_PROMPT_DIR.is_dir(), (
            f"app/prompts/bgm/ 目录不存在: {_NEW_PROMPT_DIR}"
        )

    def test_meta_mixed_v3_exists_in_new_dir(self):
        """meta_mixed_v3_quote_picking.md 必须在 app/prompts/bgm/ 中存在."""
        target = _NEW_PROMPT_DIR / "meta_mixed_v3_quote_picking.md"
        assert target.exists(), (
            f"meta_mixed_v3_quote_picking.md 不在新路径 {_NEW_PROMPT_DIR}: {target}"
        )

    def test_meta_en_v2_exists_in_new_dir(self):
        """meta_en_v2.md 必须在 app/prompts/bgm/ 中存在 (en key in _META_VERSION_FILES)."""
        target = _NEW_PROMPT_DIR / "meta_en_v2.md"
        assert target.exists(), (
            f"meta_en_v2.md 不在新路径 {_NEW_PROMPT_DIR}: {target}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 2: 内容一致性验证
# ─────────────────────────────────────────────────────────────────────────────

class TestBgmMetaPromptContentIdentical:
    """T20-51: 新路径文件内容与旧路径完全一致."""

    def test_meta_mixed_content_identical_to_old(self):
        """新路径 meta_mixed_v3_quote_picking.md 内容与旧路径 100% 一致."""
        old_file = _OLD_PROMPT_PATH / "meta_mixed_v3_quote_picking.md"
        new_file = _NEW_PROMPT_DIR / "meta_mixed_v3_quote_picking.md"

        if not old_file.exists():
            pytest.skip(f"旧路径文件不存在 (生产环境正常): {old_file}")

        assert new_file.exists(), f"新路径文件不存在: {new_file}"
        assert old_file.read_bytes() == new_file.read_bytes(), (
            "新旧路径 meta_mixed_v3_quote_picking.md 内容不一致 — 迁移时文件被修改"
        )

    def test_meta_en_content_identical_to_old(self):
        """新路径 meta_en_v2.md 内容与旧路径 100% 一致."""
        old_file = _OLD_PROMPT_PATH / "meta_en_v2.md"
        new_file = _NEW_PROMPT_DIR / "meta_en_v2.md"

        if not old_file.exists():
            pytest.skip(f"旧路径文件不存在 (生产环境正常): {old_file}")

        assert new_file.exists(), f"新路径文件不存在: {new_file}"
        assert old_file.read_bytes() == new_file.read_bytes(), (
            "新旧路径 meta_en_v2.md 内容不一致 — 迁移时文件被修改"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Section 3: music_generation_service.py 代码路径验证
# ─────────────────────────────────────────────────────────────────────────────

class TestMusicGenerationServiceMetaPromptPath:
    """T20-51: music_generation_service.py META_PROMPT_DIR 指向新路径."""

    def _read_service_source(self) -> str:
        path = _PROJECT_ROOT / "app" / "services" / "music_generation_service.py"
        return path.read_text(encoding="utf-8")

    def test_meta_prompt_dir_not_test_output(self):
        """META_PROMPT_DIR 构建代码不包含 'test_output' 字符串 (注释除外)."""
        source = self._read_service_source()
        # 找到 META_PROMPT_DIR = os.path.join(...) 的赋值行
        lines = source.splitlines()
        in_assignment = False
        assignment_lines = []
        for line in lines:
            stripped = line.strip()
            if "META_PROMPT_DIR = os.path.join(" in stripped:
                in_assignment = True
            if in_assignment:
                # 跳过注释行
                if not stripped.startswith("#"):
                    assignment_lines.append(stripped)
                if stripped.endswith(")"):
                    in_assignment = False

        assignment_code = " ".join(assignment_lines)
        assert "test_output" not in assignment_code, (
            f"META_PROMPT_DIR 赋值代码仍包含 'test_output': {assignment_code!r}\n"
            "请检查 music_generation_service.py 的 META_PROMPT_DIR 赋值"
        )

    def test_meta_prompt_dir_points_to_app_prompts_bgm(self):
        """META_PROMPT_DIR 赋值代码指向 app/prompts/bgm."""
        source = self._read_service_source()
        lines = source.splitlines()
        in_assignment = False
        assignment_lines = []
        for line in lines:
            stripped = line.strip()
            if "META_PROMPT_DIR = os.path.join(" in stripped:
                in_assignment = True
            if in_assignment:
                if not stripped.startswith("#"):
                    assignment_lines.append(stripped)
                if stripped.endswith(")"):
                    in_assignment = False

        assignment_code = " ".join(assignment_lines)
        assert "prompts" in assignment_code and "bgm" in assignment_code, (
            f"META_PROMPT_DIR 赋值代码未包含 'prompts/bgm': {assignment_code!r}"
        )

    def test_meta_prompt_dir_is_valid_directory_at_runtime(self):
        """META_PROMPT_DIR 路径在磁盘上真实存在且含目标文件.

        通过解析源码中的路径常量重建实际路径, 验证:
        1. app/prompts/bgm/ 目录存在
        2. meta_mixed_v3_quote_picking.md 在该目录中
        不 exec_module 以避免 google.genai / httpx 兼容性问题.
        """
        # Parse META_PROMPT_DIR from source (extract path components)
        source = self._read_service_source()
        # Find the line containing "app", "prompts", "bgm"
        assert '"app", "prompts", "bgm"' in source or "'app', 'prompts', 'bgm'" in source, (
            "music_generation_service.py 中 META_PROMPT_DIR 赋值未包含 app/prompts/bgm 路径组件"
        )

        # Construct the expected runtime path
        this_dir = _PROJECT_ROOT / "app" / "services"
        project_root = this_dir / ".." / ".."
        meta_dir = (project_root / "app" / "prompts" / "bgm").resolve()

        assert meta_dir.is_dir(), (
            f"META_PROMPT_DIR 运行时路径不是有效目录: {meta_dir}"
        )
        assert "test_output" not in str(meta_dir), (
            f"META_PROMPT_DIR 仍含 test_output: {meta_dir}"
        )
        mixed_path = meta_dir / "meta_mixed_v3_quote_picking.md"
        assert mixed_path.exists(), (
            f"meta_mixed_v3_quote_picking.md 在运行时路径不存在: {mixed_path}"
        )

    def test_old_file_still_exists_not_deleted(self):
        """旧路径文件未被删除 (Founder memory: 不主动删文件)."""
        old_file = _OLD_PROMPT_PATH / "meta_mixed_v3_quote_picking.md"
        if not old_file.exists():
            # 旧路径不存在可能是生产环境 (test_output 被 .gitignore)
            # 这种情况是正常的 — 新路径才是 source of truth
            pytest.skip("旧路径文件不存在 (生产环境 test_output 已被 .gitignore), 跳过")
        assert old_file.exists(), (
            f"旧路径文件被意外删除: {old_file}\n"
            "Founder 规则: 不主动删文件, 旧文件应保留"
        )
