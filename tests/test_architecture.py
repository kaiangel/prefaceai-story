"""
架构适应度测试 (Architecture Fitness Tests) - Harness Engineering Sensor

用代码强制执行架构规则，而不是靠文档+自觉。
灵感来源：OpenAI Codex 实验的"强制分层架构" + Mitchell Hashimoto 原则。

这些测试会在每次 git commit 前由 PreCommit hook 自动执行。
执行时间目标 < 10 秒。

覆盖的架构规则：
1. 前后端边界隔离 (EP-003)
2. Shot 生成默认使用 NB2 模型 (EP-001 衍生)
3. Image prompt 模板/构建不含中文 (EP-004)
4. Pipeline 5 阶段核心服务文件完整性
5. 参考图生成必须串行 portrait → fullbody (EP-002)
"""

import ast
import os
import re

# 项目根目录（tests/ 的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_path(*parts):
    """构建相对于项目根目录的绝对路径"""
    return os.path.join(PROJECT_ROOT, *parts)


# =========================================================================
# 1. 前后端边界隔离
# =========================================================================

def test_frontend_does_not_import_backend():
    """前端 TypeScript/TSX 文件不应直接引用后端 Python 模块路径。

    保护的架构规则：前后端通过 HTTP API 通信，前端不应有对后端
    Python 模块（app/services、app/models 等）的直接 import。
    违反此规则意味着前后端耦合，破坏了 API 边界。
    """
    frontend_dir = _project_path("frontend", "src")
    if not os.path.isdir(frontend_dir):
        return  # frontend 目录不存在时跳过

    # 后端模块路径模式
    backend_patterns = [
        re.compile(r"""from\s+['"]app/"""),        # from 'app/...'
        re.compile(r"""import\s+['"]app/"""),       # import 'app/...'
        re.compile(r"""require\(['"]app/"""),       # require('app/...')
        re.compile(r"""from\s+['"]\.\./app/"""),    # from '../app/...'
        re.compile(r"""from\s+['"]\.\.\/\.\.\/app/"""),  # from '../../app/...'
    ]

    violations = []
    for root, _dirs, files in os.walk(frontend_dir):
        for f in files:
            if not f.endswith(('.ts', '.tsx', '.js', '.jsx')):
                continue
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    content = fh.read()
            except (IOError, UnicodeDecodeError):
                continue
            for pattern in backend_patterns:
                if pattern.search(content):
                    rel = os.path.relpath(filepath, PROJECT_ROOT)
                    violations.append(rel)
                    break

    assert not violations, (
        f"前端文件直接引用了后端 Python 模块路径（应通过 API 通信）:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def test_backend_does_not_import_frontend():
    """后端 Python 文件不应引用前端模块。

    保护的架构规则：后端不应 import 或引用 frontend/ 目录下的任何模块。
    后端是独立的 Python 服务，不应依赖前端 Node.js 代码。
    """
    backend_dir = _project_path("app")
    if not os.path.isdir(backend_dir):
        return  # app 目录不存在时跳过

    # 前端模块引用模式
    frontend_patterns = [
        re.compile(r'^\s*from\s+frontend\b'),
        re.compile(r'^\s*import\s+frontend\b'),
        re.compile(r'^\s*from\s+["\']frontend/'),
    ]

    violations = []
    for root, _dirs, files in os.walk(backend_dir):
        for f in files:
            if not f.endswith('.py'):
                continue
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fh:
                    for line_num, line in enumerate(fh, 1):
                        for pattern in frontend_patterns:
                            if pattern.search(line):
                                rel = os.path.relpath(filepath, PROJECT_ROOT)
                                violations.append(f"{rel}:{line_num}")
                                break
            except (IOError, UnicodeDecodeError):
                continue

    assert not violations, (
        f"后端 Python 文件引用了前端模块（应通过 API 通信）:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


# =========================================================================
# 2. Shot 生成默认使用 NB2 模型
# =========================================================================

def test_shot_generation_uses_nb2_model():
    """Shot 图像生成的默认配置必须使用 NB2（Nano Banana 2）模型。

    保护的架构规则：Founder 决策 NB2 为默认主力生图模型。
    NB2 角色一致性 ~95%，速度快 3-5x，成本降 50%。
    Pro 模型仅作为未来 Premium 用户储备。

    检查项：
    1. ImageGenerator 类中定义了 NB2_MODEL 常量
    2. NB2_MODEL 的值包含 'gemini-3.1-flash-image'（NB2 模型标识）
    3. generate_image() 函数的 use_pro_model 参数默认值为 False
    """
    target_file = _project_path("app", "services", "image_generator.py")
    if not os.path.exists(target_file):
        return  # 文件不存在时跳过

    with open(target_file, 'r', encoding='utf-8') as fh:
        content = fh.read()
        tree = ast.parse(content)

    # 检查 1: NB2_MODEL 常量存在
    nb2_model_found = False
    nb2_model_value = None
    for node in ast.walk(tree):
        # 查找类属性赋值: NB2_MODEL = "..."
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'NB2_MODEL':
                    nb2_model_found = True
                    if isinstance(node.value, ast.Constant):
                        nb2_model_value = node.value.value
                elif isinstance(target, ast.Attribute) and target.attr == 'NB2_MODEL':
                    nb2_model_found = True
                    if isinstance(node.value, ast.Constant):
                        nb2_model_value = node.value.value

    assert nb2_model_found, (
        "image_generator.py 中未找到 NB2_MODEL 常量定义。"
        "Shot 生成必须使用 NB2 模型（Founder 决策）。"
    )

    # 检查 2: NB2_MODEL 值包含 NB2 模型标识
    assert nb2_model_value is not None and 'gemini-3.1-flash-image' in str(nb2_model_value), (
        f"NB2_MODEL 的值应包含 'gemini-3.1-flash-image'，"
        f"当前值: {nb2_model_value}"
    )

    # 检查 3: generate_image() 的 use_pro_model 参数默认值为 False
    use_pro_default_found = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == 'generate_image':
                # 检查参数默认值
                args = node.args
                # defaults 对应最后 N 个参数
                n_defaults = len(args.defaults)
                n_args = len(args.args)
                for i, default in enumerate(args.defaults):
                    arg_index = n_args - n_defaults + i
                    if arg_index < n_args:
                        arg_name = args.args[arg_index].arg
                        if arg_name == 'use_pro_model':
                            if isinstance(default, ast.Constant) and default.value is False:
                                use_pro_default_found = True

    assert use_pro_default_found, (
        "generate_image() 函数的 use_pro_model 参数默认值必须为 False。"
        "NB2 是默认主力模型，use_pro_model=False 是正确的默认配置。"
    )


# =========================================================================
# 3. Image Prompt 模板和构建函数不含中文
# =========================================================================

def test_prompt_templates_are_english():
    """Image prompt 模板/风格配置的英文输出部分不应包含中文。

    保护的架构规则：所有发送给 Gemini 的 image prompt 必须是英文。
    中文 prompt 会导致 Gemini 生成质量下降或出现意外行为。

    检查方式：
    1. storyboard_prompts.py 中的 STYLE_PROMPTS 字典值必须全英文
       （这些值直接拼进 image prompt）
    2. style_enforcer.py 中 StyleEnforcement 的 mandatory_keywords、
       forbidden_keywords、style_description、quality_keywords 必须全英文
       （这些值直接注入 image prompt 开头）

    不检查（允许中文的内容）：
    - 翻译字典的 key（中文 -> 英文映射，key 就是中文）
    - LLM 系统提示词（指导 LLM 如何写英文 prompt）
    - 日志/print 消息
    - 注释和 docstring
    """
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    violations = []

    # === 检查 1: storyboard_prompts.py 的 STYLE_PROMPTS 值 ===
    storyboard_file = _project_path("app", "prompts", "storyboard_prompts.py")
    if os.path.exists(storyboard_file):
        with open(storyboard_file, 'r', encoding='utf-8') as fh:
            source = fh.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            pass
        else:
            for node in ast.walk(tree):
                # 查找 STYLE_PROMPTS = { ... } 或 BASE_NEGATIVE_PROMPTS = [...]
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        target_name = None
                        if isinstance(target, ast.Name):
                            target_name = target.id
                        if target_name in ('STYLE_PROMPTS', 'BASE_NEGATIVE_PROMPTS',
                                           'STYLE_NEGATIVE_PROMPTS'):
                            # 检查字典的值（不检查 key）或列表元素
                            _check_dict_or_list_values(
                                node.value, target_name, storyboard_file,
                                chinese_pattern, violations
                            )

    # === 检查 2: style_enforcer.py 的 StyleEnforcement 配置值 ===
    enforcer_file = _project_path("app", "services", "style_enforcer.py")
    if os.path.exists(enforcer_file):
        with open(enforcer_file, 'r', encoding='utf-8') as fh:
            source = fh.read()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            pass
        else:
            # 查找 StyleEnforcement(...) 调用中的关键参数
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    func_name = None
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if func_name == 'StyleEnforcement':
                        for kw in node.keywords:
                            if kw.arg in ('mandatory_keywords', 'forbidden_keywords',
                                          'style_description', 'quality_keywords'):
                                _check_ast_value_for_chinese(
                                    kw.value, f"StyleEnforcement.{kw.arg}",
                                    enforcer_file, chinese_pattern, violations
                                )

    assert not violations, (
        f"Image prompt 配置中发现中文字符"
        f"（发送给 Gemini 的 prompt 必须全英文）:\n"
        + "\n".join(f"  - {v}" for v in violations)
    )


def _check_dict_or_list_values(node, var_name, filepath, chinese_pattern, violations):
    """递归检查 AST 字典值或列表元素中的中文。"""
    if isinstance(node, ast.Dict):
        for value in node.values:
            _check_ast_value_for_chinese(value, var_name, filepath, chinese_pattern, violations)
    elif isinstance(node, ast.List):
        for elt in node.elts:
            _check_ast_value_for_chinese(elt, var_name, filepath, chinese_pattern, violations)


def _check_ast_value_for_chinese(node, context, filepath, chinese_pattern, violations):
    """检查 AST 节点值（字符串/列表/字典）中是否包含中文。"""
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if chinese_pattern.search(node.value):
            line = getattr(node, 'lineno', '?')
            preview = node.value[:60].replace('\n', '\\n')
            violations.append(f"{rel}:{line} ({context}) -> \"{preview}\"")
    elif isinstance(node, ast.List):
        for elt in node.elts:
            _check_ast_value_for_chinese(elt, context, filepath, chinese_pattern, violations)
    elif isinstance(node, ast.Dict):
        for v in node.values:
            _check_ast_value_for_chinese(v, context, filepath, chinese_pattern, violations)


# =========================================================================
# 4. Pipeline 5 阶段核心服务文件完整性
# =========================================================================

def test_pipeline_services_exist():
    """5 阶段 Pipeline 的核心服务文件必须存在。

    保护的架构规则：序话Story 的 Pipeline 由 5 个阶段组成，
    每个阶段对应一个核心服务文件。缺少任何一个文件意味着
    Pipeline 无法完整运行。

    Stage 1: StoryOutlineGenerator  - 故事大纲
    Stage 2: CharacterDesigner      - 角色设计
    Stage 3: ScreenplayWriter       - 分场剧本
    Stage 4: StoryboardDirector     - 分镜脚本
    Stage 5: ImageGenerator         - 镜头图像生成
    """
    required_services = {
        "Stage 1 (StoryOutlineGenerator)": "app/services/story_outline_generator.py",
        "Stage 2 (CharacterDesigner)": "app/services/character_designer.py",
        "Stage 3 (ScreenplayWriter)": "app/services/screenplay_writer.py",
        "Stage 4 (StoryboardDirector)": "app/services/storyboard_director.py",
        "Stage 5 (ImageGenerator)": "app/services/image_generator.py",
    }

    missing = []
    for stage_name, filepath in required_services.items():
        full_path = _project_path(filepath)
        if not os.path.exists(full_path):
            missing.append(f"{stage_name}: {filepath}")

    assert not missing, (
        f"Pipeline 核心服务文件缺失（Pipeline 无法完整运行）:\n"
        + "\n".join(f"  - {m}" for m in missing)
    )


# =========================================================================
# 5. 参考图生成必须串行（portrait -> fullbody）
# =========================================================================

def test_reference_generation_is_serial():
    """参考图生成必须是串行的：先 portrait 再 fullbody，不能并行。

    保护的架构规则：串行生成参考图是角色一致性的关键。
    先生成 portrait（正面肖像），再用 portrait 作为参考生成 fullbody（全身图）。
    如果两者并行（asyncio.gather），fullbody 无法参考 portrait 的面部特征，
    导致"不像同一个人"的 bug（EP-002）。

    检查项：
    1. reference_image_manager.py 中 generate_character_multi_refs 函数存在
    2. portrait 生成在 fullbody 生成之前（代码顺序）
    3. 不存在将 portrait 和 fullbody 放入同一个 asyncio.gather 的模式
    """
    target_file = _project_path("app", "services", "reference_image_manager.py")
    if not os.path.exists(target_file):
        return  # 文件不存在时跳过

    with open(target_file, 'r', encoding='utf-8') as fh:
        content = fh.read()

    # 检查 1: generate_character_multi_refs 函数存在
    assert 'generate_character_multi_refs' in content, (
        "reference_image_manager.py 中未找到 generate_character_multi_refs 函数。"
        "这是参考图串行生成的核心函数。"
    )

    # 检查 2: portrait 在 fullbody 之前生成
    # 在 generate_character_multi_refs 函数范围内，检查 portrait 生成代码在 fullbody 之前
    portrait_gen_pattern = re.compile(
        r"ref_type\s*=\s*['\"]portrait['\"]", re.MULTILINE
    )
    fullbody_gen_pattern = re.compile(
        r"ref_type\s*=\s*['\"]fullbody['\"]", re.MULTILINE
    )

    portrait_matches = list(portrait_gen_pattern.finditer(content))
    fullbody_matches = list(fullbody_gen_pattern.finditer(content))

    assert portrait_matches, (
        "reference_image_manager.py 中未找到 portrait 类型参考图生成代码"
    )
    assert fullbody_matches, (
        "reference_image_manager.py 中未找到 fullbody 类型参考图生成代码"
    )

    # 找到 generate_character_multi_refs 函数内的 portrait 和 fullbody
    # 确认 portrait 的位置在 fullbody 之前
    func_start = content.find('generate_character_multi_refs')
    if func_start >= 0:
        func_content = content[func_start:]
        portrait_pos = func_content.find("ref_type='portrait'")
        if portrait_pos < 0:
            portrait_pos = func_content.find('ref_type="portrait"')
        fullbody_pos = func_content.find("ref_type='fullbody'")
        if fullbody_pos < 0:
            fullbody_pos = func_content.find('ref_type="fullbody"')

        if portrait_pos >= 0 and fullbody_pos >= 0:
            assert portrait_pos < fullbody_pos, (
                "参考图生成顺序错误：fullbody 出现在 portrait 之前。"
                "必须先生成 portrait，再用 portrait 作为参考生成 fullbody。"
            )

    # 检查 3: 不存在将 portrait 和 fullbody 同时放入 asyncio.gather 的模式
    # 在 reference_image_manager.py 中不应有 asyncio.gather
    assert 'asyncio.gather' not in content, (
        "reference_image_manager.py 中发现 asyncio.gather。"
        "参考图（portrait + fullbody）必须串行生成，不能并行。"
        "并行会导致 fullbody 无法使用 portrait 作为参考，破坏角色一致性。"
    )


# =========================================================================
# 6. .env.example 与 Settings 类字段双向对比（EP-016 工程化防护）
# =========================================================================

def test_env_example_matches_settings():
    """.env.example 与 app/config.py 的 Settings 类字段必须双向对齐。

    保护的架构规则（EP-016）：
    - .env.example 有但 Settings 没有 → 用户按模板填了值，但启动时 Pydantic
      extra_forbidden 会报错，导致 "我明明按文档配置了还是报错" 的用户体验灾难
    - Settings 有但 .env.example 没有 → 用户无法知道该字段存在，配置盲区

    实现方式（AST 解析）：
    - 不 import Settings 类，避免触发模块级 settings = get_settings() 导致 DB 连接
    - 手动 AST 解析 Settings 类的所有类属性名
    - 解析 .env.example 中所有 KEY=value 格式的行（跳过 # 注释行和空行）

    白名单规则：
    - Settings-only 白名单（内部配置，无需在 .env.example 暴露）：
      这些字段由代码默认值控制，普通用户不需要配置
    - .env.example-only 白名单：无豁免。.env.example 有但 Settings 没有的字段
      会触发 Pydantic extra_forbidden 启动报错，必须 100% 对齐，无例外

    FAIL 时信息：明确显示哪些字段在哪一侧缺失，以及修复建议。
    """
    env_example_path = _project_path(".env.example")
    config_py_path = _project_path("app", "config.py")

    # ── 前置检查：文件必须存在 ─────────────────────────────────────────────
    if not os.path.exists(env_example_path):
        raise AssertionError(
            ".env.example 文件不存在。\n"
            "修复: 在项目根目录创建 .env.example（参考 Settings 类字段）"
        )
    if not os.path.exists(config_py_path):
        raise AssertionError(
            "app/config.py 文件不存在。\n"
            "修复: 确认 Settings 类配置文件路径正确"
        )

    # ── Step 1: 解析 .env.example 的所有 KEY ──────────────────────────────
    env_example_keys: set[str] = set()
    with open(env_example_path, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue
            # 解析 KEY=value 格式（value 可以为空）
            if '=' in line:
                key = line.split('=', 1)[0].strip()
                if key:  # 确保 key 非空
                    env_example_keys.add(key)

    # ── Step 2: AST 解析 app/config.py 的 Settings 类所有字段 ─────────────
    # 使用 AST 避免 import 触发模块级 settings = get_settings() → DB 连接
    settings_fields: set[str] = set()
    with open(config_py_path, 'r', encoding='utf-8') as fh:
        source = fh.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise AssertionError(f"app/config.py 语法错误，无法解析：{e}")

    # 找到 Settings 类定义，提取所有类属性名
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Settings':
            for item in node.body:
                # 类属性注解（FIELD_NAME: Type = default_value）
                if isinstance(item, ast.AnnAssign):
                    target = item.target
                    if isinstance(target, ast.Name):
                        # 只取全大写字段（环境变量命名约定）
                        if target.id.isupper():
                            settings_fields.add(target.id)

    if not settings_fields:
        raise AssertionError(
            "无法从 app/config.py 中解析到 Settings 类字段。\n"
            "请确认 Settings 类定义存在且字段使用 FIELD: Type = default 格式"
        )

    # ── Step 3: 白名单定义 ────────────────────────────────────────────────
    #
    # Settings-only 白名单：这些字段在 Settings 类中有默认值，属于内部配置，
    # 普通用户不需要在 .env.example 中看到也不需要配置。
    # 它们可以不在 .env.example 中，但必须在 Settings 中（白名单本身保证这点）。
    settings_only_whitelist: set[str] = {
        # 代码行为控制（内部 flag，默认值适合所有场景）
        "PROMPT_FORMAT",            # b_prime|legacy，代码已有合理默认值
        "PIPELINE_COST_LIMIT",      # 单次 Pipeline 成本上限，有默认值 $10

        # 分镜拆分配置——已在 .env.example 中暴露，此处保留为文档兼容
        # （实际上这些字段在 .env.example 里有，不需要白名单，但保留无害）

        # 图像生成开发用跳过 flag（开发调试用，生产不需要配置）
        "SKIP_IMAGE_GENERATION",    # 开发用：用 R8 测试图替代真实生图，默认 False

        # Wave 4 集成说明：MUREKA_API_KEY 已移除白名单，
        # .env.example 已补充该字段，Settings 类已声明，三方完全对齐
    }

    # .env.example-only 白名单：无豁免
    # .env.example 中存在但 Settings 没有的字段会直接导致 Pydantic extra_forbidden
    # 启动报错，属于生产事故级别，必须 100% 对齐，无任何白名单豁免

    # ── Step 4: 双向对比 ──────────────────────────────────────────────────
    # 4a: .env.example 有但 Settings 没有（危险！启动即报错，无白名单豁免）
    in_example_not_in_settings = env_example_keys - settings_fields

    # 4b: Settings 有但 .env.example 没有（用户配置盲区）
    # 白名单字段豁免（内部配置，用户不需要知道）
    in_settings_not_in_example = (settings_fields - env_example_keys) - settings_only_whitelist

    # ── Step 5: 断言并输出清晰的修复建议 ─────────────────────────────────
    errors = []

    if in_example_not_in_settings:
        sorted_missing = sorted(in_example_not_in_settings)
        errors.append(
            f"❌ 以下字段在 .env.example 中存在，但 Settings 类未声明（会导致启动 Pydantic 报错）:\n"
            + "\n".join(f"    - {k}" for k in sorted_missing)
            + "\n  修复: 在 app/config.py 的 Settings 类中添加这些字段的类型注解和默认值\n"
            + "  例如: FIELD_NAME: str = \"\"  # 字段说明"
        )

    if in_settings_not_in_example:
        sorted_missing = sorted(in_settings_not_in_example)
        errors.append(
            f"❌ 以下字段在 Settings 类中存在，但 .env.example 未暴露（用户配置盲区）:\n"
            + "\n".join(f"    - {k}" for k in sorted_missing)
            + "\n  修复选项 A（推荐）: 在 .env.example 中添加这些字段（带说明注释）\n"
            + "  修复选项 B: 若确为内部配置，将字段加入 settings_only_whitelist"
        )

    assert not errors, (
        "【EP-016】.env.example 与 Settings 类字段不一致！\n\n"
        + "\n\n".join(errors)
        + "\n\n"
        + f"  调试信息:\n"
        + f"    .env.example 字段数: {len(env_example_keys)}\n"
        + f"    Settings 字段数: {len(settings_fields)}\n"
        + f"    Settings-only 白名单: {sorted(settings_only_whitelist)}"
    )
