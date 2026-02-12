"""图文匹配对齐的prompt模板"""


def build_alignment_prompt(
    images: list,
    segments: list,
    full_text: str
) -> str:
    """
    构建图文匹配的prompt

    Args:
        images: 图片信息列表 [{"scene_id": 1, "visual_description": "..."}, ...]
        segments: Whisper返回的segments [{"start": 0.0, "end": 5.0, "text": "..."}, ...]
        full_text: 完整旁白文本

    Returns:
        用于Gemini的prompt
    """
    # 格式化segments信息
    segments_info = []
    for i, seg in enumerate(segments):
        segments_info.append(
            f"[段落{i+1}] {seg['start']:.2f}s - {seg['end']:.2f}s: {seg.get('text', '')}"
        )

    # 格式化图片信息
    images_info = []
    for i, img in enumerate(images):
        desc = img.get('visual_description', img.get('description', '无描述'))
        images_info.append(
            f"图片{i+1} (scene_id={img['scene_id']}): {desc[:100]}..."
            if len(desc) > 100 else
            f"图片{i+1} (scene_id={img['scene_id']}): {desc}"
        )

    prompt = f"""你是一个专业的视频编辑助手。请分析以下图片和音频文本，将每张图片匹配到最合适的音频时间段。

## 音频转录（带时间戳）

{chr(10).join(segments_info)}

## 图片列表

{chr(10).join(images_info)}

## 任务

分析每张图片的内容，将其匹配到语义上最相关的音频段落。

## 匹配原则

1. **语义匹配**：图片内容应与对应文本在语义上相关
2. **顺序性**：图片通常按故事顺序排列，匹配结果应大致保持顺序
3. **完整覆盖**：所有图片必须分配时间段，所有时间段必须被覆盖
4. **无重叠**：相邻图片的时间段不能重叠
5. **时长合理**：每张图片的停留时长应合理（通常5-30秒）

## 输出格式

请以JSON格式输出匹配结果：

```json
{{
  "matches": [
    {{
      "scene_id": 1,
      "start_segment_index": 0,
      "end_segment_index": 2,
      "reasoning": "简短说明匹配理由"
    }}
  ]
}}
```

注意：
- scene_id 必须与图片列表中的scene_id对应
- start_segment_index 和 end_segment_index 是段落的索引（从0开始）
- 请严格按照JSON格式输出，不要添加其他内容
"""
    return prompt


def build_simple_alignment_prompt(
    scene_count: int,
    segments: list,
    scene_descriptions: list = None
) -> str:
    """
    构建简化的对齐prompt（不需要图片）

    当我们已知场景数量和描述时，可以直接让LLM分配时间段

    Args:
        scene_count: 场景数量
        segments: Whisper返回的segments
        scene_descriptions: 场景描述列表（可选）

    Returns:
        用于Gemini的prompt
    """
    # 格式化segments信息
    segments_info = []
    for i, seg in enumerate(segments):
        segments_info.append(
            f"[{i}] {seg['start']:.2f}s - {seg['end']:.2f}s: {seg.get('text', '')}"
        )

    # 格式化场景描述
    scenes_info = ""
    if scene_descriptions:
        scenes_list = []
        for i, desc in enumerate(scene_descriptions):
            scenes_list.append(f"场景{i+1}: {desc[:80]}...")
        scenes_info = f"""
## 场景描述

{chr(10).join(scenes_list)}
"""

    prompt = f"""你是一个视频编辑助手。请将音频段落分配给{scene_count}个场景。

## 音频转录（共{len(segments)}个段落）

{chr(10).join(segments_info)}
{scenes_info}
## 任务

将上述{len(segments)}个音频段落分配给{scene_count}个场景，确保：
1. 每个场景至少分配1个段落
2. 段落按顺序分配，不能跳跃
3. 分配尽量均匀

## 输出格式（JSON）

```json
{{
  "allocations": [
    {{
      "scene_id": 1,
      "segment_indices": [0, 1, 2]
    }},
    {{
      "scene_id": 2,
      "segment_indices": [3, 4]
    }}
  ]
}}
```

请严格按照JSON格式输出。
"""
    return prompt


def build_validation_prompt(
    timeline: list,
    audio_duration: float
) -> str:
    """
    构建时间轴验证的prompt

    用于让LLM检查和修正时间轴

    Args:
        timeline: 初步生成的时间轴
        audio_duration: 音频总时长

    Returns:
        验证prompt
    """
    timeline_info = []
    for item in timeline:
        timeline_info.append(
            f"场景{item['scene_id']}: {item['start_time']:.2f}s - {item['end_time']:.2f}s "
            f"(时长: {item['duration']:.2f}s)"
        )

    prompt = f"""请检查以下视频时间轴是否有问题：

## 音频总时长
{audio_duration:.2f}秒

## 当前时间轴

{chr(10).join(timeline_info)}

## 检查项

1. 是否从0秒开始？
2. 是否覆盖到音频结尾（{audio_duration:.2f}秒）？
3. 是否有时间重叠？
4. 是否有时间间隙？
5. 每个场景的时长是否合理（5-60秒）？

## 输出格式

如果没有问题：
```json
{{"valid": true}}
```

如果有问题，请说明并给出修正后的时间轴：
```json
{{
  "valid": false,
  "issues": ["问题1", "问题2"],
  "corrected_timeline": [
    {{"scene_id": 1, "start_time": 0.0, "end_time": 15.0}},
    ...
  ]
}}
```
"""
    return prompt
