"""
BGM 音乐生成服务 — Wave 2 Pipeline Integration

负责整合以下组件为可在 Pipeline 中调用的单一函数：
  1. story_music_extractor.py  — 从 outline/screenplay 提取故事数据
  2. Claude Haiku 4.5 API     — 将故事数据转为 Mureka BGM prompt（v3.2 mixed meta-prompt）
  3. Mureka API               — 生成纯音乐 BGM（auto model = mureka-9）
  4. ffmpeg_post_processor.py — 切水印 + 裁时长 + LUFS QA

主入口：generate_bgm_for_chapter(chapter_id, project_id, outline, screenplay, ...) -> dict

设计约定：
  - SSL certifi fix 在模块顶部全局应用（Python 3.11 framework SSL 链问题）
  - 占位符替换用 str.replace 链式调用（避免 .format() 误吞 meta-prompt 内花括号）
  - system prompt 使用 prompt cache（cache_control: ephemeral），user prompt 每次不同不缓存
  - Haiku 最多 3 次重试，Mureka 最多 3 次重试（复用 call_mureka() 内部重试机制）
  - BGM 生成失败时抛出异常（Pipeline 调用方负责 try/except，不阻塞 Pipeline）
"""

import json
import logging
import os
import re
import time
import urllib.request
import urllib.error

import ssl
import certifi

# 强制 urllib 全局使用 certifi 的 CA bundle（修复 Python 3.11 framework SSL 证书链问题）
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

import anthropic

# B43: AsyncAnthropic for non-blocking event loop usage (Anthropic + messages.create → AsyncAnthropic + await)
import asyncio

# BUG-MUREKA-BLOCK-EVENT-LOOP (Wave 6 / 2026-05-11):
# Mureka 轮询期间（约 2 min）原 urllib.request + time.sleep 同步阻塞 FastAPI event loop，
# 导致 /health 5s 超时 Monitor 误报 alive_no_health。
# 改造：urllib → aiohttp (异步 HTTP 客户端)，time.sleep → asyncio.sleep
import aiohttp

from app.config import settings
from app.services.story_music_extractor import extract_story_for_music
from app.services.ffmpeg_post_processor import process_bgm

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 路径常量
# ──────────────────────────────────────────────

# meta-prompt 文件目录
# T20-51: 从 test_output/ 迁至 app/prompts/bgm/ (生产 deploy 安全路径)
# 旧路径: test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/
# 新路径: app/prompts/bgm/ (正式代码资源目录, 不被 .gitignore 排除)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")
META_PROMPT_DIR = os.path.join(
    _PROJECT_ROOT,
    "app", "prompts", "bgm"
)

# meta-prompt 文件名映射（meta_version → filename）
_META_VERSION_FILES = {
    "mixed": "meta_mixed_v3_quote_picking.md",
    "en": "meta_en_v2.md",
}

# Mureka API 配置
MUREKA_GENERATE_URL = "https://api.mureka.cn/v1/instrumental/generate"
MUREKA_QUERY_URL_TPL = "https://api.mureka.cn/v1/instrumental/query/{task_id}"
MUREKA_POLL_INTERVAL = 8       # 轮询间隔（秒）
MUREKA_MAX_WAIT = 300          # 最大等待时间（秒）
MUREKA_MAX_RETRIES = 3         # 最大重试次数

# 目标时长映射：story_type → 秒数
TARGET_DURATION_MAP = {
    "快闪": 60,
    "短篇": 90,
    "中篇": 180,
}
DEFAULT_TARGET_DURATION_SEC = 180

# 积分消耗（mock）
CREDITS_FIRST_GEN = 10
CREDITS_CHANGE_BGM = 5
CREDITS_REGEN = 10


# ──────────────────────────────────────────────
# Wave 7 / DEC-026 — BGM prompt linter (style_category 必备/禁用词检查)
# ──────────────────────────────────────────────
#
# 用于检查 Haiku 输出的 BGM prompt 是否含目标 style_category 必备词、是否
# 误用了禁用词。如果任一缺失/泄露 → 重新调一次 Haiku（最多 2 次），仍失败则
# 返回原 prompt + 在 log 标黄警告（不阻塞 BGM 生成）。
#
# 必备词 (REQUIRED): 至少出现 1 个该 category 的特征乐器/调式 → 才算"穿对衣服"
# 禁用词 (FORBIDDEN): 不能出现的跨 category 错位词 → 出现即"穿错衣服"
#
# 用小写匹配。匹配采用"包含子串"(`token in prompt_lower`)，宽松一点，避免
# 词形变化漏判（"strings" 包含 "string"，"guqin-like" 包含 "guqin"）。
#
# 8 个 category (5 主 + 3 sub) 全覆盖：
#   - chinese_traditional: 中国古风 (古琴/笛/二胡/五声)
#   - ink_painting:        水墨延伸 (chinese_traditional 极简变体)
#   - western_realistic:   现代西式 (钢琴/弦乐)
#   - sci_fi:              赛博/未来 (合成器/电子)
#   - japanese_anime:      日漫/管弦民谣
#   - fantasy_children:    儿童绘本 (铃铛/木琴/玩具感)
#   - cartoon_humor:       俏皮卡通 (节奏感强/反转感)
#   - generic:             兜底无强约束（不做硬验证）

