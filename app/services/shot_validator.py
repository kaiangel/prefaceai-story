"""
T17+T28: Shot 后置视觉验证服务

使用 Haiku 4.5 对生成的 shot 图片进行视觉质检：
1. 角色数量是否匹配预期 (T20-6 v2: universal skip 智能判断)
2. ~~是否存在重复对话气泡~~ (T20-6 v2: 已禁用 — false positive 太多, B36 本就是 warning mode)
3. 关键道具是否存在（T28: 升级 D3, 2026-05-12）

验证不通过时上层 pipeline 会 retry 生成。

═════════════════════════════════════════════════════════════════════════════
D3 升级（BUG-T13-T17-VALIDATOR-FALLBACK 修复，2026-05-12）
═════════════════════════════════════════════════════════════════════════════

问题: test13 Shot 6 验证失败 — `composition.foreground/background` 是 LLM 写的
完整构图描述句（90-366 字符，如 "blurred edge of a monitor screen corner in the
extreme near foreground, casting a cold blue-white glow"），被 pipeline_orchestrator
当作 key_props 字符串原样喂给 Haiku 做"是否存在"匹配，Haiku 找不到字符串完整对应
的对象 → false → 触发 prop_missing fail。

实测: 18 shots 中有 2 shots 受影响（Shot 6 全失 + Shot 15 半失，11% 误判率）。

D3 修复策略（3 层防御）:
1. **D3-A 净化层**: 收到 key_props 后，对每个 prop 字符串做净化提取
   - 长描述句（>40 chars）→ 提取 1-3 个核心名词短语作为"探针"
   - 简短道具名（≤40 chars）→ 直接使用
2. **D3-B Prompt 层**: 升级 props 检测 prompt 为 LENIENT 模式
   - 明确告诉 Haiku："长描述含多对象时，AT LEAST ONE 可见即算 found"
   - 加 SELF-CHECK: "找不到字符串完整匹配但语义对应的元素也算 found"
3. **D3-C 阈值层**: 把 missing > 50% 改为更宽松的 fail 条件
   - 保留 T28 拦截真正灾难（全部 props 都丢）
   - 单条/部分缺失只 log 不 fail

═════════════════════════════════════════════════════════════════════════════
T20-6 v2 升级（2026-05-18，ShotValidator universal 缺陷修复）
═════════════════════════════════════════════════════════════════════════════

问题（test18 实证）:
- Shot 5/13 报"角色数量不匹配预期2实际0" — 但这些是 B51 fallback 或 wide shot,
  prompt 明确写"No character interaction" → Seedream 故意不画人, validator 不该报 FAIL
- Shot 14 报"检测到重复对话气泡" — 实际只 1 个 thought bubble, Founder 验收看图无重复
  → vision LLM false positive

修复策略 (universal, 不 hardcode 任何故事类型):
1. **universal skip 智能判断**: 对以下 shot 跳过角色数量检查 (universal helper):
   - shot._is_fallback = True (B51 fallback shots)
   - shot.shot_type 含 "wide" / "establishing" / "environmental" (本就允许纯环境)
   - shot.image_prompt 明确含 "No character" / "no character interaction" / "Pure environmental" 等指令
   - shot.characters_in_scene 为空 (作者意图无角色)
2. **关闭 has_duplicate_bubbles 检测** (方案 A 推荐):
   - vision prompt 删除 question 2 (duplicate bubbles 不再询问)
   - validate_shot 中删除"检测到重复对话气泡" reason
   - 理由: B36 本就是 warning mode, false positive 比 true positive 多, 误导
3. **向后兼容**: validate_shot 函数签名加 `shot: Optional[dict] = None` 参数,
   旧调用 (不传 shot) 行为不变 (skip 检查不触发, 走原 expected_count 严格检查)

调用方升级 (需 Backend 跟进, AI-ML 范围外):
- pipeline_orchestrator.py L1285 `validate_shot(...)` 调用加 `shot=shot` 参数
- 加了之后 universal skip 才真正生效
- 不加也不破坏现有行为 (因为参数有默认值 None)

═════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import json
import base64
import io
import random
import re
import logging
from typing import Optional, List
from PIL import Image

logger = logging.getLogger("xuhua")

# RISK-T18-H: ShotValidator 跳过计数器（API 报错时 fail-open 但不真验证）
# 追踪跳过率，方便 PM/DevOps 监控验证失效程度
validator_skipped_count: int = 0

# RISK-T20-14 (2026-05-19): Anthropic 429 / 529 退避重试常量
# 之前 ShotValidator 遇到 Anthropic 529 Overloaded 直接 fail-open（test17 v2 实测 18/18 全 fail-open），
# B51 fallback 形同虚设。现加退避重试机制（类似 Seedream SEEDREAM_HTTP_RETRIES=3）：
#   - 退避阶梯: 2 / 8 / 30 秒
#   - jitter: ±30% (防止多 shot 并行验证时 retry storm)
#   - 仅对 429 (rate_limit) / 529 (overloaded) / 503 (service_unavailable) 退避
#   - 其他错误 (400/401/超大图等) 直接 fail-open（不无意义重试）
#   - 最多 3 次重试 (4 次总尝试), 仍失败才走 fail-open
SHOT_VALIDATOR_RETRY_DELAYS_SEC: tuple[int, ...] = (2, 8, 30)
SHOT_VALIDATOR_RETRY_JITTER_RATIO: float = 0.30
SHOT_VALIDATOR_RETRYABLE_STATUS_CODES: tuple[int, ...] = (429, 529, 503)


def _compress_for_claude(image_bytes: bytes, max_bytes: int = 3_500_000) -> tuple[bytes, str]:
    """压缩到 < 3.5 MB binary（base64 膨胀 ~33% 后仍 < 4.7 MB，安全低于 Anthropic 5 MB 限制）。

    Wave 14 RISK-T19-7 修复：
    - 旧 target 4.5 MB → base64 后 ~6 MB，仍超 Anthropic 5 MB base64 limit → IMAGE_TOO_LARGE_SKIPPED
    - 新 target 3.5 MB binary → base64 后 ~4.65 MB，安全
    - 新策略：resize 优先（大图减像素数比 quality 压缩更高效），再 quality 微调
    - 增强 logging：打印压缩前后 size + ratio + 分辨率变化

    Returns:
        (compressed_bytes, media_type) — media_type 可能从 image/png 变为 image/jpeg
    """
    original_size = len(image_bytes)
    if original_size <= max_bytes:
        return image_bytes, "image/png"

    img = Image.open(io.BytesIO(image_bytes))
    # 转 RGB（JPEG 不支持 RGBA/LA）
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")

    orig_w, orig_h = img.size
    logger.info(
        f"[ShotValidator] 图片压缩开始: {original_size / 1_048_576:.2f} MB "
        f"({orig_w}x{orig_h}) → target < {max_bytes / 1_048_576:.1f} MB binary "
        f"(base64 后 < {max_bytes * 1.34 / 1_048_576:.1f} MB)"
    )

    # 策略 A: resize 优先（减少像素数，对高分辨率大图最有效）+ quality 微调
    # 对 1664x2218 → 1280x1707 这类 Seedream 输出图效果最好
    for scale in [0.75, 0.60, 0.50, 0.40]:
        new_size = (int(orig_w * scale), int(orig_h * scale))
        img2 = img.resize(new_size, Image.LANCZOS)
        for quality in [80, 65]:
            buf = io.BytesIO()
            img2.save(buf, format="JPEG", quality=quality, optimize=True)
            data = buf.getvalue()
            ratio = len(data) / original_size
            if len(data) <= max_bytes:
                logger.info(
                    f"[ShotValidator] 压缩完成: {original_size / 1_048_576:.2f} MB → "
                    f"{len(data) / 1_048_576:.2f} MB "
                    f"(scale={scale:.2f}, quality={quality}, ratio={ratio:.1%}, "
                    f"size={new_size[0]}x{new_size[1]})"
                )
                return data, "image/jpeg"

    # 策略 B: 极端情况兜底（极高分辨率图）
    for scale in [0.30, 0.25]:
        new_size = (int(orig_w * scale), int(orig_h * scale))
        img2 = img.resize(new_size, Image.LANCZOS)
        buf = io.BytesIO()
        img2.save(buf, format="JPEG", quality=55, optimize=True)
        data = buf.getvalue()
        ratio = len(data) / original_size
        if len(data) <= max_bytes:
            logger.warning(
                f"[ShotValidator] 极端压缩（scale={scale:.2f}）: "
                f"{original_size / 1_048_576:.2f} MB → {len(data) / 1_048_576:.2f} MB "
                f"(ratio={ratio:.1%}, size={new_size[0]}x{new_size[1]})"
            )
            return data, "image/jpeg"

    # 最坏情况：返回当前最低分辨率版（不应触达此分支）
    logger.error(
        f"[ShotValidator] ❌ 无法压缩到 {max_bytes / 1_048_576:.1f} MB 以内！"
        f"最终大小: {len(data) / 1_048_576:.2f} MB — 将原样返回，可能触发 API 限制"
    )
    return data, "image/jpeg"  # 最坏情况返回最低分辨率版

try:
    import anthropic
except ImportError:
    anthropic = None


HAIKU_MODEL = "claude-haiku-4-5-20251001"

# T20-47 (2026-05-20): ShotValidator 主模型升级为 Sonnet 4.6，Haiku 4.5 为降级备用
# 背景: test20 Anthropic 区域性过载, ShotValidator 原用 Haiku, 27 shot 中 13 个 4/4 retry 全 529
# → fail-open (skipped_count=13, 48% shot 未验证).
# 修复:
#   1. 主模型升级为 Sonnet 4.6 (更好的视觉理解质量, 尤其 anatomy 检测)
#   2. Sonnet 4.6 全 4 次 529 → 降级切 Haiku 4.5 retry 4 次 (Haiku throughput 更高, 较少过载)
#   3. Haiku 也全 fail → fail-open + log reason=SONNET_AND_HAIKU_OVERLOADED
#   4. fail-open 率 > 30% → ERROR 级日志告警 (DevOps 监控)
SONNET_MODEL = "claude-sonnet-4-6"  # T20-50-fix-round3: 去掉不存在的 -20251101 后缀 (404 NotFoundError)

# fail-open 率告警阈值: 当此 run 内 fail-open 占比 > 30% 时记 ERROR
FAIL_OPEN_RATE_ALERT_THRESHOLD = 0.30
# 追踪本 run 总 shot 验证数 (与 validator_skipped_count 一起算 fail-open 率)
validator_total_count: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# RISK-T20-14 (2026-05-19): Anthropic 429 / 529 退避重试 helper
# ─────────────────────────────────────────────────────────────────────────────

def _is_retryable_anthropic_error(exc: Exception) -> tuple[bool, int | None]:
    """判断 Anthropic 异常是否值得退避重试 (429 / 529 / 503).

    Returns:
        (retryable, status_code): retryable=True 表示应该退避 + 重试,
                                  status_code 是异常 HTTP 状态码 (None 表示非 HTTP 异常)
    """
    # 优先匹配 status_code 属性 (APIStatusError 子类: RateLimitError 429 /
    # OverloadedError 529 / ServiceUnavailableError 503 / InternalServerError 500)
    status_code = getattr(exc, "status_code", None)
    if status_code is None:
        # 兜底: 从异常 message 提取 (旧版 SDK 或 generic APIError)
        msg = str(exc).lower()
        for code in SHOT_VALIDATOR_RETRYABLE_STATUS_CODES:
            if f"{code}" in msg and (
                "overload" in msg or "rate" in msg or "unavailable" in msg
            ):
                status_code = code
                break
    if status_code in SHOT_VALIDATOR_RETRYABLE_STATUS_CODES:
        return True, status_code
    # 文本兜底: "overloaded" / "rate limit" 字样 → retryable
    msg_lower = str(exc).lower()
    if "overloaded" in msg_lower or "rate_limit" in msg_lower or "rate limit" in msg_lower:
        return True, status_code
    return False, status_code


async def _call_anthropic_with_retry(
    client,
    *,
    model: str,
    max_tokens: int,
    temperature: float,
    messages: list,
    shot_id_for_log: str = "?",
):
    """对 Anthropic 调用加 429/529/503 退避重试 (RISK-T20-14).

    设计:
        - 总尝试次数 = len(SHOT_VALIDATOR_RETRY_DELAYS_SEC) + 1 = 4 次 (3 次重试)
        - 仅对 429 / 529 / 503 + overloaded/rate-limit 文本异常退避
        - 其他异常 (400/401/超大图/网络断) 直接 raise 不重试
        - 每次重试 sleep delay + jitter (±30%)
        - 退避期间 log WARNING; 最终失败 log ERROR (让 PM/DevOps 在日志区分)

    Returns:
        Anthropic response object (成功)

    Raises:
        最后一次的异常 (失败时由调用方走 fail-open 路径)
    """
    last_exc: Exception | None = None
    total_attempts = len(SHOT_VALIDATOR_RETRY_DELAYS_SEC) + 1  # 4
    for attempt in range(1, total_attempts + 1):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            if attempt > 1:
                logger.info(
                    f"[ShotValidator] Shot {shot_id_for_log}: Anthropic 调用 attempt "
                    f"{attempt}/{total_attempts} 重试后成功 (T20-14)"
                )
            return response
        except Exception as exc:
            last_exc = exc
            retryable, status_code = _is_retryable_anthropic_error(exc)
            if not retryable or attempt >= total_attempts:
                # 不可重试 / 已达上限 → 让调用方走 fail-open
                if attempt >= total_attempts and retryable:
                    logger.error(
                        f"[ShotValidator] Shot {shot_id_for_log}: Anthropic 调用 "
                        f"{total_attempts} 次全部失败 (T20-14), 最后错误 "
                        f"status={status_code} {type(exc).__name__}: {str(exc)[:200]}"
                    )
                raise
            # 可重试: 退避 + jitter
            delay_idx = min(attempt - 1, len(SHOT_VALIDATOR_RETRY_DELAYS_SEC) - 1)
            base_delay = SHOT_VALIDATOR_RETRY_DELAYS_SEC[delay_idx]
            jitter = random.uniform(
                -base_delay * SHOT_VALIDATOR_RETRY_JITTER_RATIO,
                base_delay * SHOT_VALIDATOR_RETRY_JITTER_RATIO,
            )
            delay = max(1.0, base_delay + jitter)
            logger.warning(
                f"[ShotValidator] Shot {shot_id_for_log}: Anthropic {status_code} "
                f"(attempt {attempt}/{total_attempts}), sleep {delay:.1f}s 后重试 (T20-14)"
            )
            await asyncio.sleep(delay)
    # 理论不可达 (for 循环要么 return 要么 raise) — 防御性兜底
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("_call_anthropic_with_retry: unreachable code")


async def _call_sonnet_with_haiku_fallback(
    client,
    *,
    max_tokens: int,
    temperature: float,
    messages: list,
    shot_id_for_log: str = "?",
) -> tuple[object, str]:
    """T20-47 (2026-05-20): Sonnet 4.6 主模型 + Haiku 4.5 降级备用.

    设计:
        Phase 1: 尝试 Sonnet 4.6 (质量更好, 尤其 anatomy 检测)
            - 4 次总尝试 (同原 T20-14 退避机制)
            - 遇 429/529/503 退避重试
            - 4 次全失 (retryable) → 进 Phase 2 Haiku 降级
            - 非 retryable 错误 (400/401/超大图) → 直接 raise (不进 Haiku)
        Phase 2: 切 Haiku 4.5 (throughput 更高, 较少过载)
            - 同样 4 次总尝试 + 退避
            - 若成功 log INFO 标记 "HAIKU_FALLBACK"
            - 全失 → raise 最后异常 (调用方走 fail-open + SONNET_AND_HAIKU_OVERLOADED reason)

    Returns:
        (response, model_used): model_used 是 SONNET_MODEL 或 HAIKU_MODEL (供日志)

    Raises:
        最后一次的异常 (调用方走 fail-open)
    """
    # Phase 1: Sonnet 4.6
    sonnet_last_exc: Exception | None = None
    try:
        response = await _call_anthropic_with_retry(
            client,
            model=SONNET_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
            shot_id_for_log=shot_id_for_log,
        )
        return response, SONNET_MODEL
    except Exception as exc:
        sonnet_last_exc = exc
        retryable, status_code = _is_retryable_anthropic_error(exc)
        if not retryable:
            # 非过载错误 (400/401/超大图等) → 不进 Haiku, 直接 raise
            logger.warning(
                f"[ShotValidator] Shot {shot_id_for_log}: Sonnet 4.6 非 retryable 错误 "
                f"({type(exc).__name__} status={status_code}), 不降级 Haiku (T20-47)"
            )
            raise
        # retryable 上限失败 → 降级 Haiku
        logger.warning(
            f"[ShotValidator] Shot {shot_id_for_log}: Sonnet 4.6 全部 {len(SHOT_VALIDATOR_RETRY_DELAYS_SEC) + 1} 次 "
            f"529/429 失败 → 降级切 Haiku 4.5 (T20-47)"
        )

    # Phase 2: Haiku 4.5 降级
    try:
        response = await _call_anthropic_with_retry(
            client,
            model=HAIKU_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
            shot_id_for_log=shot_id_for_log,
        )
        logger.info(
            f"[ShotValidator] Shot {shot_id_for_log}: [T20-47] Haiku 4.5 FALLBACK 验证成功 "
            f"(Sonnet 4.6 过载)"
        )
        return response, HAIKU_MODEL
    except Exception as haiku_exc:
        # 两个模型都 fail → 调用方走 fail-open + SONNET_AND_HAIKU_OVERLOADED
        logger.error(
            f"[ShotValidator] Shot {shot_id_for_log}: [T20-47] Sonnet 4.6 + Haiku 4.5 "
            f"全部失败 (SONNET_AND_HAIKU_OVERLOADED), 走 fail-open. "
            f"Sonnet exc: {str(sonnet_last_exc)[:100]}; "
            f"Haiku exc: {str(haiku_exc)[:100]}"
        )
        raise haiku_exc  # raise Haiku 最后异常，调用方捕获后记 SONNET_AND_HAIKU_OVERLOADED


# D3-A 净化辅助：把长构图描述截断为可读的 probe（防 prompt 膨胀 + 提高可视化日志可读性）
# 注意：净化不影响 Haiku 的语义匹配（已通过 D3-B prompt 升级让 Haiku 做 lenient match），
# 这里截断只是让传给 Haiku 的 probe 字符串更紧凑，不破坏语义。
PROP_PROBE_MAX_CHARS = 80  # 单条 probe 最大字符；超过则截断 + 省略号
PROP_LONG_DESC_THRESHOLD = 40  # 超过此长度视为"长描述句"（仅用于日志区分，不影响行为）

# D3-A 描述句中常见的"非道具修饰词"，用于截断时尽量保留前置核心名词
_DESC_SPLIT_HINTS = re.compile(
    r"\s+(?:in the |on the |at the |from the |with |that |which |"
    r"casting |showing |reflecting |extending |stretching |receding |"
    r"leaning |partially |slightly |faintly |dimly |barely )",
    flags=re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# T20-6 v2 (2026-05-18): universal skip 智能判断 (角色数量检查)
# ─────────────────────────────────────────────────────────────────────────────
# 哪些 shot 不该被强制检查角色数量? (universal, 不 hardcode 任何故事类型)
#
# 1. _is_fallback = True 的 B51 fallback shot
#    → fallback prompt 即使改进后仍可能强调环境/纯环境镜头
# 2. shot_type 含 "wide" / "establishing" / "environmental" 的镜头
#    → 这些景别本来就允许纯环境无人
# 3. characters_in_scene 为空 (作者意图就是无人镜头)
# 4. image_prompt 明确写"No characters" / "no character interaction" / "Pure environmental" 等指令
#    → Stage 4 LLM 已显式声明无角色, validator 不该强检
#
# 该 helper 是 pure function, 可独立测试, 不需要 Haiku 调用.

# universal skip 关键词 (image_prompt 检查), 全小写, 用 in 判断
_PROMPT_NO_CHARACTER_HINTS = (
    "no characters",
    "no character interaction",
    "no specific character interaction",
    "environmental composition",
    "pure environmental",
    "pure architectural",
    "empty scene",
    "no human figure",
    "no people visible",
    "no people present",
    "no person visible",
    "no figures visible",
    "without characters",
    "without any characters",
)

# universal skip shot_type 关键词
_SHOT_TYPE_ENVIRONMENTAL_KEYWORDS = (
    "wide",          # wide_shot, extreme_wide_shot, medium_wide_shot
    "establishing",  # establishing_shot
    "environmental",  # 显式环境镜头
    "insert",        # insert shots 一般不强检角色
    "cutaway",       # cutaway 也是环境/道具特写
    "landscape",     # 通用 landscape shot
)


def should_skip_character_count_check(shot: Optional[dict]) -> tuple[bool, str]:
    """T20-6 v2 (2026-05-18): 判断是否应跳过角色数量检查.

    universal 判断规则 (不 hardcode 任何故事类型):
    - shot is None / 不是 dict → 不跳过 (向后兼容旧调用)
    - shot._is_fallback = True → 跳过 (B51 fallback)
    - shot.shot_type 含 wide/establishing/environmental/insert/cutaway/landscape → 跳过
    - shot.characters_in_scene 为空 → 跳过 (作者意图)
    - shot.image_prompt 含 "No character" 等指令 → 跳过 (LLM 显式声明)

    Args:
        shot: shot dict (来自 Stage 4 storyboard), 含 _is_fallback / shot_type /
              image_prompt / characters_in_scene 等字段

    Returns:
        (should_skip, reason): should_skip=True 跳过检查, reason 是日志原因
    """
    if not shot or not isinstance(shot, dict):
        return False, ""

    # 规则 1: B51 fallback shot
    if shot.get("_is_fallback") is True:
        return True, "fallback_shot"

    # 规则 2: shot_type 含 wide/establishing/environmental/insert/cutaway
    shot_type = (shot.get("shot_type") or "").lower()
    # 也检查 camera.shot_size (Stage 4 输出在这里)
    camera = shot.get("camera") or {}
    if isinstance(camera, dict):
        shot_size = (camera.get("shot_size") or "").lower()
        shot_type_check = f"{shot_type} {shot_size}"
    else:
        shot_type_check = shot_type
    for kw in _SHOT_TYPE_ENVIRONMENTAL_KEYWORDS:
        if kw in shot_type_check:
            return True, f"environmental_shot_type:{kw}"

    # 规则 3: characters_in_scene 为空 (Stage 4 LLM 明确无角色)
    chars = shot.get("characters_in_scene")
    if isinstance(chars, list) and len(chars) == 0:
        return True, "empty_characters_in_scene"

    # 规则 4: image_prompt 明确含 "No character" 等指令
    prompt = (shot.get("image_prompt") or "").lower()
    for hint in _PROMPT_NO_CHARACTER_HINTS:
        if hint in prompt:
            return True, f"prompt_hint:{hint[:30]}"

    return False, ""


def _sanitize_prop_probe(raw: str) -> str:
    """把 LLM 生成的长构图描述净化为紧凑 probe 字符串。

    策略（按优先级）：
    1. 去首尾空白
    2. 如果 ≤ PROP_PROBE_MAX_CHARS → 原样返回
    3. 尝试在第一个"非道具修饰词"前截断（保留核心名词部分）
    4. 否则硬截断到 PROP_PROBE_MAX_CHARS - 3 + "..."

    注意：这只影响传给 Haiku 的 probe 字符串显示长度，Haiku 已被 D3-B prompt 指示做语义匹配，
    截断不会损害 lenient 匹配。

    Args:
        raw: LLM 生成的原始字段值（如 composition.foreground）

    Returns:
        净化后的 probe 字符串（≤ PROP_PROBE_MAX_CHARS）
    """
    s = (raw or "").strip()
    if not s:
        return s
    if len(s) <= PROP_PROBE_MAX_CHARS:
        return s

    # 尝试在第一个修饰词位置截断
    match = _DESC_SPLIT_HINTS.search(s)
    if match and match.start() <= PROP_PROBE_MAX_CHARS:
        truncated = s[: match.start()].strip().rstrip(",;.")
        if len(truncated) >= 4:  # 防止截得太短
            return truncated

    # 否则硬截断
    return s[: PROP_PROBE_MAX_CHARS - 3].rstrip(" ,;.") + "..."

VALIDATION_PROMPT_BASE = """Analyze this comic panel image precisely:

