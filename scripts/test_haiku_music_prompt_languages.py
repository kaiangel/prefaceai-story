#!/usr/bin/env python3
"""
TASK-MUSIC-LANG-AB Step 2 — 语言策略 A/B/C 验证脚本

用年夜饭故事 JSON 提取 14 个占位符数据，填入 3 个语言变体 meta-prompt，
分别调 Anthropic API (claude-haiku-4-5) 生成 music prompt，
再调 Mureka API (auto, n=1) 生成 BGM。

产出（在 test_output/manualtest/sq_upgrade_ab_test/20260304_113630/ 下）：
  bgm_haiku_en.mp3    bgm_haiku_en_prompt.txt
  bgm_haiku_cn.mp3    bgm_haiku_cn_prompt.txt
  bgm_haiku_mixed.mp3 bgm_haiku_mixed_prompt.txt

设计原则：
  - 不 import app.main / pipeline 栈，避免 DB 连接副作用
  - 只 import app.config.settings（仅读取 ANTHROPIC_API_KEY / MUREKA_API_KEY）
  - 占位符替换用手动 str.replace 链式调用，避免 .format() 误吞 prompt 内的花括号
  - Mureka 调用用 urllib + ensure_ascii=False（EP-015 规范）
  - 函数独立，可被 Pipeline 复用
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

import ssl
import certifi

# 强制 urllib 全局使用 certifi 的 CA bundle（修复 Python 3.11 framework SSL 证书链问题）
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import anthropic

# 只 import settings，不触发 app.main 的 DB 连接
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import settings

# ──────────────────────────────────────────────
# 路径常量
# ──────────────────────────────────────────────

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STORY_DIR = os.path.join(
    _BASE_DIR, "..",
    "test_output", "manualtest", "sq_upgrade_ab_test", "20260304_113630"
)
OUTLINE_PATH = os.path.join(_STORY_DIR, "1_outline.json")
SCREENPLAY_PATH = os.path.join(_STORY_DIR, "3_screenplay.json")
META_PROMPT_DIR = os.path.join(_STORY_DIR, "meta_prompts")
OUTPUT_DIR = _STORY_DIR  # 产出文件放同目录

# 年夜饭故事的旁白金句（硬编码，来自 story_input_format.md 的已知数据）
# AI-ML 在 story_input_format.md 中选出的 4 句金句，使用前 2 句（最高画面感）
NARRATION_QUOTES_HARDCODED = (
    "父亲的筷子落在桌面那一声，比窗外任何一声爆竹都响。"
    "\n"
    "窗玻璃是黑的，只有他自己的脸悬在那片黑暗里——冷青色的，和身后红灯笼的暖光不属于同一个世界。"
)

# Mureka API 配置
MUREKA_BASE_URL = "https://api.mureka.cn"
MUREKA_GENERATE_URL = f"{MUREKA_BASE_URL}/v1/instrumental/generate"
MUREKA_QUERY_URL_TPL = f"{MUREKA_BASE_URL}/v1/instrumental/query/{{task_id}}"
MUREKA_POLL_INTERVAL = 8   # 轮询间隔（秒）
MUREKA_MAX_WAIT = 300       # 最大等待时间（秒）
MUREKA_MAX_RETRIES = 3      # Mureka 生成失败最大重试次数

# ──────────────────────────────────────────────
# 6 个故事路径配置
# ──────────────────────────────────────────────

STORIES = [
    {
        "id": 1, "name": "最后一投",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/prompt_bubble/slamdunk_dialogue/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/prompt_bubble/slamdunk_dialogue/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/prompt_bubble/slamdunk_dialogue"),
    },
    {
        "id": 2, "name": "外公的秋梨膏",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614"),
    },
    {
        "id": 3, "name": "年夜饭上的战争",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/sq_upgrade_ab_test/20260304_113630/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/sq_upgrade_ab_test/20260304_113630/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/sq_upgrade_ab_test/20260304_113630"),
    },
    {
        "id": 4, "name": "拿铁上的告白",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/cross_style_test/20260228_152134/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/cross_style_test/20260228_152134/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/cross_style_test/20260228_152134"),
    },
    {
        "id": 5, "name": "墨痕",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r4/20260310_155024/story_B/20260310_161426/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r4/20260310_155024/story_B/20260310_161426/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/e2e_regression_r4/20260310_155024/story_B/20260310_161426"),
    },
    {
        "id": 6, "name": "终点站前的余温",
        "outline": os.path.join(_BASE_DIR, "..", "test_output/manualtest/phase2/20251231_181728/1_outline.json"),
        "screenplay": os.path.join(_BASE_DIR, "..", "test_output/manualtest/phase2/20251231_181728/3_screenplay.json"),
        "output_dir": os.path.join(_BASE_DIR, "..", "test_output/manualtest/phase2/20251231_181728"),
    },
]


# ──────────────────────────────────────────────
# 数据提取
# ──────────────────────────────────────────────

def extract_story_data(outline_path: str, screenplay_path: str, quote_mode: str = "hardcoded") -> dict:
    """
    从 1_outline.json + 3_screenplay.json 提取占位符对应的字典。

    Args:
        outline_path: 1_outline.json 路径
        screenplay_path: 3_screenplay.json 路径
        quote_mode: "hardcoded" 或 "haiku-pick"
            - hardcoded: 使用年夜饭硬编码金句，返回 narration_quotes 字段
            - haiku-pick: 拼接所有 scene 的 narration，返回 full_narration 字段

    Returns:
        dict: 键为占位符名（不含双大括号），值为对应的字符串
    """
    with open(outline_path, encoding="utf-8") as f:
        outline = json.load(f)
    with open(screenplay_path, encoding="utf-8") as f:
        screenplay = json.load(f)

    # ── 来自 outline ──
    story_title = outline.get("title", "")
    narrative_pace = outline.get("narrative_pace", "")
    overall_mood = outline.get("visual_tone", {}).get("overall_mood", "")

    arc = outline.get("emotional_arc", {})
    emotional_arc_opening = arc.get("opening", "")
    emotional_arc_midpoint = arc.get("midpoint", "")
    emotional_arc_climax = arc.get("climax", "")
    emotional_arc_resolution = arc.get("resolution", "")

    color_palette_list = outline.get("visual_tone", {}).get("color_palette", [])
    color_palette = ", ".join(color_palette_list)

    # ── 来自 screenplay（按 scene_id 顺序）──
    scenes = screenplay.get("scenes", [])
    scenes_sorted = sorted(scenes, key=lambda s: s.get("scene_id", 0))

    sound_design_hints_parts = []
    narration_tones_parts = []
    narration_paces_parts = []
    scene_moods_parts = []
    temperature_feels_parts = []
    narration_parts = []

    for scene in scenes_sorted:
        scene_id = scene.get("scene_id", "?")
        atm = scene.get("atmosphere", {})

        hint = atm.get("sound_design_hint", "").strip()
        if hint:
            sound_design_hints_parts.append(f"Scene {scene_id}: {hint}")

        tone = scene.get("narration_tone", "").strip()
        if tone:
            narration_tones_parts.append(f"Scene {scene_id}: {tone}")

        pace = scene.get("narration_pace", "").strip()
        if pace:
            narration_paces_parts.append(f"Scene {scene_id}: {pace}")

        mood = atm.get("mood", "").strip()
        if mood:
            scene_moods_parts.append(f"Scene {scene_id}: {mood}")

        temp = atm.get("temperature_feel", "").strip()
        if temp:
            temperature_feels_parts.append(f"Scene {scene_id}: {temp}")

        # 收集旁白（haiku-pick 模式用）
        narration = scene.get("narration", "").strip()
        if narration:
            narration_parts.append(f"[Scene {scene_id}] {narration}")

    sound_design_hints = "\n".join(sound_design_hints_parts)
    narration_tones = "\n".join(narration_tones_parts)
    narration_paces = "\n".join(narration_paces_parts)
    scene_moods = "\n".join(scene_moods_parts)
    temperature_feels = "\n".join(temperature_feels_parts)

    result = {
        "story_title": story_title,
        "narrative_pace": narrative_pace,
        "overall_mood": overall_mood,
        "emotional_arc_opening": emotional_arc_opening,
        "emotional_arc_midpoint": emotional_arc_midpoint,
        "emotional_arc_climax": emotional_arc_climax,
        "emotional_arc_resolution": emotional_arc_resolution,
        "color_palette": color_palette,
        "sound_design_hints": sound_design_hints,
        "narration_tones": narration_tones,
        "narration_paces": narration_paces,
        "scene_moods": scene_moods,
        "temperature_feels": temperature_feels,
    }

    if quote_mode == "hardcoded":
        # 硬编码模式：使用年夜饭固定金句（仅支持年夜饭故事）
        result["narration_quotes"] = NARRATION_QUOTES_HARDCODED
    else:
        # haiku-pick 模式：拼接所有 scene 的 narration，按 scene_id 顺序
        result["full_narration"] = "\n\n".join(narration_parts)

    return result


# ──────────────────────────────────────────────
# Meta-prompt 解析
# ──────────────────────────────────────────────

def load_meta_prompt(lang: str, version: str = "v2", quote_mode: str = "hardcoded") -> tuple[str, str]:
    """
    从 meta-prompt 文件解析 system prompt 和 user prompt 模板。

    文件选择逻辑：
      - haiku-pick 模式: meta_{lang}_v3_quote_picking.md
      - hardcoded 模式, version=v2: meta_{lang}_v2.md
      - hardcoded 模式, version=v1: meta_{lang}.md

    文件格式约定（ai-ml 产出格式）：
      ## SYSTEM PROMPT  或  ## 系统提示词（SYSTEM PROMPT）
        ... 内容 ...
      ## USER PROMPT TEMPLATE  或  ## 用户提示词模板（USER PROMPT TEMPLATE）
        ... 内容 ...

    Args:
        lang: 语言变体（"en" / "cn" / "mixed"）
        version: meta-prompt 版本（"v1" / "v2"），hardcoded 模式下有效
        quote_mode: "hardcoded" 或 "haiku-pick"

    Returns:
        (system_prompt, user_prompt_template) 两个字符串
    """
    if quote_mode == "haiku-pick":
        filename = f"meta_{lang}_v3_quote_picking.md"
    elif version == "v2":
        filename = f"meta_{lang}_v2.md"
    else:
        filename = f"meta_{lang}.md"

    path = os.path.join(META_PROMPT_DIR, filename)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 用正则将文件按 ## 二级标题分段
    # 匹配形如 "## XXX PROMPT" 或 "## 系统/用户提示词" 的标题
    sections: dict[str, str] = {}
    # 将文件按 "^## " 分割
    parts = re.split(r"(?m)^## ", content)
    for part in parts[1:]:  # parts[0] 是文件头，跳过
        first_newline = part.find("\n")
        if first_newline == -1:
            continue
        header_line = part[:first_newline].strip()
        body = part[first_newline + 1:].strip()
        sections[header_line] = body

    # 找 system/user 两部分
    system_prompt = ""
    user_prompt_template = ""

    for header, body in sections.items():
        header_upper = header.upper()
        # 匹配 SYSTEM PROMPT 相关标题
        if "SYSTEM PROMPT" in header_upper or "系统提示词" in header:
            system_prompt = body
        # 匹配 USER PROMPT TEMPLATE 相关标题
        elif ("USER PROMPT" in header_upper or "用户提示词" in header):
            user_prompt_template = body

    if not system_prompt:
        raise ValueError(f"[load_meta_prompt] 未能解析 system prompt，lang={lang}，文件: {path}")
    if not user_prompt_template:
        raise ValueError(f"[load_meta_prompt] 未能解析 user prompt template，lang={lang}，文件: {path}")

    return system_prompt, user_prompt_template


def fill_placeholders(template: str, story_data: dict) -> str:
    """
    用手动 replace 链式替换 {{placeholder}} 占位符，
    避免 str.format() 误吞 prompt 内的 {"type": "text"} 等花括号。

    Args:
        template: 含 {{key}} 占位符的模板字符串
        story_data: 占位符 key → 值 的字典

    Returns:
        替换后的完整 user prompt 字符串
    """
    result = template
    for key, value in story_data.items():
        result = result.replace("{{" + key + "}}", value)
    return result


# ──────────────────────────────────────────────
# Anthropic API 调用
# ──────────────────────────────────────────────

def call_haiku(system: str, user: str) -> str:
    """
    调 Anthropic API (claude-haiku-4-5) 生成 music prompt 文本。

    Args:
        system: system prompt 字符串
        user: 已填充占位符的 user prompt 字符串

    Returns:
        Haiku 生成的 music prompt 文本

    Raises:
        anthropic.APIError: API 调用失败时向上抛出
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw_text = msg.content[0].text.strip()
    cleaned = clean_haiku_output(raw_text)
    return cleaned


