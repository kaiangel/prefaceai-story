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

from app.config import settings
from app.services.story_music_extractor import extract_story_for_music
from app.services.ffmpeg_post_processor import process_bgm

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# 路径常量
# ──────────────────────────────────────────────

# meta-prompt 文件目录（相对于项目根目录）
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")
META_PROMPT_DIR = os.path.join(
    _PROJECT_ROOT,
    "test_output", "manualtest", "sq_upgrade_ab_test", "20260304_113630", "meta_prompts"
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


def _call_haiku_with_cache(system_prompt: str, user_prompt: str) -> str:
    """
    调 Anthropic API (claude-haiku-4-5) 生成 music prompt 文本。
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
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # system prompt 使用 cache_control: ephemeral（1 小时 TTL 内重复调用节省 token）
    msg = client.messages.create(
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


def _call_haiku_with_retry(system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
    """
    带重试的 Haiku API 调用，最多重试 max_retries 次。

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        max_retries: 最大重试次数（默认 3）

    Returns:
        清理后的 music prompt 文本

    Raises:
        RuntimeError: 多次重试后仍失败
    """
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[MusicGenerationService] Haiku 调用第 {attempt} 次...")
            result = _call_haiku_with_cache(system_prompt, user_prompt)
            logger.info(f"[MusicGenerationService] Haiku 调用成功，输出 {len(result)} 字符")
            return result
        except Exception as e:
            last_error = e
            logger.warning(f"[MusicGenerationService] Haiku 第 {attempt} 次失败: {e}")
            if attempt < max_retries:
                logger.info(f"[MusicGenerationService] 等待 5s 后重试...")
                time.sleep(5)

    raise RuntimeError(
        f"[MusicGenerationService] Haiku 调用在 {max_retries} 次重试后仍失败。最后错误: {last_error}"
    )


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
    """
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=_mureka_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _mureka_get(url: str) -> dict:
    """用 urllib 发起 GET 请求到 Mureka API"""
    req = urllib.request.Request(url, headers=_mureka_headers(), method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_file(url: str, output_path: str) -> None:
    """下载 URL 内容保存到 output_path"""
    urllib.request.urlretrieve(url, output_path)


def _call_mureka(prompt: str, output_path: str) -> dict:
    """
    调 Mureka API 生成纯音乐 BGM，轮询直到 succeeded，下载 mp3 到 output_path。
    最多重试 MUREKA_MAX_RETRIES 次（含 generate 请求失败 + 轮询失败）。

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
            logger.info(f"[MusicGenerationService] Mureka 发起生成请求（第 {attempt} 次）...")
            gen_resp = _mureka_post(MUREKA_GENERATE_URL, payload)
            task_id = gen_resp.get("id", "")
            if not task_id:
                raise RuntimeError(f"Mureka generate 响应缺少 id 字段: {gen_resp}")
            logger.info(f"[MusicGenerationService] Mureka task_id={task_id}，开始轮询...")

            # Step 2: 轮询直到 succeeded / failed
            elapsed = 0
            while elapsed < MUREKA_MAX_WAIT:
                time.sleep(MUREKA_POLL_INTERVAL)
                elapsed += MUREKA_POLL_INTERVAL
                query_url = MUREKA_QUERY_URL_TPL.format(task_id=task_id)
                query_resp = _mureka_get(query_url)
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

                    # Step 3: 下载 mp3
                    logger.info(f"[MusicGenerationService] 下载 mp3 -> {output_path}")
                    _download_file(mp3_url, output_path)
                    logger.info(f"[MusicGenerationService] Mureka 完成  duration_ms={duration_ms}")
                    return {"task_id": task_id, "duration_ms": duration_ms}

                elif status in ("failed", "timeouted", "cancelled"):
                    reason = query_resp.get("failed_reason", "unknown")
                    raise RuntimeError(f"Mureka 任务失败 status={status} reason={reason}")

                # 其余 status（preparing / queued / running / reviewing）继续轮询

            raise RuntimeError(f"Mureka 任务超时（>{MUREKA_MAX_WAIT}s），task_id={task_id}")

        except (urllib.error.URLError, RuntimeError, Exception) as e:
            last_error = e
            logger.warning(f"[MusicGenerationService] Mureka 第 {attempt} 次失败: {e}")
            if attempt < MUREKA_MAX_RETRIES:
                logger.info(f"[MusicGenerationService] 等待 10s 后重试...")
                time.sleep(10)

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

def generate_bgm_for_chapter(
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
) -> dict:
    """
    为单个 chapter 生成 BGM，完整整合 Haiku + Mureka + FFmpeg 后处理。

    Flow：
      1. extract_story_for_music() → 15 字段 story_data
      2. _select_meta_version(regen_count) → meta_version
      3. _load_meta_prompt(meta_version) → (system_prompt, user_prompt_template)
      4. _fill_placeholders(user_prompt_template, story_data) → user_prompt
      5. _call_haiku_with_retry(system_prompt, user_prompt) → bgm_prompt（带重试）
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
    story_data = extract_story_for_music(
        outline=outline,
        screenplay=screenplay,
        visual_style_hint=visual_style_hint,
        max_scenes=6,
    )
    logger.info(f"[MusicGenerationService] story_data 提取完成，story_title={story_data.get('story_title', 'N/A')}")

    # Step 2: 选择 meta_version
    meta_version = _select_meta_version(regen_count)
    logger.info(f"[MusicGenerationService] Step 2: meta_version={meta_version} (regen_count={regen_count})")

    # Step 3: 加载 meta-prompt
    logger.info(f"[MusicGenerationService] Step 3: 加载 meta-prompt ({meta_version})...")
    system_prompt, user_prompt_template = _load_meta_prompt(meta_version)

    # Step 4: 填充占位符
    logger.info("[MusicGenerationService] Step 4: 填充 user prompt 占位符...")
    user_prompt = _fill_placeholders(user_prompt_template, story_data)

    # Step 5: 调 Haiku（含重试）
    logger.info("[MusicGenerationService] Step 5: 调 Haiku 4.5 生成 BGM prompt...")
    bgm_prompt = _call_haiku_with_retry(system_prompt, user_prompt)

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

    mureka_result = _call_mureka(bgm_prompt, raw_mp3_path)
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
