"""
Book narration prompt templates for XuhuaStory.

This module contains prompts for generating book explanation/narration videos.
It's a side experiment to verify if XuhuaStory can handle book content.

NOTE: This is experimental code. Do not modify existing story/storyboard prompts.
"""

from .book_outline_prompt import build_book_outline_prompt
from .book_narration_prompt import build_book_narration_prompt
from .book_storyboard_prompt import build_book_storyboard_prompt

__all__ = [
    "build_book_outline_prompt",
    "build_book_narration_prompt",
    "build_book_storyboard_prompt",
]
