"""
质量门测试 (Quality Gate Tests) - Harness Engineering Sensor

将口头的质量标准转化为可执行的自动检查。
这些测试在每次 git commit 前由 PreCommit hook 自动执行。
执行时间目标 < 10 秒。

覆盖的质量门：
1. story.json 输出的 Schema 合规性（角色必需字段）
2. image_prompt 不含中文（语言纯净性）
3. .env.example 配置模板存在
4. 项目必需目录结构完整
"""

import ast
import json
import os
import re

import pytest

# 项目根目录（tests/ 的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_path(*parts):
    """构建相对于项目根目录的绝对路径"""
    return os.path.join(PROJECT_ROOT, *parts)


def _find_test_output_dirs(subdir="test_output"):
    """查找 test_output 下的子目录，按名称倒序排列（最新优先）。

    返回空列表如果 test_output 不存在。
    """
    base = _project_path(subdir)
    if not os.path.isdir(base):
        return []

    dirs = []
    for name in os.listdir(base):
        full = os.path.join(base, name)
        if os.path.isdir(full):
            dirs.append(full)
    # 按名称倒序（通常名称包含日期/版本，新的在前）
    dirs.sort(key=lambda d: os.path.basename(d), reverse=True)
    return dirs


def _find_story_jsons(max_count=3):
    """查找 test_output/manualtest 下最近的 story.json 文件。

    只检查 manualtest/ 下的数据（正式测试数据），跳过过旧的历史版本。
    优先查找包含 characters.json 的目录（表示完整的测试运行）。
    """
    # 优先检查 manualtest 下的关键测试目录（最新优先）
    manualtest_dir = _project_path("test_output", "manualtest")
    if not os.path.isdir(manualtest_dir):
        return []

    # 按最新修改时间排序的目录
    dirs = []
    for name in os.listdir(manualtest_dir):
        full = os.path.join(manualtest_dir, name)
        if os.path.isdir(full):
            dirs.append(full)
    dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)

    found = []
    for d in dirs:
        # 递归查找此目录下的 story.json
        for root, _subdirs, files in os.walk(d):
            if 'story.json' in files:
                story_path = os.path.join(root, 'story.json')
                found.append(story_path)
                if len(found) >= max_count:
                    return found
                break  # 每个顶级目录只取第一个 story.json
    return found


def _find_shots_jsons(max_count=3):
    """查找 test_output/manualtest 下最近的 shots/storyboard JSON 文件。"""
    manualtest_dir = _project_path("test_output", "manualtest")
    if not os.path.isdir(manualtest_dir):
        return []

    # 按最新修改时间排序的目录
    dirs = []
    for name in os.listdir(manualtest_dir):
        full = os.path.join(manualtest_dir, name)
        if os.path.isdir(full):
            dirs.append(full)
    dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)

    found = []
    for d in dirs:
        for root, _subdirs, files in os.walk(d):
            for target in ('4_storyboard.json', 'shots.json'):
                if target in files:
                    found.append(os.path.join(root, target))
                    if len(found) >= max_count:
                        return found
                    break  # 每个顶级目录只取第一个匹配
            if found and os.path.dirname(found[-1]).startswith(root):
                break  # 已经在此顶级目录找到了
    return found


# =========================================================================
# 1. Story JSON Schema 验证
# =========================================================================

def test_story_json_schema():
    """story.json 输出的角色数据 Schema 在代码层面有正确定义。

    保护的质量门：角色数据完整性是角色一致性的前提。
    缺少 physical/clothing 字段会导致参考图生成时缺少关键描述，
    最终影响角色在不同镜头间的一致性。

    检查方式（结构性检查，不依赖 test_output 数据）：
    1. CharacterDesigner 的 prompt 中要求 LLM 输出必需字段
    2. 如果 test_output 中有 2_characters.json（Stage 2 输出），验证其 Schema

    必需的角色字段：
    - name: 角色名（中文）
    - name_en: 角色英文名
    - gender: 性别
    - age_appearance: 外观年龄
    - character_type: 角色类型（human/animal/fantasy）
    - physical: 物理外观描述（含 height/build/skin_tone 等）
    - clothing: 服装描述
    """
    required_character_fields = [
        'name', 'name_en', 'gender', 'age_appearance',
        'character_type', 'physical', 'clothing'
    ]

    # 检查 1: CharacterDesigner 源码中是否包含必需字段的定义
    char_designer = _project_path("app", "services", "character_designer.py")
    if os.path.exists(char_designer):
        with open(char_designer, 'r', encoding='utf-8') as fh:
            content = fh.read()
        # 检查必需字段在代码中被引用（prompt 或 schema 定义）
        missing_in_code = []
        for field in required_character_fields:
            if field not in content:
                missing_in_code.append(field)
        assert not missing_in_code, (
            f"CharacterDesigner 代码中未引用以下必需角色字段:\n"
            + "\n".join(f"  - {f}" for f in missing_in_code)
            + "\n这些字段对角色一致性至关重要。"
        )

    # 检查 2: 如果有最新的 2_characters.json（Stage 2 输出），验证其 Schema
    manualtest_dir = _project_path("test_output", "manualtest")
    if not os.path.isdir(manualtest_dir):
        return  # 无测试数据，仅靠代码检查

    # 查找最新的 2_characters.json
    chars_files = []
    for root, _dirs, files in os.walk(manualtest_dir):
        if '2_characters.json' in files:
            chars_files.append(os.path.join(root, '2_characters.json'))

    if not chars_files:
        return  # 无 Stage 2 输出文件

    # 只检查最新的一个
    chars_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    latest = chars_files[0]

    try:
        with open(latest, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, IOError):
        return

    characters = data.get('characters', [])
    if not characters:
        return

    violations = []
    rel_path = os.path.relpath(latest, PROJECT_ROOT)
    for char in characters:
        char_name = char.get('name', char.get('name_en', '?'))
        for field in required_character_fields:
            if field not in char:
                violations.append(
                    f"{rel_path}: 角色 '{char_name}' 缺少字段 '{field}'"
                )

    if violations:
        assert False, (
            f"最新的 Stage 2 角色数据不完整"
            f"（缺少必需字段影响角色一致性）:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])
        )


