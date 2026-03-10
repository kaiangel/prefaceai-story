"""Image generation service using Gemini API"""

import asyncio
import time
import base64
from io import BytesIO
from typing import Optional, List, Tuple
from enum import Enum
from PIL import Image

from google import genai
from google.genai import types

from app.config import settings
from app.prompts.storyboard_prompts import (
    translate_image_prompt_to_english,
    prepare_shot_prompt_for_generation,
    _simple_translate_prompt,
    Phase2PromptBuilder
)
from app.services.style_enforcer import StyleEnforcer


def _strip_speaker_for_native(text: str) -> str:
    """剥离说话者前缀，提取纯文字内容（用于原生文字渲染 prompt 构建）"""
    import re
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心|（[^）]*）)?[：:]\s*[「"『]?(.+?)[」"』]?$'
    match = re.match(pattern, text.strip())
    if match:
        return match.group(1)
    return text


def _extract_speaker_name(text: str) -> str:
    """从带说话者前缀的文本中提取说话者名（中文），用于气泡指向指令"""
    import re
    match = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', text.strip())
    if match:
        return match.group(1)
    return ""


def build_native_text_prompt(text_overlay: dict) -> str:
    """
    根据 text_overlay 数据构建 TEXT OVERLAY REQUIREMENT 指令块，
    用于 NB2 原生渲染中文文字（不依赖 TextOverlay 后处理）。

    参考实现: tests/test_nb2_text_test.py B组 build_text_overlay_prompt()

    Args:
        text_overlay: shot 的 text_overlay 数据字典，包含 text_type, chinese_text, speaker_position 等

    Returns:
        TEXT OVERLAY REQUIREMENT 指令块字符串，空字符串表示无需文字渲染
    """
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")
    position = text_overlay.get("speaker_position", "bottom")

    if text_type == "none" or not chinese_text:
        return ""

    blocks = []

    if text_type == "thought":
        text = chinese_text if isinstance(chinese_text, str) else chinese_text[0]
        clean = _strip_speaker_for_native(text)
        blocks.append(
            f"TEXT OVERLAY REQUIREMENT:\n"
            f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
            f"height approximately 18% of frame.\n"
            f"Display Chinese text '{clean}' in white font, centered alignment.\n"
            f"Inner monologue style: represents character's private thoughts."
        )

    elif text_type == "narration":
        text = chinese_text if isinstance(chinese_text, str) else chinese_text[0]
        clean = _strip_speaker_for_native(text)
        blocks.append(
            f"TEXT OVERLAY REQUIREMENT:\n"
            f"A semi-transparent black bar (at the {position}) spanning the full width of the image, "
            f"height approximately 18% of frame.\n"
            f"Display Chinese text '{clean}' in white font, centered alignment.\n"
            f"Narrative caption style: objective narration."
        )

    elif text_type == "dialogue":
        # TASK-PROMPT-BUBBLE: dialogue now embedded in [SCENE DESCRIPTION]
        # via build_dialogue_scene_embed(), no longer appended as TEXT OVERLAY
        return ""

    elif text_type in ["dialogue_with_thought", "narration_with_thought",
                        "narration_with_dialogue", "dialogue_with_narration"]:
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        bubble_idx = 0
        for i, item in enumerate(texts):
            # 结构化元数据格式: {"type": "dialogue|thought|narration", "text": "..."}
            if isinstance(item, dict) and "type" in item:
                sub_type = item["type"]
                txt = item.get("text", "")
            else:
                # 回退: 从文本内容推断子类型（兼容旧格式 LLM 输出）
                txt = item
                if "内心：" in txt or "内心:" in txt:
                    sub_type = "thought"
                elif txt.startswith("旁白：") or txt.startswith("「"):
                    sub_type = "narration"
                elif "：「" in txt or ":「" in txt or "：\"" in txt:
                    sub_type = "dialogue"
                else:
                    sub_type = "narration"

            clean = _strip_speaker_for_native(txt)

            if sub_type == "thought":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Inner monologue):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered."
                )
            elif sub_type == "narration":
                blocks.append(
                    f"TEXT OVERLAY REQUIREMENT ({i+1} - Narration):\n"
                    f"A semi-transparent black bar (at the bottom) spanning the full width, "
                    f"height approximately 15% of frame.\n"
                    f"Display Chinese text '{clean}' in white font, centered."
                )
            elif sub_type == "dialogue":
                # TASK-PROMPT-BUBBLE: dialogue sub-items in compound types
                # are now handled by build_dialogue_scene_embed() and embedded
                # in [SCENE DESCRIPTION]. Skip TEXT OVERLAY for dialogue.
                pass

    return "\n\n".join(blocks)


def _resolve_speaker_label(
    chinese_name: str,
    characters: list = None,
    speaker_format: str = "chinese"
) -> str:
    """
    TASK-PROMPT-BUBBLE-FOLLOWUP: 根据 speaker_format 将中文说话者名转换为指定格式。

    Args:
        chinese_name: 从台词提取的中文名（如 "顾建国"）
        characters: 角色数据列表（含 id/name/name_en）
        speaker_format: "chinese"(默认) | "english" | "char_id"

    Returns:
        转换后的说话者标签
    """
    if not chinese_name:
        return ""

    if speaker_format == "chinese" or not characters:
        return chinese_name

    # 查找角色数据
    char_data = next(
        (c for c in characters
         if c.get("name") == chinese_name or chinese_name in c.get("name", "")),
        None
    )

    if not char_data:
        # 找不到匹配角色，回退到中文名
        return chinese_name

    if speaker_format == "english":
        return char_data.get("name_en", "") or chinese_name
    elif speaker_format == "char_id":
        return char_data.get("id", "") or chinese_name

    return chinese_name


# TASK-PROMPT-BUBBLE-FOLLOWUP-R2: 语言约束映射
# 当前仅实现简体中文，未来可扩展繁体中文/英语/西班牙语/法文等
_TEXT_LANGUAGE_CONFIG = {
    "zh-CN": {
        "text_descriptor": "Simplified Chinese",
        "constraint": "All text in speech bubbles MUST be in Simplified Chinese characters only. Do NOT use Traditional Chinese characters.",
    },
    "zh-TW": {
        "text_descriptor": "Traditional Chinese",
        "constraint": "All text in speech bubbles MUST be in Traditional Chinese characters.",
    },
    "en": {
        "text_descriptor": "English",
        "constraint": "All text in speech bubbles MUST be in English.",
    },
}