STYLE_REQUIRED_KEYWORDS: dict[str, list[str]] = {
    "chinese_traditional": [
        "guqin", "dizi", "xiao", "pipa", "guzheng", "erhu", "ruan", "yangqin",
        "pentatonic", "chinese", "bamboo flute", "silk string", "古琴", "笛", "箫",
        "二胡", "古筝", "琵琶", "戏鼓", "战鼓", "铜钟",
    ],
    "ink_painting": [
        # ink_painting 必须出现至少 1 个 Chinese 乐器或明确的"中国 ink/水墨"标记
        # 不允许只靠 "sparse" / "silence" 这类通用氛围词混过
        "guqin", "dizi", "xiao", "pipa", "ruan", "guzheng", "pentatonic",
        "chinese ink", "ink wash", "bamboo flute",
        "古琴", "笛", "箫", "古筝", "琵琶", "二胡", "留白",
    ],
    "western_realistic": [
        "piano", "strings", "violin", "cello", "viola", "guitar", "acoustic",
        "orchestra", "chamber",
    ],
    "sci_fi": [
        "synth", "synthesizer", "electronic", "pad", "808", "drone", "glitch",
        "sub bass", "arp", "vocoder", "neon", "modular", "analog synth",
    ],
    "japanese_anime": [
        "shamisen", "shakuhachi", "koto", "taiko", "harp", "horn", "orchestra",
        "anime", "wind instrument", "woodwind", "三味线", "尺八",
    ],
    "fantasy_children": [
        "glockenspiel", "bell", "celesta", "music box", "xylophone", "ukulele",
        "harp", "chime", "toy piano", "marimba",
    ],
    "cartoon_humor": [
        "snare", "brass stab", "syncopated", "bouncy", "tuba", "trombone",
        "kazoo", "pizzicato", "playful",
    ],
    "generic": [],  # 不做硬约束
}

STYLE_FORBIDDEN_KEYWORDS: dict[str, list[str]] = {
    "chinese_traditional": [
        # 严禁出现纯西式/电子/卡通/嘶吼 - 视觉听觉割裂的根因
        "distorted strings", "drum kit", "trap beat", "808 bass",
        "saxophone", "electric guitar", "synthesizer pad", "analog synth",
        "punk", "metal", "rock", "edm", "dubstep",
    ],
    "ink_painting": [
        "distorted strings", "drum kit", "808", "trap", "rock", "edm",
        "synthesizer pad", "saxophone", "punk",
    ],
    "western_realistic": [
        # 西式现代故事不要硬塞古筝/中国五声音阶
        "guqin", "dizi", "erhu", "pentatonic chinese", "shamisen",
        # 中文字符
        "古琴", "二胡", "古筝", "唢呐",
    ],
    "sci_fi": [
        # 赛博朋克/未来感故事忌古典中国乐器或田园弦乐主导
        "guqin", "dizi", "erhu", "harpsichord", "traditional folk",
        "fingerpicked acoustic guitar", "pentatonic",
        # 中文字符
        "古琴", "二胡", "古筝", "唢呐",
    ],
    "japanese_anime": [
        "guqin", "dizi", "erhu", "808 bass", "trap beat",
        # 中文字符（避免 prompt 用 "二胡"/"古琴"/"笛" 等绕过英文 forbidden）
        "古琴", "二胡", "笛", "古筝", "战鼓", "唢呐",
    ],
    "fantasy_children": [
        # 儿童故事忌金属/电吉他/嘶吼/暗黑
        "distorted", "metal", "rock", "808 bass", "trap", "shrieking",
        "growl", "scream", "death metal",
    ],
    "cartoon_humor": [
        # 卡通搞笑忌严肃/沉重/葬礼感
        "funeral", "dirge", "hopeless", "suffocating", "dread",
    ],
    "generic": [],
}


def _validate_bgm_prompt(prompt: str, style_category: str) -> tuple[bool, list[str], list[str]]:
    """
    Wave 7 / DEC-026 — 检查 BGM prompt 是否符合 style_category 的必备词/禁用词约束。

    匹配规则：
      - 大小写不敏感
      - 子串包含匹配（"strings" 包含 "string"，"guqin-like" 包含 "guqin"）
      - 必备词列表只要命中**任意 1 个**即算通过
      - 禁用词列表任何 1 个出现即算泄露

    Args:
        prompt: Haiku 输出的 BGM prompt 文本（含 <quotes> 块）
        style_category: 目标 BGM 一级分类

    Returns:
        (is_valid, missing_required, leaked_forbidden)
        - is_valid: True 当且仅当至少命中 1 个必备词 AND 0 个禁用词
        - missing_required: 当 0 个必备词命中时返回完整必备词表（供 retry 时给 Haiku 提示）
        - leaked_forbidden: 实际泄露的禁用词列表
    """
    if not prompt or not isinstance(prompt, str):
        return False, [], []

    # generic / 未知 category 不做硬约束（避免误杀）
    if style_category not in STYLE_REQUIRED_KEYWORDS:
        return True, [], []

    required = STYLE_REQUIRED_KEYWORDS[style_category]
    forbidden = STYLE_FORBIDDEN_KEYWORDS.get(style_category, [])

    prompt_lower = prompt.lower()

    # 必备词 — 命中任意 1 个即通过
    if required:
        any_required_hit = any(kw.lower() in prompt_lower for kw in required)
    else:
        any_required_hit = True  # 空必备词列表（如 generic）→ 默认通过

    # 禁用词 — 任何 1 个出现即泄露
    leaked = [kw for kw in forbidden if kw.lower() in prompt_lower]

    is_valid = any_required_hit and len(leaked) == 0

    # 如果 required 全失，返回完整必备词作为 missing 列表（给 retry 用）
    missing_required = [] if any_required_hit else list(required)

    return is_valid, missing_required, leaked


