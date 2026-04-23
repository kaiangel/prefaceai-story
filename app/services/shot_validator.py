"""
T17+T28: Shot 后置视觉验证服务

使用 Haiku 4.5 对生成的 shot 图片进行视觉质检：
1. 角色数量是否匹配预期
2. 是否存在重复对话气泡
3. 关键道具是否存在（T28: >50% 缺失则判定失败）

验证不通过时上层 pipeline 会 retry 生成。
"""

import json
import base64
import io
from typing import Optional, List
from PIL import Image

try:
    import anthropic
except ImportError:
    anthropic = None


HAIKU_MODEL = "claude-haiku-4-5-20251001"

VALIDATION_PROMPT_BASE = """Analyze this comic panel image precisely:

1. How many distinct human characters are visible in this image who appear to be NAMED/FEATURED subjects of the scene? Count carefully — include partially visible characters (e.g., only face or upper body shown) who are positioned as scene subjects with distinct, deliberate clothing/appearance. Do NOT count: animals, objects, decorative background figures, unnamed bystanders, passersby, crowd members, or ambient human figures who are clearly NOT the focus of the scene. FOCUS on characters with intentional styling who are central to the composition.

2. Are there any speech bubbles or thought bubbles containing IDENTICAL duplicate text? (Same text appearing in two or more separate bubbles)

3. Does this image contain any VISUAL UNNATURALNESS caused by image generation errors? Check these 3 dimensions:
   a) ANATOMICAL: disconnected or floating body parts not attached to a body, extra limbs (3+ hands or arms on one person), severely incorrect finger count, joints bent in physically impossible directions
   b) PHYSICS: people or objects defying gravity without any support or fantasy context, body poses that are physically impossible for a human skeleton
   c) SPATIAL: major scale inconsistencies (e.g., an adult character rendered the same height as a small child standing next to them)

   CRITICAL — Do NOT flag these as unnatural (they are intentional artistic choices):
   - Stylized proportions: anime large eyes, cartoon oversized heads, pixel art blocky shapes, chibi proportions
   - Artistic simplification: ink-wash minimalist limbs, watercolor soft/blurred edges, oil painting rough brushwork
   - Intentional surreal or fantasy elements: dream sequences, magical floating, supernatural events
   - Exaggerated expressions or dynamic action poses common in manga/comic art

   Only flag issues that clearly appear to be IMAGE GENERATION FAILURES — artifacts the artist did NOT intend."""

VALIDATION_PROMPT_PROPS = """
4. For each of the following key props, is it clearly visible in the image? Answer true if present, false if not found: {props_list}"""

VALIDATION_RESPONSE_BASE = """
Respond ONLY with JSON, no other text:
{"character_count": N, "has_duplicate_bubbles": true/false, "has_visual_unnaturalness": true/false, "unnaturalness_details": "brief description or empty string"}"""

VALIDATION_RESPONSE_WITH_PROPS = """
Respond ONLY with JSON, no other text:
{"character_count": N, "has_duplicate_bubbles": true/false, "has_visual_unnaturalness": true/false, "unnaturalness_details": "brief description or empty string", "props_found": {"prop_name": true/false, ...}}"""


