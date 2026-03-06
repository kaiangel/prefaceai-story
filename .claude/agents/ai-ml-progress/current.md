# AI-ML Agent - 当前任务

> **最后更新**: 2026-03-06
> **状态**: TASK-PROMPT-BUBBLE-FOLLOWUP-R2 两项任务完成

---

## 刚完成

### TASK-PROMPT-BUBBLE-FOLLOWUP-R2 -- R2 补测 + text_language 约束

**完成时间**: 2026-03-06 14:10
**修改文件**: `app/services/image_generator.py`
**新增文件**: `tests/test_speaker_format_abc_r2.py`

**Task A: R2 补测 (P0)** -- 修复 R1 ref_manager bug，三组公平对比:
- R1 Bug: 每组 `new ReferenceImageManager()`，B/C 组无参考图
- R2 Fix: 循环外生成参考图一次，所有组共用同一个实例
- A 组 (中文名): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 305s
- B 组 (英文名): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 416s
- C 组 (char_ID): 10/10 成功, 10/10 对话嵌入, avg 4.4 refs/shot, 332s
- 报告: `test_output/manualtest/prompt_bubble/speaker_format_test_r2/comparison_report.md`

**Task B: text_language 约束 (P1)** -- 繁简约束 + 多语言预留:
- `build_dialogue_scene_embed()` 新增 `text_language: str = "zh-CN"` 参数
- 新增 `_TEXT_LANGUAGE_CONFIG` 字典 (zh-CN/zh-TW/en)
- 气泡描述 "Chinese text" -> "Simplified Chinese text" + 末尾语言约束
- 向后兼容: 生产代码第 829 行默认 zh-CN，无需改动

---

## 待处理队列

| 任务 | 优先级 | 状态 |
|------|--------|------|
| TASK-PROMPT-BUBBLE | P0 | PM PASS |
| TASK-PROMPT-BUBBLE-FOLLOWUP | P1 | 完成 (R1, 有 ref_manager bug) |
| TASK-PROMPT-BUBBLE-FOLLOWUP-R2 | P0 | 完成 (等 Founder 人工检查 30 张图) |
| 6人场景一致性 90%->95% | P2 | 暂缓 |

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-06 | TASK-PROMPT-BUBBLE-FOLLOWUP-R2: R2 补测 30/30 成功 + text_language zh-CN 约束 |
| 2026-03-06 | TASK-PROMPT-BUBBLE-FOLLOWUP: 精确测量 (-455 chars, -8.0%) + A/B/C 命名格式对比 (30/30 成功) |
| 2026-03-05 | TASK-PROMPT-BUBBLE: 对话气泡嵌入场景描述 + prompt 冗余精简 + 2x10-shot 验证 |
| 2026-03-04 | Shot 15/18 优化 (Rule #7/#8) + SQ-4/SQ-5/Bug#3 重新应用 |
| 2026-03-04 | Bug #3 修复: 神秘路人负面约束 (Rule #6) |
| 2026-03-04 | Step 5b 完成: SQ-3/4/5 代码修改 |
| 2026-03-03 | slam_dunk 句序修复 + TASK-STYLE-DESC-REWRITE 15个风格场域式 |
