"""Chapter schemas"""

from datetime import datetime
from pydantic import BaseModel
from typing import Any


class HydrateHints(BaseModel):
    """Wave 9 / DEC-030: 告诉 frontend 当前阶段应该 hydrate 哪个 endpoint 拿展示数据。

    schema:
      endpoint: API 路径（相对路径，含 /chapters/{n}/ 前缀）
      display_field: response 内主要展示字段名（前端 hydrate 后从此字段取数据）
      expected_data_shape: 字段形状描述（"list[Character]" / "list[Scene]" / "list[Shot]" 等）
    """

    endpoint: str
    display_field: str
    expected_data_shape: str


class ChapterStatus(BaseModel):
    """Chapter generation status

    B46: failed_shot_count / partial_failure — frontend 用这两个字段检测部分失败。
    status 仍为 'completed'（不破坏前端现有逻辑），用 failed_shot_count > 0 判断是否有图缺失。

    Wave 9 / DEC-030: backend status authoritative — frontend state 从此 response 派生。
    新增字段:
      - ui_phase: 当前用户应该看哪个 UI 阶段（frontend createUrl / subPhase 派生用）
      - hydrate_hints: 当前阶段应该 hydrate 哪个 endpoint（顺解 T15-3）
      - characters_confirmed / scenes_confirmed: R4-1/R4-2 闸门状态（frontend subPhase 派生用）
      - storyboard_ready: chapter.storyboard_json 非空 → True（frontend 判断 /scenes vs /preview）
      - outline_ready: chapter.full_script 非空 → True（Stage 1 完成）
    """

    status: str
    stage: str | None
    progress: int
    estimated_remaining_seconds: int | None
    actual_elapsed_sec: int | None = None  # Wave 11.3 / T17-5: 当前任务已运行秒数（frontend 可用于校验 ETA 合理性）
    message: str | None
    # B46: 部分失败字段
    failed_shot_count: int = 0    # 失败的 shot 数量（0 = 全部成功）
    partial_failure: bool = False  # True 表示有 shot 生成失败

    # RISK-T20-9 (2026-05-18): 动态 ETA 参数 — frontend 可读取这些参数本地算 ETA fallback
    # 当 estimated_remaining_seconds=null 时, frontend 用 actual_shot_count × 80 / max_concurrent
    # + bgm baseline 计算 image_generation 阶段 ETA（替代旧 hardcoded STAGE_BUDGET_SECONDS=1440）
    # universal: 任何 shot count (5/19/29/50) 都准确, 不再 hardcode worst-case
    actual_shot_count: int | None = None  # Stage 4 完成后真实 shot 数（早期 stage = null）
    max_concurrent: int | None = None     # Seedream 并发数（IMAGE_MAX_CONCURRENT，默认 3）

    # RISK-T20-13 (2026-05-19): Shot 级真实计数字段 — frontend 用这些字段算 ETA，不再 regex 解析 message
    # 之前 frontend 只能从 message 字段 regex 抠"已生成 X/Y" — 字符串解析不可靠，且更新延迟
    # 现在 backend 直接 expose 3 个字段:
    #   shots_total      = chapter.storyboard_json 解析（等同 actual_shot_count，独立字段语义更清）
    #   shots_completed  = Stage 5 progress 反推（成功+失败合计，对齐 pipeline 内 _done 计数）
    #   shots_failed     = job.failed_shot_count（DB 直读，T15-9 mid-stage 实时累加）
    # 早期 stage (storyboard 没生成) 全部返 null，不破坏向后兼容
    # universal: 任何 shot count 都准确, 不依赖 message 字符串格式
    shots_total: int | None = None      # Stage 4 完成后总 shot 数（= actual_shot_count）
    shots_completed: int | None = None  # 已完成的 shot 数（成功 + 失败合计, image_generation stage 内动态更新）
    shots_failed: int | None = None     # 已失败的 shot 数（= job.failed_shot_count）

    # Wave 9 / DEC-030: backend authoritative state 字段
    # T21-NEW-7 (2026-05-21 v1.4 DEC-047): 新增 ui_phase "scene_references_review" + 2 字段
    # ui_phase 9 状态机: input | outline_review | char_review_pending | char_review |
    #   scene_review_pending | scene_review | storyboard_running |
    #   scene_references_review | shot_generating | completed
    ui_phase: str = "input"
    hydrate_hints: HydrateHints | None = None
    characters_confirmed: bool = False  # project.characters_confirmed 直读
    scenes_confirmed: bool = False      # project.scenes_confirmed 直读
    # T21-NEW-7 v1.4: Stage 4.5 scene_image_preparation 配套字段
    scene_references_ready: bool = False  # chapter.scene_references_json 非空 → True (Stage 4.5 完成)
    scene_references_confirmed: bool = False  # project.scene_references_confirmed 直读 (R4-3 闸门)
    storyboard_ready: bool = False      # chapter.storyboard_json 非空
    outline_ready: bool = False         # chapter.full_script / scenes_json 非空


class ChapterResponse(BaseModel):
    """Basic chapter information"""

    id: str
    project_id: str
    chapter_number: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChapterStory(BaseModel):
    """Full story content for a chapter.

    scenes and characters are raw dicts from the pipeline output.
    Stage 3 ScreenplayWriter produces scenes with fields like scene_id,
    scene_heading, time_of_day, atmosphere, etc. — not the old
    location/time/mood/visual_description naming. Using Dict[str, Any]
    avoids schema validation errors from field-name mismatch.
    Frontend adapts field names directly from the raw pipeline output.
    """

    title: str
    summary: str
    full_script: dict[str, Any]
    scenes: list[dict[str, Any]]
    characters: list[dict[str, Any]]