def build_dialogue_scene_embed(
    text_overlay: dict,
    characters: list = None,
    speaker_format: str = "chinese",
    text_language: str = "zh-CN",
    characters_in_scene: list = None
) -> str:
    """
    TASK-PROMPT-BUBBLE: 将对话气泡指令嵌入 [SCENE DESCRIPTION]，
    而非作为 prompt 末尾的 TEXT OVERLAY REQUIREMENT。

    Founder 实测证明：NB2 用 ~30 字简单 prompt 就能完美渲染对话气泡。
    当前 ~9000 字 prompt 中对话指令被淹没（注意力权重 < 1%）。
    将对话融入场景描述，让模型将气泡视为场景构图的一部分。

    Args:
        text_overlay: shot 的 text_overlay 数据字典
        characters: 角色数据列表（用于 speaker_format 转换）
        speaker_format: "chinese"(默认) | "english" | "char_id"
        text_language: 气泡文字语言 "zh-CN"(默认简体中文) | "zh-TW" | "en" 等
        characters_in_scene: T6 — 当前 shot 可见角色 char_id 列表，
            speaker 不在列表中时跳过该 dialogue 行

    Returns:
        嵌入场景描述的对话气泡文本，空字符串表示无对话
    """
    text_type = text_overlay.get("text_type", "none")
    chinese_text = text_overlay.get("chinese_text", "")

    if not chinese_text:
        return ""

    # 获取语言配置
    lang_config = _TEXT_LANGUAGE_CONFIG.get(text_language, _TEXT_LANGUAGE_CONFIG["zh-CN"])
    text_desc = lang_config["text_descriptor"]
    lang_constraint = lang_config["constraint"]

    dialogue_lines = []

    # T6: 构建 中文名→char_id 映射，用于 speaker-visibility 校验
    _name_to_id = {}
    if characters and characters_in_scene is not None:
        for c in characters:
            char_id = c.get("id", "")
            char_name = c.get("name", "")
            if char_id and char_name:
                _name_to_id[char_name] = char_id
                # 也支持部分匹配（如 "林守正" 匹配 "林守正（老林）"）
                for name_part in [char_name]:
                    if name_part not in _name_to_id:
                        _name_to_id[name_part] = char_id

    def _is_speaker_visible(speaker_zh: str) -> bool:
        """T6: 检查说话者是否在当前 shot 可见角色列表中"""
        if characters_in_scene is None or not speaker_zh:
            return True  # 未提供列表时不做过滤
        char_id = _name_to_id.get(speaker_zh)
        if not char_id:
            # 尝试部分匹配
            for name, cid in _name_to_id.items():
                if speaker_zh in name or name in speaker_zh:
                    char_id = cid
                    break
        if not char_id:
            return True  # 找不到映射时不过滤（安全降级）
        return char_id in characters_in_scene

    def _build_bubble_line(speaker: str, clean_text: str) -> str:
        if speaker:
            return (
                f"Near {speaker}, a white speech bubble with rounded corners "
                f"displays {text_desc} text '{clean_text}' in black font."
            )
        return (
            f"A white speech bubble with rounded corners "
            f"displays {text_desc} text '{clean_text}' in black font."
        )

    if text_type == "dialogue":
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for txt in texts:
            if isinstance(txt, dict):
                txt = txt.get('text', '')
            clean = _strip_speaker_for_native(txt)
            speaker_zh = _extract_speaker_name(txt)
            # T6: speaker 不在画面中时跳过该 dialogue 行
            if not _is_speaker_visible(speaker_zh):
                print(f"    [T6] 跳过不可见 speaker dialogue: {speaker_zh}")
                continue
            speaker = _resolve_speaker_label(speaker_zh, characters, speaker_format)
            dialogue_lines.append(_build_bubble_line(speaker, clean))

    elif text_type in ["dialogue_with_thought", "narration_with_thought",
                        "narration_with_dialogue", "dialogue_with_narration"]:
        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
        for item in texts:
            if isinstance(item, dict) and "type" in item:
                sub_type = item["type"]
                txt = item.get("text", "")
            else:
                txt = item
                if "内心：" in txt or "内心:" in txt:
                    sub_type = "thought"
                elif txt.startswith("旁白：") or txt.startswith("「"):
                    sub_type = "narration"
                elif "：「" in txt or ":「" in txt or "：\"" in txt:
                    sub_type = "dialogue"
                else:
                    sub_type = "narration"

            if sub_type == "dialogue":
                clean = _strip_speaker_for_native(txt)
                speaker_zh = _extract_speaker_name(txt)
                # T6: speaker 不在画面中时跳过该 dialogue 行
                if not _is_speaker_visible(speaker_zh):
                    print(f"    [T6] 跳过不可见 speaker dialogue(compound): {speaker_zh}")
                    continue
                speaker = _resolve_speaker_label(speaker_zh, characters, speaker_format)
                dialogue_lines.append(_build_bubble_line(speaker, clean))

    if dialogue_lines:
        # 追加语言约束 + T15 气泡去重指令
        dedup_instruction = "Render each speech bubble EXACTLY ONCE at its designated position. Never duplicate any dialogue line in the image."
        return " ".join(dialogue_lines) + f" {lang_constraint} {dedup_instruction}"
    return ""


class ErrorType(Enum):
    """图像生成错误类型分类

    用于智能重试策略：
    - API_ERROR: 网络/服务问题，可直接重试
    - RATE_LIMIT: 限流，等待后重试
    - CONTENT_SAFETY: 内容被拒，需要改写prompt后重试
    - FORMAT_ERROR: 参数错误，需要修复
    - UNKNOWN: 未知错误
    """
    API_ERROR = "api_error"           # 网络/服务问题，可直接重试
    RATE_LIMIT = "rate_limit"         # 限流，等待后重试
    CONTENT_SAFETY = "content_safety" # 内容被拒，需要改写后重试
    FORMAT_ERROR = "format_error"     # 参数错误，需要修复
    UNKNOWN = "unknown"