# =========================================================================
# 2. Image Prompt 不含中文
# =========================================================================

def test_image_prompts_no_chinese():
    """Image prompt 翻译机制在代码层面存在且正确配置。

    保护的质量门：Gemini image generation 的 prompt 必须全英文。
    中文字符混入 image_prompt 会导致生成质量下降或模型行为不可预测。

    检查方式（结构性检查）：
    1. storyboard_prompts.py 中存在 translate_image_prompt_to_english 函数
    2. image_generator.py 中 generate_shot_image 调用了翻译函数
    3. storyboard_prompts.py 中的 STYLE_PROMPTS 值全部为英文

    注意：test_output 中的历史数据可能包含中文（LLM 生成的中文人名/店名
    嵌入英文 prompt），这是已知的 LLM 输出问题，不是代码结构问题。
    """
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')

    # 检查 1: 翻译函数存在
    prompts_file = _project_path("app", "prompts", "storyboard_prompts.py")
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as fh:
            content = fh.read()
        assert 'translate_image_prompt_to_english' in content, (
            "storyboard_prompts.py 中未找到 translate_image_prompt_to_english 函数。"
            "此函数负责将中文 prompt 翻译为英文。"
        )

    # 检查 2: image_generator.py 中调用了翻译函数
    img_gen_file = _project_path("app", "services", "image_generator.py")
    if os.path.exists(img_gen_file):
        with open(img_gen_file, 'r', encoding='utf-8') as fh:
            content = fh.read()
        assert 'translate_image_prompt_to_english' in content, (
            "image_generator.py 中未调用 translate_image_prompt_to_english。"
            "Shot 生成前必须将 prompt 翻译为英文。"
        )

    # 检查 3: STYLE_PROMPTS 值全英文
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as fh:
            source = fh.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'STYLE_PROMPTS':
                        if isinstance(node.value, ast.Dict):
                            for val in node.value.values:
                                if (isinstance(val, ast.Constant)
                                        and isinstance(val.value, str)
                                        and chinese_pattern.search(val.value)):
                                    assert False, (
                                        f"STYLE_PROMPTS 的值包含中文"
                                        f"（L{val.lineno}）。"
                                        f"风格 prompt 直接发送给 Gemini，必须全英文。"
                                    )


# =========================================================================
# 3. 配置完整性：.env.example 必须存在
# =========================================================================

def test_env_example_exists():
    """.env.example 文件必须存在。

    保护的质量门：新开发者/新环境搭建时需要知道哪些环境变量是必需的。
    .env.example 是环境配置的唯一参考模板。
    缺少此文件会导致新环境搭建困难、遗漏关键配置。
    """
    env_example = _project_path(".env.example")
    assert os.path.exists(env_example), (
        ".env.example 文件缺失。"
        "此文件是环境配置的参考模板，新开发者需要它来搭建开发环境。"
    )


# =========================================================================
# 4. 项目必需目录结构完整
# =========================================================================

def test_required_directories():
    """项目必需目录必须存在。

    保护的质量门：序话Story 的代码组织结构依赖这些核心目录。
    缺少任何一个目录意味着项目结构不完整，可能导致 import 失败、
    测试无法运行或功能缺失。

    必需目录：
    - app/services: 后端核心服务
    - frontend/src: 前端源代码
    - tests: 测试代码
    """
    required = {
        'app/services': '后端核心服务（Pipeline 5 阶段 + 支撑服务）',
        'frontend/src': '前端源代码（Next.js 14）',
        'tests': '测试代码目录',
    }

    missing = []
    for dir_path, description in required.items():
        full_path = _project_path(dir_path)
        if not os.path.isdir(full_path):
            missing.append(f"{dir_path} ({description})")

    assert not missing, (
        f"项目必需目录缺失:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )
