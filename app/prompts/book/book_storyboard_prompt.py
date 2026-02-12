"""
Book Storyboard Prompt - Stage 3 for book narration videos.

Generates image prompts (shots) from narration script.
This replaces StoryboardDirector for book content.

Key difference from story storyboard:
- Focus on CONCEPT VISUALIZATION, not character consistency
- Static, metaphorical imagery rather than action scenes
- Abstract concepts must become concrete, visualizable scenes
"""


# Concept visualization instruction block
CONCEPT_VISUALIZATION_BLOCK = """
═══════════════════════════════════════════════════════════════════
CONCEPT VISUALIZATION RULES - CRITICAL FOR BOOK CONTENT
═══════════════════════════════════════════════════════════════════

This is a BOOK EXPLANATION video, not a story. The images must visualize IDEAS.

ABSOLUTE REQUIREMENTS:
1. Abstract concepts MUST be converted to concrete, visualizable scenes
2. NO text overlays, titles, infographics, charts, or diagrams in the image
3. NO bullet points, lists, or written words visible in the image
4. Use METAPHORICAL scenes to represent ideas
5. People/figures should be GENERIC (not specific recurring characters)

VISUALIZATION TECHNIQUES:
- "Power of stories" → diverse people gathered around a storyteller
- "Agricultural trap" → exhausted farmer vs. free hunter-gatherer
- "Money as fiction" → gold coins floating between diverse traders
- "Scientific revolution" → scientist peering into unknown darkness with a small lamp
- "Happiness paradox" → wealthy person looking melancholy in luxury vs. simple farmer smiling

FORBIDDEN ELEMENTS:
- Text on screen (NO quotes, NO titles, NO labels)
- Charts, graphs, timelines, infographics
- Abstract geometric patterns representing ideas
- Floating text or speech bubbles
- Book covers or pages with visible text

═══════════════════════════════════════════════════════════════════
"""


def build_book_storyboard_prompt(
    narration_script: dict,
    visual_style: str = "illustration"
) -> str:
    """
    Build prompt for generating image prompts (storyboard) from narration script.

    Args:
        narration_script: Output from Stage 2 (book_narration_prompt)
            Expected fields:
            - book_title, author
            - opening_hook, closing_statement
            - narration_segments: list with narration_text, visual_direction
        visual_style: Visual style for all images

    Returns:
        Prompt string for LLM
    """

    # Extract key fields
    book_title = narration_script.get("book_title", "Unknown Book")
    author = narration_script.get("author", "Unknown Author")
    total_duration = narration_script.get("total_duration", 180)
    opening_hook = narration_script.get("opening_hook", "")
    closing_statement = narration_script.get("closing_statement", "")
    segments = narration_script.get("narration_segments", [])

    # Format segments for prompt
    segments_text = ""
    for seg in segments:
        segments_text += f"""
Segment {seg.get('segment_id', '?')}:
- Insight: {seg.get('insight_title', '')}
- Narration (Chinese): {seg.get('narration_text', '')}
- Visual Direction: {seg.get('visual_direction', '')}
- Duration: {seg.get('duration_hint', 30)} seconds
"""

    # Get style-specific guidance
    style_guidance = _get_style_guidance(visual_style)

    return f"""You are an expert visual director for book explanation videos. Your task is to create detailed image prompts that visualize abstract concepts.

{CONCEPT_VISUALIZATION_BLOCK}

## Input: Narration Script

**Book**: {book_title} by {author}
**Total Duration**: {total_duration} seconds
**Visual Style**: {visual_style}

**Opening Hook**:
{opening_hook}

**Segments**:
{segments_text}

**Closing Statement**:
{closing_statement}

## Your Task

Create image prompts (shots) for each narration segment. Each segment should have 1-2 shots.

## Output Requirements

Return a JSON object with the following structure:

```json
{{
  "book_title": "{book_title}",
  "visual_style": "{visual_style}",
  "total_shots": <number of shots>,
  "shots": [
    {{
      "shot_id": 1,
      "segment_ref": <segment_id this shot belongs to>,
      "shot_purpose": "<opening_hook/insight_visualization/transition/closing>",
      "image_prompt": "<ENGLISH ONLY: Complete image generation prompt. Include scene description, composition, lighting, mood, style keywords. Must be concrete and visualizable. 100-200 words.>",
      "shot_type": "<wide shot/medium shot/close-up/extreme close-up/establishing shot>",
      "camera_angle": "<eye level/low angle/high angle/bird's eye/dutch angle>",
      "mood": "<emotional keywords in English>",
      "color_palette": "<dominant colors>",
      "narration_text": "<Copy the Chinese narration text this shot accompanies>"
    }}
  ]
}}
```

## Critical Rules for image_prompt

1. **MUST be entirely in English** - No Chinese characters
2. **MUST be concrete and visualizable** - Real scenes, real objects, real people
3. **MUST NOT contain any text elements** - No titles, labels, quotes visible in image
4. **Include style keywords at the end** - "{visual_style} style, [quality keywords]"

### Image Prompt Structure:

```
[Scene Description] + [Subject Details] + [Composition] + [Lighting/Atmosphere] + [Style Keywords]
```

### Example Image Prompts:

GOOD (for "Cognitive Revolution"):
"A prehistoric cave scene at twilight. A group of early humans sit in a semicircle around a crackling fire, their weathered faces illuminated by warm orange flames. The central figure, an elder with graying hair, gestures dramatically toward the cave ceiling where smoke creates ethereal, ghost-like shapes that seem to form animals and spirits. Other tribe members look up in wonder, their eyes reflecting the firelight. Dramatic chiaroscuro lighting, warm earth tones contrasting with cool blue shadows. {visual_style} style, detailed, atmospheric, cinematic composition, masterful lighting."

GOOD (for "Agricultural Trap"):
"Split composition image. Left half: A weary farmer in simple clothes bends over rows of golden wheat under harsh midday sun, sweat on brow, back aching, tied to the land. Right half: A hunter-gatherer walks freely through a lush green forest, carrying a simple spear, relaxed posture, surrounded by abundance of nature. The contrast between confinement and freedom, exhaustion and vitality. Symbolic divide down the center. {visual_style} style, rich colors, thoughtful composition, allegorical imagery."

BAD:
- "An image showing the concept of cognitive revolution" (too abstract)
- "Text saying 'The Agricultural Trap' with a farmer" (NO TEXT!)
- "A timeline of human history" (NO INFOGRAPHICS!)
- "The book cover of Sapiens" (NO BOOK IMAGES!)

## Style Guidance for {visual_style}

{style_guidance}

## Shot Type Guidelines

- **Opening Hook**: Usually wide/establishing shot to set the scene
- **Insight Visualization**: Mix of wide and medium shots for concepts
- **Emotional Moments**: Close-ups for impact
- **Transitions**: Can use symbolic imagery
- **Closing**: Wide shot, often with uplifting/contemplative mood

## Composition Tips

- Use visual metaphors heavily
- Contrast and juxtaposition work well for "vs" concepts
- Environmental storytelling (details tell the story)
- Lighting as emotional indicator
- Consider split-screen for before/after or comparison concepts

Now generate the shots. Return ONLY the JSON, no additional text.
"""


def _get_style_guidance(style: str) -> str:
    """Get style-specific guidance for image prompts."""

    style_guides = {
        "illustration": """
- Rich, detailed scenes with artistic interpretation
- Vibrant but harmonious color palettes
- Can include slightly stylized elements
- Quality keywords: detailed illustration, artistic, rich colors, professional artwork
""",
        "realistic": """
- Photorealistic rendering, documentary-style
- Natural lighting and authentic environments
- People should look real, not stylized
- Quality keywords: photorealistic, cinematic, natural lighting, documentary style
""",
        "watercolor": """
- Soft edges, flowing colors, dreamy atmosphere
- Impressionistic rather than precise
- Light, airy feel with visible brushwork texture
- Quality keywords: watercolor painting, soft edges, dreamy, artistic brushstrokes
""",
        "ink": """
- Chinese ink wash aesthetic (水墨风)
- High contrast, minimalist composition
- Emphasis on negative space and brushwork
- Quality keywords: Chinese ink wash, sumi-e style, minimalist, traditional brush painting
""",
        "oil_painting": """
- Rich, textured, classical art feel
- Deep colors and dramatic lighting
- Visible brushwork and painterly quality
- Quality keywords: oil painting style, classical art, rich textures, museum quality
""",
        "digital_art": """
- Modern digital illustration aesthetic
- Clean lines with gradient coloring
- Can include subtle glow effects
- Quality keywords: digital art, modern illustration, clean aesthetic, professional digital painting
"""
    }

    return style_guides.get(style, style_guides["illustration"])


# Example input for testing
BOOK_STORYBOARD_EXAMPLE_INPUT = {
    "book_title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "total_duration": 180,
    "opening_hook": "如果有人告诉你，小麦才是地球上最成功的物种，你会相信吗？在读完《人类简史》之后，你可能会改变看法。",
    "narration_segments": [
        {
            "segment_id": 1,
            "insight_ref": 1,
            "insight_title": "认知革命",
            "narration_text": "七万年前的某一天，一个智人做了一件其他动物从未做过的事——他开始讲故事。不是关于食物或危险的故事，而是关于根本不存在的东西：神灵、祖先、命运。这种讲述虚构故事的能力，改变了一切。",
            "visual_direction": "Wide establishing shot of a prehistoric campfire scene at night. A group of early humans sit in a circle, their faces lit by flickering firelight. Smoke rises and seems to form ghostly shapes against the starry sky. Camera slowly pushes toward the central figure who gestures animatedly. Warm orange lighting contrasts with deep blue night sky.",
            "duration_hint": 35
        },
        {
            "segment_id": 2,
            "insight_ref": 2,
            "insight_title": "农业陷阱",
            "narration_text": "你以为是人类驯化了小麦？赫拉利说，其实是小麦驯化了人类。想想看，为了照顾这些娇贵的植物，我们的祖先放弃了自由自在的游猎生活，开始弯腰耕种，开始为天气担忧，开始被土地束缚。",
            "visual_direction": "Split composition: left side shows an exhausted farmer bent over in golden wheat fields under harsh sun; right side shows a carefree hunter-gatherer walking freely through lush forest. Visual contrast between bondage and freedom.",
            "duration_hint": 35
        }
    ],
    "closing_statement": "这就是人类简史告诉我们的：我们统治世界，不是因为我们最强壮，而是因为我们最会讲故事。下次当你看到货币、国旗、或者公司logo时，想想看——这些都是我们共同相信的虚构故事。"
}
