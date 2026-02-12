# 序话Story - 分镜细化优化指令

## 问题诊断

当前系统生成的scene数量太少（13张图配8分钟音频，平均37秒/张），而市面主流漫剧是6-8秒/张。

**根本原因**：
1. 故事生成阶段没有控制每个scene的narration长度
2. 分镜决策阶段是1:1映射，没有拆分逻辑
3. 中文TTS实际速度约4字/秒（240字/分钟），比预估的200字/分钟更慢

**目标**：
- 每个shot对应6-10秒音频（约25-40字narration）
- 8分钟视频应该有48-80张图

---

## 优化方案：两阶段控制

### 阶段1：故事生成prompt微调（软性约束）

修改 `app/prompts/story_generation.py`，在prompt中增加场景拆分指导：

```python
def build_story_generation_prompt(...):
    # ... 现有代码 ...
    
    # 在"创作要点"部分增加以下内容：
    prompt += """
## 创作要点

1. **故事节奏**: 短视频观众注意力有限，开头3秒必须抓人，每个场景都要有信息增量

2. **场景拆分原则**（重要！）: 
   - 每个scene的narration控制在**40-80字**（对应10-20秒音频）
   - 如果一个情节单元内容较多，应拆分成多个连续scene
   - 拆分依据：地点变化、人物动作变化、镜头切换（全景/中景/特写）、情绪转折
   - 例如"篝火夜谈"可以拆成：全景入场 → 特写讲述者 → 特写倾听者 → 温馨合影
   
3. **视觉思维**: 每个scene的visual_description要具体到可以直接用于AI图像生成，描述单一画面

4. **字数与时长对应**:
   - 中文TTS朗读速度约 4字/秒
   - 40字 ≈ 10秒，80字 ≈ 20秒
   - duration_hint 应该 = narration字数 ÷ 4

5. **角色一致性**: characters中的外貌描述要详细且固定

6. **分镜数量参考**: 
   - 3分钟视频（180秒）→ 约18-30个scene
   - 5分钟视频（300秒）→ 约30-50个scene
   - 8分钟视频（480秒）→ 约48-80个scene

现在开始创作：
"""
```

### 阶段2：分镜细化服务（兜底拆分）

在 `app/services/storyboard_service.py` 中新增拆分逻辑：

