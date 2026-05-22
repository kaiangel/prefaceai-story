"""
RISK-T19-4 Wave 13 — scene_heading 中文防御单测

验证点:
1. _contains_chinese() 对 scene_heading 各种情况的检测
2. fallback_image_prompt 构建：scene_heading 含中文时替换为 "Scene {scene_id}"
3. fallback_image_prompt 构建：scene_heading 英文时正常使用
4. 最终 image_prompt 不含超过 5% 中文字符（pipeline_schemas 阈值）
5. 与 Wave 12 atmosphere 防御回归兼容
"""

import pytest
import re

# ─── 从 storyboard_director 模块导入 ─────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.storyboard_director import _contains_chinese, _atmosphere_to_str


# ═══════════════════════════════════════════════════════════════════════
# Helper: 模拟 fallback_image_prompt 构建逻辑（与 storyboard_director.py L682-699 同源）
# ═══════════════════════════════════════════════════════════════════════

def _build_fallback_prompt(scene_heading: str, atmosphere, scene_id: int) -> str:
    """
    复现 storyboard_director.py B51 fallback 路径中的 image_prompt 构建，
    包含 RISK-T19-4 Wave 13 scene_heading 中文防御逻辑。
    """
    atmosphere_str = _atmosphere_to_str(atmosphere)

    # RISK-T19-4: scene_heading 中文检测 → 安全占位
    if _contains_chinese(scene_heading):
        scene_heading_safe = f"Scene {scene_id}"
    else:
        scene_heading_safe = scene_heading

    return (
        f"Establishing shot of {scene_heading_safe}. "
        f"{'Atmosphere: ' + atmosphere_str + '. ' if atmosphere_str else ''}"
        f"Wide angle, showing the environment and setting clearly. "
        f"No specific character interaction required."
    )


def _chinese_ratio(text: str) -> float:
    """计算字符串中 CJK 字符比例（与 pipeline_schemas.py 同逻辑）。"""
    if not text:
        return 0.0
    chinese_chars = re.findall(r"[一-鿿]", text)
    return len(chinese_chars) / len(text)


# ═══════════════════════════════════════════════════════════════════════
# Case 1: scene_heading 含中文 → 替换为 "Scene {id}"，prompt 无中文
# ═══════════════════════════════════════════════════════════════════════

def test_scene_heading_chinese_birch_grove():
    """测试用例：'白桦树下' 含中文 → 替换为 Scene 13，image_prompt 无中文。"""
    heading = "EXT. 白桦树下 - 立春清晨 - 晴"
    atmosphere = {"mood": "warmth", "sound_design_hint": "bird calls in birch forest"}
    scene_id = 13

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    # 核心验证：prompt 中不含中文
    assert _chinese_ratio(prompt) <= 0.05, (
        f"image_prompt 中文比例 {_chinese_ratio(prompt):.0%} 超过阈值 5%: {prompt}"
    )
    # 安全占位存在
    assert "Scene 13" in prompt
    # 原中文不泄露
    assert "白桦" not in prompt
    assert "立春" not in prompt


def test_scene_heading_chinese_ancestral_hall():
    """测试用例：'祠堂' 含中文 → 替换为 Scene 5，image_prompt 无中文。"""
    heading = "INT. 祠堂 - 傍晚 - 阴"
    atmosphere = {"mood": "solemn", "sound_design_hint": "distant incense smoke crackle"}
    scene_id = 5

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert _chinese_ratio(prompt) <= 0.05
    assert "Scene 5" in prompt
    assert "祠堂" not in prompt


def test_scene_heading_chinese_and_atmosphere_chinese():
    """测试用例：scene_heading 含中文 + atmosphere str 也含中文 → 两者都防御，prompt 无中文。"""
    heading = "EXT. 胡同小巷 - 深夜 - 雨"
    # atmosphere 是旧 str 格式含中文（Wave 12 _atmosphere_to_str 防御）
    atmosphere = "tranquil, 远处犬吠，石板路雨声，夜色凉彻骨"
    scene_id = 7

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert _chinese_ratio(prompt) <= 0.05, (
        f"image_prompt 中文比例 {_chinese_ratio(prompt):.0%} > 5%: {prompt}"
    )
    assert "Scene 7" in prompt
    assert "胡同" not in prompt
    assert "犬吠" not in prompt


def test_scene_heading_chinese_with_location_id_style():
    """测试用例：scene_heading 含中文数字季节词 → 防御生效。"""
    heading = "EXT. 白桦树林 - 初春晌午 - 晴朗"
    atmosphere = "peaceful"
    scene_id = 10

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert _chinese_ratio(prompt) <= 0.05
    assert "Scene 10" in prompt
    assert "白桦" not in prompt


def test_scene_heading_chinese_only_location():
    """测试用例：scene_heading 仅含纯中文地名（无 EXT/INT 前缀）。"""
    heading = "冬日山谷"
    atmosphere = ""
    scene_id = 3

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert _chinese_ratio(prompt) <= 0.05
    assert "Scene 3" in prompt
    assert "冬日" not in prompt


# ═══════════════════════════════════════════════════════════════════════
# Case 2: scene_heading 英文 → 正常使用，不替换
# ═══════════════════════════════════════════════════════════════════════