class ShotValidator:
    """Haiku 4.5 视觉验证器 — 验证 shot 图片的角色数量和气泡重复"""

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        if anthropic is None:
            print("[ShotValidator] ❌ anthropic 模块未安装 — 所有视觉验证将被跳过（pip install anthropic）")
            return
        try:
            self.client = anthropic.AsyncAnthropic()
            print("[ShotValidator] ✅ Haiku 4.5 视觉验证器已初始化")
        except Exception as e:
            print(f"[ShotValidator] ❌ Anthropic 客户端初始化失败: {e} — 所有视觉验证将被跳过")

    async def validate_shot(
        self,
        pil_image: Image.Image,
        expected_character_count: int,
        text_overlay_data: Optional[dict] = None,
        key_props: Optional[List[str]] = None
    ) -> dict:
        """
        验证单个 shot 图片

        Args:
            pil_image: 生成的 PIL 图片
            expected_character_count: 预期角色数量（来自 characters_visible）
            text_overlay_data: text_overlay 数据（用于判断是否有对话需要检测气泡重复）
            key_props: T28 关键道具列表（来自 shot 的 image_prompt 中提取的道具）

        Returns:
            {
                "valid": bool,
                "actual_character_count": int,
                "has_duplicate_bubbles": bool,
                "missing_props": list[str],
                "reason": str  # 不通过时的原因
            }
        """
        if not self.client:
            print("[ShotValidator] ⚠️ client=None，跳过验证（返回 valid=True）")
            return {"valid": True, "actual_character_count": -1,
                    "has_duplicate_bubbles": False, "missing_props": [],
                    "has_visual_unnaturalness": False, "unnaturalness_details": "",
                    "reason": "validator disabled"}

        props_desc = f", key_props={key_props}" if key_props else ""
        print(f"[ShotValidator] 验证开始: expected_chars={expected_character_count}{props_desc}")

        try:
            # PIL Image → base64
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            image_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

            # T28: 构建 prompt（根据是否有 key_props 动态调整）
            prompt_text = VALIDATION_PROMPT_BASE
            if key_props:
                props_list = ", ".join(f'"{p}"' for p in key_props)
                prompt_text += VALIDATION_PROMPT_PROPS.format(props_list=props_list)
                prompt_text += VALIDATION_RESPONSE_WITH_PROPS
            else:
                prompt_text += VALIDATION_RESPONSE_BASE

            # 调用 Haiku 4.5
            response = await self.client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=384,  # T-H: 256→384（unnaturalness_details 描述可能较长）
                temperature=0.2,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }]
            )

            # 解析 JSON 响应
            raw_text = response.content[0].text.strip()
            # 提取 JSON（应对模型可能添加的多余文字）
            json_start = raw_text.find("{")
            json_end = raw_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(raw_text[json_start:json_end])
            else:
                print(f"[ShotValidator] ⚠️ 无法解析 Haiku 响应: {raw_text}")
                return {"valid": True, "actual_character_count": -1,
                        "has_duplicate_bubbles": False, "missing_props": [],
                        "has_visual_unnaturalness": False, "unnaturalness_details": "",
                        "reason": "parse error, skip"}

            actual_count = result.get("character_count", -1)
            has_dupes = result.get("has_duplicate_bubbles", False)
            has_unnaturalness = result.get("has_visual_unnaturalness", False)
            unnaturalness_details = result.get("unnaturalness_details", "")

            # T-H Phase 1: 自然度仅日志，不纳入 valid 判定
            if has_unnaturalness:
                print(f"[ShotValidator] ℹ️ 自然度警告: {unnaturalness_details}")

            # 判定逻辑
            reasons = []

            # S1: 角色数量验证（允许 ±1 容差，因为部分遮挡/背景角色）
            if expected_character_count > 0 and actual_count >= 0:
                if abs(actual_count - expected_character_count) > 1:
                    reasons.append(
                        f"角色数量不匹配: 预期{expected_character_count}, 实际{actual_count}"
                    )

            # S5: 气泡重复验证
            if has_dupes:
                reasons.append("检测到重复对话气泡")

            # T28: 道具存在性检测
            missing_props = []
            if key_props:
                props_found = result.get("props_found", {})
                for prop in key_props:
                    if not props_found.get(prop, True):  # 默认 True（fail-open）
                        missing_props.append(prop)
                # 超过 50% 关键道具缺失 → invalid
                if len(missing_props) > len(key_props) / 2:
                    reasons.append(
                        f"关键道具缺失过多: {len(missing_props)}/{len(key_props)} ({', '.join(missing_props)})"
                    )

            valid = len(reasons) == 0
            result_dict = {
                "valid": valid,
                "actual_character_count": actual_count,
                "has_duplicate_bubbles": has_dupes,
                "missing_props": missing_props,
                "has_visual_unnaturalness": has_unnaturalness,
                "unnaturalness_details": unnaturalness_details,
                "reason": "; ".join(reasons) if reasons else "pass"
            }

            # T30: 完整结果日志
            status = "✅ PASS" if valid else "❌ FAIL"
            props_log = f", missing_props={missing_props}" if missing_props else ""
            print(f"[ShotValidator] {status}: chars={actual_count}/{expected_character_count}, dupes={has_dupes}{props_log}")

            return result_dict

        except Exception as e:
            print(f"[ShotValidator] ⚠️ 验证异常（fail-open）: {e}")
            return {"valid": True, "actual_character_count": -1,
                    "has_duplicate_bubbles": False, "missing_props": [],
                    "has_visual_unnaturalness": False, "unnaturalness_details": "",
                    "reason": f"error: {e}"}