```python
import json
import google.generativeai as genai
from app.config import settings

class StoryboardService:
    
    # 拆分阈值配置
    MAX_NARRATION_LENGTH = 60  # 超过60字的scene需要拆分
    TARGET_SHOT_LENGTH = 40    # 目标每个shot约40字（10秒）
    MIN_SHOT_LENGTH = 25       # 最小shot长度
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_storyboard(
        self,
        scenes: list[dict],
        characters: list[dict],
        style_preset: str,
        aspect_ratio: str = "16:9"
    ) -> list[dict]:
        """
        生成分镜板
        
        流程：
        1. 遍历所有scene
        2. 检测是否需要拆分（narration > MAX_NARRATION_LENGTH）
        3. 需要拆分的调用LLM细化
        4. 不需要拆分的直接生成image_prompt
        5. 返回完整的shot列表
        """
        storyboard = []
        shot_index = 1
        
        for scene in scenes:
            scene_id = scene.get('scene_id', len(storyboard) + 1)
            narration = scene.get('narration', '')
            narration_length = len(narration)
            
            if narration_length > self.MAX_NARRATION_LENGTH:
                # 需要拆分
                sub_shots = await self._split_scene_to_shots(
                    scene=scene,
                    characters=characters,
                    style_preset=style_preset
                )
                
                for i, shot in enumerate(sub_shots):
                    shot['shot_id'] = shot_index
                    shot['original_scene_id'] = scene_id
                    shot['aspect_ratio'] = aspect_ratio
                    storyboard.append(shot)
                    shot_index += 1
            else:
                # 不需要拆分，直接生成
                shot = self._create_shot_from_scene(
                    scene=scene,
                    characters=characters,
                    style_preset=style_preset
                )
                shot['shot_id'] = shot_index
                shot['original_scene_id'] = scene_id
                shot['aspect_ratio'] = aspect_ratio
                storyboard.append(shot)
                shot_index += 1
        
        return storyboard
    
    async def _split_scene_to_shots(
        self,
        scene: dict,
        characters: list[dict],
        style_preset: str
    ) -> list[dict]:
        """
        将长场景拆分成多个shot
        
        调用LLM分析narration中的视觉切换点，拆分成独立的画面单元
        """
        narration = scene.get('narration', '')
        visual_description = scene.get('visual_description', '')
        location = scene.get('location', '')
        time = scene.get('time', '')
        mood = scene.get('mood', '')
        
        # 计算需要拆成几个shot
        estimated_shots = max(2, len(narration) // self.TARGET_SHOT_LENGTH)
        
        # 构建拆分prompt
        prompt = f"""你是一位专业的分镜师。请将以下场景拆分成 {estimated_shots} 个独立的镜头（shot）。

## 原始场景

**地点**: {location}
**时间**: {time}
**氛围**: {mood}
**视觉描述**: {visual_description}
**旁白文本**: {narration}

## 出场角色

{json.dumps([{{"name": c["name"], "description": c["description"]}} for c in characters], ensure_ascii=False, indent=2)}

## 拆分要求

1. **每个shot对应25-50字的narration**（约6-12秒音频）
2. **每个shot描述单一画面**，有明确的视觉焦点
3. **拆分依据**：
   - 镜头切换（全景/中景/特写/仰拍/俯拍）
   - 人物动作变化
   - 视觉焦点转移
   - 情绪节奏变化
4. **保持连贯性**：拆分后的shots应该流畅衔接
5. **narration分配**：将原文本按语义边界分配给各shot，不要改写

## 输出格式

请以JSON格式输出：

```json
{{
  "shots": [
    {{
      "shot_index": 1,
      "shot_type": "全景/中景/特写/...",
      "visual_description": "这个镜头的具体画面描述，用于图像生成",
      "narration_segment": "对应的旁白文本段落（从原文截取，不要改写）",
      "focus": "画面焦点（人物/物体/场景）",
      "camera_angle": "镜头角度（平视/仰拍/俯拍/侧面）"
    }}
  ]
}}
```

请严格按照JSON格式输出，确保narration_segment拼接起来等于原始narration。
"""
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "response_mime_type": "application/json"
                }
            )
            
            result = json.loads(response.text)
            shots = result.get('shots', [])
            
            # 转换为标准shot格式
            formatted_shots = []
            for shot in shots:
                formatted_shots.append({
                    "image_prompt": self._build_shot_prompt(
                        shot=shot,
                        characters=characters,
                        style_preset=style_preset,
                        location=location,
                        time=time,
                        mood=mood
                    ),
                    "negative_prompt": build_negative_prompt(style_preset),
                    "narration_segment": shot.get('narration_segment', ''),
                    "shot_type": shot.get('shot_type', ''),
                    "visual_description": shot.get('visual_description', ''),
                    "duration_hint": len(shot.get('narration_segment', '')) / 4  # 4字/秒
                })
            
            return formatted_shots
            
        except Exception as e:
            # 拆分失败，回退到简单的按字数切分
            print(f"LLM拆分失败，使用简单切分: {e}")
            return self._simple_split(scene, characters, style_preset)
    
    def _simple_split(
        self,
        scene: dict,
        characters: list[dict],
        style_preset: str
    ) -> list[dict]:
        """
        简单的按字数切分（LLM拆分失败时的兜底方案）
        """
        narration = scene.get('narration', '')
        visual_description = scene.get('visual_description', '')
        
        # 按句号/感叹号/问号分割
        import re
        sentences = re.split(r'([。！？])', narration)
        
        # 重新组合句子（保留标点）
        segments = []
        current_segment = ''
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i+1] if i+1 < len(sentences) else ''
            
            if len(current_segment) + len(sentence) < self.TARGET_SHOT_LENGTH * 1.5:
                current_segment += sentence + punct
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence + punct
        
        if current_segment:
            segments.append(current_segment)
        
        # 生成shots
        shots = []
        for i, segment in enumerate(segments):
            shots.append({
                "image_prompt": build_image_prompt(
                    {**scene, 'visual_description': f"{visual_description} (第{i+1}部分)"},
                    characters,
                    style_preset
                ),
                "negative_prompt": build_negative_prompt(style_preset),
                "narration_segment": segment,
                "shot_type": "中景",
                "visual_description": visual_description,
                "duration_hint": len(segment) / 4
            })
        
        return shots
    
    def _build_shot_prompt(
        self,
        shot: dict,
        characters: list[dict],
        style_preset: str,
        location: str,
        time: str,
        mood: str
    ) -> str:
        """
        为单个shot构建图像生成prompt
        """
        from app.prompts.storyboard_prompts import STYLE_PROMPTS, extract_characters_from_narration
        
        visual_desc = shot.get('visual_description', '')
        shot_type = shot.get('shot_type', '')
        camera_angle = shot.get('camera_angle', '平视')
        focus = shot.get('focus', '')
        narration = shot.get('narration_segment', '')
        
        # 提取出现的角色
        scene_characters = extract_characters_from_narration(narration, characters)
        
        # 构建prompt
        prompt_parts = [
            visual_desc,
            f"Shot type: {shot_type}",
            f"Camera angle: {camera_angle}",
            f"Setting: {location}, {time}, {mood} atmosphere",
        ]
        
        if focus:
            prompt_parts.append(f"Focus on: {focus}")
        
        if scene_characters:
            char_descs = [f"{c['name']}: {c['description']}" for c in scene_characters]
            prompt_parts.append("Characters: " + "; ".join(char_descs))
        
        prompt_parts.append(f"Style: {STYLE_PROMPTS.get(style_preset, style_preset)}")
        prompt_parts.append("high quality, detailed, professional artwork")
        
        return ", ".join(prompt_parts)
    
    def _create_shot_from_scene(
        self,
        scene: dict,
        characters: list[dict],
        style_preset: str
    ) -> dict:
        """
        将不需要拆分的scene直接转为shot
        """
        from app.prompts.storyboard_prompts import build_image_prompt, build_negative_prompt
        
        return {
            "image_prompt": build_image_prompt(scene, characters, style_preset),
            "negative_prompt": build_negative_prompt(style_preset),
            "narration_segment": scene.get('narration', ''),
            "shot_type": "中景",
            "visual_description": scene.get('visual_description', ''),
            "duration_hint": len(scene.get('narration', '')) / 4
        }
```