def clean_haiku_output(text: str) -> str:
    """清理 Haiku 输出里的污染: markdown fence + 非 quotes 的 XML 标签。

    清理规则：
    1. 去除开头的 markdown fence（``` 或 ```lang）
    2. 去除结尾的 markdown fence
    3. 去除行内 markdown fence（罕见但有可能）
    4. 去除非 <quotes> / </quotes> 的 XML/HTML 残留标签
       （<quotes> 和 </quotes> 是合法格式，必须保留）
    """
    # 去除开头的 markdown fence（``` 或 ```lang）
    text = re.sub(r'^\s*```[a-zA-Z]*\s*\n', '', text)
    # 去除结尾的 markdown fence
    text = re.sub(r'\n?\s*```\s*$', '', text)
    # 去除行内 markdown fence（罕见但有可能）
    text = re.sub(r'```[a-zA-Z]*\n?', '', text)
    # 去除非 <quotes> 的 XML/HTML 标签（保留 <quotes> 和 </quotes>）
    text = re.sub(r'</?(?!quotes\b)[a-zA-Z_][^>]*>', '', text)
    return text.strip()


# ──────────────────────────────────────────────
# Mureka API 调用
# ──────────────────────────────────────────────

def _mureka_headers() -> dict:
    """返回 Mureka API 所需的 HTTP header"""
    return {
        "Authorization": f"Bearer {settings.MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }


def _mureka_post(url: str, payload: dict) -> dict:
    """
    用 urllib 发起 POST 请求到 Mureka API（EP-015 规范）。
    使用 ensure_ascii=False 保留中文字符。

    Returns:
        JSON 响应字典
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=_mureka_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _mureka_get(url: str) -> dict:
    """
    用 urllib 发起 GET 请求到 Mureka API。

    Returns:
        JSON 响应字典
    """
    req = urllib.request.Request(url, headers=_mureka_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_file(url: str, output_path: str) -> None:
    """下载 URL 内容保存到 output_path"""
    urllib.request.urlretrieve(url, output_path)


def call_mureka(prompt: str, output_path: str) -> dict:
    """
    调 Mureka API 生成纯音乐 BGM，轮询直到 succeeded，下载 mp3 到 output_path。

    失败时重试最多 MUREKA_MAX_RETRIES 次（含 generate 请求失败 + 轮询失败）。

    Args:
        prompt: 由 Haiku 生成的 music prompt 文本（≤1024 字符）
        output_path: 保存 mp3 的完整路径

    Returns:
        dict: {"task_id": str, "duration_ms": int}

    Raises:
        RuntimeError: 多次重试后仍失败
    """
    last_error: Exception | None = None

    for attempt in range(1, MUREKA_MAX_RETRIES + 1):
        try:
            # Step 1: 发起生成请求
            payload = {"model": "auto", "n": 1, "prompt": prompt}
            print(f"  [Mureka] 发起生成请求（第 {attempt} 次尝试）...")
            gen_resp = _mureka_post(MUREKA_GENERATE_URL, payload)
            task_id = gen_resp.get("id", "")
            if not task_id:
                raise RuntimeError(f"Mureka generate 响应缺少 id 字段: {gen_resp}")
            print(f"  [Mureka] task_id={task_id}，开始轮询...")

            # Step 2: 轮询直到 succeeded / failed
            elapsed = 0
            while elapsed < MUREKA_MAX_WAIT:
                time.sleep(MUREKA_POLL_INTERVAL)
                elapsed += MUREKA_POLL_INTERVAL
                query_url = MUREKA_QUERY_URL_TPL.format(task_id=task_id)
                query_resp = _mureka_get(query_url)
                status = query_resp.get("status", "")
                print(f"  [Mureka] elapsed={elapsed}s  status={status}")

                if status == "succeeded":
                    choices = query_resp.get("choices", [])
                    if not choices:
                        raise RuntimeError(f"Mureka succeeded 但 choices 为空: {query_resp}")
                    mp3_url = choices[0].get("url", "")
                    duration_ms = choices[0].get("duration", 0)
                    if not mp3_url:
                        raise RuntimeError(f"Mureka choices[0].url 为空: {choices[0]}")

                    # Step 3: 下载 mp3
                    print(f"  [Mureka] 下载 mp3 -> {output_path}")
                    _download_file(mp3_url, output_path)
                    print(f"  [Mureka] 完成  duration_ms={duration_ms}")
                    return {"task_id": task_id, "duration_ms": duration_ms}

                elif status in ("failed", "timeouted", "cancelled"):
                    reason = query_resp.get("failed_reason", "unknown")
                    raise RuntimeError(f"Mureka 任务失败 status={status} reason={reason}")

                # 其余 status（preparing / queued / running / reviewing）继续轮询

            raise RuntimeError(f"Mureka 任务超时（>{MUREKA_MAX_WAIT}s），task_id={task_id}")

        except (urllib.error.URLError, RuntimeError, Exception) as e:
            last_error = e
            print(f"  [Mureka] 第 {attempt} 次失败: {e}")
            if attempt < MUREKA_MAX_RETRIES:
                print(f"  [Mureka] 等待 10s 后重试...")
                time.sleep(10)

    raise RuntimeError(
        f"Mureka 调用在 {MUREKA_MAX_RETRIES} 次重试后仍失败。最后错误: {last_error}"
    )


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def main() -> None:
    """
    主流程：

    hardcoded 模式（默认，向后兼容）：
      - 只跑年夜饭（--stories single，原行为）
      - 跑 en / cn / mixed 三语言变体
      - 每个变体：Haiku 生成 music prompt → 调 Mureka 生成 BGM mp3
      - 产出命名：bgm_haiku_{lang}.mp3（v1）/ bgm_haiku_{lang}_v2.mp3（v2）

    haiku-pick 模式（--quote-mode haiku-pick）：
      - 支持 --stories single（只跑年夜饭）或 --stories all-six（循环 6 个故事）
      - 每个故事跑 en 和 mixed 两个变体（不跑 cn）
      - 只调 Haiku，不调 Mureka（验证金句挑选质量）
      - 产出：{story_dir}/haiku_quote_test_{lang}_output.txt
    """
    parser = argparse.ArgumentParser(
        description="语言策略 A/B/C 验证脚本 — 支持 v1 / v2 meta-prompt 及 haiku-pick 金句自挑模式"
    )
    parser.add_argument(
        "--version",
        choices=["v1", "v2"],
        default="v2",
        help="meta-prompt 版本：v1 用 meta_{lang}.md，v2 用 meta_{lang}_v2.md（默认 v2）；hardcoded 模式下有效",
    )
    parser.add_argument(
        "--quote-mode",
        choices=["hardcoded", "haiku-pick"],
        default="hardcoded",
        help="金句模式：hardcoded=使用年夜饭硬编码金句（默认），haiku-pick=让 Haiku 自挑金句（用 v3 meta-prompt）",
    )
    parser.add_argument(
        "--stories",
        choices=["single", "all-six"],
        default="single",
        help="故事范围：single=只跑年夜饭（默认），all-six=循环 6 个故事（haiku-pick 模式）",
    )
    args = parser.parse_args()
    version = args.version
    quote_mode = args.quote_mode
    stories_mode = args.stories

    print("\n" + "=" * 60)
    print("TASK-MUSIC-LANG-AB Step 2 — 语言策略 A/B/C 验证")
    print(f"[版本] meta-prompt version = {version}")
    print(f"[模式] quote_mode = {quote_mode}  stories = {stories_mode}")
    print("=" * 60)

    # ── 验证 API Key ──
    if not settings.ANTHROPIC_API_KEY:
        print("[错误] ANTHROPIC_API_KEY 未设置，退出")
        sys.exit(1)
    # Mureka 仅在 hardcoded 模式下需要
    if quote_mode == "hardcoded" and not settings.MUREKA_API_KEY:
        print("[错误] MUREKA_API_KEY 未设置，退出")
        sys.exit(1)

    # ── 确定要处理的故事列表 ──
    if stories_mode == "all-six":
        stories_to_run = STORIES
    else:
        # single 模式：只跑年夜饭（STORIES[2]，id=3）
        stories_to_run = [STORIES[2]]

    # ── 确定语言变体 ──
    if quote_mode == "haiku-pick":
        langs = ["en", "mixed"]  # haiku-pick 模式不跑 cn
    else:
        langs = ["en", "cn", "mixed"]  # hardcoded 模式跑全三语言

    results_summary = []

    for story in stories_to_run:
        story_id = story["id"]
        story_name = story["name"]
        outline_path = story["outline"]
        screenplay_path = story["screenplay"]
        story_output_dir = story["output_dir"]

        print(f"\n{'=' * 60}")
        print(f"[故事 {story_id}] {story_name}")
        print(f"{'=' * 60}")

        # ── Step 1: 提取故事数据 ──
        print(f"\n[Step 1] 提取故事数据...")
        try:
            story_data = extract_story_data(outline_path, screenplay_path, quote_mode)
        except Exception as e:
            print(f"  [错误] 提取故事数据失败: {e}，跳过故事 {story_name}")
            for lang in langs:
                results_summary.append({"story": story_name, "lang": lang, "status": "FAIL_DATA", "error": str(e)})
            continue

        print(f"  故事标题: {story_data['story_title']}")
        print(f"  叙事节奏: {story_data['narrative_pace']}")
        print(f"  整体基调: {story_data['overall_mood']}")
        print(f"  情感弧线: {story_data['emotional_arc_opening']} → {story_data['emotional_arc_resolution']}")
        print(f"  scene 数量（sound_design_hints 行数）: {story_data['sound_design_hints'].count(chr(10)) + 1}")
        if quote_mode == "hardcoded":
            print(f"  narration_quotes 使用硬编码（2 句）")
        else:
            full_narration = story_data.get("full_narration", "")
            narration_scenes = full_narration.count("[Scene ") if full_narration else 0
            print(f"  full_narration 已拼接（{narration_scenes} 个 scene，共 {len(full_narration)} chars）")

        # ── Step 2: 逐语言处理 ──
        for lang in langs:
            print(f"\n{'─' * 60}")
            print(f"[故事 {story_id}: {story_name}] 语言变体: {lang.upper()}")
            print(f"{'─' * 60}")

            # ── 输出文件路径 ──
            if quote_mode == "haiku-pick":
                # haiku-pick 模式产出到各故事自己的 output_dir
                output_txt_path = os.path.join(story_output_dir, f"haiku_quote_test_{lang}_output.txt")
                # haiku-pick 模式不产出 mp3
                bgm_path = None
            else:
                # hardcoded 模式：v1 保持原命名；v2 加 _v2 后缀（不覆盖 v1 产出）
                if version == "v2":
                    output_txt_path = os.path.join(OUTPUT_DIR, f"bgm_haiku_{lang}_v2_prompt.txt")
                    bgm_path = os.path.join(OUTPUT_DIR, f"bgm_haiku_{lang}_v2.mp3")
                else:
                    output_txt_path = os.path.join(OUTPUT_DIR, f"bgm_haiku_{lang}_prompt.txt")
                    bgm_path = os.path.join(OUTPUT_DIR, f"bgm_haiku_{lang}.mp3")

            # ── a. 加载 meta-prompt ──
            if quote_mode == "haiku-pick":
                meta_filename = f"meta_{lang}_v3_quote_picking.md"
            elif version == "v2":
                meta_filename = f"meta_{lang}_v2.md"
            else:
                meta_filename = f"meta_{lang}.md"

            try:
                print(f"  [meta-prompt] 加载 {meta_filename}（quote_mode={quote_mode}）...")
                system, user_template = load_meta_prompt(lang, version, quote_mode)
                print(f"  [meta-prompt] system 长度={len(system)} chars，user_template 长度={len(user_template)} chars")
            except Exception as e:
                print(f"  [错误] 加载 meta-prompt 失败: {e}，跳过 lang={lang}")
                results_summary.append({"story": story_name, "lang": lang, "status": "FAIL", "error": str(e)})
                continue

            # ── b. 填充占位符 ──
            user_filled = fill_placeholders(user_template, story_data)
            remaining = re.findall(r"\{\{[^}]+\}\}", user_filled)
            if remaining:
                # 过滤掉说明性文字中的占位符提及（如示例文本中的 {{full_narration}} 标签）
                # 只有在 user_filled 中 **未被替换** 的占位符才需要警告
                # 说明：story_data 里有 full_narration 或 narration_quotes，
                # 但 meta-prompt 示例文字中可能有 {{full_narration}} 作为解释性文字出现，
                # 这些在模板中不会被替换（因为 story_data 的 key 已匹配）。
                # 实际上如果 remaining 不空说明模板里有未提供的 key，需要告警。
                print(f"  [警告] 有未替换的占位符: {remaining}")
            else:
                placeholder_count = 13 if quote_mode == "haiku-pick" else 14
                print(f"  [fill] {placeholder_count} 个占位符全部替换完成，user prompt 长度={len(user_filled)} chars")

            # ── c. 调 Haiku 生成 music prompt ──
            try:
                print(f"  [Haiku] 调用 claude-haiku-4-5...")
                music_prompt = call_haiku(system, user_filled)
                print(f"  [Haiku] 生成完成，响应长度={len(music_prompt)} chars")
            except Exception as e:
                print(f"  [错误] Haiku 调用失败: {e}，跳过 lang={lang}")
                results_summary.append({"story": story_name, "lang": lang, "status": "FAIL_HAIKU", "error": str(e)})
                continue

            # ── d. 保存产出文件 ──
            with open(output_txt_path, "w", encoding="utf-8") as f:
                f.write(music_prompt)
            print(f"  [保存] 输出 -> {output_txt_path}")
            print(f"  [内容预览]\n  {'─' * 40}")
            for line in music_prompt.split("\n"):
                print(f"    {line}")
            print(f"  {'─' * 40}")

            if quote_mode == "haiku-pick":
                # ── BGM prompt 部分超上限检查（haiku-pick 模式）──
                quotes_match = re.search(r'<quotes>.*?</quotes>', music_prompt, re.DOTALL)
                if quotes_match:
                    bgm_prompt_part = music_prompt[quotes_match.end():].strip()
                    MUREKA_LIMIT = 1024
                    SAFE_MARGIN = 50  # 留出缓冲
                    if len(bgm_prompt_part) > MUREKA_LIMIT - SAFE_MARGIN:
                        print(f"  [警告] BGM prompt 部分 {len(bgm_prompt_part)} 字符接近 Mureka 1024 上限")
                        # 不自动截断（会损坏内容），只警告。PM 审查后决定是否重生成

                # haiku-pick 模式不调 Mureka，直接记录成功
                results_summary.append({
                    "story": story_name,
                    "lang": lang,
                    "status": "OK",
                    "haiku_response_len": len(music_prompt),
                    "output_file": output_txt_path,
                })
                print(f"  [完成] story={story_name}  lang={lang}  (Mureka 跳过，仅验证金句质量)")
            else:
                # ── e. 调 Mureka 生成 BGM（hardcoded 模式）──
                try:
                    mureka_result = call_mureka(music_prompt, bgm_path)
                    duration_sec = mureka_result["duration_ms"] / 1000
                    print(
                        f"  [完成] lang={lang}  "
                        f"task_id={mureka_result['task_id']}  "
                        f"duration={duration_sec:.1f}s  "
                        f"mp3={bgm_path}"
                    )
                    results_summary.append({
                        "story": story_name,
                        "lang": lang,
                        "status": "OK",
                        "haiku_prompt_len": len(music_prompt),
                        "task_id": mureka_result["task_id"],
                        "duration_ms": mureka_result["duration_ms"],
                    })
                except Exception as e:
                    print(f"  [错误] Mureka 调用失败: {e}，lang={lang} 的 mp3 未生成")
                    results_summary.append({
                        "story": story_name,
                        "lang": lang,
                        "status": "FAIL_MUREKA",
                        "haiku_prompt_len": len(music_prompt),
                        "error": str(e),
                    })

    # ── 汇总报告 ──
    print(f"\n{'=' * 60}")
    print("汇总报告")
    print(f"{'=' * 60}")
    for r in results_summary:
        story = r.get("story", "unknown")
        lang = r["lang"]
        status = r["status"]
        if status == "OK" and quote_mode == "haiku-pick":
            print(
                f"  [{story}/{lang}] OK  "
                f"haiku_len={r['haiku_response_len']}  "
                f"file={os.path.basename(r['output_file'])}"
            )
        elif status == "OK":
            print(
                f"  [{story}/{lang}] OK  "
                f"haiku_len={r['haiku_prompt_len']}  "
                f"task_id={r['task_id']}  "
                f"duration={r['duration_ms'] / 1000:.1f}s"
            )
        else:
            print(f"  [{story}/{lang}] {status}  error={r.get('error', '')}")

    ok_count = sum(1 for r in results_summary if r["status"] == "OK")
    total_count = len(results_summary)
    print(f"\n  成功: {ok_count}/{total_count}")

    if quote_mode == "haiku-pick":
        print(f"\n  产出文件（每个故事目录下）:")
        for r in results_summary:
            if r["status"] == "OK":
                print(f"    {r['output_file']}")
    else:
        print(f"  产出目录: {OUTPUT_DIR}")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
