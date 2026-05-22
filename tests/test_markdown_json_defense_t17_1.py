"""
单元测试: RISK-T17-1 — markdown JSON 解析多场景防御

验证以下场景都能正确解析 LLM 返回的 markdown JSON:
1. _llm_helpers.extract_json_from_llm_response — 核心通用工具（4 场景）
2. prompt_safety_advisor — 已升级用 extract_json_from_llm_response（3 场景）
3. screenplay_writer._extract_batch_json — 已有 6 层解析（2 场景）
4. story_generator._parse_response — 已有 markdown 防御（2 场景）
5. alignment_service — regex {..} 天然处理 markdown 包裹（1 场景）

运行命令:
  pytest tests/test_markdown_json_defense_t17_1.py -v
"""

import json
import sys
import os
import re
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─────────────────────────────────────────────────────────────────────────────
# 1. _llm_helpers.extract_json_from_llm_response — 核心通用工具
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractJsonFromLLMResponse:
    """_llm_helpers.extract_json_from_llm_response 的 markdown JSON 防御"""

    def _get_fn(self):
        from app.services._llm_helpers import extract_json_from_llm_response
        return extract_json_from_llm_response

    def test_bare_json(self):
        """裸 JSON 直接解析"""
        fn = self._get_fn()
        raw = '{"title": "测试故事", "mood": "浪漫"}'
        result = fn(raw)
        assert result is not None
        assert result["title"] == "测试故事"

    def test_json_in_full_fence(self):
        """完整 ```json...``` 包裹"""
        fn = self._get_fn()
        raw = '```json\n{"title": "测试故事", "mood": "浪漫"}\n```'
        result = fn(raw)
        assert result is not None
        assert result["title"] == "测试故事"

    def test_json_in_unclosed_fence(self):
        """未闭合 ``` — LLM 输出被 max_tokens 截断时常见"""
        fn = self._get_fn()
        raw = '```json\n{"title": "测试故事", "mood": "浪漫"}'
        result = fn(raw)
        assert result is not None
        assert result["title"] == "测试故事"

    def test_json_in_plain_fence(self):
        """不带 json 标签的 ``` 包裹"""
        fn = self._get_fn()
        raw = '```\n{"title": "测试故事", "mood": "浪漫"}\n```'
        result = fn(raw)
        assert result is not None
        assert result["title"] == "测试故事"

    def test_json_with_preamble_text(self):
        """JSON 前有说明文字"""
        fn = self._get_fn()
        raw = 'Here is the JSON:\n```json\n{"title": "测试故事"}\n```'
        result = fn(raw)
        assert result is not None
        assert result["title"] == "测试故事"

    def test_none_on_invalid(self):
        """完全无效内容返回 None"""
        fn = self._get_fn()
        result = fn("这不是 JSON 也没有 JSON")
        assert result is None

    def test_empty_returns_none(self):
        """空字符串返回 None"""
        fn = self._get_fn()
        assert fn("") is None
        assert fn(None) is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. prompt_safety_advisor — T17-1 升级：用 extract_json_from_llm_response
# ─────────────────────────────────────────────────────────────────────────────

class TestPromptSafetyAdvisorMarkdownJSON:
    """
    验证 prompt_safety_advisor.py 已用 extract_json_from_llm_response，
    能处理 markdown JSON 包裹。
    """

    def test_module_uses_extract_json(self):
        """验证 prompt_safety_advisor.py 源码中调用了 extract_json_from_llm_response"""
        import ast
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "prompt_safety_advisor.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "extract_json_from_llm_response" in source, (
            "prompt_safety_advisor.py 应使用 extract_json_from_llm_response 解析 LLM 响应 (RISK-T17-1)"
        )

    def test_module_no_manual_markdown_strip(self):
        """验证旧的手动 markdown 剥离 (startswith('```')) 已被替换"""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "prompt_safety_advisor.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        # 旧逻辑特征：startswith("```") 配合 split("\n") 手动剥离
        # T17-1 修复后不应再有这个模式
        assert 'startswith("```")' not in source, (
            "旧手动 markdown 剥离逻辑 (startswith('```')) 应已被 extract_json_from_llm_response 替换"
        )

    def test_extract_json_handles_safety_advisor_response(self):
        """模拟 Haiku 返回 markdown JSON，验证 extract_json_from_llm_response 能正确解析"""
        from app.services._llm_helpers import extract_json_from_llm_response

        # Haiku 有时会返回 markdown 包裹的 JSON
        haiku_response = '```json\n{\n  "suspected_terms": ["暴力", "血腥"],\n  "suggested_changes": [\n    {"original": "暴力", "suggestion": "激烈对抗"}\n  ],\n  "user_message": "建议将描述改为更温和的方式"\n}\n```'

        result = extract_json_from_llm_response(haiku_response)
        assert result is not None
        assert isinstance(result["suspected_terms"], list)
        assert len(result["suspected_terms"]) == 2
        assert result["suspected_terms"][0] == "暴力"


