"""
Error Pattern Sensors — 6 个历史错误模式的结构性测试

保护 ERROR_PATTERNS.md 中记录的 EP-005/006/007/009/013/014，
确保对应的防护逻辑存在于代码中，防止回归。

这些是结构性测试（检查代码中是否存在防护逻辑），不是功能测试。
执行时间 < 5 秒。
"""

import ast
import inspect
import os
import re
import textwrap

import pytest

# 项目根目录
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_source(relative_path: str) -> str:
    """读取项目源文件内容"""
    full_path = os.path.join(ROOT, relative_path)
    assert os.path.exists(full_path), f"源文件不存在: {relative_path}"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_ast(relative_path: str) -> ast.Module:
    """解析源文件的 AST"""
    source = _read_source(relative_path)
    return ast.parse(source, filename=relative_path)


# ---------------------------------------------------------------------------
# EP-005: Shot 拆分后丢失 characters_in_scene
# ---------------------------------------------------------------------------


class TestEP005ShotCharactersInScene:
    """EP-005: Shot 拆分后必须继承 characters_in_scene。

    storyboard_service.py 的 scene→shot 转换逻辑中，拆分和不拆分两条路径
    都必须将 scene 的 characters_in_scene 赋给 shot。如果缺失，shot 生成时
    不会传入角色参考图，导致角色变脸。
    """

    def test_shots_have_characters_in_scene(self):
        """EP-005 sensor: 检查 storyboard_service.py 中 shot 拆分后
        是否有 characters_in_scene 继承逻辑。

        验证方式：源码中同时存在：
        1. 获取 scene 的 characters_in_scene
        2. 将其赋值给 shot（至少两处——拆分和不拆分路径）
        """
        source = _read_source("app/services/storyboard_service.py")

        # 1. 从 scene 获取 characters_in_scene
        assert "characters_in_scene" in source, (
            "storyboard_service.py 中没有 characters_in_scene 相关逻辑"
        )

        # 2. scene 级别获取
        assert re.search(
            r"scene.*\.get\(['\"]characters_in_scene['\"]",
            source,
        ), "未从 scene 获取 characters_in_scene"

        # 3. 赋值给 shot（应有至少两处：拆分路径 + 不拆分路径）
        # 不使用 DOTALL，确保每行独立匹配
        assign_pattern = re.compile(
            r"shot\[.{0,40}characters_in_scene.{0,10}\]\s*="
        )
        assign_count = len(assign_pattern.findall(source))
        assert assign_count >= 2, (
            f"characters_in_scene 赋值给 shot 的代码只找到 {assign_count} 处，"
            f"预期 >= 2（拆分 + 不拆分两条路径）"
        )


# ---------------------------------------------------------------------------
# EP-006: 繁简体不匹配导致音画对齐失败
# ---------------------------------------------------------------------------


class TestEP006TraditionalChineseAlignment:
    """EP-006: alignment_service.py 必须有繁简转换函数。

    Whisper 经常输出繁体中文，如果不做繁简转换就匹配，音画对齐会大面积失败。
    """

    def test_alignment_handles_traditional_chinese(self):
        """EP-006 sensor: 检查 alignment_service.py 中是否有繁简转换函数
        （_convert_to_simplified 或类似），且该函数被实际调用。
        """
        source = _read_source("app/services/alignment_service.py")

        # 1. 繁简转换函数存在
        has_convert_func = (
            "_convert_to_simplified" in source
            or "convert_to_simplified" in source
            or "traditional_to_simplified" in source
        )
        assert has_convert_func, (
            "alignment_service.py 缺少繁简转换函数 "
            "(_convert_to_simplified / convert_to_simplified / traditional_to_simplified)"
        )

        # 2. 函数被调用（不只是定义）
        # 定义行用 def，调用行不以 def 开头
        lines = source.split("\n")
        call_lines = [
            line for line in lines
            if ("_convert_to_simplified" in line or "convert_to_simplified" in line)
            and not line.strip().startswith("def ")
            and not line.strip().startswith("#")
            and not line.strip().startswith('"""')
        ]
        assert len(call_lines) >= 1, (
            "繁简转换函数已定义但未被调用——EP-006 防护无效"
        )


# ---------------------------------------------------------------------------
# EP-007: 条漫 Gemini 渲染中文文字乱码
# ---------------------------------------------------------------------------


