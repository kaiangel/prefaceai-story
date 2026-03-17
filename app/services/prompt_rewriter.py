"""
Prompt 安全改写服务
使用 Claude Sonnet 4.6 智能改写被 Gemini 内容安全过滤拒绝的 prompt

TASK-RESILIENCE-001-B 交付物
Created: 2026-01-28
Author: @Backend

使用场景:
当 ImageGenerator 检测到 ErrorType.CONTENT_SAFETY 错误时，
调用本服务对 prompt 进行智能改写，然后重试图像生成。
"""

import os
from typing import Optional, Dict

from app.prompts.prompt_safety_rewrite import (
    build_rewrite_prompt,
    build_scene_ref_rewrite_prompt,
    build_char_ref_rewrite_prompt,
    apply_simple_replacements,
    detect_sensitive_content,
    GENRE_SPECIFIC_RULES,
)


class PromptRewriter:
    """
    Prompt 安全改写服务

    提供两层改写策略：
    1. Sonnet 4.6 智能改写 - 保持语义连贯、保留艺术风格（推荐）
    2. 简单规则替换 - 零成本、即时响应（降级方案）

    使用示例:
        rewriter = PromptRewriter()

        # 检测是否需要改写
        if rewriter.needs_rewrite(prompt):
            # 智能改写
            new_prompt = await rewriter.rewrite(prompt)
            # 如果智能改写失败，降级到简单替换
            if not new_prompt:
                new_prompt = rewriter.rewrite_simple(prompt)
    """

    # 主模型: Claude Sonnet 4.6
    SONNET_MODEL = "claude-sonnet-4-6"
    MAX_TOKENS = 2000

    def __init__(self):
        """初始化 PromptRewriter"""
        self.client = None
        self.gemini_client = None
        self._init_client()

    def _init_client(self):
        """初始化 LLM 客户端（主: Claude Sonnet 4.6, 备: Gemini 3.1 Flash）"""
        # 主模型: Claude Sonnet 4.6
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.client = anthropic.AsyncAnthropic(api_key=api_key)
                print("[PromptRewriter] ✅ Anthropic 客户端初始化成功 (Sonnet 4.6)")
            else:
                print("[PromptRewriter] ⚠️ ANTHROPIC_API_KEY 未设置")
        except ImportError:
            print("[PromptRewriter] ⚠️ anthropic 包未安装")
        except Exception as e:
            print(f"[PromptRewriter] ⚠️ Anthropic 客户端初始化失败: {e}")

        # 备用模型: Gemini 3.1 Flash
        try:
            from google import genai
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                self.gemini_client = genai.Client(api_key=gemini_key)
                print("[PromptRewriter] ✅ Gemini 3.1 Flash 备用客户端初始化成功")
        except Exception:
            pass

    def needs_rewrite(self, prompt: str) -> bool:
        """
        检测 prompt 是否需要改写

        Args:
            prompt: 要检测的 prompt

        Returns:
            是否包含敏感内容
        """
        detection = detect_sensitive_content(prompt)
        if detection["has_sensitive"]:
            print(f"[PromptRewriter] 检测到 {detection['count']} 个敏感词")
            print(f"[PromptRewriter] 敏感类别: {detection['categories']}")
        return detection["has_sensitive"]

    def detect(self, prompt: str) -> Dict:
        """
        详细检测 prompt 中的敏感内容

        Args:
            prompt: 要检测的 prompt

        Returns:
            检测结果，包含 has_sensitive, categories, count, details
        """
        return detect_sensitive_content(prompt)

    async def rewrite(self, prompt: str, debug: bool = False) -> Optional[str]:
        """
        使用 Sonnet 4.6 智能改写 prompt

        保持艺术风格和情感，同时替换敏感内容。
        推荐方案，成本约 $0.001/次。

        Args:
            prompt: 被 Gemini 拒绝的原始 prompt
            debug: 是否返回调试信息

        Returns:
            改写后的 prompt，失败返回 None
        """
        if not self.client and not self.gemini_client:
            print("[PromptRewriter] ❌ 无可用 LLM 客户端，无法使用智能改写")
            return None

        try:
            print(f"[PromptRewriter] 🔄 开始智能改写 (Sonnet 4.6)...")
            print(f"[PromptRewriter] 原始 prompt 长度: {len(prompt)} 字符")

            # 构建改写 prompt
            rewrite_prompt = build_rewrite_prompt(prompt, debug_mode=debug)

            rewritten = None

            # 优先使用 Claude Sonnet 4.6
            if self.client:
                try:
                    response = await self.client.messages.create(
                        model=self.SONNET_MODEL,
                        max_tokens=self.MAX_TOKENS,
                        messages=[{"role": "user", "content": rewrite_prompt}]
                    )
                    rewritten = response.content[0].text.strip()
                except Exception as ce:
                    print(f"[PromptRewriter] Claude失败: {ce}，尝试Gemini备用")

            # Fallback到Gemini 3.1 Flash
            if rewritten is None and self.gemini_client:
                try:
                    response = await self.gemini_client.aio.models.generate_content(
                        model="gemini-3.1-flash-preview",
                        contents=rewrite_prompt,
                        config={"max_output_tokens": self.MAX_TOKENS}
                    )
                    rewritten = response.text.strip()
                except Exception as ge:
                    print(f"[PromptRewriter] Gemini也失败: {ge}")
                    return None

            if rewritten is None:
                return None

            # 验证结果
            if not rewritten or len(rewritten) < 50:
                print(f"[PromptRewriter] ⚠️ 改写结果过短，可能失败")
                return None

            print(f"[PromptRewriter] ✅ 智能改写完成")
            print(f"[PromptRewriter] 改写后 prompt 长度: {len(rewritten)} 字符")

            # 再次检测改写后是否还有敏感内容
            post_detection = detect_sensitive_content(rewritten)
            if post_detection["has_sensitive"]:
                print(f"[PromptRewriter] ⚠️ 改写后仍有 {post_detection['count']} 个敏感词")
            else:
                print(f"[PromptRewriter] ✅ 改写后无敏感内容")

            return rewritten

        except Exception as e:
            print(f"[PromptRewriter] ❌ 智能改写失败: {e}")
            return None

    def rewrite_simple(self, prompt: str, genre: Optional[str] = None) -> str:
        """
        简单规则替换（降级方案）

        使用预定义的敏感词替换规则，不调用 LLM。
        零成本、即时响应，但可能影响句子流畅性。

        Args:
            prompt: 被 Gemini 拒绝的原始 prompt
            genre: 可选，题材类型（wuxia/mystery/cyberpunk/war）

        Returns:
            替换后的 prompt
        """
        print(f"[PromptRewriter] 🔄 开始简单规则替换...")

        # 先检测敏感内容
        detection = detect_sensitive_content(prompt)
        if detection["has_sensitive"]:
            print(f"[PromptRewriter] 发现 {detection['count']} 个敏感词需要替换")

        # 应用替换
        rewritten = apply_simple_replacements(prompt, genre)

        print(f"[PromptRewriter] ✅ 简单替换完成")

        # 再次检测
        post_detection = detect_sensitive_content(rewritten)
        if post_detection["has_sensitive"]:
            remaining = post_detection['count']
            print(f"[PromptRewriter] ⚠️ 仍有 {remaining} 个敏感词未替换")
        else:
            print(f"[PromptRewriter] ✅ 所有敏感词已替换")

        return rewritten

    async def rewrite_with_fallback(
        self,
        prompt: str,
        genre: Optional[str] = None,
        max_attempts: int = 2
    ) -> str:
        """
        带降级的改写流程

        先尝试智能改写，失败则降级到简单规则替换。

        Args:
            prompt: 被 Gemini 拒绝的原始 prompt
            genre: 可选，题材类型
            max_attempts: 最大智能改写尝试次数

        Returns:
            改写后的 prompt
        """
        original_prompt = prompt

        # 1. 尝试智能改写
        for attempt in range(max_attempts):
            print(f"[PromptRewriter] 智能改写尝试 {attempt + 1}/{max_attempts}")
            rewritten = await self.rewrite(prompt)
            if rewritten:
                # 检查是否还有敏感内容
                detection = detect_sensitive_content(rewritten)
                if not detection["has_sensitive"]:
                    return rewritten
                # 如果还有敏感内容，用改写后的继续尝试
                prompt = rewritten

        # 2. 降级到简单规则替换
        print(f"[PromptRewriter] 智能改写未能完全清除敏感内容，降级到简单替换")
        return self.rewrite_simple(original_prompt, genre)

    async def rewrite_scene_ref(self, prompt: str) -> Optional[str]:
        """L3a: 场景参考图专用改写（使用 SCENE_REF_REWRITE_PROMPT）"""
        if not self.client and not self.gemini_client:
            print("[PromptRewriter] ❌ 无可用 LLM 客户端，场景参考改写失败")
            return None
        try:
            print(f"[PromptRewriter] 🔄 场景参考图改写 (Sonnet 4.6)...")
            rewrite_prompt = build_scene_ref_rewrite_prompt(prompt)
            rewritten = None
            if self.client:
                try:
                    response = await self.client.messages.create(
                        model=self.SONNET_MODEL,
                        max_tokens=self.MAX_TOKENS,
                        messages=[{"role": "user", "content": rewrite_prompt}]
                    )
                    rewritten = response.content[0].text.strip()
                except Exception as ce:
                    print(f"[PromptRewriter] Claude失败: {ce}，尝试Gemini备用")
            if rewritten is None and self.gemini_client:
                try:
                    response = await self.gemini_client.aio.models.generate_content(
                        model="gemini-3.1-flash-preview",
                        contents=rewrite_prompt,
                        config={"max_output_tokens": self.MAX_TOKENS}
                    )
                    rewritten = response.text.strip()
                except Exception as ge:
                    print(f"[PromptRewriter] Gemini也失败: {ge}")
                    return None
            if rewritten and len(rewritten) >= 50:
                print(f"[PromptRewriter] ✅ 场景参考图改写完成 ({len(rewritten)} 字符)")
                return rewritten
            return None
        except Exception as e:
            print(f"[PromptRewriter] ❌ 场景参考图改写失败: {e}")
            return None

    async def rewrite_char_ref(self, prompt: str) -> Optional[str]:
        """L3b: 角色参考图专用改写（使用 CHAR_REF_REWRITE_PROMPT）"""
        if not self.client and not self.gemini_client:
            print("[PromptRewriter] ❌ 无可用 LLM 客户端，角色参考改写失败")
            return None
        try:
            print(f"[PromptRewriter] 🔄 角色参考图改写 (Sonnet 4.6)...")
            rewrite_prompt = build_char_ref_rewrite_prompt(prompt)
            rewritten = None
            if self.client:
                try:
                    response = await self.client.messages.create(
                        model=self.SONNET_MODEL,
                        max_tokens=self.MAX_TOKENS,
                        messages=[{"role": "user", "content": rewrite_prompt}]
                    )
                    rewritten = response.content[0].text.strip()
                except Exception as ce:
                    print(f"[PromptRewriter] Claude失败: {ce}，尝试Gemini备用")
            if rewritten is None and self.gemini_client:
                try:
                    response = await self.gemini_client.aio.models.generate_content(
                        model="gemini-3.1-flash-preview",
                        contents=rewrite_prompt,
                        config={"max_output_tokens": self.MAX_TOKENS}
                    )
                    rewritten = response.text.strip()
                except Exception as ge:
                    print(f"[PromptRewriter] Gemini也失败: {ge}")
                    return None
            if rewritten and len(rewritten) >= 50:
                print(f"[PromptRewriter] ✅ 角色参考图改写完成 ({len(rewritten)} 字符)")
                return rewritten
            return None
        except Exception as e:
            print(f"[PromptRewriter] ❌ 角色参考图改写失败: {e}")
            return None

    @staticmethod
    def get_supported_genres() -> list:
        """获取支持的题材类型列表"""
        return list(GENRE_SPECIFIC_RULES.keys())


# 单例实例，方便直接导入使用
_rewriter_instance = None


def get_rewriter() -> PromptRewriter:
    """获取 PromptRewriter 单例"""
    global _rewriter_instance
    if _rewriter_instance is None:
        _rewriter_instance = PromptRewriter()
    return _rewriter_instance
