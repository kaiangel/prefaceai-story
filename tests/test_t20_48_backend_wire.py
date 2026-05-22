"""
T20-48 Backend Wire — storyboard_director.py 注入 ANATOMY_FIDELITY_RULES

验证目标:
1. storyboard_director.py 顶部 import 含 ANATOMY_FIDELITY_RULES
2. _build_scene_prompt() 模板字符串含 {ANATOMY_FIDELITY_RULES} 占位符
3. _build_prompt() (dead code) 模板字符串同步含 {ANATOMY_FIDELITY_RULES}
4. ANATOMY_FIDELITY_RULES 紧跟 SEEDREAM_SAFETY_AVOIDANCE_RULES 之后（顺序正确）
5. storyboard_prompts.py 中 ANATOMY_FIDELITY_RULES 含关键文本 "EXACTLY 2 hands"
6. 文件语法正确 (py_compile)
"""

import sys
import re
import py_compile
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def director_source():
    path = project_root / "app" / "services" / "storyboard_director.py"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prompts_source():
    path = project_root / "app" / "prompts" / "storyboard_prompts.py"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test 1: Import 层验证
# ---------------------------------------------------------------------------

class TestImportLayer:
    """storyboard_director.py import 块含 ANATOMY_FIDELITY_RULES"""

    def test_anatomy_fidelity_rules_imported(self, director_source):
        """T20-48 wire: storyboard_director.py 顶部 import 含 ANATOMY_FIDELITY_RULES"""
        assert "ANATOMY_FIDELITY_RULES" in director_source, (
            "T20-48 wire 未接通: storyboard_director.py 缺少 import ANATOMY_FIDELITY_RULES"
        )

    def test_anatomy_fidelity_rules_from_storyboard_prompts(self, director_source):
        """ANATOMY_FIDELITY_RULES 从 storyboard_prompts 导入（非本地定义）"""
        # 确认 from app.prompts.storyboard_prompts import 行存在
        assert "from app.prompts.storyboard_prompts import" in director_source, (
            "找不到 from app.prompts.storyboard_prompts import 语句"
        )
        # ANATOMY_FIDELITY_RULES 在文件中出现，且跟 storyboard_prompts import 块相邻
        # 用行级检查：找 storyboard_prompts import 块的行范围，确认 ANATOMY_FIDELITY_RULES 在其中
        lines = director_source.splitlines()
        import_start = None
        import_end = None
        for i, line in enumerate(lines):
            if "from app.prompts.storyboard_prompts import" in line:
                import_start = i
            if import_start is not None and import_end is None and i > import_start and line.strip() == ")":
                import_end = i
                break
        assert import_start is not None, "找不到 storyboard_prompts import 起始行"
        assert import_end is not None, "找不到 storyboard_prompts import 结束行 '）'"
        import_block = "\n".join(lines[import_start:import_end + 1])
        assert "ANATOMY_FIDELITY_RULES" in import_block, (
            f"ANATOMY_FIDELITY_RULES 不在 storyboard_prompts import 块内 (L{import_start+1}-{import_end+1})，"
            "请确认从正确模块导入"
        )


# ---------------------------------------------------------------------------
# Test 2: _build_scene_prompt() 注入验证（主路径）
# ---------------------------------------------------------------------------