class TestEP007ComicModeTextFree:
    """EP-007: 条漫相关 prompt 模板必须包含 TEXT-FREE 指令。

    Gemini 无法正确渲染中文，条漫模式下 image_prompt 不能包含文字生成指令。
    system_instruction 中必须有 TEXT-FREE 指令阻止模型生成任何文字。
    """

    def test_comic_mode_prompt_no_text_instruction(self):
        """EP-007 sensor: 检查 storyboard_prompts.py 的 system instruction
        中包含 TEXT-FREE 或 DO NOT include any text 指令。
        """
        source = _read_source("app/prompts/storyboard_prompts.py")

        has_text_free = "TEXT-FREE" in source or "TEXT_FREE" in source
        has_do_not_text = "DO NOT" in source and (
            "text" in source.lower()
        )

        assert has_text_free or has_do_not_text, (
            "storyboard_prompts.py 缺少 TEXT-FREE / 'DO NOT include any text' 指令，"
            "条漫模式下 Gemini 会生成中文乱码 (EP-007)"
        )

        # 进一步检查：TEXT-FREE 指令在 system instruction builder 中
        # build_system_instruction_phase2 函数应包含 TEXT-FREE
        assert re.search(
            r"def\s+build_system_instruction_phase2",
            source,
        ), "build_system_instruction_phase2 函数不存在"

        # 提取该函数体，确认 TEXT-FREE 在其中
        func_match = re.search(
            r"def\s+build_system_instruction_phase2\b.*?(?=\ndef\s|\Z)",
            source,
            re.DOTALL,
        )
        assert func_match, "无法提取 build_system_instruction_phase2 函数体"
        func_body = func_match.group(0)
        assert "TEXT-FREE" in func_body, (
            "build_system_instruction_phase2 函数体中缺少 TEXT-FREE 指令"
        )


# ---------------------------------------------------------------------------
# EP-009: IMAGE 编号与 contents 数组不对应
# ---------------------------------------------------------------------------


class TestEP009ImageReferenceNumbering:
    """EP-009: prompt 中 IMAGE 编号映射必须与 contents 数组组装逻辑一致。

    DEC-014 后 previous_shot_image 已移除，Image 1 = 第一个角色参考图。
    如果 prompt 描述与 contents 实际顺序不符，模型会混淆角色身份。
    """

    def test_image_reference_numbering_consistent(self):
        """EP-009 sensor: 检查 storyboard_prompts.py 使用标签声明式
        参考图映射（SQ-1），且 image_generator.py 的 contents 数组
        按 [prompt, ref_img_1, ref_img_2, ...] 顺序组装。

        DEC-014 后不应有 previous_shot 占位。
        """
        prompts_source = _read_source("app/prompts/storyboard_prompts.py")
        ig_source = _read_source("app/services/image_generator.py")

        # 1. storyboard_prompts.py 使用标签声明式（SQ-1）
        # 检查 build_character_reference_mapping_phase2 存在
        assert "build_character_reference_mapping_phase2" in prompts_source, (
            "storyboard_prompts.py 缺少 build_character_reference_mapping_phase2"
        )

        # 2. 标签声明式：不依赖 IMAGE N 精确对应
        # 函数注释或代码中应提到 "label" 方式
        func_match = re.search(
            r"def\s+build_character_reference_mapping_phase2\b.*?(?=\ndef\s|\Z)",
            prompts_source,
            re.DOTALL,
        )
        assert func_match, "无法提取 build_character_reference_mapping_phase2"
        func_body = func_match.group(0)
        assert "label" in func_body.lower(), (
            "build_character_reference_mapping_phase2 未使用标签声明式 (SQ-1)"
        )

        # 3. image_generator.py contents 组装：prompt 在前，参考图在后
        # contents = [full_prompt] ... contents.append(ref_img)
        assert re.search(r"contents\s*=\s*\[.*prompt", ig_source), (
            "image_generator.py 中 contents 数组未以 prompt 开头"
        )

        # 4. DEC-014: 不应有 previous_shot 作为 contents 元素
        # 检查 Phase2 generate 函数中无 contents.append(previous_shot) 或类似
        # 注意：注释中提到 "previous_shot removed" 是正常的，只检查实际代码
        phase2_marker = ig_source.find("# 4. 构建contents")
        if phase2_marker >= 0:
            phase2_section = ig_source[phase2_marker:]
            # 查找实际将 previous_shot 加入 contents 的代码（非注释行）
            section_lines = phase2_section[:800].split("\n")
            code_lines_with_prev_shot = [
                line for line in section_lines
                if "previous_shot" in line
                and "contents" in line
                and not line.strip().startswith("#")
            ]
            assert len(code_lines_with_prev_shot) == 0, (
                "image_generator.py contents 组装中仍有 previous_shot 加入 contents "
                "的代码（DEC-014 应已移除）"
            )


