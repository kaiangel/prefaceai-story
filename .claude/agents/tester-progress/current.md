# Tester Agent - 当前任务

> **最后更新**: 2026-03-06 17:30
> **状态**: 🔄 TASK-E2E-REGRESSION 执行中

---

## 当前任务

### TASK-E2E-REGRESSION — 综合 E2E 回归测试

**目标**: 覆盖所有近期代码变更的端到端回归验证

**测试参数**:
- 2 组故事 × 10 shots:
  - Story A: 都市情感 / illustration 风格
  - Story B: 古装武侠 / ink 风格
- 完整 Stage 1→5 pipeline (不 resume)
- NB2 模型 (默认)
- speaker_format='english', text_language='zh-CN'
- use_native_text=True

**7 维度验收**:

| # | 维度 | 说明 |
|---|------|------|
| 1 | 成功率 | shots 生成成功比例 |
| 2 | 角色一致性 | 同角色跨 shot 外貌是否一致 |
| 3 | 风格一致性 | 全 10 shots 风格统一 |
| 4 | 对话气泡渲染 | NB2 原生气泡出现率+质量 |
| 5 | speaker_format=english | "Near {英文名}" 格式生效 |
| 6 | text_language=zh-CN | 全部简体中文，无繁体 |
| 7 | 场景描述准确性 | 构图/光线/氛围与 image_prompt 一致 |

**覆盖变更点**:
- TASK-PROMPT-BUBBLE: 对话嵌入场景描述 (build_dialogue_scene_embed)
- TASK-PROMPT-BUBBLE-FOLLOWUP: speaker_format + text_language
- TASK-BUBBLE-SPEAKER-FORMAT-DEPLOY: 生产代码接入
- SQ-1~SQ-8: Shot 质量改进
- DEC-014: previous_shot_image 移除
- System Instruction 精简 (~400→~150 chars)
- Quality Suffix 禁用

**输出**:
- 测试脚本: `tests/test_e2e_regression.py`
- 图片: `test_output/manualtest/e2e_regression/{timestamp}/`
- 对比报告: `test_output/manualtest/e2e_regression/comparison_report.md`

---

## 历史完成

### TASK-SHOT-QUALITY-BUGFIX 回归验证 ✅ PASS (4/4 Bug + 4.36/5)
### Step 7: SQ-1~SQ-8 A/B 对比验证 ✅ PASS (B 4.27/5 vs A 3.58/5, +19.3%)
### Step 4: ink + realistic 验证 ✅ (ink 4.2 + realistic 4.575)
### TASK-DIALOGUE-DENSE-TEST ✅ (4.5/5, dialogue 79.3%)
### TASK-CROSS-STYLE-TEST ✅ (B 4.38 vs A 3.88)
### TASK-AB-STYLE-DESC ✅ (B 4.5 vs A 4.17)
### TASK-NB2-TEXT-TEST ✅
### TASK-E2E-TEST-2 ✅
### TASK-E2E-VALIDATE Step 2 ✅
### TASK-REF-PREPROCESS ✅
### TASK-V5-ACCEPTANCE ✅