class TestBuildScenePromptInjection:
    """_build_scene_prompt() 的 f-string 模板含 {ANATOMY_FIDELITY_RULES} 占位符"""

    def test_anatomy_fidelity_in_build_scene_prompt(self, director_source):
        """T20-48 wire: _build_scene_prompt() prompt 含 ANATOMY_FIDELITY_RULES 占位符"""
        # 找到 _build_scene_prompt 方法
        method_match = re.search(
            r'def _build_scene_prompt\(.*?\n(.*?)(?=\n    def |\nclass |\Z)',
            director_source,
            re.DOTALL
        )
        assert method_match is not None, "找不到 _build_scene_prompt() 方法体"

        method_body = method_match.group(1)
        assert "{ANATOMY_FIDELITY_RULES}" in method_body, (
            "T20-48 wire 未接通: _build_scene_prompt() 方法体缺少 {ANATOMY_FIDELITY_RULES} 占位符"
        )

    def test_anatomy_after_seedream_safety_in_scene_prompt(self, director_source):
        """_build_scene_prompt() 中 ANATOMY_FIDELITY_RULES 在 SEEDREAM_SAFETY_AVOIDANCE_RULES 之后"""
        seedream_pos = director_source.find(
            "{SEEDREAM_SAFETY_AVOIDANCE_RULES}\n\n{ANATOMY_FIDELITY_RULES}"
        )
        assert seedream_pos != -1, (
            "T20-48 顺序错误: _build_scene_prompt() 中 {ANATOMY_FIDELITY_RULES} "
            "应紧跟在 {SEEDREAM_SAFETY_AVOIDANCE_RULES} 之后"
        )


# ---------------------------------------------------------------------------
# Test 3: _build_prompt() 同步验证（dead code 防漏）
# ---------------------------------------------------------------------------

class TestBuildPromptSyncInjection:
    """_build_prompt() dead code 同步含 {ANATOMY_FIDELITY_RULES}（避免未来 dead → active 时遗漏）"""

    def test_anatomy_fidelity_in_build_prompt(self, director_source):
        """T20-48 wire: _build_prompt() 亦含 ANATOMY_FIDELITY_RULES（dead code 同步）"""
        # 至少 2 处 {ANATOMY_FIDELITY_RULES}（一处 _build_scene_prompt，一处 _build_prompt）
        occurrences = director_source.count("{ANATOMY_FIDELITY_RULES}")
        assert occurrences >= 2, (
            f"T20-48 wire: {{ANATOMY_FIDELITY_RULES}} 仅出现 {occurrences} 次，"
            "期望至少 2 次 (_build_scene_prompt + _build_prompt)"
        )


# ---------------------------------------------------------------------------
# Test 4: storyboard_prompts.py 定义验证
# ---------------------------------------------------------------------------

class TestPromptDefinition:
    """storyboard_prompts.py 中 ANATOMY_FIDELITY_RULES 内容符合预期"""

    def test_anatomy_fidelity_rules_defined(self, prompts_source):
        """storyboard_prompts.py 含 ANATOMY_FIDELITY_RULES 定义"""
        assert "ANATOMY_FIDELITY_RULES" in prompts_source, (
            "storyboard_prompts.py 中找不到 ANATOMY_FIDELITY_RULES 定义，"
            "请确认 AI-ML 已完成 T20-48 prompt 层任务"
        )

    def test_anatomy_fidelity_rules_contains_exactly_2_hands(self, prompts_source):
        """ANATOMY_FIDELITY_RULES 含关键约束文本 'EXACTLY 2 hands'"""
        assert "EXACTLY 2 hands" in prompts_source, (
            "ANATOMY_FIDELITY_RULES 缺少关键约束 'EXACTLY 2 hands'，"
            "规则内容可能不完整"
        )

    def test_anatomy_fidelity_rules_contains_anatomy_fidelity_header(self, prompts_source):
        """ANATOMY_FIDELITY_RULES 含标题 'ANATOMY FIDELITY'"""
        assert "ANATOMY FIDELITY" in prompts_source, (
            "ANATOMY_FIDELITY_RULES 缺少标题 'ANATOMY FIDELITY'"
        )


# ---------------------------------------------------------------------------
# Test 5: 语法验证
# ---------------------------------------------------------------------------

class TestSyntaxValid:
    """py_compile 验证改动后语法正确"""

    def test_storyboard_director_syntax(self):
        """storyboard_director.py 语法正确"""
        path = str(project_root / "app" / "services" / "storyboard_director.py")
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"storyboard_director.py 语法错误: {e}")

    def test_storyboard_prompts_syntax(self):
        """storyboard_prompts.py 语法正确"""
        path = str(project_root / "app" / "prompts" / "storyboard_prompts.py")
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            pytest.fail(f"storyboard_prompts.py 语法错误: {e}")