def _build_repair_hint(missing_required: list[str], leaked_forbidden: list[str], style_category: str) -> str:
    """
    根据 linter 结果构建给 Haiku 第二次调用的 repair hint 段落，追加在 user_prompt 末尾。
    """
    parts = [
        "\n\n---\n\n",
        "**⚠️ 上一次输出未通过 BGM 通用性 linter，请按以下指引重新生成：**\n\n",
        f"- 目标 style_category: `{style_category}`\n",
    ]
    if missing_required:
        # 只列前 8 个，避免污染 prompt 上下文太多
        sample = ", ".join(missing_required[:8])
        parts.append(
            f"- ❌ 缺失必备词（至少出现 1 个）：{sample}\n"
            f"- 必须在 BGM prompt 中至少出现一个上述乐器或调式词\n"
        )
    if leaked_forbidden:
        sample = ", ".join(leaked_forbidden)
        parts.append(
            f"- ❌ 误用了禁用词：{sample}\n"
            f"- 必须把这些词从 BGM prompt 中删除，换成 style_category={style_category} 的对应词\n"
        )
    parts.append(
        "- 严禁跨 style_category 混用乐器/调性词\n"
        "- 重新输出完整的 <quotes>...</quotes> + BGM prompt（按原格式）\n"
    )
    return "".join(parts)


# ──────────────────────────────────────────────
# T20-45: BGM 时长信号 linter（短片信号词检测）
# Mureka API 无 duration 参数，时长完全由 prompt 语义决定。
# 短片信号词会导致 Mureka 输出 <60s 短片；需要时长框架词触发 ≥150s。
# ──────────────────────────────────────────────

# 短片信号词 — 作为主要结构词时让 Mureka 推断"短、终止、无后续"
_DURATION_SHORT_SIGNALS: list[str] = [
    "suddenly stops",
    "abruptly ends",
    "abruptly stops",
    "cuts off",
    "no resolution",
    "question hanging",
    "no answer",
    "long silences",
    "long silence",
]

# 时长框架词 — 至少出现 1 个才能触发 ≥150s 输出
_DURATION_FRAMEWORK_WORDS: list[str] = [
    "sustained",
    "continuous",
    "continuously",
    "extended",
    "building",
    "developing",
    "unfolding",
    "gradually",
    "slowly evolving",
    "deepening",
    "expanding",
    "layering",
    "throughout",
    "persisting",
    "carrying through",
    "long-form",
]


def _check_bgm_duration_signals(prompt: str) -> tuple[bool, list[str], bool]:
    """
    T20-45 — 检测 BGM prompt 是否包含"短片信号词"或缺少"时长框架词"。

    Mureka API 无 duration 参数，时长完全由 prompt 语义决定：
    - 短片信号词（如 "suddenly stops"）→ Mureka 推断短片（<60s）
    - 时长框架词（如 "sustained"）→ Mureka 推断长段（≥150s）

    Returns:
        (has_duration_issue, leaked_short_signals, has_framework_word)
        - has_duration_issue: True 当"泄露了短片信号词" OR "缺失时长框架词"
        - leaked_short_signals: 实际检测到的短片信号词列表
        - has_framework_word: True 当至少命中 1 个时长框架词
    """
    if not prompt or not isinstance(prompt, str):
        return False, [], False

    prompt_lower = prompt.lower()

    # 检测短片信号词（子串匹配，大小写不敏感）
    leaked_short = [w for w in _DURATION_SHORT_SIGNALS if w.lower() in prompt_lower]

    # 检测时长框架词（子串匹配）
    has_framework = any(w.lower() in prompt_lower for w in _DURATION_FRAMEWORK_WORDS)

    has_duration_issue = bool(leaked_short) or not has_framework

    return has_duration_issue, leaked_short, has_framework


def _build_duration_repair_hint(leaked_short: list[str], has_framework: bool) -> str:
    """
    T20-45 — 构建时长修复 hint，追加到 user_prompt 末尾触发 Haiku 重新生成。
    """
    parts = [
        "\n\n---\n\n",
        "**⚠️ 上一次 BGM prompt 包含短片信号词或缺少时长框架词，"
        "会导致 Mureka 生成 <60s 短片，请按以下规则重新生成：**\n\n",
        "目标：BGM ≥ 150 秒（约 2.5 分钟）。\n\n",
    ]
    if leaked_short:
        sample = "、".join(leaked_short)
        parts.append(
            f"- [ERROR] 检测到短片信号词（禁止用作主要结构词）：{sample}\n"
            "- 这些词让 Mureka 推断'音乐在此终止'——必须删除或替换\n"
        )
    if not has_framework:
        parts.append(
            "- ❌ 缺少时长框架词——必须在 BGM prompt 中至少出现 1 个：\n"
            "  sustained / continuous / extended / building / developing / unfolding / "
            "gradually / slowly evolving / deepening / expanding / layering / throughout\n"
        )
    parts.append(
        "- 替换示例（悬疑）：把 'A question hanging. No answer.' → "
        "'Sustained low drone building beneath unresolved tension, continuously deepening.'\n"
        "- 重新输出完整的 <quotes>...</quotes> + BGM prompt（按原格式）\n"
    )
    return "".join(parts)


# ──────────────────────────────────────────────
# meta-prompt 解析
# ──────────────────────────────────────────────

