# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-03-06

---

## 当前状态速览

```
状态: TASK-PROMPT-BUBBLE-FOLLOWUP-R2 两项任务完成
下一步: 等 Founder 人工检查 30 张 R2 对比图片，确定最优 speaker_format
```

---

## TASK-PROMPT-BUBBLE-FOLLOWUP-R2 -- R2 补测 + text_language 约束 @PM @Founder

### Task A: R2 补测 (修复 R1 ref_manager bug)

**R1 Bug**: 每组 `new ReferenceImageManager()`，B/C 组 ref_count=0
**R2 Fix**: 循环外生成参考图一次，三组共用同一个实例

| 组 | speaker_format | 成功率 | 对话嵌入 | 平均参考图/shot | 耗时 |
|---|---|---|---|---|---|
| A (Chinese Name) | chinese | 10/10 | 10/10 | 4.4 | 305s |
| B (English Name) | english | 10/10 | 10/10 | 4.4 | 416s |
| C (char_ID) | char_id | 10/10 | 10/10 | 4.4 | 332s |

**图片**: `test_output/manualtest/prompt_bubble/speaker_format_test_r2/{A_chinese,B_english,C_char_id}/images/`
**Prompts**: `.../{A_chinese,B_english,C_char_id}/prompts/`
**报告**: `test_output/manualtest/prompt_bubble/speaker_format_test_r2/comparison_report.md`

### Task B: text_language 约束 + 多语言预留

**代码改动** (`image_generator.py`):
- 新增 `_TEXT_LANGUAGE_CONFIG` 字典 (zh-CN/zh-TW/en 三种语言配置)
- `build_dialogue_scene_embed()` 新增 `text_language: str = "zh-CN"` 参数
- 气泡描述 "Chinese text" -> "Simplified Chinese text" + 末尾语言约束
- 向后兼容: 生产代码第 829 行默认 zh-CN，无需改动

---

## TASK-PROMPT-BUBBLE-FOLLOWUP -- 精确测量 + 命名格式对比 (R1)

### 任务 1: 精确 prompt 尺寸测量

| 模块 | 优化前 (chars) | 优化后 (chars) | 差异 |
|------|---------------|---------------|------|
| System Instruction | 635 | 339 | -296 |
| Quality Suffix | 59 | 0 | -59 |
| TEXT OVERLAY (dialogue) | 210 | 0 | -210 |
| Dialogue Scene Embed | 0 | 113 | +113 |
| **总 prompt (Shot 1)** | **5707** | **5252** | **-455 (-8.0%)** |
| **总 prompt (Shot 5)** | **5258** | **4803** | **-455 (-8.7%)** |

### 任务 2: A/B/C 命名格式对比 (R1, 有 bug)

- R1 结果 B/C 组无参考图 -- 已被 R2 补测替代，以 R2 结果为准

---

## TASK-PROMPT-BUBBLE -- Prompt 架构优化 (PM PASS)

### 对话气泡渲染流程变更

| 文字类型 | 优化前 | 优化后 |
|---------|--------|--------|
| dialogue | prompt 末尾 TEXT OVERLAY REQUIREMENT (~200 chars, <1% 注意力) | 嵌入 [SCENE DESCRIPTION] (~100 chars/条, 高注意力) |
| thought | prompt 末尾 TEXT OVERLAY REQUIREMENT | **不变** |
| narration | prompt 末尾 TEXT OVERLAY REQUIREMENT | **不变** |
| 复合类型 | 全部通过 TEXT OVERLAY | dialogue 嵌入场景, thought/narration 保持 TEXT OVERLAY |

---

## Prompt 核心约束 (必读)

### 1. 图像 Prompt 必须全英文
### 2. Shot 生成用 NB2 模型 (DEC-012 后已切换)
### 3. 参考图必须完整传入
### 4. 所有图像统一 2:3 宽高比 (TASK-ASPECT-2x3 + DEC-010)
### 5. DIALOGUE-SYSTEM 规则 (dialogue>=60%, thought 15-25%, narration<=10%, none禁止)
### 6. DEC-014: previous_shot_image 已移除
### 7. TASK-PROMPT-BUBBLE: 对话气泡嵌入场景描述，不再通过 TEXT OVERLAY
### 8. TASK-PROMPT-BUBBLE-FOLLOWUP: `build_dialogue_scene_embed()` 支持 speaker_format 参数
### 9. TASK-PROMPT-BUBBLE-FOLLOWUP-R2: `build_dialogue_scene_embed()` 支持 text_language 参数 (默认 zh-CN)

---

## 风格系统

15 种风格全部已升级场域式:
realistic, cartoon, pixar_3d, anime, ghibli, illustration, watercolor, children_book, manga, slam_dunk, korean_webtoon, oil_painting, cyberpunk, ink, pixel