# ---------------------------------------------------------------------------
# EP-013: JSON 引号修复不完整导致 Pipeline 中断
# ---------------------------------------------------------------------------


class TestEP013JsonRepairStateMachine:
    """EP-013: LLM 输出的 JSON 必须有鲁棒的修复/清理逻辑。

    LLM 生成的 JSON 经常包含未转义引号等格式错误。story_outline_generator.py
    中应有状态机级别的 JSON 修复函数（_fix_unescaped_quotes），而不仅是
    简单的正则替换。
    """

    def test_json_repair_state_machine_exists(self):
        """EP-013 sensor: 检查 story_outline_generator.py 中有 JSON 修复逻辑
        （状态机方案 _fix_unescaped_quotes 或等价实现）。

        验证要点：
        1. 修复函数存在
        2. 函数在 _extract_json 中被调用（修复→解析链路完整）
        """
        source = _read_source("app/services/story_outline_generator.py")

        # 1. 修复函数存在
        has_fix_func = (
            "_fix_unescaped_quotes" in source
            or "repair_json" in source
            or "fix_json" in source
        )
        assert has_fix_func, (
            "story_outline_generator.py 缺少 JSON 修复函数 "
            "(_fix_unescaped_quotes / repair_json / fix_json)"
        )

        # 2. 修复函数使用状态机（逐字符遍历 + in_string 状态跟踪）
        # 检查特征代码片段
        has_state_machine_traits = (
            "in_string" in source
            and ("while" in source or "for" in source)
        )
        assert has_state_machine_traits, (
            "JSON 修复函数缺少状态机特征（in_string + 循环遍历），"
            "简单正则无法覆盖所有 edge case (EP-013)"
        )

        # 3. _extract_json 调用了修复函数
        extract_match = re.search(
            r"def\s+_extract_json\b.*?(?=\n    def\s|\Z)",
            source,
            re.DOTALL,
        )
        assert extract_match, "_extract_json 函数不存在"
        extract_body = extract_match.group(0)
        assert (
            "_fix_unescaped_quotes" in extract_body
            or "repair_json" in extract_body
            or "fix_json" in extract_body
        ), "_extract_json 未调用 JSON 修复函数——修复→解析链路断裂"


# ---------------------------------------------------------------------------
# EP-014: confirm-outline 数据未传入 Pipeline
# ---------------------------------------------------------------------------


class TestEP014ConfirmedOutlineUsed:
    """EP-014: pipeline_orchestrator.py 必须有使用用户确认后大纲的逻辑。

    用户在 Stage B 修改的 mood、selected_ending 等必须传入 Pipeline。
    orchestrator.run() 必须接受 confirmed_outline 参数，且有条件跳过
    LLM 生成（直接使用确认后的大纲）。
    """

    def test_confirmed_outline_used_in_pipeline(self):
        """EP-014 sensor: 检查 pipeline_orchestrator.py 中有
        confirmed_outline 相关代码路径。

        验证要点：
        1. run() 方法接受 confirmed_outline 参数
        2. 有条件判断：如果有 confirmed_outline 则跳过 Stage 1 LLM 生成
        3. confirmed_outline 被赋值给 outline 变量（实际使用）
        """
        source = _read_source("app/services/pipeline_orchestrator.py")

        # 1. run() 方法签名中有 confirmed_outline 参数
        assert re.search(
            r"def\s+run\b.*confirmed_outline",
            source,
            re.DOTALL,
        ), "pipeline_orchestrator.py run() 缺少 confirmed_outline 参数"

        # 2. 条件判断：if confirmed_outline
        assert re.search(
            r"if\s+confirmed_outline",
            source,
        ), "pipeline_orchestrator.py 缺少 'if confirmed_outline' 条件判断"

        # 3. confirmed_outline 被赋值给 outline（实际使用）
        assert re.search(
            r"outline\s*=\s*confirmed_outline",
            source,
        ), (
            "pipeline_orchestrator.py 中 confirmed_outline 未被赋值给 outline——"
            "用户确认后的大纲不会被实际使用 (EP-014)"
        )
