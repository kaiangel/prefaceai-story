"""
Book Outline Prompt - Stage 1 for book narration videos.

Extracts key insights from a book and prepares visual concepts for each insight.
This replaces StoryOutlineGenerator for book content.
"""


def build_book_outline_prompt(
    book_title: str,
    author: str,
    book_summary: str,
    target_duration: int = 180,
    num_insights: int = 5,
    style: str = "illustration"
) -> str:
    """
    Build prompt for extracting key insights from a book.

    Args:
        book_title: Title of the book
        author: Author name
        book_summary: Summary/core content of the book (user provided)
        target_duration: Target video duration in seconds (default 3 min)
        num_insights: Number of key insights to extract (3-7)
        style: Visual style for image generation

    Returns:
        Prompt string for LLM
    """

    return f"""You are an expert book analyst and content creator. Your task is to extract the key insights from a book and prepare them for a narration video.

## Input Book Information

**Book Title**: {book_title}
**Author**: {author}
**Summary/Content**:
{book_summary}

## Your Task

Extract {num_insights} core insights from this book that would make an engaging {target_duration // 60}-minute explanation video.

## Output Requirements

Return a JSON object with the following structure:

```json
{{
  "book_title": "{book_title}",
  "book_title_en": "<English translation of the title>",
  "author": "{author}",
  "core_theme": "<One sentence describing the book's central message, in Chinese>",
  "core_theme_en": "<Same in English>",
  "target_audience": "<Who would benefit from this book, in Chinese>",
  "tone": "<The tone for narration: informative/inspirational/thought-provoking/humorous, in Chinese>",
  "visual_style": "{style}",
  "key_insights": [
    {{
      "insight_id": 1,
      "title": "<Insight title in Chinese, catchy and memorable>",
      "title_en": "<Same in English>",
      "summary": "<2-3 sentence explanation of this insight, in Chinese>",
      "summary_en": "<Same in English>",
      "visual_concept": "<ENGLISH ONLY: Detailed visual scene description for image generation. Must be a concrete, visualizable scene, not abstract text or diagrams.>",
      "emotional_arc": "<The emotional impact: surprising/enlightening/thought-provoking/inspiring>",
      "duration_hint": <suggested seconds for this insight, integer>
    }}
  ],
  "opening_hook_idea": "<A provocative question or statement to start the video, in Chinese>",
  "closing_message_idea": "<The takeaway message to end with, in Chinese>"
}}
```

## Critical Rules

1. **Visual Concept MUST be in English** - This will be used for image generation with Gemini.

2. **Visual Concept MUST be concrete scenes**, NOT:
   - Text on screen
   - Infographics or charts
   - Abstract patterns
   - Lists or bullet points

   GOOD examples:
   - "A group of primitive humans sitting around a campfire at night, smoke rising into the starry sky, forming shapes of mythical creatures"
   - "Split image: a farmer bent over in exhaustion tending wheat fields on the left, a carefree hunter-gatherer walking freely through a forest on the right"
   - "A medieval merchant at a crowded bazaar, gold coins floating magically between diverse traders of different cultures"

   BAD examples:
   - "Text showing 'Cognitive Revolution'" (NO TEXT)
   - "A chart comparing GDP" (NO CHARTS)
   - "Abstract representation of human progress" (TOO ABSTRACT)

3. **Duration hints should sum to approximately {target_duration} seconds**

4. **Each insight should be self-contained** - understandable without reading the book

5. **Maintain the book's core message** - don't oversimplify or distort the author's intent

6. **Order insights logically** - build from foundation to conclusion

## Style Guidance for Visual Concepts

Since the visual style is "{style}", visual concepts should suit this style:
- illustration: Rich, detailed scenes with artistic flair
- realistic: Photorealistic scenes, documentary-style imagery
- watercolor: Soft, dreamy, atmospheric scenes
- ink: Minimalist, high-contrast, traditional aesthetics

Now analyze the book and generate the JSON output. Return ONLY the JSON, no additional text.
"""


# Example usage template for testing
BOOK_OUTLINE_EXAMPLE_INPUT = {
    "book_title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "book_summary": """
《人类简史》讲述了人类从7万年前的认知革命到21世纪的科技革命的历程。

核心观点：
1. 认知革命：智人能够创造和相信虚构故事（神话、宗教、国家、货币），这是人类统治地球的关键
2. 农业革命是"史上最大骗局"：人类以为驯化了小麦，实际上是小麦驯化了人类
3. 帝国、货币、宗教是统一人类的三大力量
4. 科学革命：承认无知是进步的开始
5. 快乐悖论：物质进步不等于幸福增加
""",
    "target_duration": 180,
    "num_insights": 5,
    "style": "illustration"
}
