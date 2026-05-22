"""
RISK-T15-10 / Wave 9 Phase 3 — 画外音/off-screen audio 处理规则单测

背景：test15 Shot 21 narration "走廊里短暂出现压低的声音与移动的脚步" 是画外音 cue
（主角独自在走廊，声音来自房间内不可见的人）。Stage 4 LLM 错误地把声音翻译成
画面元素 "Two blurred nurse silhouettes move inside the room"，导致 image_prompt
自相矛盾（EXACTLY 1 character + Two silhouettes），Seedream 真渲染 3-4 个角色，
T17 ShotValidator 两次 retry 全失败。

修复：
1. 新建 OFF_SCREEN_SOUND_HANDLING_RULES 常量（storyboard_prompts.py）
2. 注入到 Stage 4 prompt 两个 build 路径（storyboard_director.py L915 + L1233）
3. 强化 IMAGE PROMPT QUALITY REQUIREMENTS Rule 6 (STRICT CHARACTER COUNT)

本测试不依赖 google.genai / anthropic / settings — 纯静态文本/AST 验证，确保：
- 规则常量定义存在且包含必要关键词
- Rule 6 已加 "OFF-SCREEN AUDIO DOES NOT COUNT" 强化
- Stage 4 prompt 模板（storyboard_director.py 源码）真的注入了新规则
- 不破坏已有规则常量
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROMPTS_FILE = ROOT / "app" / "prompts" / "storyboard_prompts.py"
DIRECTOR_FILE = ROOT / "app" / "services" / "storyboard_director.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ===================== 1. 规则常量存在性 =====================

def test_off_screen_rule_constant_defined():
    """storyboard_prompts.py 必须定义 OFF_SCREEN_SOUND_HANDLING_RULES 常量"""
    src = _read(PROMPTS_FILE)
    tree = ast.parse(src)
    assigned_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned_names.add(t.id)
    assert "OFF_SCREEN_SOUND_HANDLING_RULES" in assigned_names, (
        "Expected OFF_SCREEN_SOUND_HANDLING_RULES module-level constant in "
        "app/prompts/storyboard_prompts.py"
    )


def test_off_screen_rule_constant_nonempty():
    """常量必须非空（避免占位符或空串误提交）"""
    src = _read(PROMPTS_FILE)
    # 抽取常量字符串内容
    pattern = re.compile(
        r'OFF_SCREEN_SOUND_HANDLING_RULES\s*=\s*"""(.+?)"""',
        re.DOTALL,
    )
    m = pattern.search(src)
    assert m is not None, "OFF_SCREEN_SOUND_HANDLING_RULES 必须使用三引号字符串"
    body = m.group(1)
    assert len(body) >= 1000, (
        f"OFF_SCREEN_SOUND_HANDLING_RULES 长度 {len(body)} 太短，应至少 1000 字符 "
        "（覆盖 cue 类型表 / 翻译对比 / forbidden 列表 / decision checklist）"
    )


# ===================== 2. 规则关键内容 =====================

# 规则必须显式提到的关键短语
REQUIRED_PHRASES = [
    # 核心概念
    "OFF-SCREEN",
    "characters_in_scene",
    # 中文 narration cue
    "脚步",
    "走廊里传来脚步声",
    # forbidden 短语示例
    "silhouettes",
    "blurred",
    # 决策机制
    "ground truth",
    # 修复方向
    "EXACTLY",
]


def test_off_screen_rule_contains_required_phrases():
    """规则必须显式提到核心关键短语，确保 LLM 能识别 cue 并应用"""
    src = _read(PROMPTS_FILE)
    pattern = re.compile(
        r'OFF_SCREEN_SOUND_HANDLING_RULES\s*=\s*"""(.+?)"""',
        re.DOTALL,
    )
    body = pattern.search(src).group(1)
    missing = [p for p in REQUIRED_PHRASES if p not in body]
    assert not missing, (
        f"OFF_SCREEN_SOUND_HANDLING_RULES 缺少关键短语: {missing}\n"
        "这些短语对 LLM 识别 cue/避免错误翻译至关重要"
    )


def test_off_screen_rule_has_chinese_cue_table():
    """规则必须包含中文 narration cue 翻译表（LLM 需要看到具体中文样例）"""
    src = _read(PROMPTS_FILE)
    pattern = re.compile(
        r'OFF_SCREEN_SOUND_HANDLING_RULES\s*=\s*"""(.+?)"""',
        re.DOTALL,
    )
    body = pattern.search(src).group(1)
    # 至少 6 个中文 cue 样例（脚步声/远处的声音/警报声 等）
    chinese_cues = [
        "脚步",
        "警报",
        "声音",
        "喊",
        "门",
    ]
    found = [c for c in chinese_cues if c in body]
    assert len(found) >= 5, (
        f"中文 cue 样例不足（找到 {len(found)}/{len(chinese_cues)}）；"
        f"missing: {set(chinese_cues) - set(found)}"
    )


def test_off_screen_rule_has_t15_canonical_example():
    """必须包含 RISK-T15-10 具体 case 的范例（Shot 21 林晓月走廊）"""
    src = _read(PROMPTS_FILE)
    pattern = re.compile(
        r'OFF_SCREEN_SOUND_HANDLING_RULES\s*=\s*"""(.+?)"""',
        re.DOTALL,
    )
    body = pattern.search(src).group(1)
    # 走廊 + 林晓月 + 压低的声音 这套组合至少要有一处
    assert (
        "走廊里短暂出现压低的声音与移动的脚步" in body
        or ("走廊" in body and "脚步" in body and "Lin Xiaoyue" in body)
    ), "应该包含 RISK-T15-10 canonical 范例（走廊脚步声 + 主角独立画面）"


# ===================== 3. Rule 6 强化 =====================

def test_rule6_character_count_strengthened():
    """Rule 6 STRICT CHARACTER COUNT 必须加上 'OFF-SCREEN AUDIO DOES NOT COUNT' 强化"""
    src = _read(DIRECTOR_FILE)
    # Rule 6 段落
    rule6_match = re.search(
        r"###\s*6\.\s*STRICT CHARACTER COUNT.+?###\s*7\.",
        src,
        re.DOTALL,
    )
    assert rule6_match is not None, "Rule 6 块未找到"
    rule6 = rule6_match.group(0)
    assert "OFF-SCREEN AUDIO DOES NOT COUNT" in rule6, (
        "Rule 6 必须显式加 'OFF-SCREEN AUDIO DOES NOT COUNT' 强化句\n"
        "（指向 OFF-SCREEN AUDIO HANDLING block）"
    )
    assert "OFF-SCREEN AUDIO HANDLING block" in rule6 or "OFF-SCREEN" in rule6, (
        "Rule 6 必须引用 OFF-SCREEN AUDIO HANDLING block，让 LLM 知道去哪查规则"
    )


# ===================== 4. Stage 4 prompt 模板注入 =====================

def test_storyboard_director_imports_off_screen_rule():
    """storyboard_director.py 必须 import OFF_SCREEN_SOUND_HANDLING_RULES"""
    src = _read(DIRECTOR_FILE)
    assert "OFF_SCREEN_SOUND_HANDLING_RULES" in src, (
        "storyboard_director.py 必须 import 新规则常量"
    )
    # 验证在 import 块中
    import_match = re.search(
        r"from\s+app\.prompts\.storyboard_prompts\s+import\s*\((.+?)\)",
        src,
        re.DOTALL,
    )
    assert import_match is not None, "未找到 from app.prompts.storyboard_prompts import 块"
    imported = import_match.group(1)
    assert "OFF_SCREEN_SOUND_HANDLING_RULES" in imported, (
        "OFF_SCREEN_SOUND_HANDLING_RULES 必须在 from app.prompts.storyboard_prompts "
        "import (...) 块内"
    )


def test_off_screen_rule_injected_into_prompt_templates():
    """两个 Stage 4 prompt build 路径必须都注入 OFF_SCREEN_SOUND_HANDLING_RULES"""
    src = _read(DIRECTOR_FILE)
    # 用 f-string 占位符 {OFF_SCREEN_SOUND_HANDLING_RULES} 出现次数
    occurrences = src.count("{OFF_SCREEN_SOUND_HANDLING_RULES}")
    assert occurrences >= 2, (
        f"OFF_SCREEN_SOUND_HANDLING_RULES 在 prompt 模板中只出现 {occurrences} 次，"
        "应至少 2 次（_build_scene_prompt + _build_prompt 两个路径都必须注入）"
    )


def test_off_screen_rule_near_narration_extraction():
    """新规则必须紧贴 NARRATION_TO_VISUAL_EXTRACTION_RULES 后面注入
    （它们属于同一类：narration → visual 翻译规则）"""
    src = _read(DIRECTOR_FILE)
    # 找所有 NARRATION_TO_VISUAL_EXTRACTION_RULES 占位符的位置
    narration_positions = [
        m.start() for m in re.finditer(r"\{NARRATION_TO_VISUAL_EXTRACTION_RULES\}", src)
    ]
    off_screen_positions = [
        m.start() for m in re.finditer(r"\{OFF_SCREEN_SOUND_HANDLING_RULES\}", src)
    ]
    assert len(narration_positions) >= 2 and len(off_screen_positions) >= 2, (
        "两个 prompt build 路径都应有 narration + off_screen 占位符"
    )
    # 每个 OFF_SCREEN 占位符前面 ~500 字节内必须有一个 NARRATION 占位符
    for off_pos in off_screen_positions:
        nearest_narration = max(
            (n for n in narration_positions if n < off_pos), default=-1
        )
        assert nearest_narration != -1, f"OFF_SCREEN @{off_pos} 前面没有 NARRATION 占位符"
        distance = off_pos - nearest_narration
        assert distance < 500, (
            f"OFF_SCREEN @{off_pos} 距上一个 NARRATION @{nearest_narration} "
            f"={distance} bytes（应 <500，紧邻注入）"
        )


# ===================== 5. 不破坏已有规则 =====================

EXISTING_RULES = [
    "NARRATION_TO_VISUAL_EXTRACTION_RULES",
    "COMIC_MODE_NARRATIVE_RULES",
    "HAND_PROP_ANATOMY_RULES",
    "HAIR_COLOR_REQUIREMENT_RULE",
    "SCENE_PROP_CONTINUITY_RULES",
]


def test_existing_rules_still_present():
    """既有规则常量必须仍然存在（regression guard）"""
    prompts_src = _read(PROMPTS_FILE)
    director_src = _read(DIRECTOR_FILE)
    # 在 prompts 文件定义
    prompts_tree = ast.parse(prompts_src)
    assigned = set()
    for node in ast.walk(prompts_tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned.add(t.id)
    for rule in ["NARRATION_TO_VISUAL_EXTRACTION_RULES", "COMIC_MODE_NARRATIVE_RULES",
                 "HAND_PROP_ANATOMY_RULES", "HAIR_COLOR_REQUIREMENT_RULE"]:
        assert rule in assigned, f"已有规则 {rule} 在 storyboard_prompts.py 中消失"
    # 在 director 文件被 import 或定义
    for rule in EXISTING_RULES:
        assert rule in director_src, f"已有规则 {rule} 在 storyboard_director.py 中消失"


# ===================== 6. py_compile 健康度 =====================

def test_both_files_py_compile_clean():
    """两个修改的文件必须能 py_compile 干净通过"""
    import py_compile
    py_compile.compile(str(PROMPTS_FILE), doraise=True)
    py_compile.compile(str(DIRECTOR_FILE), doraise=True)


# ===================== 7. 主入口（可直接跑）=====================

if __name__ == "__main__":
    import sys
    funcs = [v for k, v in list(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {fn.__name__}: {e}")
            failed += 1
    total = len(funcs)
    print(f"\n=== {total - failed}/{total} PASS ===")
    sys.exit(0 if failed == 0 else 1)