### 阶段3：更新alignment_service.py

对齐服务需要适配新的shot结构。主要变化是：
- 输入从`scenes`变成`shots`
- 每个shot有自己的`narration_segment`，对齐更精确

```python
# 在 alignment_service.py 中

async def align_shots_to_audio(
    self,
    shots: list[dict],          # 分镜后的shots（非原始scenes）
    segments: list[dict],       # Whisper返回的segments
    full_text: str,
    audio_duration: float
) -> list[dict]:
    """
    将shots与音频时间段对齐
    
    新逻辑：
    1. 每个shot有自己的narration_segment
    2. 在Whisper segments中找到对应的时间范围
    3. 基于文本匹配而非LLM推理，更精确
    """
    timeline = []
    
    # 构建segment文本索引（用于快速匹配）
    segment_text_positions = self._build_segment_index(segments, full_text)
    
    for shot in shots:
        narration = shot.get('narration_segment', '')
        
        # 在完整文本中找到这段narration的位置
        start_pos, end_pos = self._find_text_position(narration, full_text)
        
        # 根据文本位置找到对应的时间范围
        start_time, end_time = self._get_time_range(
            start_pos, end_pos, segment_text_positions, segments
        )
        
        timeline.append({
            "shot_id": shot.get('shot_id'),
            "original_scene_id": shot.get('original_scene_id'),
            "image_prompt": shot.get('image_prompt'),
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "narration_segment": narration
        })
    
    # 验证和调整
    timeline = self._validate_and_adjust(timeline, audio_duration)
    
    return timeline

def _build_segment_index(self, segments: list, full_text: str) -> list:
    """
    构建segment在完整文本中的位置索引
    """
    index = []
    current_pos = 0
    
    for seg in segments:
        seg_text = seg['text'].strip()
        # 在full_text中找到这段文本
        pos = full_text.find(seg_text, current_pos)
        if pos == -1:
            pos = current_pos  # 找不到就用当前位置
        
        index.append({
            "start_pos": pos,
            "end_pos": pos + len(seg_text),
            "start_time": seg['start'],
            "end_time": seg['end'],
            "text": seg_text
        })
        
        current_pos = pos + len(seg_text)
    
    return index

def _find_text_position(self, narration: str, full_text: str) -> tuple:
    """
    找到narration在完整文本中的字符位置
    """
    # 清理文本
    narration_clean = narration.strip()
    
    # 直接查找
    start = full_text.find(narration_clean)
    if start != -1:
        return start, start + len(narration_clean)
    
    # 如果找不到完整匹配，尝试模糊匹配（取前20字）
    if len(narration_clean) > 20:
        prefix = narration_clean[:20]
        start = full_text.find(prefix)
        if start != -1:
            return start, start + len(narration_clean)
    
    # 实在找不到，返回-1
    return -1, -1

def _get_time_range(
    self,
    start_pos: int,
    end_pos: int,
    segment_index: list,
    segments: list
) -> tuple:
    """
    根据文本位置获取对应的时间范围
    """
    if start_pos == -1:
        # 找不到位置，均分时间
        return 0, 0
    
    start_time = None
    end_time = None
    
    for seg_info in segment_index:
        # 找到包含start_pos的segment
        if start_time is None and seg_info['start_pos'] <= start_pos < seg_info['end_pos']:
            start_time = seg_info['start_time']
        
        # 找到包含end_pos的segment
        if seg_info['start_pos'] < end_pos <= seg_info['end_pos']:
            end_time = seg_info['end_time']
            break
        
        # 如果end_pos超过了当前segment，继续找
        if seg_info['end_pos'] < end_pos:
            end_time = seg_info['end_time']
    
    if start_time is None:
        start_time = 0
    if end_time is None:
        end_time = segments[-1]['end'] if segments else 0
    
    return start_time, end_time
```

