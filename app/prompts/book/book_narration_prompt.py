"""
Book Narration Prompt - Stage 2 for book narration videos.

Generates narration script from book outline insights.
This replaces ScreenplayWriter for book content.
"""


def build_book_narration_prompt(
    book_outline: dict,
) -> str:
    """
    Build prompt for generating narration script from book outline.

    Args:
        book_outline: Output from Stage 1 (book_outline_prompt)
            Expected fields:
            - book_title, author, core_theme
            - key_insights: list of insights with visual_concept
            - opening_hook_idea, closing_message_idea

    Returns:
        Prompt string for LLM
    """

    # Extract key fields from outline
    book_title = book_outline.get("book_title", "Unknown Book")
    author = book_outline.get("author", "Unknown Author")
    core_theme = book_outline.get("core_theme", "")
    tone = book_outline.get("tone", "informative")
    visual_style = book_outline.get("visual_style", "illustration")
    opening_hook = book_outline.get("opening_hook_idea", "")
    closing_message = book_outline.get("closing_message_idea", "")
    key_insights = book_outline.get("key_insights", [])

    # Format insights for prompt
    insights_text = ""
    for i, insight in enumerate(key_insights, 1):
        insights_text += f"""
Insight {i}:
- Title: {insight.get('title', '')}
- Title (EN): {insight.get('title_en', '')}
- Summary: {insight.get('summary', '')}
- Visual Concept: {insight.get('visual_concept', '')}
- Emotional Arc: {insight.get('emotional_arc', '')}
- Duration Hint: {insight.get('duration_hint', 30)} seconds
"""

    return f"""You are an expert content writer for book explanation videos. Your task is to transform book insights into an engaging narration script.

## Input: Book Outline

**Book**: {book_title} by {author}
**Core Theme**: {core_theme}
**Tone**: {tone}
**Visual Style**: {visual_style}
**Opening Hook Idea**: {opening_hook}
**Closing Message Idea**: {closing_message}

**Key Insights**:
{insights_text}

## Your Task

Create a narration script that:
1. Opens with a hook to grab attention
2. Explains each insight in an engaging, conversational way
3. Closes with a memorable takeaway message

## Output Requirements

Return a JSON object with the following structure:

```json
{{
  "book_title": "{book_title}",
  "author": "{author}",
  "total_duration": <total duration in seconds>,
  "opening_hook": "<Opening hook text in Chinese, grabbing attention, 2-3 sentences>",
  "narration_segments": [
    {{
      "segment_id": 1,
      "insight_ref": <insight_id from outline>,
      "insight_title": "<insight title in Chinese>",
      "narration_text": "<Narration text in CHINESE for TTS. Should be conversational, engaging, easy to listen to. 80-150 characters per segment.>",
      "visual_direction": "<ENGLISH ONLY: Detailed visual direction for image generation. Describe the scene, camera movement suggestion, key visual elements. Must be concrete and visualizable.>",
      "duration_hint": <duration in seconds>,
      "transition_note": "<optional: transition hint to next segment>"
    }}
  ],
  "closing_statement": "<Closing statement in Chinese, memorable takeaway, 2-3 sentences>"
}}
```

## Critical Rules

### For narration_text (Chinese):
1. **Must be in Chinese** - This will be read aloud by TTS
2. **Conversational tone** - Write as if speaking to a friend, not reading a textbook
3. **Rhythm and flow** - Vary sentence length, use rhetorical questions, create pauses
4. **No jargon** - Explain complex concepts in simple terms
5. **Each segment: 80-150 characters** - Approximately 20-40 seconds when read aloud
6. **Information density** - Every sentence should add value, no filler

### For visual_direction (English):
1. **Must be in English** - This will be used for image generation
2. **Concrete scenes only** - Must be visualizable, NO text/charts/diagrams
3. **Include camera suggestions** - "wide establishing shot", "slowly zoom in", "focus on hands"
4. **Describe atmosphere** - Lighting, mood, color tone
5. **Reference the visual_concept from outline** but expand with more detail

### Visual Direction Good vs Bad Examples:

GOOD:
- "Wide establishing shot of a prehistoric campfire scene at night. A group of early humans sit in a circle, their faces lit by flickering firelight. Smoke rises and seems to form ghostly shapes against the starry sky. Camera slowly pushes toward the central figure who gestures animatedly. Warm orange lighting contrasts with deep blue night sky."

BAD:
- "Show the concept of cognitive revolution" (too abstract)
- "Text appears: 'The Cognitive Revolution'" (no text!)
- "A diagram showing human evolution" (no diagrams!)

### Structure Guidelines:

1. **Opening Hook** (10-15 seconds):
   - Start with a surprising fact, question, or provocative statement
   - Immediately engage the viewer's curiosity

2. **Body Segments** (one per insight):
   - Each insight gets 1-2 narration segments
   - Use storytelling techniques: "Imagine...", "Think about...", "Here's the twist..."
   - Build from simple to complex concepts
   - Use analogies and relatable examples

3. **Closing Statement** (10-15 seconds):
   - Summarize the core message
   - Leave the viewer with something to think about
   - Optional: call to action (read the book, share your thoughts)

## Writing Style Examples

Instead of: "认知革命发生在大约7万年前，使人类能够创造虚构概念。"
Write: "七万年前的某一天，一个智人做了一件其他动物从未做过的事——他开始讲故事。不是关于食物或危险的故事，而是关于根本不存在的东西：神灵、祖先、命运。"

Instead of: "农业革命让人类定居并发展文明。"
Write: "你以为是人类驯化了小麦？赫拉利说，其实是小麦驯化了人类。想想看，为了照顾这些娇贵的植物，我们的祖先放弃了自由自在的游猎生活，开始弯腰耕种，开始为天气担忧，开始被土地束缚。"

Now generate the narration script. Return ONLY the JSON, no additional text.
"""


# Example input for testing
BOOK_NARRATION_EXAMPLE_INPUT = {
    "book_title": "人类简史",
    "book_title_en": "Sapiens: A Brief History of Humankind",
    "author": "尤瓦尔·赫拉利",
    "core_theme": "人类如何从无名小卒成为地球主宰",
    "target_audience": "对人类历史和命运感兴趣的读者",
    "tone": "thought-provoking",
    "visual_style": "illustration",
    "key_insights": [
        {
            "insight_id": 1,
            "title": "认知革命",
            "title_en": "Cognitive Revolution",
            "summary": "7万年前，智人突然开始创造虚构故事，这种能力让人类能够大规模协作，统治地球。",
            "visual_concept": "A group of primitive humans sitting around a campfire at night, smoke rising into the starry sky, forming shapes of mythical creatures and spirits. The central figure gestures animatedly while others listen in rapt attention.",
            "emotional_arc": "surprising",
            "duration_hint": 35
        },
        {
            "insight_id": 2,
            "title": "农业陷阱",
            "title_en": "The Agricultural Trap",
            "summary": "农业革命被称为'史上最大骗局'，人类以为驯化了小麦，实际上是小麦驯化了人类。",
            "visual_concept": "Split scene composition: on the left, an exhausted farmer bent over in a golden wheat field under harsh sunlight; on the right, a carefree hunter-gatherer walking freely through a lush green forest.",
            "emotional_arc": "thought-provoking",
            "duration_hint": 35
        }
    ],
    "opening_hook_idea": "如果有人告诉你，小麦才是地球上最成功的物种，你会相信吗？",
    "closing_message_idea": "我们统治世界，不是因为我们最强壮，而是因为我们最会讲故事。"
}
