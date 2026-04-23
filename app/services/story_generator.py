"""Story generation service using Google Gemini API with Claude fallback"""

import asyncio
import json
import re
import time
from google import genai
from google.genai import types
import anthropic
from app.config import settings
from app.prompts.story_generation import build_story_generation_prompt


class StoryGenerator:
    """Service for generating stories using Claude (primary) with Gemini fallback"""

    # Model priority: Claude first, then Gemini
    CLAUDE_MODEL = "claude-sonnet-4-6"  # Claude Sonnet 4.6 as primary (DEC-012)

    GEMINI_MODELS = [
        "gemini-3.1-flash-lite-preview",  # Gemini 3.1 Flash
        "gemini-2.5-flash",      # Fast and reliable Gemini fallback
    ]

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    def __init__(self):
        # Initialize Claude client (primary)
        self.claude_client = None
        self.async_claude_client = None
        if settings.ANTHROPIC_API_KEY:
            self.claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.async_claude_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Initialize Gemini client (fallback)
        self.gemini_client = None
        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

        self.model_name = self.CLAUDE_MODEL  # Default to Claude

    async def generate_story(
        self,
        idea: str,
        style: str,
        chapter_number: int = 1,
        total_chapters: int = 1,
        duration_minutes: int = 3,
        character_count: int = 2,
        language: str = "zh-CN",
        previous_summary: str | None = None,
        characters_json: str | None = None,
        min_scenes: int | None = None,
    ) -> dict:
        """
        Call AI to generate story (async version with streaming and retry)
        First tries Gemini models, then falls back to Claude if all fail.

        Returns:
            Parsed story JSON object
        """
        prompt = build_story_generation_prompt(
            idea=idea,
            style=style,
            chapter_number=chapter_number,
            total_chapters=total_chapters,
            duration_minutes=duration_minutes,
            character_count=character_count,
            language=language,
            previous_summary=previous_summary,
            characters_json=characters_json,
            min_scenes=min_scenes,
        )

        # Try Claude first (primary)
        if self.async_claude_client:
            result = await self._try_claude_async(prompt)
            if result["success"]:
                return result

        # If Claude failed, try Gemini models as fallback
        if self.gemini_client:
            result = await self._try_gemini_async(prompt)
            if result["success"]:
                return result

        return {
            "success": False,
            "error": "All models (Claude and Gemini) failed after retries.",
            "raw_response": None,
        }

    async def _try_gemini_async(self, prompt: str) -> dict:
        """Try Gemini models with retries (async)"""
        config = types.GenerateContentConfig(
            temperature=0.8,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        last_error = None

        for model in self.GEMINI_MODELS:
            for attempt in range(self.MAX_RETRIES):
                try:
                    full_response = ""
                    async for chunk in self.gemini_client.aio.models.generate_content_stream(
                        model=model,
                        contents=prompt,
                        config=config,
                    ):
                        if chunk.text:
                            full_response += chunk.text

                    result = self._parse_response(full_response)

                    return {
                        "success": True,
                        "data": result,
                        "model_used": model,
                        "provider": "gemini",
                        "attempts": attempt + 1,
                    }

                except Exception as e:
                    last_error = str(e)
                    if attempt < self.MAX_RETRIES - 1:
                        await asyncio.sleep(self.RETRY_DELAY)
                    continue

        return {
            "success": False,
            "error": f"Gemini failed: {last_error}",
        }

    async def _try_claude_async(self, prompt: str) -> dict:
        """Try Claude as fallback (async)"""
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Claude requires JSON extraction from response
                system_prompt = """You are a professional screenwriter.
Always respond with valid JSON only. No markdown, no explanation, just pure JSON.
For complex stories with many scenes, output all scenes in a single JSON response."""

                message = await self.async_claude_client.messages.create(
                    model=self.CLAUDE_MODEL,
                    max_tokens=16384,  # Increased for longer stories
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system=system_prompt,
                )

                response_text = message.content[0].text
                result = self._parse_response(response_text)

                return {
                    "success": True,
                    "data": result,
                    "model_used": self.CLAUDE_MODEL,
                    "provider": "anthropic",
                    "attempts": attempt + 1,
                }

            except Exception as e:
                last_error = str(e)
                print(f"Claude attempt {attempt + 1} failed: {last_error}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                continue

        return {
            "success": False,
            "error": f"Claude failed: {last_error}",
        }

    def _parse_response(self, text: str) -> dict:
        """Parse JSON response, handling markdown code blocks"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract ```json``` block
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            # Try to extract any JSON object
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError(f"Could not parse JSON from response: {text[:200]}...")

    def generate_story_sync(
        self,
        idea: str,
        style: str,
        chapter_number: int = 1,
        total_chapters: int = 1,
        duration_minutes: int = 3,
        character_count: int = 2,
        language: str = "zh-CN",
        previous_summary: str | None = None,
        characters_json: str | None = None,
    ) -> dict:
        """
        Synchronous version for testing and background tasks.
        First tries Gemini models, then falls back to Claude if all fail.

        Returns:
            Parsed story JSON object
        """
        prompt = build_story_generation_prompt(
            idea=idea,
            style=style,
            chapter_number=chapter_number,
            total_chapters=total_chapters,
            duration_minutes=duration_minutes,
            character_count=character_count,
            language=language,
            previous_summary=previous_summary,
            characters_json=characters_json,
        )

        # Try Claude first (primary)
        if self.claude_client:
            result = self._try_claude_sync(prompt)
            if result["success"]:
                return result

        # If Claude failed, try Gemini models as fallback
        if self.gemini_client:
            result = self._try_gemini_sync(prompt)
            if result["success"]:
                return result

        return {
            "success": False,
            "error": "All models (Claude and Gemini) failed after retries.",
            "raw_response": None,
        }

    def _try_gemini_sync(self, prompt: str) -> dict:
        """Try Gemini models with retries (sync)"""
        config = types.GenerateContentConfig(
            temperature=0.8,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )

        last_error = None

        for model in self.GEMINI_MODELS:
            for attempt in range(self.MAX_RETRIES):
                try:
                    full_response = ""
                    for chunk in self.gemini_client.models.generate_content_stream(
                        model=model,
                        contents=prompt,
                        config=config,
                    ):
                        if chunk.text:
                            full_response += chunk.text

                    result = self._parse_response(full_response)

                    return {
                        "success": True,
                        "data": result,
                        "model_used": model,
                        "provider": "gemini",
                        "attempts": attempt + 1,
                    }

                except Exception as e:
                    last_error = str(e)
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(self.RETRY_DELAY)
                    continue

        return {
            "success": False,
            "error": f"Gemini failed: {last_error}",
        }

    def _try_claude_sync(self, prompt: str) -> dict:
        """Try Claude as fallback (sync)"""
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            try:
                system_prompt = """You are a professional screenwriter.
Always respond with valid JSON only. No markdown, no explanation, just pure JSON."""

                message = self.claude_client.messages.create(
                    model=self.CLAUDE_MODEL,
                    max_tokens=16384,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system=system_prompt,
                )

                response_text = message.content[0].text
                result = self._parse_response(response_text)

                return {
                    "success": True,
                    "data": result,
                    "model_used": self.CLAUDE_MODEL,
                    "provider": "anthropic",
                    "attempts": attempt + 1,
                }

            except Exception as e:
                last_error = str(e)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
                continue

        return {
            "success": False,
            "error": f"Claude failed: {last_error}",
        }
