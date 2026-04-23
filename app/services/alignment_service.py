"""音画对齐服务 - 使用Gemini进行图文匹配"""

import asyncio
import base64
import json
import re
from io import BytesIO
from typing import List, Optional

from PIL import Image
from google import genai
from google.genai import types
import anthropic

from app.config import settings
from app.prompts.alignment_prompts import (
    build_alignment_prompt,
    build_simple_alignment_prompt
)


class AlignmentService:
    """
    音画对齐服务

    核心逻辑：
    1. 接收Whisper的时间戳数据和所有场景图片
    2. 调用Gemini 3.1 Flash分析图片内容与文本语义
    3. 智能匹配每张图片应该对应哪个时间段
    4. 输出精确的时间轴映射

    对齐误差目标：≤ 80ms

    模型优先级: Claude Sonnet 4.6 (主) → Gemini 3.1 Flash (备用)
    """

    def __init__(self):
        # 主模型: Claude Sonnet 4.6
        self.claude_client = None
        self.claude_model = "claude-sonnet-4-6"
        if settings.ANTHROPIC_API_KEY:
            self.claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        # 备用模型: Gemini 3.1 Flash
        self.gemini_client = None
        self.gemini_model = "gemini-3.1-flash-lite-preview"
        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

        if not self.gemini_client and not self.claude_client:
            print("Warning: No LLM API key set, alignment service will fail")

    async def align_images_to_audio(
        self,
        images: List[dict],
        segments: List[dict],
        full_text: str,
        audio_duration: float,
        use_visual_matching: bool = True
    ) -> List[dict]:
        """
        将图片与音频时间段对齐

        Args:
            images: 场景图片列表
                [{"scene_id": 1, "path": "...", "visual_description": "..."}]
            segments: Whisper返回的时间戳段落
                [{"start": 0.0, "end": 5.0, "text": "..."}]
            full_text: 完整的旁白文本
            audio_duration: 音频总时长（秒）
            use_visual_matching: 是否使用图片视觉匹配（传图给LLM）

        Returns:
            [
                {
                    "scene_id": 1,
                    "image_path": "path/to/image.png",
                    "start_time": 0.0,
                    "end_time": 18.4,
                    "duration": 18.4,
                    "matched_text": "对应的旁白文本段落",
                    "segment_indices": [0, 1, 2]
                },
                ...
            ]
        """
        if not self.gemini_client and not self.claude_client:
            # 如果没有配置任何LLM，使用简单的均匀分配
            return self._fallback_alignment(images, segments, audio_duration)

        if not segments:
            # 没有segment，均匀分配
            return self._uniform_allocation(images, audio_duration)

        try:
            if use_visual_matching and all(img.get('path') for img in images):
                # 使用图片视觉匹配
                matching = await self._visual_alignment(images, segments, full_text)
            else:
                # 使用文本描述匹配
                matching = await self._text_alignment(images, segments)

            # 计算精确时间轴
            timeline = self._calculate_timeline(
                matching=matching,
                images=images,
                segments=segments,
                audio_duration=audio_duration
            )

            # 验证和调整
            timeline = self._validate_and_adjust(timeline, audio_duration)

            return timeline

        except Exception as e:
            print(f"Alignment failed: {e}, using fallback")
            return self._fallback_alignment(images, segments, audio_duration)

    async def _visual_alignment(
        self,
        images: List[dict],
        segments: List[dict],
        full_text: str
    ) -> dict:
        """
        使用图片视觉信息进行匹配

        将图片发送给Gemini进行分析
        """
        # 准备图片
        encoded_images = await self._prepare_images(images)

        # 构建prompt
        prompt = build_alignment_prompt(images, segments, full_text)

        # 构建多模态内容
        contents = []

        # 添加图片
        for i, img_data in enumerate(encoded_images):
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img_data["base64"]),
                    mime_type="image/jpeg"
                )
            )
            contents.append(f"[图片{i+1}: scene_id={img_data['scene_id']}]")

        # 添加prompt
        contents.append(prompt)

        response_text = None

        # 优先使用 Claude Sonnet 4.6（支持多模态图片输入）
        if self.claude_client:
            try:
                # 构建Claude多模态内容
                claude_content = []
                for i, img_data in enumerate(encoded_images):
                    claude_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_data["base64"]
                        }
                    })
                    claude_content.append({
                        "type": "text",
                        "text": f"[图片{i+1}: scene_id={img_data['scene_id']}]"
                    })
                claude_content.append({"type": "text", "text": prompt})

                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=16384,
                    temperature=0.2,
                    messages=[{"role": "user", "content": claude_content}]
                )
                response_text = response.content[0].text
            except Exception as e:
                print(f"  [AlignmentService] Claude视觉对齐失败: {e}，尝试Gemini")

        # Fallback到Gemini 3 Pro
        if response_text is None and self.gemini_client:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=16384
                    )
                )
                response_text = response.text
            except Exception as e:
                print(f"  [AlignmentService] Gemini视觉对齐也失败: {e}")

        if response_text is None:
            return {"matches": []}

        # 解析响应
        return self._parse_matching_response(response_text)

    async def _text_alignment(
        self,
        images: List[dict],
        segments: List[dict]
    ) -> dict:
        """
        仅使用文本描述进行匹配

        不发送图片，只根据描述匹配
        """
        scene_descriptions = [
            img.get('visual_description', img.get('description', ''))
            for img in images
        ]

        prompt = build_simple_alignment_prompt(
            scene_count=len(images),
            segments=segments,
            scene_descriptions=scene_descriptions
        )

        response_text = None

        # 优先使用 Claude Sonnet 4.6
        if self.claude_client:
            try:
                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=16384,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            except Exception as e:
                print(f"  [AlignmentService] Claude文本对齐失败: {e}，尝试Gemini")

        # Fallback到Gemini 3 Pro
        if response_text is None and self.gemini_client:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=16384
                    )
                )
                response_text = response.text
            except Exception as e:
                print(f"  [AlignmentService] Gemini文本对齐也失败: {e}")

        if response_text is None:
            return {"matches": []}

        return self._parse_allocation_response(response_text, images)

    async def _prepare_images(
        self,
        images: List[dict],
        max_size: int = 512
    ) -> List[dict]:
        """
        压缩图片并转为base64

        使用较小尺寸以节省token
        """
        encoded = []

        for img_info in images:
            try:
                path = img_info.get("path")
                if not path:
                    continue

                # 加载并压缩
                img = Image.open(path)
                img.thumbnail((max_size, max_size))

                # 转为JPEG base64（JPEG比PNG小）
                buffer = BytesIO()
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(buffer, format="JPEG", quality=85)
                b64 = base64.b64encode(buffer.getvalue()).decode()

                encoded.append({
                    "scene_id": img_info["scene_id"],
                    "base64": b64
                })

            except Exception as e:
                print(f"Failed to prepare image {img_info.get('scene_id')}: {e}")

        return encoded

    def _parse_matching_response(self, response_text: str) -> dict:
        """
        解析LLM返回的匹配结果

        Args:
            response_text: LLM的响应文本

        Returns:
            {"matches": [{"scene_id": 1, "start_segment_index": 0, "end_segment_index": 2}, ...]}
        """
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {"matches": []}

    def _parse_allocation_response(
        self,
        response_text: str,
        images: List[dict]
    ) -> dict:
        """
        解析简化对齐的响应

        将allocations格式转换为matches格式
        """
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())

                if "allocations" in data:
                    matches = []
                    for alloc in data["allocations"]:
                        indices = alloc.get("segment_indices", [])
                        if indices:
                            matches.append({
                                "scene_id": alloc["scene_id"],
                                "start_segment_index": min(indices),
                                "end_segment_index": max(indices)
                            })
                    return {"matches": matches}

                return data

        except json.JSONDecodeError:
            pass

        return {"matches": []}

    def _calculate_timeline(
        self,
        matching: dict,
        images: List[dict],
        segments: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        根据匹配结果计算精确时间轴
        """
        timeline = []
        matches = matching.get("matches", [])

        # 创建scene_id到图片信息的映射
        image_map = {img["scene_id"]: img for img in images}

        for match in matches:
            scene_id = match.get("scene_id")
            start_idx = match.get("start_segment_index", 0)
            end_idx = match.get("end_segment_index", start_idx)

            # 确保索引在有效范围内
            start_idx = max(0, min(start_idx, len(segments) - 1))
            end_idx = max(start_idx, min(end_idx, len(segments) - 1))

            # 获取对应的时间范围
            start_time = segments[start_idx]["start"]
            end_time = segments[end_idx]["end"]

            # 收集匹配的文本
            matched_texts = [
                segments[i].get("text", "")
                for i in range(start_idx, end_idx + 1)
            ]

            # 获取图片路径
            img_info = image_map.get(scene_id, {})

            timeline.append({
                "scene_id": scene_id,
                "image_path": img_info.get("path", ""),
                "start_time": start_time,
                "end_time": end_time,
                "duration": round(end_time - start_time, 3),
                "matched_text": " ".join(matched_texts),
                "segment_indices": list(range(start_idx, end_idx + 1))
            })

        # 按start_time排序
        timeline.sort(key=lambda x: x["start_time"])

        return timeline

    def _validate_and_adjust(
        self,
        timeline: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        验证并调整时间轴

        确保：
        1. 时间轴从0开始
        2. 时间轴覆盖整个音频
        3. 无重叠无间隙
        4. 处理时间戳乱序的情况
        """
        if not timeline:
            return timeline

        n = len(timeline)

        # 第一步：修复明显错误的时间戳（end < start 或者值为0）
        for i, item in enumerate(timeline):
            start = item.get("start_time", 0)
            end = item.get("end_time", 0)

            # 如果end_time为0或者小于start_time，需要修复
            if end <= start or end == 0:
                # 使用基于位置的估算
                estimated_start = (i / n) * audio_duration
                estimated_end = ((i + 1) / n) * audio_duration
                item["start_time"] = round(estimated_start, 3)
                item["end_time"] = round(estimated_end, 3)

        # 第二步：按start_time排序（确保时间递增）
        # 但保持shot_id不变
        sorted_indices = sorted(range(n), key=lambda x: timeline[x].get("start_time", 0))

        # 检查是否有严重乱序（超过50%位置变动），如果是则使用均匀分配
        position_changes = sum(1 for i, idx in enumerate(sorted_indices) if abs(i - idx) > 1)
        if position_changes > n * 0.5:
            # 时间戳太混乱，使用均匀分配
            time_per_shot = audio_duration / n
            for i, item in enumerate(timeline):
                item["start_time"] = round(i * time_per_shot, 3)
                item["end_time"] = round((i + 1) * time_per_shot, 3)
        else:
            # 第三步：调整第一个场景从0开始
            timeline[0]["start_time"] = 0.0

            # 第四步：确保递增，消除间隙和重叠
            for i in range(1, n):
                prev_end = timeline[i - 1]["end_time"]
                curr_start = timeline[i]["start_time"]
                curr_end = timeline[i]["end_time"]

                # 如果当前开始时间小于前一个结束时间，说明有重叠
                if curr_start < prev_end:
                    timeline[i]["start_time"] = prev_end

                # 如果有较大间隙，调整边界
                elif curr_start - prev_end > 0.08:  # 80ms阈值
                    mid_point = (prev_end + curr_start) / 2
                    timeline[i - 1]["end_time"] = round(mid_point, 3)
                    timeline[i]["start_time"] = round(mid_point, 3)

                # 确保当前结束时间大于开始时间
                if timeline[i]["end_time"] <= timeline[i]["start_time"]:
                    # 使用合理的估算
                    remaining_duration = audio_duration - timeline[i]["start_time"]
                    remaining_shots = n - i
                    estimated_duration = remaining_duration / remaining_shots
                    timeline[i]["end_time"] = round(timeline[i]["start_time"] + estimated_duration, 3)

        # 确保最后一个场景覆盖到音频结尾
        timeline[-1]["end_time"] = audio_duration

        # 重新计算duration
        for item in timeline:
            item["duration"] = round(
                item["end_time"] - item["start_time"],
                3
            )

        return timeline

    def _fallback_alignment(
        self,
        images: List[dict],
        segments: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        简单的回退对齐策略

        当LLM不可用时，使用基于segment数量的简单分配
        """
        if not images:
            return []

        if not segments:
            return self._uniform_allocation(images, audio_duration)

        # 尝试将segments均匀分配给scenes
        scene_count = len(images)
        segment_count = len(segments)

        # 每个场景分配的segment数量
        segments_per_scene = max(1, segment_count // scene_count)

        timeline = []
        seg_idx = 0

        for i, img in enumerate(images):
            # 计算该场景的segment范围
            start_idx = seg_idx
            if i < scene_count - 1:
                end_idx = min(seg_idx + segments_per_scene - 1, segment_count - 1)
            else:
                # 最后一个场景获取剩余所有segment
                end_idx = segment_count - 1

            # 获取时间范围
            start_time = segments[start_idx]["start"] if start_idx < segment_count else 0
            end_time = segments[end_idx]["end"] if end_idx < segment_count else audio_duration

            # 收集文本
            matched_texts = [
                segments[j].get("text", "")
                for j in range(start_idx, end_idx + 1)
                if j < segment_count
            ]

            timeline.append({
                "scene_id": img["scene_id"],
                "image_path": img.get("path", ""),
                "start_time": start_time,
                "end_time": end_time,
                "duration": round(end_time - start_time, 3),
                "matched_text": " ".join(matched_texts),
                "segment_indices": list(range(start_idx, end_idx + 1))
            })

            seg_idx = end_idx + 1

        # 验证和调整
        return self._validate_and_adjust(timeline, audio_duration)

    def _uniform_allocation(
        self,
        images: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        均匀分配时间

        当没有segment信息时使用
        """
        if not images:
            return []

        time_per_scene = audio_duration / len(images)
        timeline = []

        for i, img in enumerate(images):
            start_time = i * time_per_scene
            end_time = (i + 1) * time_per_scene if i < len(images) - 1 else audio_duration

            timeline.append({
                "scene_id": img["scene_id"],
                "image_path": img.get("path", ""),
                "start_time": round(start_time, 3),
                "end_time": round(end_time, 3),
                "duration": round(end_time - start_time, 3),
                "matched_text": "",
                "segment_indices": []
            })

        return timeline

    async def quick_align(
        self,
        scene_count: int,
        segments: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        快速对齐（不使用LLM）

        根据segment数量和场景数量进行简单分配

        Args:
            scene_count: 场景数量
            segments: Whisper返回的segments
            audio_duration: 音频总时长

        Returns:
            时间轴列表
        """
        if not segments or scene_count <= 0:
            # 均匀分配
            time_per_scene = audio_duration / max(1, scene_count)
            return [
                {
                    "scene_id": i + 1,
                    "start_time": round(i * time_per_scene, 3),
                    "end_time": round((i + 1) * time_per_scene, 3)
                    if i < scene_count - 1 else audio_duration,
                    "duration": round(time_per_scene, 3)
                }
                for i in range(scene_count)
            ]

        # 基于segment的分配
        images = [{"scene_id": i + 1} for i in range(scene_count)]
        return self._fallback_alignment(images, segments, audio_duration)

    # ============== Shot Alignment Methods ==============

    async def align_shots_to_audio(
        self,
        shots: List[dict],
        segments: List[dict],
        full_text: str,
        audio_duration: float
    ) -> List[dict]:
        """
        将shots与音频时间段对齐

        新逻辑：
        1. 每个shot有自己的narration_segment
        2. 在Whisper segments中找到对应的时间范围
        3. 基于文本匹配而非LLM推理，更精确

        Args:
            shots: 分镜后的shots列表
            segments: Whisper返回的segments
            full_text: 完整的旁白文本
            audio_duration: 音频总时长

        Returns:
            带时间戳的shot列表
        """
        if not shots:
            return []

        if not segments:
            # 没有segment，根据duration_hint分配
            return self._allocate_by_duration_hint(shots, audio_duration)

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
                "duration": round(end_time - start_time, 3),
                "narration_segment": narration,
                "shot_type": shot.get('shot_type', ''),
                "visual_description": shot.get('visual_description', ''),
                "scene_style": shot.get('scene_style', {}),
                "story_phase": shot.get('story_phase', '')
            })

        # 验证和调整
        timeline = self._validate_and_adjust(timeline, audio_duration)

        return timeline

    def _build_segment_index(
        self,
        segments: List[dict],
        full_text: str
    ) -> List[dict]:
        """
        构建segment在完整文本中的位置索引
        """
        index = []
        current_pos = 0

        for seg in segments:
            seg_text = seg.get('text', '').strip()
            if not seg_text:
                continue

            # 在full_text中找到这段文本
            pos = full_text.find(seg_text, current_pos)
            if pos == -1:
                # 尝试模糊匹配（去除空格）
                clean_seg = seg_text.replace(' ', '')
                clean_full = full_text.replace(' ', '')
                clean_pos = clean_full.find(clean_seg)
                if clean_pos != -1:
                    pos = clean_pos
                else:
                    pos = current_pos  # 找不到就用当前位置

            index.append({
                "start_pos": pos,
                "end_pos": pos + len(seg_text),
                "start_time": seg.get('start', 0),
                "end_time": seg.get('end', 0),
                "text": seg_text
            })

            current_pos = pos + len(seg_text)

        return index

    def _convert_to_simplified(self, text: str) -> str:
        """
        将繁体中文转换为简体中文

        Whisper经常返回繁体中文，需要转换后才能与简体中文的原文匹配
        """
        # 常见繁简对照（只列出对齐时常见的字）
        traditional_to_simplified = {
            '後': '后', '鐵': '铁', '燈': '灯', '個': '个', '裡': '里',
            '開': '开', '種': '种', '這': '这', '們': '们', '説': '说',
            '對': '对', '時': '时', '會': '会', '來': '来', '過': '过',
            '進': '进', '還': '还', '電': '电', '現': '现', '發': '发',
            '經': '经', '動': '动', '處': '处', '從': '从', '頭': '头',
            '點': '点', '間': '间', '問': '问', '機': '机', '關': '关',
            '長': '长', '當': '当', '實': '实', '無': '无', '樣': '样',
            '見': '见', '體': '体', '書': '书', '學': '学', '應': '应',
            '給': '给', '產': '产', '話': '话', '幾': '几', '變': '变',
            '車': '车', '讓': '让', '認': '认', '場': '场', '馬': '马',
            '親': '亲', '輕': '轻', '聲': '声', '號': '号', '歡': '欢',
            '層': '层', '準': '准', '寫': '写', '決': '决', '統': '统',
            '調': '调', '壓': '压', '許': '许', '設': '设', '獲': '获',
            '確': '确', '響': '响', '報': '报', '驗': '验', '據': '据',
            '議': '议', '環': '环', '選': '选', '讀': '读', '樂': '乐',
            '導': '导', '隊': '队', '辦': '办', '運': '运', '區': '区',
            '節': '节', '農': '农', '遠': '远', '願': '愿', '畫': '画',
            '邊': '边', '類': '类', '離': '离', '達': '达', '滿': '满',
            '積': '积', '結': '结', '觀': '观', '幫': '帮', '務': '务',
            '蘭': '兰', '識': '识', '師': '师', '條': '条', '飛': '飞',
            '殺': '杀', '齊': '齐', '圖': '图', '讓': '让', '養': '养',
            '護': '护', '組': '组', '買': '买', '總': '总', '術': '术',
            '醫': '医', '興': '兴', '參': '参', '該': '该', '貨': '货',
            '質': '质', '專': '专', '著': '着', '雙': '双', '裝': '装',
            '親': '亲', '擔': '担', '備': '备', '補': '补', '資': '资',
            '構': '构', '歷': '历', '複': '复', '屬': '属', '廣': '广',
            '僅': '仅', '漸': '渐', '係': '系', '顯': '显', '壞': '坏',
            '擁': '拥', '執': '执', '臉': '脸', '創': '创', '負': '负',
            '齒': '齿', '優': '优', '軟': '软', '歸': '归', '極': '极',
            '級': '级', '紀': '纪', '絕': '绝', '習': '习', '縣': '县',
            '濟': '济', '純': '纯', '終': '终', '繼': '继', '線': '线',
            '續': '续', '緊': '紧', '網': '网', '練': '练', '維': '维',
            '綠': '绿', '縮': '缩', '鏡': '镜', '聲': '声', '藝': '艺',
            '頭': '头', '顧': '顾', '響': '响', '順': '顺', '領': '领',
            '題': '题', '願': '愿', '颳': '刮', '風': '风', '驚': '惊',
            '體': '体', '鳥': '鸟', '傷': '伤', '佛': '佛', '僅': '仅',
            # 补充更多常见繁简对照
            '蒼': '苍', '帶': '带', '鬆': '松', '沒': '没', '開': '开',
            '説': '说', '軀': '躯', '殼': '壳', '節': '节', '張': '张',
            '國': '国', '圍': '围', '園': '园', '幹': '干', '並': '并',
            '麼': '么', '無': '无', '頓': '顿', '腦': '脑', '語': '语',
            '歲': '岁', '觸': '触', '稀': '稀', '鋪': '铺', '亂': '乱',
            '競': '竞', '賞': '赏', '貫': '贯', '輪': '轮', '淺': '浅',
            '飄': '飘', '靈': '灵', '剛': '刚', '嗎': '吗', '吶': '呐',
            '傳': '传', '嘆': '叹', '嚐': '尝', '夠': '够', '奮': '奋',
            '緣': '缘', '縱': '纵', '適': '适', '遲': '迟', '邊': '边',
            '躍': '跃', '舉': '举', '獨': '独', '獻': '献', '貼': '贴',
            '歎': '叹', '燒': '烧', '燙': '烫', '爐': '炉', '爺': '爷',
            '當': '当', '異': '异', '瘋': '疯', '療': '疗', '盜': '盗',
            '盤': '盘', '睜': '睁', '睞': '睐', '碼': '码', '禮': '礼',
        }

        result = text
        for trad, simp in traditional_to_simplified.items():
            result = result.replace(trad, simp)
        return result

    def _find_text_position(
        self,
        narration: str,
        full_text: str
    ) -> tuple:
        """
        找到narration在完整文本中的字符位置

        使用多种匹配策略处理TTS原文与Whisper识别文本之间的差异：
        - 标点符号差异（句号vs逗号）
        - 空格差异
        - 简繁体差异（Whisper常输出繁体）
        - 细微用词差异（"的"/"地"等）
        """
        if not narration:
            return -1, -1

        # 清理文本
        narration_clean = narration.strip()

        # 将full_text从繁体转为简体（Whisper常返回繁体）
        full_text_simplified = self._convert_to_simplified(full_text)

        # 直接查找
        start = full_text_simplified.find(narration_clean)
        if start != -1:
            return start, start + len(narration_clean)

        # 策略1：去除标点符号匹配
        import re
        punct_pattern = r'[。！？，、；：""''（）《》【】\s\.!?,;:\'\"\(\)\[\]]'
        narration_no_punct = re.sub(punct_pattern, '', narration_clean)
        full_text_no_punct = re.sub(punct_pattern, '', full_text_simplified)

        if narration_no_punct and len(narration_no_punct) >= 5:
            start = full_text_no_punct.find(narration_no_punct)
            if start != -1:
                # 找到了，需要计算原文中的大致位置
                # 使用比例估算
                ratio = start / len(full_text_no_punct) if full_text_no_punct else 0
                estimated_start = int(ratio * len(full_text_simplified))
                estimated_end = estimated_start + len(narration_clean)
                return estimated_start, estimated_end

        # 策略2：使用narration的前10-15字进行前缀匹配
        if len(narration_no_punct) > 10:
            prefix = narration_no_punct[:min(15, len(narration_no_punct))]
            start = full_text_no_punct.find(prefix)
            if start != -1:
                ratio = start / len(full_text_no_punct) if full_text_no_punct else 0
                estimated_start = int(ratio * len(full_text_simplified))
                estimated_end = estimated_start + len(narration_clean)
                return estimated_start, estimated_end

        # 策略3：使用子序列匹配（取narration中连续的5-8个字）
        if len(narration_no_punct) >= 8:
            # 尝试不同位置的子串
            for i in range(0, min(len(narration_no_punct) - 8, 20), 3):
                sub = narration_no_punct[i:i+8]
                start = full_text_no_punct.find(sub)
                if start != -1:
                    ratio = start / len(full_text_no_punct) if full_text_no_punct else 0
                    estimated_start = int(ratio * len(full_text_simplified))
                    estimated_end = estimated_start + len(narration_clean)
                    return estimated_start, estimated_end

        # 实在找不到，返回-1
        return -1, -1

    def _get_time_range(
        self,
        start_pos: int,
        end_pos: int,
        segment_index: List[dict],
        segments: List[dict]
    ) -> tuple:
        """
        根据文本位置获取对应的时间范围
        """
        if start_pos == -1 or not segment_index:
            # 找不到位置，返回0
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
            end_time = segments[-1].get('end', 0) if segments else 0

        return start_time, end_time

    def _allocate_by_duration_hint(
        self,
        shots: List[dict],
        audio_duration: float
    ) -> List[dict]:
        """
        根据duration_hint分配时间

        当没有segment信息时使用
        """
        if not shots:
            return []

        # 计算总的预估时长
        total_hint = sum(shot.get('duration_hint', 10) for shot in shots)

        # 按比例分配
        timeline = []
        current_time = 0

        for shot in shots:
            hint = shot.get('duration_hint', 10)
            duration = (hint / total_hint) * audio_duration if total_hint > 0 else audio_duration / len(shots)

            timeline.append({
                "shot_id": shot.get('shot_id'),
                "original_scene_id": shot.get('original_scene_id'),
                "image_prompt": shot.get('image_prompt'),
                "start_time": round(current_time, 3),
                "end_time": round(current_time + duration, 3),
                "duration": round(duration, 3),
                "narration_segment": shot.get('narration_segment', ''),
                "shot_type": shot.get('shot_type', ''),
                "visual_description": shot.get('visual_description', ''),
                "scene_style": shot.get('scene_style', {}),
                "story_phase": shot.get('story_phase', '')
            })

            current_time += duration

        # 确保最后一个覆盖到结尾
        if timeline:
            timeline[-1]['end_time'] = audio_duration
            timeline[-1]['duration'] = round(audio_duration - timeline[-1]['start_time'], 3)

        return timeline