def test_scene_heading_english_birch_grove():
    """测试用例：英文 scene_heading → 原样保留，prompt 正常。"""
    heading = "EXT. Birch grove - Early spring morning - clear"
    atmosphere = {"mood": "warmth", "sound_design_hint": "bird calls in birch forest"}
    scene_id = 13

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert "Birch grove" in prompt
    assert "Scene 13" not in prompt
    assert _chinese_ratio(prompt) <= 0.05


def test_scene_heading_english_cafe():
    """测试用例：英文 scene_heading 带地名 → 原样保留。"""
    heading = "INT. Cozy cafe - Afternoon - sunny"
    atmosphere = {"mood": "peaceful", "sound_design_hint": "coffee machine hum, soft jazz"}
    scene_id = 2

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert "Cozy cafe" in prompt
    assert _chinese_ratio(prompt) <= 0.05


def test_scene_heading_english_simple():
    """测试用例：极简英文 heading → 正常使用。"""
    heading = "EXT. Forest path - Dawn"
    atmosphere = ""
    scene_id = 1

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    assert "Forest path" in prompt
    assert "Scene 1" not in prompt
    assert _chinese_ratio(prompt) == 0.0


# ═══════════════════════════════════════════════════════════════════════
# Case 3: _contains_chinese 边界测试（含 Wave 12 regression）
# ═══════════════════════════════════════════════════════════════════════

def test_contains_chinese_false_for_english():
    assert _contains_chinese("EXT. Birch grove - Early spring morning") is False


def test_contains_chinese_true_for_chinese():
    assert _contains_chinese("EXT. 白桦树下 - 立春清晨 - 晴") is True


def test_contains_chinese_false_for_empty():
    assert _contains_chinese("") is False


def test_contains_chinese_false_for_numbers_and_symbols():
    assert _contains_chinese("EXT. Scene-13 - 2024 - clear!") is False


def test_contains_chinese_true_for_mixed():
    assert _contains_chinese("tranquil, 远山鸟鸣稀疏") is True


# ═══════════════════════════════════════════════════════════════════════
# Case 4: Wave 12 atmosphere 防御 regression（确保 Wave 13 不 break Wave 12）
# ═══════════════════════════════════════════════════════════════════════

def test_wave12_atmosphere_dict_chinese_defense():
    """Wave 12 regression: dict 格式 atmosphere 含中文字段 → 跳过，只保留英文。"""
    atm = {"mood": "tranquil", "sound_design_hint": "远山鸟鸣稀疏", "temperature_feel": "凛冽中带一丝初春的微暖"}
    result = _atmosphere_to_str(atm)
    # 含中文字段 sound_design_hint / temperature_feel 被跳过，只保留 mood
    assert "tranquil" in result
    assert "远山" not in result
    assert "凛冽" not in result


def test_wave12_atmosphere_str_chinese_defense():
    """Wave 12 regression: str 格式 atmosphere 含中文 → 提取首段英文部分。"""
    atm = "tranquil, 远山鸟鸣稀疏，踩雪声轻脆"
    result = _atmosphere_to_str(atm)
    assert "tranquil" in result
    assert "远山" not in result


def test_wave12_atmosphere_all_english_passthrough():
    """Wave 12 regression: 全英文 atmosphere → 原样通过，不被截断。"""
    atm = {"mood": "warmth", "sound_design_hint": "distant bird calls, crisp footsteps in snow"}
    result = _atmosphere_to_str(atm)
    assert "warmth" in result
    assert "distant bird calls" in result


def test_wave12_atmosphere_str_all_chinese_returns_empty():
    """Wave 12 regression: str 格式 atmosphere 完全中文 → 返回空字符串。"""
    atm = "远山鸟鸣稀疏，踩雪声轻脆，凛冽中带一丝初春的微暖"
    result = _atmosphere_to_str(atm)
    assert result == "" or not any('一' <= c <= '鿿' for c in result)


# ═══════════════════════════════════════════════════════════════════════
# Case 5: 综合 — 真实 Scene 13 数据复现（test19 失败场景）
# ═══════════════════════════════════════════════════════════════════════

def test_real_scene13_data_no_chinese_in_prompt():
    """
    用 test19 实际 Scene 13 数据验证：
    Wave 12 + Wave 13 双修后 fallback_image_prompt 中文比例 <= 5%。
    """
    # 真实 Scene 13 数据（来自 output/97974a03.../3_screenplay.json）
    heading = "EXT. 白桦树下 - 立春清晨 - 晴"
    atmosphere = "warmth, 轻快的笑声，雪地踩踏声，远处林鸟鸣叫，生机渐起, 真正感受到了春天，从心里暖起来"
    scene_id = 13

    prompt = _build_fallback_prompt(heading, atmosphere, scene_id)

    ratio = _chinese_ratio(prompt)
    assert ratio <= 0.05, (
        f"test19 Scene 13 fallback_image_prompt 中文比例 {ratio:.0%} 仍 >5%!\n"
        f"prompt: {prompt}"
    )
    # 确认安全占位被使用
    assert "Scene 13" in prompt
    # 确认原始中文不泄露
    assert "白桦" not in prompt
    assert "轻快" not in prompt