def _load_meta_prompt(meta_version: str) -> tuple[str, str]:
    """
    加载指定版本的 meta-prompt 文件，解析出 system prompt 和 user prompt 模板。

    文件格式：
      ## 系统提示词（SYSTEM PROMPT）  或  ## SYSTEM PROMPT
        ... content ...
      ## 用户提示词模板（USER PROMPT TEMPLATE）  或  ## USER PROMPT TEMPLATE
        ... content ...

    Args:
        meta_version: "mixed" 或 "en"

    Returns:
        (system_prompt, user_prompt_template)

    Raises:
        ValueError: 文件不存在或格式不对
    """
    filename = _META_VERSION_FILES.get(meta_version)
    if not filename:
        raise ValueError(f"[MusicGenerationService] 未知 meta_version: {meta_version}")

    path = os.path.join(META_PROMPT_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"[MusicGenerationService] meta-prompt 文件不存在: {path}")

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 按 "^## " 分段
    sections: dict[str, str] = {}
    parts = re.split(r"(?m)^## ", content)
    for part in parts[1:]:
        first_newline = part.find("\n")
        if first_newline == -1:
            continue
        header_line = part[:first_newline].strip()
        body = part[first_newline + 1:].strip()
        sections[header_line] = body

    system_prompt = ""
    user_prompt_template = ""

    for header, body in sections.items():
        header_upper = header.upper()
        if "SYSTEM PROMPT" in header_upper or "系统提示词" in header:
            system_prompt = body
        elif "USER PROMPT" in header_upper or "用户提示词" in header:
            user_prompt_template = body

    if not system_prompt:
        raise ValueError(f"[MusicGenerationService] 未能解析 system prompt，meta_version={meta_version}，文件: {path}")
    if not user_prompt_template:
        raise ValueError(f"[MusicGenerationService] 未能解析 user prompt template，meta_version={meta_version}，文件: {path}")

    return system_prompt, user_prompt_template


def _fill_placeholders(template: str, story_data: dict) -> str:
    """
    用手动 replace 链式替换 {{placeholder}} 占位符。
    不用 str.format() 避免误吞 meta-prompt 内的 {"type": "text"} 花括号。
    """
    result = template
    for key, value in story_data.items():
        result = result.replace("{{" + key + "}}", str(value) if value is not None else "")
    return result


# ──────────────────────────────────────────────
# Haiku API 调用（含 prompt cache）
# ──────────────────────────────────────────────

def _clean_haiku_output(text: str) -> str:
    """
    清理 Haiku 输出的污染：markdown fence + 非 <quotes> 的 XML 标签。

    保留 <quotes> 和 </quotes>（合法格式）。
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


async def _call_haiku_with_cache(system_prompt: str, user_prompt: str) -> str:
    """
    B43: 异步调 Anthropic API (claude-haiku-4-5) 生成 music prompt 文本。
    使用 AsyncAnthropic + await，避免同步阻塞 FastAPI 事件循环（B35 同类修复模式）。
    system prompt 使用 prompt cache（cache_control: ephemeral）降低重复调用成本。
    user prompt（含 full_narration 等故事数据）每次不同，不缓存。

    Args:
        system_prompt: 系统提示词（每次相同，走缓存）
        user_prompt: 已填充占位符的用户提示词（每次不同，不缓存）

    Returns:
        清理后的 music prompt 文本

    Raises:
        anthropic.APIError: API 调用失败时向上抛出
    """
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    # system prompt 使用 cache_control: ephemeral（1 小时 TTL 内重复调用节省 token）
    msg = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": user_prompt,  # 故事数据在 user prompt，不缓存
            }
        ],
    )
    raw_text = msg.content[0].text.strip()
    cleaned = _clean_haiku_output(raw_text)
    return cleaned


async def _call_haiku_with_retry(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    """
    B43: 异步带重试的 Haiku API 调用。

    T22-NEW-4 (2026-05-22): 升级为三层 fallback chain
        Haiku 4.5 → Gemini 3.1 Flash → Sonnet 4.6 (跨 provider 优先)
    Founder e2e test22 13:56 实证: Haiku 3 次 retry 全 529, 故事无 BGM.
    新方案: Haiku 失败 → 自动切 Gemini Flash → 再失败 → Sonnet 兜底.
    KEY_LEARNINGS #55 (cross-provider > cross-size).

    `max_retries` 参数保留向后兼容, 但不再直接使用 (fallback chain 内部
    每 layer 默认 retry 1 次, 总 2x3=6 次尝试, 多于旧 3 次).

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        max_retries: 旧 retry 上限 (保留 sig 兼容, 实际由 fallback chain 接管)

    Returns:
        清理后的 music prompt 文本 (经 _clean_haiku_output 处理)

    Raises:
        RuntimeError: 三层 fallback 全部失败
    """
    # 延迟 import 避免循环依赖 (llm_fallback_chain 也 import settings)
    from app.services.llm_fallback_chain import call_llm_with_fallback

    fb_result = await call_llm_with_fallback(
        user=user_prompt,
        system=system_prompt,
        max_tokens=1024,
        operation_label="music_bgm",
    )
    if not fb_result.success:
        raise RuntimeError(
            f"[MusicGenerationService] T22-NEW-4 三层 fallback 全部失败: "
            f"{fb_result.error}"
        )

    cleaned = _clean_haiku_output(fb_result.text)
    logger.info(
        f"[MusicGenerationService] T22-NEW-4 LLM ok via "
        f"{fb_result.provider_used}:{fb_result.model_used} "
        f"(chain={fb_result.chain_depth}), 输出 {len(cleaned)} 字符"
    )
    return cleaned


# ──────────────────────────────────────────────
# Mureka API 调用
# ──────────────────────────────────────────────

def _mureka_headers() -> dict:
    """返回 Mureka API 所需的 HTTP header"""
    return {
        "Authorization": f"Bearer {settings.MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }


# BUG-MUREKA-BLOCK-EVENT-LOOP (Wave 6 / 2026-05-11):
# 以下所有 Mureka HTTP 调用全部 async 化（aiohttp + asyncio.sleep）
# 避免阻塞 FastAPI uvicorn 单 worker 的 event loop
# 保留 certifi SSL 上下文（aiohttp 通过 ssl 参数传入）

async def _mureka_post(session: aiohttp.ClientSession, url: str, payload: dict) -> dict:
    """
    BUG-MUREKA-BLOCK-EVENT-LOOP: 异步 POST 请求到 Mureka API。
    使用 ensure_ascii=False 保留中文字符。
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    timeout = aiohttp.ClientTimeout(total=30)
    async with session.post(
        url,
        data=body,
        headers=_mureka_headers(),
        timeout=timeout,
    ) as resp:
        text = await resp.text()
        if resp.status >= 400:
            # 让上层 try/except 触发重试逻辑
            raise RuntimeError(f"Mureka POST {url} HTTP {resp.status}: {text[:300]}")
        return json.loads(text)