1. How many distinct human characters are visible in this image who appear to be NAMED/FEATURED subjects of the scene? Count carefully — include partially visible characters (e.g., only face or upper body shown) who are positioned as scene subjects with distinct, deliberate clothing/appearance. Do NOT count: animals, objects, decorative background figures, unnamed bystanders, passersby, crowd members, or ambient human figures who are clearly NOT the focus of the scene. FOCUS on characters with intentional styling who are central to the composition.

2. (RESERVED — duplicate bubble detection removed in T20-6 v2; field still included in response for backward compatibility, always report has_duplicate_bubbles=false.)

3. ANATOMY CHECK (CRITICAL — image generation models like Stable Diffusion / Seedream / NB2 frequently produce extra limbs/hands/faces; this is the highest-priority bug to detect).

   For EACH human character in the image, count their anatomical parts and report any SEVERE deviation:
   - hands_count: how many hands does this character have? (Normal: 2 — humans have 2 hands. Flag SEVERE if 3+)
   - arms_count: how many arms? (Normal: 2. Flag SEVERE if 3+)
   - legs_count: how many legs? (Normal: 2. Flag SEVERE if 3+)
   - feet_count: how many feet visible if framing shows lower body? (Normal: 2)
   - faces_count: how many distinct faces on this single character body? (Normal: 1. Flag SEVERE if 2+ faces share one body)
   - finger_anomaly: are fingers count clearly wrong (e.g., 6+ fingers on one hand, or 2 fingers)? Flag SEVERE if grossly wrong.
   - extra_limbs_floating: are there hands/arms/limbs that don't connect to any visible body? Flag SEVERE.

   Also check:
   a) PHYSICS: people or objects defying gravity without any support or fantasy context, body poses that are physically impossible for a human skeleton (NOT severe unless extremely obvious)
   b) SPATIAL: major scale inconsistencies (e.g., an adult rendered the same height as a small child) — only flag if extreme

   Severity classification:
   - "severe" = clear image generation failure that any viewer would notice (3+ hands, third arm growing from torso, two faces on one head, floating disembodied limb, 6+ fingers on one hand)
   - "mild" = something looks slightly off but could be artistic choice or borderline (e.g., hand at unusual angle, finger partially hidden) — do NOT flag mild as severe
   - "none" = anatomy is correct

   CRITICAL — Do NOT flag these as anatomy issues (they are intentional artistic choices):
   - Stylized proportions: anime large eyes, cartoon oversized heads, pixel art blocky shapes, chibi proportions
   - Artistic simplification: ink-wash minimalist limbs (where hand may be a brush stroke), watercolor soft/blurred edges, oil painting rough brushwork that obscures fingers
   - Intentional surreal or fantasy elements: dream sequences, magical floating, supernatural multi-armed deities (when the story is mythological/fantasy)
   - Exaggerated expressions or dynamic action poses common in manga/comic art (motion blur causing apparent extra limbs is NOT severe)
   - Hands/limbs partially out of frame or behind objects (occlusion is NOT extra limbs)

   Only mark severity="severe" when the bug is unambiguous and would clearly look broken to any viewer."""

VALIDATION_PROMPT_PROPS = """
4. PROP VISIBILITY CHECK (LENIENT semantic matching, NOT strict string matching).

   For each of the following prop probes, determine whether the IMAGE CONTAINS A VISIBLE ELEMENT
   that semantically corresponds to the probe. Mark `true` (found) liberally:

   - If the probe is a SHORT object name ("phone", "monitor", "folder", "letter"): mark true if
     ANY clearly recognizable instance of that object class is visible anywhere in the frame.
   - If the probe is a LONG descriptive phrase that mentions MULTIPLE objects/elements
     (e.g. "the nurse station counter extending right, a colleague leaning in, the dark window
     behind"): mark true if AT LEAST ONE of the mentioned elements is visible. You do NOT need
     to find every element to mark it true.
   - If the probe describes spatial framing ("blurred edge of X in the foreground", "the
     background showing Y"): mark true if X or Y is recognizably present, EVEN IF the exact
     framing/blur direction differs from the probe wording.
   - If the probe describes ambient atmosphere ("cold blue-white glow", "amber streetlamp light"):
     mark true if the lighting tone matches roughly.
   - Background characters / unnamed people mentioned in a probe count as "present" if any
     additional human figure is visible (do not treat as separate from #1 character count).

   Mark `false` ONLY when the image clearly LACKS any element that could correspond to the probe.
   Be LIBERAL: when in doubt, mark true. Probes are HINTS, not strict requirements.

   List of probes to check: {props_list}"""

VALIDATION_RESPONSE_BASE = """
Respond ONLY with JSON, no other text:
{"character_count": N, "has_duplicate_bubbles": true/false, "has_visual_unnaturalness": true/false, "unnaturalness_details": "brief description or empty string", "anatomy_severity": "severe"|"mild"|"none", "anatomy_issues": ["character_label: specific issue like '3 hands' or '2 faces'"]}"""

VALIDATION_RESPONSE_WITH_PROPS = """
Respond ONLY with JSON, no other text:
{"character_count": N, "has_duplicate_bubbles": true/false, "has_visual_unnaturalness": true/false, "unnaturalness_details": "brief description or empty string", "anatomy_severity": "severe"|"mild"|"none", "anatomy_issues": ["character_label: specific issue"], "props_found": {"probe_text": true/false, ...}}

Note on props_found keys: use the EXACT probe text as the JSON key (even if long). This lets the upstream system map results 1:1 with the probe list."""


class ShotValidator:
    """Haiku 4.5 视觉验证器 — 验证 shot 图片的角色数量和气泡重复"""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if anthropic is None:
            print("[ShotValidator] ❌ anthropic 模块未安装 — 所有视觉验证将被跳过（pip install anthropic）")
            return
        try:
            # Bug 2 fix: 显式传入 api_key，避免 SDK 从 os.environ 找不到
            # pydantic-settings 从 .env 加载到 settings，但不写入 os.environ
            from app.config import settings as _settings
            _api_key = _settings.ANTHROPIC_API_KEY or None
            self.client = anthropic.AsyncAnthropic(api_key=_api_key)
            print("[ShotValidator] ✅ Haiku 4.5 视觉验证器已初始化")
        except Exception as e:
            print(f"[ShotValidator] ❌ Anthropic 客户端初始化失败: {e} — 所有视觉验证将被跳过")

    async def validate_shot(
        self,
        pil_image: Image.Image,
        expected_character_count: int,
        text_overlay_data: Optional[dict] = None,
        key_props: Optional[List[str]] = None,
        shot: Optional[dict] = None,  # T20-6 v2 (2026-05-18): 完整 shot dict, 用于 universal skip 智能判断
    ) -> dict:
        """
        验证单个 shot 图片

        Args:
            pil_image: 生成的 PIL 图片
            expected_character_count: 预期角色数量（来自 characters_visible）
            text_overlay_data: text_overlay 数据（保留参数, T20-6 v2 后不再用于气泡重复检测）
            key_props: T28 关键道具列表（来自 shot 的 image_prompt 中提取的道具）
            shot: (T20-6 v2) 完整 shot dict — 用于 universal skip 智能判断角色数量检查
                  None 时 (向后兼容旧调用): 走原 expected_count 严格检查 (不智能 skip)
                  传入时: 对 fallback / wide / environmental / no-character shot 跳过角色数检查
                  ⚠️ Backend 需在 pipeline_orchestrator.py 加 `shot=shot` 让本特性真正生效

        Returns:
            {
                "valid": bool,
                "actual_character_count": int,
                "has_duplicate_bubbles": bool,  # T20-6 v2: 永远 False (检测已禁用)
                "missing_props": list[str],
                "reason": str  # 不通过时的原因
            }
        """
        if not self.client:
            print("[ShotValidator] ⚠️ client=None，跳过验证（返回 valid=True）")
            return {"valid": True, "actual_character_count": -1,
                    "has_duplicate_bubbles": False, "missing_props": [],
                    "has_visual_unnaturalness": False, "unnaturalness_details": "",
                    "anatomy_severity": "none", "anatomy_issues": [],
                    "reason": "validator disabled"}

        # D3-A: 净化 key_props（防长描述句污染 Haiku 匹配）
        # 上游 pipeline_orchestrator 把 composition.foreground/background 直接当 key_props，
        # 但这两个字段在 Stage 4 LLM schema 中实际是"构图描述句"（90-366 chars），不是离散道具名。
        # 净化：长描述截前 80 chars 或在修饰词前截断，让 Haiku 看到的 probe 更紧凑且仍语义可读。
        sanitized_props: List[str] = []
        sanitization_log: List[tuple] = []  # 用于日志：[(原长, 净化后, 截断标志)]
        if key_props:
            for raw in key_props:
                cleaned = _sanitize_prop_probe(raw)
                sanitized_props.append(cleaned)
                if cleaned != raw:
                    sanitization_log.append((len(raw), len(cleaned), True))
                else:
                    sanitization_log.append((len(raw), len(cleaned), False))

        props_desc = f", key_props={sanitized_props}" if sanitized_props else ""
        print(f"[ShotValidator] 验证开始: expected_chars={expected_character_count}{props_desc}")
        if sanitization_log:
            truncated = sum(1 for _, _, t in sanitization_log if t)
            if truncated > 0:
                print(f"[ShotValidator] D3-A 净化: {truncated}/{len(sanitization_log)} probes 截断（长构图描述）")

        # T20-47: 声明 global 变量（在 try 和 except 块内都使用）
        global validator_skipped_count, validator_total_count

        try:
            # PIL Image → bytes（先保存为 PNG）
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            raw_bytes = buf.getvalue()

            # Wave 14 RISK-T19-7: 压缩到 < 3.5 MB binary（base64 后 < 4.7 MB，安全低于 Anthropic 5 MB 限制）
            # 旧 target 4.5 MB 导致 base64 后 ~6 MB 仍超限 → IMAGE_TOO_LARGE_SKIPPED → 真验证被跳过
            original_size = len(raw_bytes)
            compressed_bytes, media_type = _compress_for_claude(raw_bytes)
            compressed_size = len(compressed_bytes)
            b64_size_estimate = int(compressed_size * 1.34)
            if compressed_size < original_size:
                ratio = compressed_size / original_size
                print(
                    f"[ShotValidator] 图片压缩: {original_size / 1_048_576:.2f} MB → "
                    f"{compressed_size / 1_048_576:.2f} MB ({media_type}, "
                    f"ratio={ratio:.1%}, b64≈{b64_size_estimate / 1_048_576:.2f} MB)"
                )

            image_b64 = base64.standard_b64encode(compressed_bytes).decode("utf-8")
            # 校验 base64 实际大小（不应超 4.8 MB）
            actual_b64_size = len(image_b64)
            if actual_b64_size > 4_800_000:
                logger.warning(
                    f"[ShotValidator] ⚠️ base64 大小 {actual_b64_size / 1_048_576:.2f} MB 接近 5 MB 限制！"
                    f" compressed_binary={compressed_size / 1_048_576:.2f} MB"
                )

            # T28: 构建 prompt（根据是否有 key_props 动态调整）
            # D3-A: 用净化后的 sanitized_props 拼 prompt
            prompt_text = VALIDATION_PROMPT_BASE
            if sanitized_props:
                props_list = ", ".join(f'"{p}"' for p in sanitized_props)
                prompt_text += VALIDATION_PROMPT_PROPS.format(props_list=props_list)
                prompt_text += VALIDATION_RESPONSE_WITH_PROPS
            else:
                prompt_text += VALIDATION_RESPONSE_BASE

            # T20-47 (2026-05-20): Sonnet 4.6 主模型 + Haiku 4.5 降级备用
            # 原来: Haiku 4.5 直接调 (test20 实测 13/27 shot 因 Anthropic 过载全 529 fail-open)
            # 现在: Sonnet 4.6 (质量更好) → 529/429 → 降级 Haiku 4.5 → 仍 fail → fail-open
            # T20-14: 429/529/503 退避重试 (2/8/30s + ±30% jitter) 在 _call_sonnet_with_haiku_fallback 内
            validator_total_count += 1
            _shot_id_log = str((shot or {}).get("shot_id", "?"))
            _messages = [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,  # Bug 5 fix: 压缩后可能是 image/jpeg
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }]
            response, model_used = await _call_sonnet_with_haiku_fallback(
                self.client,
                max_tokens=512,  # T-H 256→384，B17 384→512（anatomy_issues 数组每角色一条描述）
                temperature=0.2,
                messages=_messages,
                shot_id_for_log=_shot_id_log,
            )
            if model_used == HAIKU_MODEL:
                logger.info(f"[ShotValidator] Shot {_shot_id_log}: 验证模型=Haiku (T20-47 降级)")

            # 解析 JSON 响应
            raw_text = response.content[0].text.strip()
            # 提取 JSON（应对模型可能添加的多余文字）
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(raw_text[json_start:json_end])
            else:
                print(f"[ShotValidator] ⚠️ 无法解析 Haiku 响应: {raw_text}")
                return {"valid": True, "actual_character_count": -1,
                        "has_duplicate_bubbles": False, "missing_props": [],
                        "has_visual_unnaturalness": False, "unnaturalness_details": "",
                        "anatomy_severity": "none", "anatomy_issues": [],
                        "reason": "parse error, skip"}

            actual_count = result.get("character_count", -1)
            # T20-6 v2: has_duplicate_bubbles 字段读取保留 (向后兼容), 但永远不纳入 valid 判定
            # 理由: B36 本就是 warning mode, false positive 远多于 true positive (test18 Shot 14 实证误判)
            has_dupes = result.get("has_duplicate_bubbles", False)
            has_unnaturalness = result.get("has_visual_unnaturalness", False)
            unnaturalness_details = result.get("unnaturalness_details", "")
            # B17: anatomy 检测字段（默认 fail-open: severity=none, issues=[]）
            anatomy_severity = (result.get("anatomy_severity") or "none").lower()
            anatomy_issues = result.get("anatomy_issues") or []
            # 防御性：旧 prompt 可能返 string/None 而非 list
            if not isinstance(anatomy_issues, list):
                anatomy_issues = [str(anatomy_issues)] if anatomy_issues else []

            # T-H Phase 1: 通用 unnaturalness 仅日志（误伤风险高，不纳入 valid）
            if has_unnaturalness:
                print(f"[ShotValidator] ℹ️ 自然度警告（仅日志）: {unnaturalness_details}")

            # B17 Phase 2: anatomy_severity="severe" 纳入 valid 判定
            # （mild 仍仅日志，避免误伤艺术风格化）
            if anatomy_severity == "mild":
                _issues_str = "; ".join(anatomy_issues) if anatomy_issues else ""
                print(f"[ShotValidator] ℹ️ Anatomy 轻度异常（仅日志）: {_issues_str}")

            # 判定逻辑
            reasons = []

            # T20-6 v2 (2026-05-18): universal skip 智能判断角色数量检查
            # - 对 fallback / wide / environmental / no-character shot 跳过 (避免 false positive)
            # - 旧调用 (不传 shot) 走原严格检查 (向后兼容)
            skip_char_check, skip_reason = should_skip_character_count_check(shot)

            # S1: 角色数量验证（允许 ±1 容差，因为部分遮挡/背景角色）
            if skip_char_check:
                # 跳过 — 仅日志 + 记 reason 供审计 (不影响 valid)
                print(
                    f"[ShotValidator] ℹ️ T20-6 角色数量检查已跳过 (reason={skip_reason}): "
                    f"expected={expected_character_count}, actual={actual_count}"
                )
            elif expected_character_count > 0 and actual_count >= 0:
                if abs(actual_count - expected_character_count) > 1:
                    reasons.append(
                        f"角色数量不匹配: 预期{expected_character_count}, 实际{actual_count}"
                    )

            # T20-6 v2 (2026-05-18): 关闭 has_duplicate_bubbles 检测
            # 旧版逻辑 (已移除): if has_dupes: reasons.append("检测到重复对话气泡")
            # 理由: B36 本就是 warning mode, vision LLM false positive 多 (test18 Shot 14 实证),
            #       误导用户和工程团队. 字段仍读取并返回 (backward compat), 但不再触发 retry.
            if has_dupes:
                print(
                    f"[ShotValidator] ℹ️ T20-6 has_duplicate_bubbles=True (仅日志, 已禁用作 retry 触发)"
                )

            # B17: 严重 anatomy 异常（多肢/多脸/多手）→ 触发 retry
            if anatomy_severity == "severe":
                _issues_label = "; ".join(anatomy_issues) if anatomy_issues else "未提供具体描述"
                reasons.append(f"anatomy_issue: {_issues_label}")

            # T28: 道具存在性检测（D3-C 阈值放宽）
            #
            # D3-C 升级（BUG-T13-T17-VALIDATOR-FALLBACK 修复，2026-05-12）:
            # 旧策略 "missing > 50% 即 fail" 在 LLM 把构图描述句当 prop 传入时误判率高（test13: 11%）。
            # 新策略：只在 ALL props 全部 missing 且至少有 2 props 时才 fail。
            # 单条 missing / 部分 missing → 仅日志（避免误伤；T28 是辅助检测，不应主导 retry）。
            #
            # 配合 D3-A（净化）+ D3-B（lenient prompt）三层防御，正确"灾难级"prop 缺失（如全部前后景对象都没生出来）
            # 仍能被拦截，但常规"长描述里部分元素"的误判被消除。
            missing_props: list = []
            if sanitized_props:
                props_found = result.get("props_found", {})
                # D3-A: props_found 的 key 是净化后的 probe 字符串（与 sanitized_props 一一对应）
                for cleaned_probe, original_raw in zip(sanitized_props, key_props or sanitized_props):
                    # 双键匹配：先用净化后的 key 找，找不到再用原始 raw 找（fail-open）
                    found = props_found.get(cleaned_probe, props_found.get(original_raw, True))
                    if not found:
                        # 日志用原始 raw（更可读），避免在 backend log 里看到大量截断省略号
                        missing_props.append(original_raw)

                total_probes = len(sanitized_props)
                missing_count = len(missing_props)
                # 新阈值：100% 全失 + 至少 2 probes（避免单 probe 故障升级）
                # 灾难级判定（true positive）：图片完全没生出 prompt 描述的环境，说明生成跑偏严重
                if total_probes >= 2 and missing_count == total_probes:
                    reasons.append(
                        f"key_props 全部缺失 {missing_count}/{total_probes}（灾难级生成跑偏）: "
                        f"{', '.join(p[:40] + ('...' if len(p) > 40 else '') for p in missing_props)}"
                    )
                elif missing_count > 0:
                    # 部分缺失只 log 不 fail（D3-C lenient mode）
                    _missing_short = "; ".join(
                        p[:40] + ("..." if len(p) > 40 else "") for p in missing_props
                    )
                    print(
                        f"[ShotValidator] ℹ️ T28 部分 props 缺失（仅日志，D3-C lenient）: "
                        f"{missing_count}/{total_probes} — {_missing_short}"
                    )

            valid = len(reasons) == 0
            result_dict = {
                "valid": valid,
                "actual_character_count": actual_count,
                "has_duplicate_bubbles": has_dupes,
                "missing_props": missing_props,
                "has_visual_unnaturalness": has_unnaturalness,
                "unnaturalness_details": unnaturalness_details,
                "anatomy_severity": anatomy_severity,
                "anatomy_issues": anatomy_issues,
                "reason": "; ".join(reasons) if reasons else "pass"
            }

            # T30: 完整结果日志
            status = "✅ PASS" if valid else "❌ FAIL"
            props_log = f", missing_props={missing_props}" if missing_props else ""
            anat_log = f", anatomy={anatomy_severity}" if anatomy_severity != "none" else ""
            print(f"[ShotValidator] {status}: chars={actual_count}/{expected_character_count}, dupes={has_dupes}{anat_log}{props_log}")

            return result_dict

        except Exception as e:
            # RISK-T18-H: fail-open — API 报错不阻塞 pipeline，但必须明确区分"跳过"和"通过"
            # reason="API_ERROR_SKIPPED" 而非粘贴完整 error stack（之前 reason=f"error: {e}" 造成日志混淆）
            #
            # RISK-T20-14 (2026-05-19): 区分 retryable 上限失败 vs 一次性失败
            # T20-47 (2026-05-20): 区分 Sonnet+Haiku 双失败 vs 其他错误
            #   - SONNET_AND_HAIKU_OVERLOADED: 两个模型都 529 全失 → ERROR 级告警
            #   - IMAGE_TOO_LARGE_SKIPPED: 图片超大无法发送 → WARNING
            #   - OVERLOAD_RETRY_EXHAUSTED: 单模型 3 次退避全失 (历史兼容) → ERROR
            #   - API_ERROR_SKIPPED: 其他错误 → WARNING
            validator_skipped_count += 1
            err_str = str(e)
            is_size_limit = "5 MB" in err_str or "5242880" in err_str or "exceeds" in err_str
            retryable, status_code = _is_retryable_anthropic_error(e)
            # T20-47: 检测是否为 Sonnet+Haiku 双失败 (两层 helper 都 raise 同一 Haiku 异常)
            is_dual_overload = "SONNET_AND_HAIKU_OVERLOADED" in err_str or (
                retryable and "haiku" in err_str.lower()
            )
            if is_size_limit:
                skip_reason = "IMAGE_TOO_LARGE_SKIPPED"
                log_level = logging.WARNING
            elif is_dual_overload or (retryable and "SONNET_AND_HAIKU" in err_str):
                skip_reason = "SONNET_AND_HAIKU_OVERLOADED"
                log_level = logging.ERROR
            elif retryable:
                # T20-14: 3 次退避全失败才走到这里 (helper 内已 ERROR 级日志, 这里区分 reason)
                skip_reason = f"OVERLOAD_RETRY_EXHAUSTED_{status_code or 'unknown'}"
                log_level = logging.ERROR
            else:
                skip_reason = "API_ERROR_SKIPPED"
                log_level = logging.WARNING
            logger.log(
                log_level,
                f"[ShotValidator] {('ERROR' if log_level == logging.ERROR else 'WARN')} "
                f"验证跳过（fail-open, skipped_count={validator_skipped_count}）"
                f" reason={skip_reason}: {err_str[:200]}"
            )
            print(
                f"[ShotValidator] ⚠️ 验证跳过（{skip_reason}）"
                f" skipped_total={validator_skipped_count}: {err_str[:120]}"
            )
            # T20-47: fail-open 率 > 30% 时记 ERROR 告警 (DevOps 监控 Anthropic 不稳定)
            _total = max(validator_total_count, 1)
            _fail_open_rate = validator_skipped_count / _total
            if _fail_open_rate > FAIL_OPEN_RATE_ALERT_THRESHOLD:
                logger.error(
                    f"[ShotValidator] [T20-47] ❌ fail-open 率告警: "
                    f"{validator_skipped_count}/{_total} = {_fail_open_rate:.1%} > "
                    f"{FAIL_OPEN_RATE_ALERT_THRESHOLD:.0%} 阈值 — "
                    f"Anthropic 过载严重，大量 shot 未经验证直接交付！"
                )
            return {"valid": True, "actual_character_count": -1,
                    "has_duplicate_bubbles": False, "missing_props": [],
                    "has_visual_unnaturalness": False, "unnaturalness_details": "",
                    "anatomy_severity": "none", "anatomy_issues": [],
                    "reason": skip_reason}