---

## 数据结构变化

### 原来的流程
```
scenes (13个) → images (13张) → timeline (13条)
```

### 优化后的流程
```
scenes (13个) → shots (50-80个) → images (50-80张) → timeline (50-80条)
```

### shot数据结构
```json
{
  "shot_id": 1,
  "original_scene_id": 1,
  "image_prompt": "完整的图像生成prompt",
  "negative_prompt": "负面提示词",
  "narration_segment": "这个shot对应的旁白文本",
  "shot_type": "特写/中景/全景",
  "visual_description": "画面描述",
  "aspect_ratio": "16:9",
  "duration_hint": 10.5
}
```

---

## 配置项

在 `app/config.py` 中添加：

```python
# 分镜拆分配置
SHOT_MAX_NARRATION_LENGTH: int = 60    # 超过此字数的scene需要拆分
SHOT_TARGET_LENGTH: int = 40           # 目标每个shot的字数
SHOT_MIN_LENGTH: int = 25              # 最小shot字数
TTS_CHARS_PER_SECOND: float = 4.0      # TTS朗读速度（字/秒）
```

---

## 验收标准

| 标准 | 说明 |
|------|------|
| 拆分数量 | 8分钟视频应生成48-80个shot |
| 单shot时长 | 每个shot对应6-15秒音频 |
| 文本完整性 | 所有shot的narration_segment拼接 = 原始完整narration |
| 时间轴覆盖 | timeline覆盖完整音频，无间隙无重叠 |
| 向后兼容 | 不影响短narration场景的处理 |

---

## 测试建议

1. **单元测试**：测试`_split_scene_to_shots()`对长场景的拆分效果
2. **集成测试**：用之前的teststory3重新跑一遍，对比shot数量
3. **边界测试**：测试刚好60字、59字、61字的场景

---

## 执行顺序

1. 修改 `app/prompts/story_generation.py` — 增加软性约束
2. 修改 `app/services/storyboard_service.py` — 增加拆分逻辑
3. 修改 `app/prompts/storyboard_prompts.py` — 增加辅助函数
4. 修改 `app/services/alignment_service.py` — 适配shot结构
5. 更新 `app/config.py` — 添加配置项
6. 测试验证