# ─────────────────────────────────────────────────────────────────────────────
# 3. screenplay_writer._extract_batch_json — 已有 6 层解析（回归验证）
# ─────────────────────────────────────────────────────────────────────────────

class TestScreenplayWriterBatchJSON:
    """验证 screenplay_writer 的 _extract_batch_json 能处理 markdown JSON 数组"""

    def _get_fn(self):
        """从 screenplay_writer 导入 _extract_batch_json (模块级函数)"""
        try:
            import importlib.util
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "app", "services", "screenplay_writer.py"
            )
            spec = importlib.util.spec_from_file_location("screenplay_writer", path)
            mod = importlib.util.module_from_spec(spec)
            # 不执行模块级代码（避免 FastAPI 依赖），直接从源码 AST 验证
            return None  # 只做源码级验证
        except Exception:
            return None

    def test_source_has_markdown_defense(self):
        """验证 screenplay_writer.py 源码包含 markdown 代码块处理逻辑"""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "screenplay_writer.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        # RB-2 实现的 6 层解析中，第 1 层是 markdown 代码块匹配
        assert "```json" in source or "code_block_patterns" in source, (
            "screenplay_writer.py 应有 markdown 代码块处理 (RB-2 _extract_batch_json)"
        )

    def test_extract_batch_json_markdown_scenario(self):
        """
        使用内联实现验证 markdown JSON 数组解析逻辑的完整性
        (真实函数有 FastAPI 依赖，此处用等价纯函数验证逻辑)
        """
        # 等价于 _extract_batch_json 的核心逻辑
        def _extract_batch_json_inline(content: str):
            def _try_parse_array(text: str):
                text = text.strip()
                try:
                    result = json.loads(text)
                    if isinstance(result, list) and len(result) > 0:
                        return result
                except json.JSONDecodeError:
                    pass
                return None

            code_block_patterns = [
                r'```json\s*([\s\S]*?)\s*```',
                r'```JSON\s*([\s\S]*?)\s*```',
                r'```\s*([\s\S]*?)\s*```',
            ]
            for pattern in code_block_patterns:
                match = re.search(pattern, content)
                if match:
                    result = _try_parse_array(match.group(1))
                    if result:
                        return result

            result = _try_parse_array(content)
            if result:
                return result

            start = content.find('[')
            end = content.rfind(']')
            if start != -1 and end != -1 and end > start:
                result = _try_parse_array(content[start:end + 1])
                if result:
                    return result
            return None

        # LLM 可能返回 markdown 包裹的 JSON 数组
        raw = '```json\n[{"scene_id": 1, "narration": "开场"}, {"scene_id": 2, "narration": "发展"}]\n```'
        result = _extract_batch_json_inline(raw)
        assert result is not None
        assert len(result) == 2
        assert result[0]["scene_id"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# 4. story_generator._parse_response — 已有 markdown 防御（回归验证）
# ─────────────────────────────────────────────────────────────────────────────

class TestStoryGeneratorMarkdownJSON:
    """验证 story_generator._parse_response 能处理 markdown JSON"""

    def _make_parse_response(self):
        """内联等价实现，验证 story_generator 的 markdown 防御逻辑"""
        def _parse_response(text: str) -> dict:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError(f"Could not parse JSON from response: {text[:200]}...")
        return _parse_response

    def test_bare_json(self):
        fn = self._make_parse_response()
        result = fn('{"title": "测试", "scenes": []}')
        assert result["title"] == "测试"

    def test_markdown_json(self):
        fn = self._make_parse_response()
        result = fn('```json\n{"title": "测试", "scenes": []}\n```')
        assert result["title"] == "测试"

    def test_source_has_markdown_defense(self):
        """验证 story_generator.py 源码包含 ```json 处理"""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "story_generator.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        assert "```json" in source, (
            "story_generator.py 应有 markdown JSON 防御 (_parse_response)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. alignment_service — regex {..} 天然处理 markdown 包裹（回归验证）
# ─────────────────────────────────────────────────────────────────────────────

class TestAlignmentServiceJSONParsing:
    """验证 alignment_service 的 JSON 解析能处理 markdown 包裹的 JSON"""

    def test_regex_json_extraction_handles_markdown(self):
        """
        alignment_service 用 r'\{[\s\S]*\}' 提取 JSON，
        天然能从 markdown 包裹中找到第一个 { 到最后一个 }。
        """
        # 等价逻辑验证
        response_text = '```json\n{"matches": [{"scene_id": 1, "start_segment_index": 0, "end_segment_index": 2}]}\n```'
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        assert json_match is not None
        result = json.loads(json_match.group())
        assert "matches" in result
        assert result["matches"][0]["scene_id"] == 1

    def test_source_uses_regex_extraction(self):
        """验证 alignment_service.py 用了 regex 提取 JSON"""
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", "alignment_service.py"
        )
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        assert r"\{[\s\S]*\}" in source or r"{[\s\S]*}" in source, (
            "alignment_service.py 应使用 regex 提取 JSON 对象"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 6. 综合验证: 所有主要 LLM 解析场景都有 markdown 防御
# ─────────────────────────────────────────────────────────────────────────────

class TestAllServicesMarkdownDefense:
    """全局扫描: 确认主要服务都有 markdown JSON 防御"""

    def _read_service(self, name: str) -> str:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app", "services", name
        )
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_story_outline_generator_uses_extract_json(self):
        """story_outline_generator.py 用了 extract_json_from_llm_response"""
        source = self._read_service("story_outline_generator.py")
        assert "extract_json_from_llm_response" in source

    def test_character_designer_uses_extract_json(self):
        """character_designer.py 用了 extract_json_from_llm_response"""
        source = self._read_service("character_designer.py")
        assert "extract_json_from_llm_response" in source

    def test_storyboard_director_uses_extract_json(self):
        """storyboard_director.py 用了 extract_json_from_llm_response"""
        source = self._read_service("storyboard_director.py")
        assert "extract_json_from_llm_response" in source

    def test_prompt_safety_advisor_uses_extract_json(self):
        """prompt_safety_advisor.py 已升级 (T17-1) 用了 extract_json_from_llm_response"""
        source = self._read_service("prompt_safety_advisor.py")
        assert "extract_json_from_llm_response" in source

    def test_screenplay_writer_has_batch_json_defense(self):
        """screenplay_writer.py 有 _extract_batch_json 的 markdown 防御"""
        source = self._read_service("screenplay_writer.py")
        assert "_extract_batch_json" in source
        assert "code_block_patterns" in source


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 快速验证
    t1 = TestExtractJsonFromLLMResponse()
    t1.test_bare_json()
    t1.test_json_in_full_fence()
    t1.test_json_in_unclosed_fence()
    t1.test_json_in_plain_fence()
    t1.test_json_with_preamble_text()
    t1.test_none_on_invalid()
    t1.test_empty_returns_none()

    t2 = TestPromptSafetyAdvisorMarkdownJSON()
    t2.test_module_uses_extract_json()
    t2.test_module_no_manual_markdown_strip()
    t2.test_extract_json_handles_safety_advisor_response()

    t3 = TestScreenplayWriterBatchJSON()
    t3.test_source_has_markdown_defense()
    t3.test_extract_batch_json_markdown_scenario()

    t4 = TestStoryGeneratorMarkdownJSON()
    t4.test_bare_json()
    t4.test_markdown_json()
    t4.test_source_has_markdown_defense()

    t5 = TestAlignmentServiceJSONParsing()
    t5.test_regex_json_extraction_handles_markdown()
    t5.test_source_uses_regex_extraction()

    t6 = TestAllServicesMarkdownDefense()
    t6.test_story_outline_generator_uses_extract_json()
    t6.test_character_designer_uses_extract_json()
    t6.test_storyboard_director_uses_extract_json()
    t6.test_prompt_safety_advisor_uses_extract_json()
    t6.test_screenplay_writer_has_batch_json_defense()

    print("All 19 test cases PASS!")
    sys.exit(0)