class ImageGenerator:
    """
    图像生成服务

    支持的后端：
    1. Gemini 2.5 Flash Image - 快速生成
    2. Gemini 3 Pro Image Preview - 高质量生成（支持参考图）

    关键功能：
    1. 单图生成
    2. 批量生成（并行）
    3. 角色参考图支持（用于一致性）
    4. 自动重试和降级
    """

    # 模型配置
    FAST_MODEL = "gemini-2.5-flash-image"  # 快速模型（主用）
    NB2_MODEL = "gemini-3.1-flash-image-preview"  # Nano Banana 2（主力生图模型）

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    # 内容安全改写配置
    MAX_REWRITE_ATTEMPTS = 2  # 改写后最多重试次数

    def __init__(self):
        self.client = None
        self._prompt_rewriter = None  # 延迟初始化
        self._init_client()

    @property
    def prompt_rewriter(self):
        """延迟初始化 PromptRewriter，避免循环依赖"""
        if self._prompt_rewriter is None:
            try:
                from app.services.prompt_rewriter import PromptRewriter
                self._prompt_rewriter = PromptRewriter()
            except ImportError as e:
                print(f"[ImageGenerator] ⚠️ 无法导入 PromptRewriter: {e}")
        return self._prompt_rewriter

    def _init_client(self):
        """初始化 Gemini 客户端"""
        api_key = settings.GEMINI_API_KEY
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("Warning: GEMINI_API_KEY not set, image generation will fail")

    def _classify_error(self, response=None, exception: Exception = None) -> Tuple[ErrorType, str]:
        """分类错误类型，用于智能重试策略

        Args:
            response: Gemini API 响应对象（可能包含 prompt_feedback）
            exception: 捕获的异常对象

        Returns:
            (ErrorType, 错误描述字符串)

        检测优先级：
        1. 检查 response.parts 是否为 None（内容安全过滤的典型表现）
        2. 检查 response.prompt_feedback.block_reason
        3. 检查异常消息中的关键词
        """
        error_msg = ""

        # 1. 检查 response 中的内容安全信号
        if response is not None:
            # 1a. parts 为 None 是内容安全过滤的典型表现
            if response.parts is None:
                # 尝试获取更详细的 block_reason
                block_reason = None
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    feedback = response.prompt_feedback
                    if hasattr(feedback, 'block_reason') and feedback.block_reason:
                        block_reason = str(feedback.block_reason)

                if block_reason:
                    error_msg = f"Content safety blocked: {block_reason}"
                else:
                    error_msg = "Content safety blocked: response.parts is None (no block_reason provided)"

                print(f"    [ImageGenerator] ⚠️ 错误分类: CONTENT_SAFETY - {error_msg}")
                return ErrorType.CONTENT_SAFETY, error_msg

            # 1b. 检查是否有 candidates 且状态异常
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason'):
                        reason = str(candidate.finish_reason).upper()
                        if 'SAFETY' in reason or 'BLOCKED' in reason:
                            error_msg = f"Content safety blocked: candidate finish_reason={reason}"
                            print(f"    [ImageGenerator] ⚠️ 错误分类: CONTENT_SAFETY - {error_msg}")
                            return ErrorType.CONTENT_SAFETY, error_msg

        # 2. 检查异常消息
        if exception is not None:
            error_str = str(exception).lower()

            # 2a. 内容安全相关
            safety_keywords = ['safety', 'blocked', 'prohibited', 'harmful', 'inappropriate',
                             'content policy', 'violat', 'offensive', 'dangerous']
            if any(kw in error_str for kw in safety_keywords):
                error_msg = f"Content safety exception: {str(exception)}"
                print(f"    [ImageGenerator] ⚠️ 错误分类: CONTENT_SAFETY - {error_msg}")
                return ErrorType.CONTENT_SAFETY, error_msg

            # 2b. 限流相关
            rate_limit_keywords = ['rate limit', 'quota', '429', 'too many requests', 'resource exhausted']
            if any(kw in error_str for kw in rate_limit_keywords):
                error_msg = f"Rate limit: {str(exception)}"
                print(f"    [ImageGenerator] ⚠️ 错误分类: RATE_LIMIT - {error_msg}")
                return ErrorType.RATE_LIMIT, error_msg

            # 2c. 参数/格式错误
            format_keywords = ['invalid', 'parameter', 'argument', 'format', 'malformed', '400']
            if any(kw in error_str for kw in format_keywords):
                error_msg = f"Format error: {str(exception)}"
                print(f"    [ImageGenerator] ⚠️ 错误分类: FORMAT_ERROR - {error_msg}")
                return ErrorType.FORMAT_ERROR, error_msg

            # 2d. API/网络错误
            api_keywords = ['network', 'timeout', 'connection', '500', '502', '503', '504',
                           'internal', 'unavailable', 'service error']
            if any(kw in error_str for kw in api_keywords):
                error_msg = f"API error: {str(exception)}"
                print(f"    [ImageGenerator] ⚠️ 错误分类: API_ERROR - {error_msg}")
                return ErrorType.API_ERROR, error_msg

            # 2e. 特殊情况：'NoneType' object is not iterable - 这是 response.parts 为 None 时迭代导致
            if "'nonetype' object is not iterable" in error_str:
                error_msg = "Content safety blocked: response.parts is None (iteration failed)"
                print(f"    [ImageGenerator] ⚠️ 错误分类: CONTENT_SAFETY - {error_msg}")
                return ErrorType.CONTENT_SAFETY, error_msg

            error_msg = f"Unknown exception: {str(exception)}"
        else:
            error_msg = "Unknown error (no response or exception provided)"

        print(f"    [ImageGenerator] ⚠️ 错误分类: UNKNOWN - {error_msg}")
        return ErrorType.UNKNOWN, error_msg

    def _preprocess_reference_to_aspect_ratio(self, ref_img: Image.Image, target_ratio: str) -> Image.Image:
        """将参考图中心裁剪到目标宽高比，消除比例不匹配对生成的影响

        Args:
            ref_img: PIL Image 参考图
            target_ratio: 目标宽高比字符串，如 "9:16"

        Returns:
            裁剪后的 PIL Image（如果不需要裁剪则返回原图）
        """
        w, h = ref_img.size
        target_w_ratio, target_h_ratio = map(int, target_ratio.split(':'))
        target = target_w_ratio / target_h_ratio
        current = w / h

        if abs(current - target) < 0.01:  # 已经匹配，不裁剪
            return ref_img

        if current > target:  # 图太宽，左右裁
            new_w = int(h * target)
            left = (w - new_w) // 2
            cropped = ref_img.crop((left, 0, left + new_w, h))
            pct = round((1 - new_w / w) * 100, 1)
            print(f"    [ImageGenerator] 参考图预处理: {w}x{h} → {new_w}x{h} (裁剪宽度{pct}%)")
            return cropped
        else:  # 图太高，上下裁
            new_h = int(w / target)
            top = (h - new_h) // 2
            cropped = ref_img.crop((0, top, w, top + new_h))
            pct = round((1 - new_h / h) * 100, 1)
            print(f"    [ImageGenerator] 参考图预处理: {w}x{h} → {w}x{new_h} (裁剪高度{pct}%)")
            return cropped

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        aspect_ratio: str = "2:3",
        reference_images: Optional[List[Image.Image]] = None,
        style_preset: str = None,
        use_pro_model: bool = False,
        image_size: str = "1K",
        **kwargs
    ) -> dict:
        """
        生成单张图像

        Args:
            prompt: 图像生成提示词
            negative_prompt: 负面提示词（会合并到prompt中）
            aspect_ratio: 宽高比 (16:9, 9:16, 1:1, 4:3, 3:4 等)
            reference_images: 参考图像列表（PIL Image对象）
            style_preset: 风格预设
            use_pro_model: 是否使用NB2主力模型（默认False用Flash）
            image_size: 图像尺寸 (1K, 2K, 4K)

        Returns:
            {
                "success": True,
                "image_data": "base64编码的图像",
                "pil_image": PIL.Image对象,
                "image_format": "png",
                "width": 1920,
                "height": 1080,
                "model_used": "gemini-2.5-flash-image",
                "generation_time_seconds": 12.5
            }
        """
        if not self.client:
            return {
                "success": False,
                "error": "Gemini client not initialized. Check GEMINI_API_KEY."
            }

        # 选择模型
        # 注意：gemini-2.5-flash-image 也支持参考图，只是质量可能不如NB2
        # model = self.NB2_MODEL if (use_pro_model or reference_images) else self.FAST_MODEL
        model = self.NB2_MODEL if use_pro_model else self.FAST_MODEL  # Flash也支持参考图

        # 构建完整prompt
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f". Avoid: {negative_prompt}"

        # 构建内容
        contents = [full_prompt]
        if reference_images:
            # 添加参考图（预处理到目标宽高比）
            print(f"    [ImageGenerator] 传入 {len(reference_images)} 张参考图")
            for i, ref_img in enumerate(reference_images[:14]):  # 最多14张
                if hasattr(ref_img, 'size'):
                    print(f"      参考图 {i+1}: {ref_img.size[0]}x{ref_img.size[1]}")
                    ref_img = self._preprocess_reference_to_aspect_ratio(ref_img, aspect_ratio)
                contents.append(ref_img)
            print(f"    [ImageGenerator] contents 共 {len(contents)} 个元素 (1个prompt + {len(contents)-1}张图)")

        # 调试日志：记录Gemini请求结构
        print(f"\n    [ImageGenerator] === Gemini请求结构 ===")
        print(f"      model: {model}")
        print(f"      contents类型: [str] + [{len(contents)-1} x PIL.Image]")
        print(f"      config.response_modalities: ['IMAGE']")
        print(f"      config.aspect_ratio: {aspect_ratio}")
        print(f"      system_instruction: 无 (Gemini图像生成不使用)")
        print(f"      prompt前200字符: {full_prompt[:200]}...")
        print(f"    [ImageGenerator] ========================")

        # 配置
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        )

        start_time = time.time()
        last_error = None
        last_error_type = ErrorType.UNKNOWN

        for attempt in range(self.MAX_RETRIES):
            try:
                # 使用异步调用
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )

                # 🚨 关键修复：先检查 response.parts 是否为 None（内容安全过滤）
                if response.parts is None:
                    error_type, error_msg = self._classify_error(response=response)
                    last_error_type = error_type
                    last_error = error_msg
                    print(f"    [ImageGenerator] 尝试 {attempt + 1}/{self.MAX_RETRIES} 失败: {error_msg}")

                    # 内容安全错误不直接重试（需要改写prompt），但先完成本轮重试循环
                    if error_type == ErrorType.CONTENT_SAFETY:
                        # 直接退出重试循环，返回错误信息供上层处理（改写prompt后重试）
                        break

                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

                # 提取图像
                for part in response.parts:
                    if part.inline_data is not None:
                        # 获取图像数据 - 可能是 google-genai 的 Image 对象
                        genai_image = part.as_image()

                        # 转换为 PIL Image
                        # genai Image 对象有 _pil_image 属性或可以通过 BytesIO 转换
                        if hasattr(genai_image, '_pil_image'):
                            pil_image = genai_image._pil_image
                        elif hasattr(genai_image, 'data'):
                            # 如果有 data 属性，直接使用
                            pil_image = Image.open(BytesIO(genai_image.data))
                        else:
                            # 尝试直接使用，或通过保存/加载转换
                            try:
                                # genai Image 可能可以直接当作 PIL Image 使用
                                buffer = BytesIO()
                                genai_image.save(buffer)  # 不带 format 参数
                                buffer.seek(0)
                                pil_image = Image.open(buffer)
                            except Exception:
                                # 如果上述都失败，尝试直接使用 inline_data
                                image_bytes = base64.b64decode(part.inline_data.data)
                                pil_image = Image.open(BytesIO(image_bytes))

                        # 转换为base64
                        output_buffer = BytesIO()
                        pil_image.save(output_buffer, "PNG")
                        image_data = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

                        generation_time = time.time() - start_time

                        return {
                            "success": True,
                            "image_data": image_data,
                            "pil_image": pil_image,
                            "image_format": "png",
                            "width": pil_image.width,
                            "height": pil_image.height,
                            "model_used": model,
                            "generation_time_seconds": round(generation_time, 2)
                        }

                # 没有找到图像（response.parts非空但没有图像数据）
                last_error = "No image in response"
                last_error_type = ErrorType.UNKNOWN

            except Exception as e:
                error_type, error_msg = self._classify_error(exception=e)
                last_error_type = error_type
                last_error = error_msg
                print(f"    [ImageGenerator] 尝试 {attempt + 1}/{self.MAX_RETRIES} 失败: {error_msg}")

                # 内容安全错误不直接重试
                if error_type == ErrorType.CONTENT_SAFETY:
                    break

                # 限流错误等待更长时间
                if error_type == ErrorType.RATE_LIMIT:
                    wait_time = self.RETRY_DELAY * (attempt + 1) * 2  # 双倍等待
                    print(f"    [ImageGenerator] 限流等待 {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

        return {
            "success": False,
            "error": f"Image generation failed after {self.MAX_RETRIES} attempts: {last_error}",
            "error_type": last_error_type.value,  # 返回错误类型供上层处理
            "model_used": model,
            "generation_time_seconds": round(time.time() - start_time, 2)
        }

    async def generate_shot_image(
        self,
        shot: dict,
        reference_images: Optional[List[Image.Image]] = None,
        aspect_ratio: str = "2:3",
        use_llm_translation: bool = True,
        **kwargs
    ) -> dict:
        """
        生成单个shot的场景图片

        Phase 2.0 默认使用 NB2（Nano Banana 2, gemini-3.1-flash-image-preview）生成 shot 图。
        NB2 角色一致性 ~95%，速度快 3-5x，成本降 50%。
        generate_shot_image() 始终调用 NB2_MODEL，不经过 use_pro_model 切换。

        优先使用shot的image_prompt字段，并自动翻译为英文

        Args:
            shot: shot数据字典，包含：
                - image_prompt: LLM生成的图像描述
                - visual_description: 视觉描述
                - shot_type: 镜头类型
                - characters_in_scene: 角色列表
            reference_images: 参考图像列表（PIL Image对象）
            aspect_ratio: 宽高比
            use_llm_translation: 是否使用LLM翻译（True则异步翻译，False则使用简单字典翻译）
            use_pro_model: 已弃用参数（Phase 2.0 始终使用 NB2_MODEL）

        Returns:
            生成结果字典
        """
        # 1. 获取shot的image_prompt
        image_prompt = shot.get('image_prompt', '')

        if not image_prompt:
            # 没有image_prompt，从其他字段构建
            visual_desc = shot.get('visual_description', '')
            shot_type = shot.get('shot_type', 'medium shot')
            if visual_desc:
                image_prompt = f"{visual_desc}. Shot type: {shot_type}."

        # 2. 翻译为英文
        if use_llm_translation and self.client:
            try:
                translated_prompt = await translate_image_prompt_to_english(
                    image_prompt,
                    client=self.client
                )
                print(f"    [ImageGenerator] prompt翻译完成 (LLM)")
            except Exception as e:
                print(f"    [ImageGenerator] LLM翻译失败，使用简单翻译: {e}")
                translated_prompt = _simple_translate_prompt(image_prompt)
        else:
            translated_prompt = _simple_translate_prompt(image_prompt)
            print(f"    [ImageGenerator] prompt翻译完成 (字典)")

        # 3. 添加负面提示（如果shot有）
        negative_prompt = shot.get('negative_prompt', '')

        # 4. 调用生成
        result = await self.generate_image(
            prompt=translated_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            reference_images=reference_images,
            **kwargs
        )

        # 5. 添加额外信息
        if result.get("success"):
            result["original_prompt"] = image_prompt
            result["translated_prompt"] = translated_prompt
            result["shot_id"] = shot.get('shot_id')

        return result

    async def generate_shot_image_phase2(
        self,
        shot: dict,
        storyboard: dict,
        characters: dict,
        style_preset: str = "anime",
        reference_images: Optional[List[Image.Image]] = None,
        screenplay: Optional[dict] = None,
        aspect_ratio: str = "2:3",
        use_native_text: bool = True,
        **kwargs
    ) -> dict:
        """
        Phase 2.0 增强版Shot图像生成

        核心增强：
        1. system_instruction - 全局风格锚定
        2. character_reference_mapping - 角色-参考图映射
        3. narrative_context - 剧情上下文（情绪/剧情连续性）

        Args:
            shot: Phase 2.0 shot数据，包含camera/composition/lighting
            storyboard: 完整storyboard数据（含global_visual_direction）
            characters: 完整角色数据 {"characters": [...]}
            style_preset: 风格预设
            reference_images: 参考图像列表 (角色参考图 + 场景参考图)
            screenplay: 剧本数据（用于获取场景氛围）
            aspect_ratio: 宽高比

        Returns:
            生成结果字典（同generate_image）
        """
        if not self.client:
            return {
                "success": False,
                "error": "Gemini client not initialized. Check GEMINI_API_KEY."
            }

        # 1. 使用Phase2PromptBuilder构建prompt包
        prompt_builder = Phase2PromptBuilder(
            storyboard=storyboard,
            characters=characters,
            style_preset=style_preset
        )

        # 计算参考图数量以正确构建IMAGE编号映射
        char_direction = shot.get("character_direction", {})
        characters_in_shot = char_direction.get("characters_visible", [])
        # SQ-2: 每个角色1张参考图（智能选择 portrait 或 fullbody）
        char_refs_count = len(characters_in_shot) * 1
        # 场景参考图 = 总参考图 - 角色参考图
        total_refs = len(reference_images) if reference_images else 0
        scene_ref_count = max(0, total_refs - char_refs_count)

        prompt_package = prompt_builder.build_full_prompt(
            shot=shot,
            screenplay=screenplay,
            include_system_instruction=True,
            scene_ref_count=scene_ref_count
        )

        # 2. 提取各部分
        system_instruction = prompt_package.get("system_instruction", "")
        critical_header = prompt_package.get("critical_header", "")
        character_mapping = prompt_package.get("character_mapping", "")
        main_prompt = prompt_package.get("image_prompt", "")
        continuity_context = prompt_package.get("continuity_context", "")
        narrative_context = prompt_package.get("narrative_context", "")

        # 3. 构建完整prompt（按teststory6.4验证的结构）
        #    顺序：关键指令头 → 角色映射 → 剧情上下文 → 风格 → 连续性 → 场景描述
        full_prompt_parts = []

        # 角色一致性关键指令头（最重要！放最前面）
        if critical_header:
            full_prompt_parts.append(critical_header)

        # 角色参考图映射（含完整身份描述）
        if character_mapping:
            full_prompt_parts.append(character_mapping)

        # 剧情上下文（新增：在风格指令之前）
        if narrative_context:
            full_prompt_parts.append(narrative_context)

        # 全局风格锚定
        if system_instruction:
            full_prompt_parts.append(f"[GLOBAL STYLE DIRECTIVE]\n{system_instruction}")

        # 连续性上下文（如果有上一shot）
        if continuity_context:
            full_prompt_parts.append(f"[CONTINUITY]\n{continuity_context}")

        # TASK-PROMPT-BUBBLE: 对话气泡嵌入场景描述（而非 prompt 末尾）
        # Founder 实测: NB2 用简单 prompt (~30 字) 即可渲染完美气泡，
        # 嵌入场景描述让模型将气泡视为构图元素，获得更高注意力权重
        dialogue_embed = ""
        if use_native_text:
            text_overlay = shot.get("text_overlay", {})
            # T6: 传入 characters_in_scene 用于 speaker-visibility 校验
            chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
            dialogue_embed = build_dialogue_scene_embed(
                text_overlay,
                characters=characters.get("characters", []),
                speaker_format='english',
                text_language='zh-CN',
                characters_in_scene=chars_visible
            )

        # 主prompt（场景描述）+ 嵌入的对话气泡
        if dialogue_embed:
            full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}\n{dialogue_embed}")
            print(f"    [ImageGenerator Phase2] 对话气泡已嵌入场景描述 ({len(dialogue_embed)} chars)")
        else:
            full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")

        full_prompt = "\n\n".join(full_prompt_parts)

        # 🚨 关键：使用 StyleEnforcer 强制风格，防止风格漂移
        # StyleEnforcer 会在 prompt 最前面添加 MANDATORY STYLE 指令
        # 包括 MUST INCLUDE (photorealistic等) 和 DO NOT USE (cartoon, anime等)
        # TASK-PROMPT-BUBBLE: 禁用 quality_suffix（与 mandatory keywords 重叠冗余）
        full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset, add_quality_suffix=False)

        # color_mode 处理：覆盖 preset 的颜色设定（用于回忆/闪回等特殊效果）
        color_mode = shot.get("color_mode", "full_color")
        if color_mode == "grayscale":
            full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in GRAYSCALE, black and white. Override any color requirements from the style preset."
        elif color_mode == "sepia":
            full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in SEPIA TONE, warm brownish monochrome. Override any color requirements from the style preset."

        # NB2 原生文字渲染：将 TEXT OVERLAY REQUIREMENT 附加到 prompt 末尾
        # TASK-PROMPT-BUBBLE: dialogue 已嵌入场景描述（上方），此处只处理 thought/narration
        # 当 use_native_text=True 时，NB2 直接在图像中渲染中文文字（旁白/心理描述）
        # 当 use_native_text=False 时，不附加文字指令，由 TextOverlay 后处理叠加
        if use_native_text:
            text_overlay = shot.get("text_overlay", {})
            native_text_block = build_native_text_prompt(text_overlay)
            if native_text_block:
                full_prompt += "\n\n" + native_text_block
                print(f"    [ImageGenerator Phase2] 原生文字渲染 (thought/narration): text_type={text_overlay.get('text_type', 'none')}")

        # DEBUG: 保存shot的完整prompt用于验证
        shot_id = shot.get("shot_id", 0)
        if shot_id in [1, 2]:  # 保存Shot 1和Shot 2用于对比验证
            try:
                import os
                debug_dir = "forclaudeweb"
                os.makedirs(debug_dir, exist_ok=True)
                filename = f"phase2_shot{shot_id:02d}_prompt.txt"
                with open(f"{debug_dir}/{filename}", "w", encoding="utf-8") as f:
                    f.write(f"=== Phase 2.0 Shot {shot_id} Prompt (角色一致性增强版) ===\n\n")
                    f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"has_previous_shot_image: False (DEC-014: removed)\n\n")
                    f.write(f"=== 完整Prompt ===\n\n")
                    f.write(full_prompt)
                print(f"    [DEBUG] Shot {shot_id} prompt已保存至 {debug_dir}/{filename}")
            except Exception as e:
                print(f"    [DEBUG] 保存prompt失败: {e}")

        # 4. 构建contents (DEC-014: previous_shot_image removed)
        contents = [full_prompt]

        # 添加参考图（预处理到目标宽高比）
        if reference_images:
            print(f"    [ImageGenerator Phase2] 传入 {len(reference_images)} 张参考图")
            for i, ref_img in enumerate(reference_images[:14]):  # 最多14张
                if hasattr(ref_img, 'size'):
                    print(f"      参考图 {i+1}: {ref_img.size[0]}x{ref_img.size[1]}")
                    ref_img = self._preprocess_reference_to_aspect_ratio(ref_img, aspect_ratio)
                contents.append(ref_img)

        # 5. 调试日志
        print(f"\n    [ImageGenerator Phase2] === Gemini请求结构 ===")
        print(f"      model: {self.NB2_MODEL}")
        print(f"      style_preset: {style_preset}")
        print(f"      has_system_instruction: {bool(system_instruction)}")
        print(f"      has_continuity: False (DEC-014: removed)")
        print(f"      reference_images: {len(reference_images) if reference_images else 0}")
        print(f"      shot camera: {shot.get('camera', {}).get('shot_size', 'N/A')}")
        print(f"      prompt前300字符: {full_prompt[:300]}...")
        print(f"    [ImageGenerator Phase2] ========================\n")

        # 6. 配置
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            ),
        )

        # 7. 调用生成（始终使用NB2主力模型）
        start_time = time.time()
        last_error = None
        last_error_type = ErrorType.UNKNOWN

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.NB2_MODEL,  # Phase 2.0 始终使用NB2
                    contents=contents,
                    config=config,
                )

                # 🚨 关键修复：先检查 response.parts 是否为 None（内容安全过滤）
                if response.parts is None:
                    error_type, error_msg = self._classify_error(response=response)
                    last_error_type = error_type
                    last_error = error_msg
                    print(f"    [ImageGenerator Phase2] 尝试 {attempt + 1}/{self.MAX_RETRIES} 失败: {error_msg}")

                    # 内容安全错误不直接重试（需要改写prompt）
                    if error_type == ErrorType.CONTENT_SAFETY:
                        break

                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))
                    continue

                # 提取图像
                for part in response.parts:
                    if part.inline_data is not None:
                        genai_image = part.as_image()

                        # 转换为 PIL Image
                        if hasattr(genai_image, '_pil_image'):
                            pil_image = genai_image._pil_image
                        elif hasattr(genai_image, 'data'):
                            pil_image = Image.open(BytesIO(genai_image.data))
                        else:
                            try:
                                buffer = BytesIO()
                                genai_image.save(buffer)
                                buffer.seek(0)
                                pil_image = Image.open(buffer)
                            except Exception:
                                image_bytes = base64.b64decode(part.inline_data.data)
                                pil_image = Image.open(BytesIO(image_bytes))

                        # 转换为base64
                        output_buffer = BytesIO()
                        pil_image.save(output_buffer, "PNG")
                        image_data = base64.b64encode(output_buffer.getvalue()).decode("utf-8")

                        generation_time = time.time() - start_time

                        return {
                            "success": True,
                            "image_data": image_data,
                            "pil_image": pil_image,
                            "image_format": "png",
                            "width": pil_image.width,
                            "height": pil_image.height,
                            "model_used": self.NB2_MODEL,
                            "generation_time_seconds": round(generation_time, 2),
                            # Phase 2.0 额外信息
                            "shot_id": shot.get("shot_id"),
                            "prompt_package": prompt_package,
                            "phase2": True
                        }

                # 没有找到图像（response.parts非空但没有图像数据）
                last_error = "No image in response"
                last_error_type = ErrorType.UNKNOWN

            except Exception as e:
                error_type, error_msg = self._classify_error(exception=e)
                last_error_type = error_type
                last_error = error_msg
                print(f"    [ImageGenerator Phase2] 尝试 {attempt + 1}/{self.MAX_RETRIES} 失败: {error_msg}")

                # 内容安全错误不直接重试
                if error_type == ErrorType.CONTENT_SAFETY:
                    break

                # 限流错误等待更长时间
                if error_type == ErrorType.RATE_LIMIT:
                    wait_time = self.RETRY_DELAY * (attempt + 1) * 2
                    print(f"    [ImageGenerator Phase2] 限流等待 {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

        return {
            "success": False,
            "error": f"Image generation failed after {self.MAX_RETRIES} attempts: {last_error}",
            "error_type": last_error_type.value,  # 返回错误类型供上层处理
            "model_used": self.NB2_MODEL,
            "generation_time_seconds": round(time.time() - start_time, 2),
            "phase2": True,
            "original_prompt": full_prompt  # 返回原始prompt供改写使用
        }

    async def generate_shot_image_phase2_safe(
        self,
        shot: dict,
        storyboard: dict,
        characters: dict,
        style_preset: str = "anime",
        reference_images: Optional[List[Image.Image]] = None,
        screenplay: Optional[dict] = None,
        aspect_ratio: str = "2:3",
        genre: Optional[str] = None,
        use_native_text: bool = True,
        **kwargs
    ) -> dict:
        """
        带内容安全自动改写的 Phase 2.0 Shot 图像生成

        在 CONTENT_SAFETY 错误时自动调用 PromptRewriter 改写 prompt 并重试。
        这是 TASK-RESILIENCE-001 的核心实现。

        流程：
        1. 调用 generate_shot_image_phase2 生成图像
        2. 如果成功，直接返回
        3. 如果失败且错误类型是 CONTENT_SAFETY：
           a. 使用 Haiku 智能改写 prompt
           b. 重试生成
           c. 如果仍失败，降级到简单规则替换再试一次

        Args:
            shot: Phase 2.0 shot数据
            storyboard: 完整storyboard数据
            characters: 完整角色数据
            style_preset: 风格预设
            reference_images: 参考图像列表
            screenplay: 剧本数据
            aspect_ratio: 宽高比
            genre: 题材类型（wuxia/mystery/cyberpunk/war），用于题材特定替换规则

        Returns:
            生成结果字典，额外包含 rewrite_info 如果进行了改写
        """
        shot_id = shot.get("shot_id", "?")
        print(f"\n[ImageGenerator] === Shot {shot_id} 安全生成开始 ===")

        # 1. 首次尝试生成
        result = await self.generate_shot_image_phase2(
            shot=shot,
            storyboard=storyboard,
            characters=characters,
            style_preset=style_preset,
            reference_images=reference_images,
            screenplay=screenplay,
            aspect_ratio=aspect_ratio,
            use_native_text=use_native_text,
            **kwargs
        )

        # 2. 如果成功，直接返回
        if result.get("success"):
            print(f"[ImageGenerator] ✅ Shot {shot_id} 首次生成成功")
            return result

        # 3. 检查是否是内容安全错误
        error_type = result.get("error_type")
        if error_type != ErrorType.CONTENT_SAFETY.value:
            # 不是内容安全错误，直接返回失败结果
            print(f"[ImageGenerator] ❌ Shot {shot_id} 失败（非内容安全错误）: {error_type}")
            return result

        # 4. 内容安全错误，尝试改写
        print(f"[ImageGenerator] ⚠️ Shot {shot_id} 触发内容安全过滤，开始智能改写...")

        original_prompt = result.get("original_prompt", "")
        if not original_prompt:
            print(f"[ImageGenerator] ❌ 无法获取原始 prompt，跳过改写")
            return result

        rewriter = self.prompt_rewriter
        if not rewriter:
            print(f"[ImageGenerator] ❌ PromptRewriter 不可用，跳过改写")
            return result

        rewrite_info = {
            "attempted": True,
            "original_prompt": original_prompt[:500] + "..." if len(original_prompt) > 500 else original_prompt,
            "rewrites": []
        }

        # 4a. 第一次改写：使用 Haiku 智能改写
        for rewrite_attempt in range(self.MAX_REWRITE_ATTEMPTS):
            print(f"[ImageGenerator] 🔄 改写尝试 {rewrite_attempt + 1}/{self.MAX_REWRITE_ATTEMPTS}")

            if rewrite_attempt == 0:
                # 第一次：使用 Haiku 智能改写
                rewritten_prompt = await rewriter.rewrite(original_prompt)
                rewrite_method = "haiku"
            else:
                # 后续：使用简单规则替换
                rewritten_prompt = rewriter.rewrite_simple(original_prompt, genre)
                rewrite_method = "simple"

            if not rewritten_prompt:
                print(f"[ImageGenerator] ⚠️ 改写失败，跳过本次尝试")
                continue

            rewrite_info["rewrites"].append({
                "attempt": rewrite_attempt + 1,
                "method": rewrite_method,
                "prompt_preview": rewritten_prompt[:200] + "..."
            })

            # 修改 shot 的 image_prompt 并重试
            modified_shot = shot.copy()
            modified_shot["image_prompt"] = rewritten_prompt

            print(f"[ImageGenerator] 🔄 使用改写后 prompt 重新生成 Shot {shot_id}...")
            retry_result = await self.generate_shot_image_phase2(
                shot=modified_shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=style_preset,
                reference_images=reference_images,
                screenplay=screenplay,
                aspect_ratio=aspect_ratio,
                use_native_text=use_native_text,
                **kwargs
            )

            if retry_result.get("success"):
                print(f"[ImageGenerator] ✅ Shot {shot_id} 改写后生成成功 (方法: {rewrite_method})")
                retry_result["rewrite_info"] = rewrite_info
                retry_result["rewrite_info"]["success"] = True
                retry_result["rewrite_info"]["successful_method"] = rewrite_method
                return retry_result

            # 检查是否仍是内容安全错误
            if retry_result.get("error_type") != ErrorType.CONTENT_SAFETY.value:
                # 改成了其他错误，可能是改写过度导致的
                print(f"[ImageGenerator] ⚠️ 改写后出现其他错误: {retry_result.get('error_type')}")

            # 更新 original_prompt 为改写后的版本，用于下一次改写尝试
            original_prompt = rewritten_prompt

        # 5. 所有改写尝试都失败
        print(f"[ImageGenerator] ❌ Shot {shot_id} 所有改写尝试均失败")
        result["rewrite_info"] = rewrite_info
        result["rewrite_info"]["success"] = False
        return result

    async def generate_batch(
        self,
        prompts: List[dict],
        max_concurrent: int = 3
    ) -> List[dict]:
        """
        批量生成图像（并行执行）

        Args:
            prompts: [{"scene_id": 1, "prompt": "...", "aspect_ratio": "16:9", ...}, ...]
            max_concurrent: 最大并发数

        Returns:
            [{"scene_id": 1, "result": {...}}, ...]
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(item: dict) -> dict:
            async with semaphore:
                result = await self.generate_image(
                    prompt=item.get("prompt", ""),
                    negative_prompt=item.get("negative_prompt", ""),
                    aspect_ratio=item.get("aspect_ratio", "2:3"),
                    reference_images=item.get("reference_images"),
                    style_preset=item.get("style_preset"),
                    use_pro_model=item.get("use_pro_model", False),
                )
                return {
                    "scene_id": item.get("scene_id"),
                    "result": result
                }

        tasks = [generate_with_semaphore(item) for item in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "scene_id": prompts[i].get("scene_id"),
                    "result": {
                        "success": False,
                        "error": str(result)
                    }
                })
            else:
                processed_results.append(result)

        return processed_results


class CharacterConsistencyManager:
    """
    角色一致性管理器

    策略：
    1. 首次生成：为每个角色生成"参考图"（角色立绘）
    2. 后续生成：将参考图作为reference_images传入
    3. Prompt强化：在每个场景的prompt中重复角色的固定描述
    """

    def __init__(self, image_generator: ImageGenerator, storage_service):
        self.image_generator = image_generator
        self.storage = storage_service
        self._character_cache = {}  # {project_id: {character_name: PIL.Image}}

    async def get_character_references(
        self,
        project_id: str,
        characters: List[dict],
        style_preset: str
    ) -> dict:
        """
        获取或生成角色参考图

        Args:
            project_id: 项目ID
            characters: 角色列表 [{"name": "...", "description": "..."}, ...]
            style_preset: 风格预设

        Returns:
            {
                "角色名": {
                    "reference_image": PIL.Image,
                    "description": "角色描述"
                }
            }
        """
        cache_key = project_id
        if cache_key not in self._character_cache:
            self._character_cache[cache_key] = {}

        references = {}

        for character in characters:
            char_name = character.get("name", "Unknown")
            char_desc = character.get("description", "")

            # 检查缓存
            if char_name in self._character_cache[cache_key]:
                references[char_name] = {
                    "reference_image": self._character_cache[cache_key][char_name],
                    "description": char_desc
                }
                continue

            # 检查本地存储
            safe_name = "".join(c if c.isalnum() else "_" for c in char_name)
            stored_path = f"{project_id}/characters/char_{safe_name}.png"
            if self.storage.image_exists(stored_path):
                pil_image = await self.storage.load_image_as_pil(stored_path)
                if pil_image:
                    self._character_cache[cache_key][char_name] = pil_image
                    references[char_name] = {
                        "reference_image": pil_image,
                        "description": char_desc
                    }
                    continue

            # 需要生成新的参考图
            portrait_result = await self.generate_character_portrait(
                character=character,
                style_preset=style_preset
            )

            if portrait_result["success"]:
                pil_image = portrait_result["pil_image"]

                # 保存到存储
                await self.storage.save_character_reference(
                    image_data=portrait_result["image_data"],
                    project_id=project_id,
                    character_name=char_name
                )

                # 缓存
                self._character_cache[cache_key][char_name] = pil_image

                references[char_name] = {
                    "reference_image": pil_image,
                    "description": char_desc
                }
            else:
                # 生成失败，仍然记录描述
                references[char_name] = {
                    "reference_image": None,
                    "description": char_desc
                }
                print(f"Warning: Failed to generate portrait for {char_name}: {portrait_result.get('error')}")

        return references

    async def generate_character_portrait(
        self,
        character: dict,
        style_preset: str
    ) -> dict:
        """
        生成角色立绘（用作后续场景的参考）

        Prompt策略：
        - 半身像或全身像
        - 纯色背景
        - 正面或3/4侧面
        - 详细的服装和特征
        """
        char_name = character.get("name", "Character")
        char_desc = character.get("description", "")
        char_personality = character.get("personality", "")

        # 风格映射
        style_keywords = {
            "realistic": "photorealistic, professional photography, studio lighting",
            "cyberpunk": "cyberpunk style, neon accents, futuristic fashion",
            "illustration": "digital illustration, vibrant colors, artstation quality",
            "ink": "Chinese ink wash style, traditional aesthetics, brush strokes",
            "cartoon": "cartoon style, cute design, bright colors",
            "chinese": "Chinese traditional style, classical elements",
            "manga": "manga style, anime character design, cel shading",
            "oil_painting": "oil painting style, classical portrait",
            "watercolor": "watercolor style, soft edges, dreamy",
            "pixel": "pixel art style, retro game aesthetic"
        }

        style_desc = style_keywords.get(style_preset, style_preset or "high quality")

        portrait_prompt = f"""Character portrait of {char_name}: {char_desc}.
Half-body shot, facing slightly to the side, neutral solid color background.
Clear facial features, detailed clothing and accessories.
Professional character design for animation or film.
Style: {style_desc}.
High quality, detailed, sharp focus, well-lit."""

        return await self.image_generator.generate_image(
            prompt=portrait_prompt,
            negative_prompt="blurry, low quality, distorted face, bad anatomy, multiple people, crowd, busy background",
            aspect_ratio="2:3",  # 竖版角色立绘（抖音适配）
            use_pro_model=True
        )

    def clear_cache(self, project_id: str = None):
        """清除缓存"""
        if project_id:
            self._character_cache.pop(project_id, None)
        else:
            self._character_cache.clear()
