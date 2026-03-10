# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-03-10

---

## 当前状态速览

```
状态: TASK-STYLE-THUMBNAILS 完成（Founder 审图通过）+ Step 7 全部 PASS
下一步: @Frontend 集成缩略图到 create 页面
```

---

## TASK-STYLE-THUMBNAILS 完成 (2026-03-10) @Frontend

**15/15 风格缩略图已就绪**，Founder 审图通过（"图片质量非常好"）。

**图片位置**: `test_output/manualtest/style_thumbnails/{中文名}.png`
- 1024×1024 PNG，15 张
- 风格: pixar_3d, ghibli, illustration, ink, slam_dunk, korean_webtoon, oil_painting, cyberpunk, realistic, cartoon, anime, watercolor, children_book, manga, pixel
- 中文文件名: 皮克斯3D.png, 吉卜力.png, 数字插画.png, 中国水墨.png, 井上雄彦.png, 韩漫.png, 油画.png, 赛博朋克.png, 写实摄影.png, 卡通动画.png, 日式动画.png, 水彩.png, 儿童绘本.png, 日漫.png, 像素艺术.png

**Prompt 文件**: `test_output/manualtest/style_thumbnails/prompts/{中文名}.txt`

**@Frontend**: 可直接用于 create 页面替换渐变色块。

---

## Step 7 修复 (2026-03-10) @PM @Backend @Tester

### T13 [P1] 条漫模式叙事自足 prompt — storyboard_prompts.py

**问题**: 条漫模式下 narration_segment 不渲染，叙事衔接仅靠 dialogue+thought，场景切换时读者感到断裂
**修复**: 新增 `COMIC_MODE_NARRATIVE_RULES` 常量（与 `NARRATION_TO_VISUAL_EXTRACTION_RULES` 同模式）:
- Rule 1: 每个 shot 的 dialogue/thought 必须自含足够叙事上下文
- Rule 2: 场景切换时首个 shot 必须用 thought/dialogue 建立转场上下文
- Rule 3: 关键剧情信息不能只存在于 narration_segment
- ✅ Backend 已完成集成（T13-INT，PM 复核 PASS）

### T14 [P1] 角色参考图跨年龄风格统一 — reference_image_manager.py

**问题**: 老年角色偏写实、年轻角色偏动漫的风格分裂
**修复**: `_build_portrait_prompt()` 和 `_build_reference_prompt()` 各追加:
> "Maintain IDENTICAL illustration style for ALL characters regardless of age, gender, or body type."

### T15 [P2] NB2 气泡重复抑制 — image_generator.py

**问题**: NB2 偶尔将同一行对话渲染两次（模型行为）
**修复**: `build_dialogue_scene_embed()` 返回值追加:
> "Render each speech bubble EXACTLY ONCE at its designated position."

---

## Step 3 修复 (2026-03-09) @PM @Backend @Tester

### T10 [P3] Stage 3 thought 比例强化 — screenplay_writer.py

**问题**: 原约束"每 scene 至少 1 个 thought"在大 scene（6+ beats）时 thought 比例不足 20%
**修复**: 按 beat 数量分档：5 beats 场景 ≥1 个 thought（20%），6+ beats 场景 ≥2 个 thought（≥20%）

---

## Step 1 修复 (2026-03-09) @PM @Backend @Tester

### T1 [P0] Stage 3 dialogue_beats type 字段 — screenplay_writer.py

**问题**: Stage 3 dialogue_beats 没有区分 dialogue/thought，覆盖率仅 52-63%
**修复**:
- dialogue_beats schema 新增 `type` 字段: `"dialogue"` 或 `"thought"`
- 每个 action_beat 强制至少 1 个 dialogue_beat（不允许裸奔）
- thought 示例: `{"beat_id": "1b_thought", "type": "thought", "speaker": "char_001", "line": "（内心独白）"}`
- 分布目标: dialogue 60-70%, thought 20-30%
- 每 scene 至少 1 个 thought beat

### T2 [P0] Stage 4 MAPPING RULES 增强 — storyboard_director.py (×2)

**问题**: narration 超标 40%/30% + thought 不足 0%/8.7% + speaker 错位 20%
**修复** (两处 MAPPING RULES 均已更新):
1. **THOUGHT GENERATION RULE**: 无 dialogue_beat 时检查 emotional_note → prefer thought over narration
2. **SPEAKER VISIBILITY RULE (COMIC MEDIUM)**: dialogue speaker 必须在 characters_visible 中，禁止反应镜头配别人台词
3. **SELF-CHECK**: 输出前自查分布，narration>15% 转 thought，thought<10% 创造 thought

### T3 [P0] Stage 3 plot_points 1:1 — screenplay_writer.py

**问题**: Story B crisis 场景被 Stage 3 静默丢弃
**修复**: PLOT POINT COVERAGE 硬约束:
- "Every plot_point from the outline MUST map to exactly one scene"
- "Do NOT merge, skip, or omit any plot_point"

---

## Prompt 核心约束 (必读)

### 1. 图像 Prompt 必须全英文
### 2. Shot 生成用 NB2 模型
### 3. 参考图必须完整传入
### 4. 所有图像统一 2:3 宽高比
### 5. text_overlay 分布: dialogue>=60%, thought 10-20%, narration<=15%, none<=5%
### 6. DEC-014: previous_shot_image 已移除
### 7. 对话气泡嵌入场景描述 (speaker_format='english', text_language='zh-CN')
### 8. TEXT-FREE 全局约束 + 参考图标签已移除 (T11)
### 9. Rule #9: 单角色每 shot 最多一个手部动作
### 10. SPEAKER VISIBILITY: dialogue speaker 必须在 characters_visible
### 11. Stage 3 dialogue_beats 区分 type: dialogue/thought
### 12. Stage 3 每个 plot_point 必须 1:1 对应 scene
### 13. Stage 3 thought 占比 ≥20%（5 beats ≥1，6+ beats ≥2）
### 14. 条漫模式: dialogue/thought 必须叙事自足，不依赖 narration
### 15. 参考图跨年龄风格统一（同线宽、同渲染技法、同风格化程度）
### 16. NB2 气泡 EXACTLY ONCE 去重指令

---

## 风格系统

15 种风格全部已升级场域式 + 缩略图已生成:
realistic, cartoon, pixar_3d, anime, ghibli, illustration, watercolor, children_book, manga, slam_dunk, korean_webtoon, oil_painting, cyberpunk, ink, pixel

**缩略图位置**: `test_output/manualtest/style_thumbnails/{中文名}.png`
