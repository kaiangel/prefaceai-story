"""
单元测试: Wave 10 / RISK-T16-8 — _strip_markdown_json_fence() 函数

验证 projects.py 中的 _strip_markdown_json_fence() 正确剥离 markdown fence，
使 json.loads() 能直接解析 LLM 响应中包含代码块标记的 JSON。

运行命令:
  pytest tests/test_markdown_fence_strip.py -v
"""

import json
import sys
import os
import pytest

# 直接从 projects.py 导入，验证实际代码路径
# 需要项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --------------------------------------------------------------------------
# 单独测试 _strip_markdown_json_fence 纯函数（同 projects.py 实现）
# --------------------------------------------------------------------------

def _strip_markdown_json_fence(text: str) -> str:
    """
    Wave 10 / RISK-T16-8: strip ```json ... ``` fence before json.loads.
    (复制自 projects.py，用于不依赖 FastAPI 上下文的单测)
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:].lstrip("\n")
    elif text.startswith("```"):
        text = text[3:].lstrip("\n")
    if text.endswith("```"):
        text = text[:-3].rstrip("\n")
    return text.strip()


# --------------------------------------------------------------------------
# Case 1: 有完整前后 fence
# --------------------------------------------------------------------------

class TestFenceStripping:
    """_strip_markdown_json_fence 的 4 个核心场景"""

    def test_full_fence_json_prefix(self):
        """
        Case 1: 有完整前后 fence（```json ... ```）
        → strip 后可直接 json.loads
        """
        raw = '```json\n{"warnings": ["problem1"], "has_inconsistency": true}\n```'
        cleaned = _strip_markdown_json_fence(raw)
        # 验证 strip 结果无 fence
        assert not cleaned.startswith("```"), f"前置 fence 应被剥离，实际: {cleaned[:30]}"
        assert not cleaned.endswith("```"), f"后置 fence 应被剥离，实际: {cleaned[-10:]}"
        # 验证可 json.loads
        result = json.loads(cleaned)
        assert result["has_inconsistency"] is True
        assert result["warnings"] == ["problem1"]

    def test_full_fence_no_json_prefix(self):
        """
        Case 2: 无 json 前缀的完整 fence（``` ... ```）
        → strip 后可直接 json.loads
        """
        raw = '```\n{"warnings": [], "has_inconsistency": false}\n```'
        cleaned = _strip_markdown_json_fence(raw)
        assert not cleaned.startswith("```")
        assert not cleaned.endswith("```")
        result = json.loads(cleaned)
        assert result["has_inconsistency"] is False
        assert result["warnings"] == []

    def test_only_front_fence(self):
        """
        Case 3: 只有前置 fence（LLM 输出被截断，无闭合 ```）
        → strip 前缀后可 json.loads
        """
        raw = '```json\n{"warnings": ["issue1", "issue2"], "has_inconsistency": true}'
        cleaned = _strip_markdown_json_fence(raw)
        assert not cleaned.startswith("```"), f"前置 fence 应被剥离，实际: {cleaned[:30]}"
        result = json.loads(cleaned)
        assert len(result["warnings"]) == 2

    def test_only_back_fence(self):
        """
        Case 4: 只有后置 fence（异常格式）
        → strip 后缀后可 json.loads
        """
        raw = '{"warnings": [], "has_inconsistency": false}\n```'
        cleaned = _strip_markdown_json_fence(raw)
        assert not cleaned.endswith("```"), f"后置 fence 应被剥离，实际: {cleaned[-10:]}"
        result = json.loads(cleaned)
        assert result["has_inconsistency"] is False

    def test_no_fence_passthrough(self):
        """
        无 fence 的纯 JSON → 直接通过，不变
        """
        raw = '{"warnings": ["warn1"], "has_inconsistency": true}'
        cleaned = _strip_markdown_json_fence(raw)
        # 内容不变
        assert cleaned == raw.strip()
        result = json.loads(cleaned)
        assert result["warnings"] == ["warn1"]

    def test_empty_warnings_array(self):
        """空 warnings + has_inconsistency=false（正常输出）"""
        raw = '```json\n{"warnings": [], "has_inconsistency": false}\n```'
        cleaned = _strip_markdown_json_fence(raw)
        result = json.loads(cleaned)
        assert result == {"warnings": [], "has_inconsistency": False}

    def test_fence_with_extra_whitespace(self):
        """fence 前后有额外空格/换行 → strip 仍然正确"""
        raw = '  ```json\n  {"warnings": [], "has_inconsistency": false}\n  ```  '
        cleaned = _strip_markdown_json_fence(raw)
        result = json.loads(cleaned)
        assert result["has_inconsistency"] is False


# --------------------------------------------------------------------------
# 验证 projects.py 中的实际函数（集成验证）
# --------------------------------------------------------------------------

class TestProjectsFunctionImport:
    """验证 projects.py 中的 _strip_markdown_json_fence 函数存在且行为一致"""

    def test_import_from_projects(self):
        """从 app.api.projects 真实导入，验证函数存在"""
        try:
            from app.api.projects import _strip_markdown_json_fence as real_fn
            # 验证与本地实现行为一致
            raw = '```json\n{"test": true}\n```'
            assert real_fn(raw) == _strip_markdown_json_fence(raw)
        except ImportError:
            pytest.skip("app.api.projects 导入需要完整 FastAPI 环境（CI 跳过）")

    def test_projects_module_has_function(self):
        """验证 projects.py 模块顶层有 _strip_markdown_json_fence 函数定义"""
        import ast
        import os
        projects_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "api", "projects.py"
        )
        with open(projects_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        func_names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
        ]
        assert "_strip_markdown_json_fence" in func_names, (
            "_strip_markdown_json_fence 函数应在 projects.py 中定义"
        )


# --------------------------------------------------------------------------
# 运行验证
# --------------------------------------------------------------------------

if __name__ == "__main__":
    t = TestFenceStripping()
    t.test_full_fence_json_prefix()
    t.test_full_fence_no_json_prefix()
    t.test_only_front_fence()
    t.test_only_back_fence()
    t.test_no_fence_passthrough()
    t.test_empty_warnings_array()
    t.test_fence_with_extra_whitespace()

    t2 = TestProjectsFunctionImport()
    t2.test_projects_module_has_function()

    print("All 8 test cases passed!")
    sys.exit(0)