async def _mureka_get(session: aiohttp.ClientSession, url: str) -> dict:
    """BUG-MUREKA-BLOCK-EVENT-LOOP: 异步 GET 请求到 Mureka API"""
    timeout = aiohttp.ClientTimeout(total=30)
    async with session.get(
        url,
        headers=_mureka_headers(),
        timeout=timeout,
    ) as resp:
        text = await resp.text()
        if resp.status >= 400:
            raise RuntimeError(f"Mureka GET {url} HTTP {resp.status}: {text[:300]}")
        return json.loads(text)


async def _download_file(session: aiohttp.ClientSession, url: str, output_path: str) -> None:
    """BUG-MUREKA-BLOCK-EVENT-LOOP: 异步下载 mp3 到 output_path（流式写入）"""
    timeout = aiohttp.ClientTimeout(total=120)  # 下载允许更长（Mureka mp3 数 MB）
    async with session.get(url, timeout=timeout) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"下载 Mureka mp3 HTTP {resp.status}: {url}")
        # 流式写入避免大 mp3 占内存峰值
        with open(output_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(64 * 1024):
                f.write(chunk)


async def _call_mureka(prompt: str, output_path: str) -> dict:
    """
    BUG-MUREKA-BLOCK-EVENT-LOOP (Wave 6 / 2026-05-11):
    异步调 Mureka API 生成纯音乐 BGM，轮询直到 succeeded，下载 mp3 到 output_path。
    最多重试 MUREKA_MAX_RETRIES 次（含 generate 请求失败 + 轮询失败）。

    改造点（vs 旧同步版）:
      - urllib.request → aiohttp.ClientSession
      - time.sleep → asyncio.sleep（不阻塞 event loop）
      - 整个函数 def → async def
      - 调用方 generate_bgm_for_chapter() 已 await（B43 已 async）

    Args:
        prompt: 由 Haiku 生成的 music prompt 文本（≤1024 字符）
        output_path: 保存 mp3 的完整路径

    Returns:
        dict: {"task_id": str, "duration_ms": int}

    Raises:
        RuntimeError: 多次重试后仍失败
    """
    last_error: Exception | None = None

    # 用 certifi 的 CA bundle 创建 SSL 上下文（保留旧版同款 SSL 修补）
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)

    async with aiohttp.ClientSession(connector=connector) as session:
        for attempt in range(1, MUREKA_MAX_RETRIES + 1):
            try:
                # Step 1: 发起生成请求
                payload = {"model": "auto", "n": 1, "prompt": prompt}
                logger.info(f"[MusicGenerationService] Mureka 发起生成请求（第 {attempt} 次）...")
                gen_resp = await _mureka_post(session, MUREKA_GENERATE_URL, payload)
                task_id = gen_resp.get("id", "")
                if not task_id:
                    raise RuntimeError(f"Mureka generate 响应缺少 id 字段: {gen_resp}")
                logger.info(f"[MusicGenerationService] Mureka task_id={task_id}，开始轮询...")

                # Step 2: 轮询直到 succeeded / failed（asyncio.sleep 不阻塞 event loop）
                elapsed = 0
                while elapsed < MUREKA_MAX_WAIT:
                    await asyncio.sleep(MUREKA_POLL_INTERVAL)
                    elapsed += MUREKA_POLL_INTERVAL
                    query_url = MUREKA_QUERY_URL_TPL.format(task_id=task_id)
                    query_resp = await _mureka_get(session, query_url)
                    status = query_resp.get("status", "")
                    logger.info(f"[MusicGenerationService] Mureka elapsed={elapsed}s  status={status}")

                    if status == "succeeded":
                        choices = query_resp.get("choices", [])
                        if not choices:
                            raise RuntimeError(f"Mureka succeeded 但 choices 为空: {query_resp}")
                        mp3_url = choices[0].get("url", "")
                        duration_ms = choices[0].get("duration", 0)
                        if not mp3_url:
                            raise RuntimeError(f"Mureka choices[0].url 为空: {choices[0]}")

                        # Step 3: 异步下载 mp3
                        logger.info(f"[MusicGenerationService] 下载 mp3 -> {output_path}")
                        await _download_file(session, mp3_url, output_path)
                        logger.info(f"[MusicGenerationService] Mureka 完成  duration_ms={duration_ms}")
                        return {"task_id": task_id, "duration_ms": duration_ms}

                    elif status in ("failed", "timeouted", "cancelled"):
                        reason = query_resp.get("failed_reason", "unknown")
                        raise RuntimeError(f"Mureka 任务失败 status={status} reason={reason}")

                    # 其余 status（preparing / queued / running / reviewing）继续轮询

                raise RuntimeError(f"Mureka 任务超时（>{MUREKA_MAX_WAIT}s），task_id={task_id}")

            except Exception as e:
                last_error = e
                logger.warning(f"[MusicGenerationService] Mureka 第 {attempt} 次失败: {e}")
                if attempt < MUREKA_MAX_RETRIES:
                    logger.info(f"[MusicGenerationService] 等待 10s 后重试...")
                    await asyncio.sleep(10)

    raise RuntimeError(
        f"[MusicGenerationService] Mureka 调用在 {MUREKA_MAX_RETRIES} 次重试后仍失败。最后错误: {last_error}"
    )


