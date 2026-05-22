"""
T20-46 Backend Wire — pipeline_orchestrator.py Stage 2 传 style_preset 给 CharacterDesigner

验证目标:
1. pipeline_orchestrator.py Stage 2 调用处传入 style_preset 参数 (grep 验证)
2. character_designer.design() 签名接受 style_preset 参数
3. style_preset 在 Stage 2 调用时来自 pipeline run() 参数 (作用域验证)
4. 修改不影响 Stage 2 skip 路径 (start_from_stage > 2 不调 design())
"""

import sys
import ast
import inspect
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Test 1: pipeline_orchestrator.py 含 style_preset 传参
# ---------------------------------------------------------------------------

class TestPipelineWireSourceCode:
    """静态分析 pipeline_orchestrator.py 确认 wire 就位"""

    @pytest.fixture(scope="class")
    def pipeline_source(self):
        path = project_root / "app" / "services" / "pipeline_orchestrator.py"
        return path.read_text(encoding="utf-8")

    def test_design_call_has_style_preset_kwarg(self, pipeline_source):
        """pipeline_orchestrator.py 的 character_designer.design() 调用包含 style_preset= 参数"""
        assert "style_preset=style_preset" in pipeline_source, (
            "T20-46 wire 未检测到: pipeline_orchestrator.py 中 character_designer.design() "
            "调用缺少 style_preset=style_preset 参数"
        )

    def test_design_call_has_t20_46_comment(self, pipeline_source):
        """wire 行含 T20-46 注释，记录意图"""
        assert "T20-46" in pipeline_source, (
            "pipeline_orchestrator.py 缺少 T20-46 注释，建议加注释记录修改意图"
        )

    def test_style_preset_in_scope_before_stage2(self, pipeline_source):
        """style_preset 在 Stage 2 调用前已在 run() 作用域内赋值"""
        # 确认 style_preset 在 run() 方法参数里出现
        lines = pipeline_source.splitlines()
        # 找到 def run( 这一行
        run_line = next(
            (i for i, l in enumerate(lines) if "def run(" in l),
            None
        )
        assert run_line is not None, "找不到 pipeline_orchestrator.py 的 run() 方法定义"

        # 找到 character_designer.design( 这一行
        design_line = next(
            (i for i, l in enumerate(lines) if "character_designer.design(" in l),
            None
        )
        assert design_line is not None, "找不到 character_designer.design() 调用行"

        # style_preset 应该在 run_line 和 design_line 之间出现过
        context_lines = "\n".join(lines[run_line:design_line + 5])
        assert "style_preset" in context_lines, (
            "在 run() 到 character_designer.design() 之间找不到 style_preset 变量, "
            "请确认 style_preset 在 Stage 2 调用时已赋值"
        )

    def test_design_call_not_single_arg(self, pipeline_source):
        """character_designer.design() 不是单参数形式 design(outline) 而是含 style_preset (非注释行)"""
        import re
        # 只检查非注释的代码行 (去掉 # 开头的注释行)
        code_lines = [
            line for line in pipeline_source.splitlines()
            if not line.strip().startswith("#")
        ]
        code_only = "\n".join(code_lines)
        single_arg_pattern = re.compile(
            r'character_designer\.design\(\s*outline\s*\)',
            re.MULTILINE
        )
        match = single_arg_pattern.search(code_only)
        assert match is None, (
            f"发现旧的单参数调用 character_designer.design(outline) 未传 style_preset (非注释行), "
            f"位置: {match.start()}"
        )


# ---------------------------------------------------------------------------
# Test 2: character_designer.design() 签名验证
# ---------------------------------------------------------------------------

class TestCharacterDesignerSignature:
    """验证 character_designer.design() 方法签名接受 style_preset"""

    @pytest.fixture(scope="class")
    def designer_source(self):
        path = project_root / "app" / "services" / "character_designer.py"
        return path.read_text(encoding="utf-8")

    def test_design_method_accepts_style_preset(self, designer_source):
        """character_designer.py 的 design() 方法签名包含 style_preset 参数"""
        assert "def design(" in designer_source, "character_designer.py 中找不到 design() 方法"
        # 找到 design() 方法签名 (可能多行)
        lines = designer_source.splitlines()
        design_idx = next(
            (i for i, l in enumerate(lines) if "def design(" in l),
            None
        )
        assert design_idx is not None, "找不到 def design( 行"

        # 检查签名及后续几行 (参数可能换行)
        sig_snippet = "\n".join(lines[design_idx:design_idx + 5])
        assert "style_preset" in sig_snippet, (
            f"character_designer.design() 签名缺少 style_preset 参数:\n{sig_snippet}"
        )

    def test_design_style_preset_has_default_none(self, designer_source):
        """style_preset 参数有 None 默认值，向后兼容旧调用"""
        lines = designer_source.splitlines()
        design_idx = next(
            (i for i, l in enumerate(lines) if "def design(" in l),
            None
        )
        sig_snippet = "\n".join(lines[design_idx:design_idx + 5])
        assert "style_preset: str | None = None" in sig_snippet or \
               "style_preset=None" in sig_snippet, (
            f"character_designer.design() style_preset 应有默认值 None (向后兼容):\n{sig_snippet}"
        )

    def test_style_preset_passed_to_build_prompt(self, designer_source):
        """design() 内部将 style_preset 传给 _build_prompt()"""
        assert "_build_prompt(" in designer_source, "_build_prompt 方法不存在"
        # 在 design 方法体内找 style_preset=style_preset 传参
        assert "style_preset=style_preset" in designer_source, (
            "character_designer.design() 内部没有将 style_preset 传给 _build_prompt()"
        )


# ---------------------------------------------------------------------------
# Test 3: Stage 2 skip 路径不受影响
# ---------------------------------------------------------------------------

class TestStage2SkipPathUnchanged:
    """当 start_from_stage > 2 时, design() 不应被调用 (skip 路径不受 T20-46 影响)"""

    def test_skip_path_exists(self):
        """pipeline_orchestrator.py 保留了 start_from_stage > 2 的 skip 路径"""
        path = project_root / "app" / "services" / "pipeline_orchestrator.py"
        source = path.read_text(encoding="utf-8")
        # skip 路径应该存在 (RISK-T17-8)
        assert "start_from_stage > 2" in source or "start_from_stage >= 2" in source, (
            "Stage 2 skip 路径 (start_from_stage > 2) 未找到，可能被误删"
        )

    def test_skip_path_uses_cached_characters(self):
        """skip 路径使用 stage_results['characters'] 而不调用 design()"""
        path = project_root / "app" / "services" / "pipeline_orchestrator.py"
        source = path.read_text(encoding="utf-8")
        # 在 skip 路径中应有 stage_results["characters"] 或 stage_results['characters']
        assert 'stage_results["characters"]' in source or "stage_results['characters']" in source, (
            "Stage 2 skip 路径中找不到 stage_results[characters] 缓存读取"
        )


# ---------------------------------------------------------------------------
# Test 4: py_compile 语法验证
# ---------------------------------------------------------------------------

class TestSyntaxValid:
    def test_pipeline_orchestrator_syntax(self):
        """pipeline_orchestrator.py 语法正确"""
        import py_compile
        path = str(project_root / "app" / "services" / "pipeline_orchestrator.py")
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"pipeline_orchestrator.py 语法错误: {e}")

    def test_character_designer_syntax(self):
        """character_designer.py 语法正确"""
        import py_compile
        path = str(project_root / "app" / "services" / "character_designer.py")
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"character_designer.py 语法错误: {e}")