# ──────────────────────────────────────────────
# meta_version 选择逻辑
# ──────────────────────────────────────────────

def _select_meta_version(regen_count: int) -> str:
    """
    根据重生次数选择 meta-prompt 版本。

    逻辑（基于 v3.2 测试发现：mixed > en）：
      regen_count == 0 → "mixed"（首次生成，最优）
      regen_count == 1 → "en"（第一次 regen，备用策略）
      regen_count >= 2 → "mixed"（回到最优，AI 随机性产生差异）

    Args:
        regen_count: 已重生成次数（0 = 首次生成）

    Returns:
        "mixed" 或 "en"
    """
    if regen_count == 0:
        return "mixed"
    elif regen_count == 1:
        return "en"
    else:
        return "mixed"


# ──────────────────────────────────────────────
# 积分计算（mock）
# ──────────────────────────────────────────────

def _calculate_credits(is_first_gen: bool, is_change_bgm: bool) -> int:
    """
    计算本次操作消耗的积分（当前为 mock 实现，Wave 3 接入真实积分系统）。

    规则：
      首次生成（regen_count == 0）→ 10 积分
      更换 BGM（is_change_bgm=True）→ 5 积分
      重新生成（regen_count > 0）→ 10 积分

    Args:
        is_first_gen: 是否首次生成（regen_count == 0）
        is_change_bgm: 是否为更换 BGM 操作

    Returns:
        积分数（整数）
    """
    if is_change_bgm:
        return CREDITS_CHANGE_BGM
    elif is_first_gen:
        return CREDITS_FIRST_GEN
    else:
        return CREDITS_REGEN


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

async def generate_bgm_for_chapter(
    chapter_id: int,
    project_id: int,
    outline: dict,
    screenplay: dict,
    output_dir: str,
    story_type: str = "短篇",
    visual_style_hint: str = "",
    regen_count: int = 0,
    bgm_volume: float = 1.0,
    is_change_bgm: bool = False,
    user_selected_mood: str | None = None,  # B33: project.user_selected_mood（最高优先级）
    style_preset: str = "",                   # Wave 7 / DEC-026: 用户 Stage A 选的 style_preset id
) -> dict:
    """
    为单个 chapter 生成 BGM，完整整合 Haiku + Mureka + FFmpeg 后处理。

    Flow（Wave 7 加入 linter 闭环）：
      1. extract_story_for_music(..., style_preset) → 19 字段 story_data
         （含 style_category / setting_period / character_dominant_type）
      2. _select_meta_version(regen_count) → meta_version
      3. _load_meta_prompt(meta_version) → (system_prompt, user_prompt_template)
      4. _fill_placeholders(user_prompt_template, story_data) → user_prompt
      5. _call_haiku_with_retry(system_prompt, user_prompt) → bgm_prompt（带重试）
      5b. _validate_bgm_prompt(bgm_prompt, style_category) → 检查必备/禁用词
          - 通过 → 进入 Step 6
          - 不通过 → 追加 repair_hint 重调 Haiku 一次（最多 1 次重修），仍不通过则
            fallback 走原 prompt + log warning（不阻塞 BGM 生成）
      6. _call_mureka(bgm_prompt, raw_mp3_path) → {"task_id", "duration_ms"}（带重试）
      7. process_bgm(raw_mp3_path, output_mp3_path, target_duration_sec, bgm_volume) → qa_result
      8. 删除临时 raw mp3，返回结果 dict

    Args:
        chapter_id: 章节 ID（用于文件命名）
        project_id: 项目 ID（用于文件命名）
        outline: Stage 1 输出的 1_outline.json 数据（dict）
        screenplay: Stage 3 输出的 3_screenplay.json 数据（dict）
        output_dir: BGM 文件输出目录（必须已存在）
        story_type: 故事篇幅类型（"快闪" / "短篇" / "中篇"），决定 target_duration_sec
        visual_style_hint: 视觉风格提示（如 "anime"），传给 story_music_extractor
        regen_count: 已重生成次数（0 = 首次），决定 meta_version
        bgm_volume: 音量系数（0.0-1.0），默认 1.0
        is_change_bgm: 是否为"更换 BGM"操作（影响积分计算）

    Returns:
        {
            "success": True,
            "bgm_url": str,            # 处理后 mp3 的绝对路径（Wave 3 换成 CDN URL）
            "meta_version": str,       # 使用的 meta-prompt 版本（"mixed" / "en"）
            "bgm_prompt": str,         # Haiku 生成的 music prompt（含 <quotes> 块）
            "mureka_task_id": str,     # Mureka 任务 ID（调试用）
            "duration_ms": int,        # Mureka 输出原始时长（毫秒）
            "target_duration_sec": int,# FFmpeg 裁剪目标时长
            "qa_result": dict,         # process_bgm 返回的 QA 详情
            "credits_used": int,       # 本次消耗积分（mock）
        }

    Raises:
        RuntimeError: Haiku 或 Mureka 多次重试后仍失败
        FileNotFoundError: meta-prompt 文件不存在
        Exception: FFmpeg 处理失败（pass 给 Pipeline，不阻塞）
    """
    logger.info(
        f"[MusicGenerationService] ===== 开始生成 BGM ====="
        f" chapter_id={chapter_id}, project_id={project_id},"
        f" story_type={story_type}, regen_count={regen_count}"
    )

    # Step 1: 提取故事数据
    logger.info("[MusicGenerationService] Step 1: 提取故事数据...")
    # B33: 优先级链 project.user_selected_mood > confirmed_outline.user_selected_mood > outline.visual_tone.overall_mood
    _effective_mood = user_selected_mood or (outline or {}).get("user_selected_mood") or None
    if _effective_mood:
        logger.info(f"[MusicGenerationService] B33: overall_mood 使用 user_selected_mood={_effective_mood!r}")
    story_data = extract_story_for_music(
        outline=outline,
        screenplay=screenplay,
        visual_style_hint=visual_style_hint,
        max_scenes=6,
        user_selected_mood=_effective_mood,  # B33: 传入 user_selected_mood
        style_preset=style_preset,           # Wave 7 / DEC-026: 透传 style_preset
    )
    # Wave 7 / DEC-026: 提取出的 BGM 通用性维度（用于 linter）
    _style_category = story_data.get("style_category", "generic")
    _setting_period = story_data.get("setting_period", "generic")
    logger.info(
        f"[MusicGenerationService] story_data 提取完成 "
        f"title={story_data.get('story_title', 'N/A')!r} "
        f"style_preset={style_preset!r} → style_category={_style_category!r} "
        f"setting_period={_setting_period!r}"
    )

    # Step 2: 选择 meta_version
    meta_version = _select_meta_version(regen_count)
    logger.info(f"[MusicGenerationService] Step 2: meta_version={meta_version} (regen_count={regen_count})")

    # Step 3: 加载 meta-prompt
    logger.info(f"[MusicGenerationService] Step 3: 加载 meta-prompt ({meta_version})...")
    system_prompt, user_prompt_template = _load_meta_prompt(meta_version)

    # Step 4: 填充占位符
    logger.info("[MusicGenerationService] Step 4: 填充 user prompt 占位符...")
    user_prompt = _fill_placeholders(user_prompt_template, story_data)

    # Step 5: 调 Haiku（含重试）— B43: await async call
    logger.info("[MusicGenerationService] Step 5: 调 Haiku 4.5 生成 BGM prompt...")
    bgm_prompt = await _call_haiku_with_retry(system_prompt, user_prompt)

    # Wave 7 / DEC-026 — Step 5a: BGM prompt linter（style_category 必备/禁用词检查）
    #   - 通过 → 直接进入 Mureka
    #   - 不通过 → 追加 repair_hint 重调 Haiku 一次，仍不通过则放行 + log warning
    is_valid, missing_required, leaked_forbidden = _validate_bgm_prompt(
        bgm_prompt, _style_category
    )
    if not is_valid and _style_category != "generic":
        logger.warning(
            f"[MusicGenerationService] BGM linter FAIL (1st pass) "
            f"style_category={_style_category} "
            f"missing_required_count={len(missing_required)} "
            f"leaked_forbidden={leaked_forbidden}"
        )
        repair_hint = _build_repair_hint(missing_required, leaked_forbidden, _style_category)
        repaired_user_prompt = user_prompt + repair_hint
        logger.info(
            f"[MusicGenerationService] BGM linter: 追加 repair_hint ({len(repair_hint)} chars) 重调 Haiku..."
        )
        try:
            bgm_prompt_v2 = await _call_haiku_with_retry(
                system_prompt, repaired_user_prompt, max_retries=2
            )
            is_valid_v2, missing_v2, leaked_v2 = _validate_bgm_prompt(
                bgm_prompt_v2, _style_category
            )
            if is_valid_v2:
                logger.info(
                    f"[MusicGenerationService] BGM linter PASS (2nd pass after repair) "
                    f"style_category={_style_category}"
                )
                bgm_prompt = bgm_prompt_v2
            else:
                logger.warning(
                    f"[MusicGenerationService] BGM linter FAIL (2nd pass) "
                    f"missing={missing_v2[:5]} leaked={leaked_v2} — "
                    f"fallback 使用第 1 次输出（不阻塞 BGM 生成）"
                )
        except Exception as _repair_e:
            logger.warning(
                f"[MusicGenerationService] BGM linter 修复调用失败（非阻塞）: {_repair_e} — "
                f"fallback 使用第 1 次输出"
            )
    elif is_valid:
        logger.info(
            f"[MusicGenerationService] BGM linter PASS (1st pass) "
            f"style_category={_style_category}"
        )

    # Step 5a-2: T20-45 — BGM 时长信号 linter（短片信号词 / 缺少时长框架词检测）
    # Mureka 无 duration 参数，时长完全由 prompt 语义决定。
    # "suddenly stops" / "no resolution" 等会导致 Mureka 输出 <60s 短片。
    # 检测到问题 → 追加 duration_repair_hint 重调 Haiku 一次（不通过仍放行，不阻塞 BGM 生成）
    _dur_issue, _leaked_short, _has_framework = _check_bgm_duration_signals(bgm_prompt)
    if _dur_issue:
        logger.warning(
            f"[MusicGenerationService] BGM duration linter FAIL — "
            f"leaked_short_signals={_leaked_short} has_framework_word={_has_framework} — "
            f"追加 duration_repair_hint 重调 Haiku..."
        )
        _dur_repair_hint = _build_duration_repair_hint(_leaked_short, _has_framework)
        _dur_repaired_user_prompt = user_prompt + _dur_repair_hint
        try:
            _bgm_prompt_dur = await _call_haiku_with_retry(
                system_prompt, _dur_repaired_user_prompt, max_retries=2
            )
            _dur_issue_v2, _leaked_v2, _has_fw_v2 = _check_bgm_duration_signals(_bgm_prompt_dur)
            if not _dur_issue_v2:
                logger.info(
                    "[MusicGenerationService] BGM duration linter PASS (2nd pass after repair) — "
                    f"has_framework_word={_has_fw_v2}"
                )
                bgm_prompt = _bgm_prompt_dur
            else:
                logger.warning(
                    f"[MusicGenerationService] BGM duration linter FAIL (2nd pass) "
                    f"leaked={_leaked_v2} has_framework={_has_fw_v2} — "
                    f"fallback 使用第 1 次输出（不阻塞 BGM 生成）"
                )
        except Exception as _dur_e:
            logger.warning(
                f"[MusicGenerationService] BGM duration repair 调用失败（非阻塞）: {_dur_e} — "
                f"fallback 使用第 1 次输出"
            )
    else:
        logger.info(
            f"[MusicGenerationService] BGM duration linter PASS — "
            f"has_framework_word={_has_framework} no_short_signals=True"
        )

    # Step 5b: 持久化 BGM prompt（B32，2026-05-09）
    # 写入 output_dir/bgm_prompt_chapter{chapter_id}.txt + 完整 INFO log
    user_selected_mood = (outline or {}).get("user_selected_mood") or (outline or {}).get("mood") or ""
    story_title = (outline or {}).get("title") or ""

    bgm_prompt_file = os.path.join(output_dir, f"bgm_prompt_chapter{chapter_id}.txt")
    from datetime import datetime as _dt
    _ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    _prompt_header = (
        f"# BGM Haiku Prompt — chapter {chapter_id} — meta_version: {meta_version}\n"
        f"# Generated: {_ts}\n"
        f"# User selected mood: {user_selected_mood}\n"
        f"# Story title: {story_title}\n\n"
    )
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(bgm_prompt_file, "w", encoding="utf-8") as _f:
            _f.write(_prompt_header + bgm_prompt)
        logger.info(
            "[MusicGenerationService] BGM prompt 已写入: %s (%d chars)",
            bgm_prompt_file, len(bgm_prompt),
        )
    except OSError as _e:
        logger.warning("[MusicGenerationService] BGM prompt 写入文件失败（非阻塞）: %s", _e)

    # INFO 级别打印完整 prompt 文本（便于直接从 log 复原）
    logger.info(
        "[MusicGenerationService] BGM prompt 完整文本 (%d chars):\n%s",
        len(bgm_prompt), bgm_prompt,
    )

    # 警告：prompt 超过 Mureka 1024 字符上限
    if len(bgm_prompt) > 1024:
        logger.warning(
            f"[MusicGenerationService] BGM prompt 长度 {len(bgm_prompt)} 超过 Mureka 1024 字符上限，"
            "Mureka 可能截断。"
        )

    # Step 6: 调 Mureka（含重试）
    logger.info("[MusicGenerationService] Step 6: 调 Mureka API 生成 BGM...")
    raw_mp3_path = os.path.join(output_dir, f"bgm_raw_chapter{chapter_id}.mp3")
    output_mp3_path = os.path.join(output_dir, f"bgm_chapter{chapter_id}.mp3")

    # BUG-MUREKA-BLOCK-EVENT-LOOP (Wave 6 / 2026-05-11): _call_mureka 已 async，必须 await
    mureka_result = await _call_mureka(bgm_prompt, raw_mp3_path)
    mureka_task_id = mureka_result.get("task_id", "")
    duration_ms = mureka_result.get("duration_ms", 0)

    # Step 7: FFmpeg 后处理
    target_duration_sec = TARGET_DURATION_MAP.get(story_type, DEFAULT_TARGET_DURATION_SEC)
    logger.info(
        f"[MusicGenerationService] Step 7: FFmpeg 后处理，"
        f"target={target_duration_sec}s, volume={bgm_volume}..."
    )
    qa_result = process_bgm(
        input_path=raw_mp3_path,
        output_path=output_mp3_path,
        target_duration_sec=target_duration_sec,
        volume=bgm_volume,
    )

    # Step 8: 删除临时 raw mp3
    if os.path.exists(raw_mp3_path):
        try:
            os.remove(raw_mp3_path)
            logger.info(f"[MusicGenerationService] 已删除临时文件: {raw_mp3_path}")
        except OSError as e:
            logger.warning(f"[MusicGenerationService] 删除临时文件失败（非阻塞）: {e}")

    # 积分计算（mock）
    is_first_gen = regen_count == 0
    credits_used = _calculate_credits(is_first_gen=is_first_gen, is_change_bgm=is_change_bgm)

    logger.info(
        f"[MusicGenerationService] ===== BGM 生成完成 ====="
        f" bgm_url={output_mp3_path}, meta_version={meta_version},"
        f" credits_used={credits_used}"
    )

    return {
        "success": True,
        "bgm_url": output_mp3_path,
        "meta_version": meta_version,
        "bgm_prompt": bgm_prompt,
        "mureka_task_id": mureka_task_id,
        "duration_ms": duration_ms,
        "target_duration_sec": target_duration_sec,
        "qa_result": qa_result,
        "credits_used": credits_used,
    }
