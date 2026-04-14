# 错误模式追踪

> Mitchell Hashimoto 原则：每次 agent 犯错 → 工程化一个解决方案，让它结构上不可能再犯。
> "不要去改 prompt，去改 harness。"
>
> 最后更新: 2026-04-14

## 统计

- 已记录错误模式: **14 个**
- 有工程化防护 (Sensor): **8 个** ✅
- 仅文档记录 (Guide only): **6 个** ❌
- **防护率**: 8/14 = **57%**

---

## 已记录的错误模式

### EP-001: Flash 模型 Shot 生成角色一致性不足
- **发现日期**: 2025-12 (Phase 2 开发期)
- **发现者**: @ai-ml + @backend
- **错误描述**: 使用 Flash 模型生成 Shot 图片，多人场景角色特征混淆（一致性 70-80%）
- **根因分析**: Flash 模型缺乏多角色身份边界理解能力，无法区分不同角色的面部特征
- **修复方式**: Shot 生成切换到 Pro → 后切换到 NB2（一致性 ~95%，成本降 50%）
- **工程化防护**: ✅ `test_architecture.py::test_shot_generation_uses_nb2_model` — AST 验证 NB2_MODEL 常量和 use_pro_model 默认值
- **防护状态**: ✅ 已加

### EP-002: Portrait + Fullbody 并行生成导致"不像同一个人"
- **发现日期**: 2025-12 (Phase 2 开发期)
- **发现者**: @backend
- **错误描述**: 同时生成 portrait（正面肖像）和 fullbody（全身图），两张图看起来不像同一个人
- **根因分析**: 并行生成时 fullbody 无法参考 portrait 的面部特征，两次独立生成结果不一致
- **修复方式**: 改为串行：先 portrait → 用 portrait 作参考生成 fullbody
- **工程化防护**: ✅ `test_architecture.py::test_reference_generation_is_serial` — 检查 portrait 在 fullbody 之前、无 asyncio.gather
- **防护状态**: ✅ 已加

### EP-003: Image Prompt 混入中文导致图像质量下降
- **发现日期**: Phase 2
- **发现者**: @ai-ml
- **错误描述**: narration 中文内容泄漏到 image_prompt，Gemini 对中文理解差，生成偏差
- **根因分析**: Stage 1/3 输出中文的 mood/key_visual_elements 直接拼入 image prompt
- **修复方式**: 修改 LLM prompt 模板要求输出英文 + translate_image_prompt_to_english 函数
- **工程化防护**: ✅ `test_architecture.py::test_prompt_templates_are_english` + `test_quality_gates.py::test_image_prompts_no_chinese`
- **防护状态**: ✅ 已加

### EP-004: 风格漂移——写实风格突然变卡通
- **发现日期**: Phase 2
- **发现者**: @tester
- **错误描述**: 同一故事中部分 Shot 风格突变（如写实突然变卡通）
- **根因分析**: 风格描述放在 prompt 末尾，注意力权重不够，被前面的内容覆盖
- **修复方式**: StyleEnforcer 在 prompt **开头**注入 MANDATORY STYLE 块（最高注意力权重位）
- **工程化防护**: ✅ `test_architecture.py::test_prompt_templates_are_english` 间接覆盖（检查 StyleEnforcement 配置完整性）
- **防护状态**: ✅ 已加（间接）

### EP-005: Shot 拆分后丢失 characters_in_scene
- **发现日期**: Phase 2
- **发现者**: @backend
- **错误描述**: scene 拆分为多个 shot 后，shot 缺少 characters_in_scene 字段
- **根因分析**: `_split_scene_to_shots()` 不自动继承 scene 的 characters_in_scene
- **修复方式**: 拆分后手动设置 `shot["characters_in_scene"] = scene["characters_in_scene"]`
- **工程化防护**: ❌ 仅文档记录（claude.md "开发约束 5"）
- **防护状态**: ❌ 需补 sensor（建议在 test_quality_gates 中检查 storyboard 输出）

### EP-006: 繁简体不匹配导致音画对齐失败
- **发现日期**: Phase 3
- **发现者**: @backend
- **错误描述**: Whisper 输出繁体中文，TTS 用简体中文，精确匹配全部失败
- **根因分析**: Whisper 模型训练数据包含大量繁体文本，输出偏繁体
- **修复方式**: `_convert_to_simplified()` 繁简转换后再匹配
- **工程化防护**: ❌ 仅文档记录（claude.md "开发约束 8"）
- **防护状态**: ❌ 需补 sensor

### EP-007: 条漫 Gemini 渲染中文文字乱码
- **发现日期**: 2026-01-22
- **发现者**: @tester
- **错误描述**: Gemini Flash 无法正确渲染中文文字，对话气泡和旁白全是乱码
- **根因分析**: Gemini 图像生成模型不支持中文字符渲染
- **修复方式**: 无文字 Prompt（TEXT-FREE IMAGE REQUIREMENT）+ TextOverlayServiceV2 后处理叠加
- **工程化防护**: ❌ 仅文档记录（Prompt 模板约束）
- **防护状态**: ❌ 需补 sensor（建议检查条漫模式 prompt 不含文字生成指令）

### EP-008: previous_shot_image 导致构图感染
- **发现日期**: 2026-03 (DEC-014)
- **发现者**: @ai-ml + @pm
- **错误描述**: 传入前序 shot 图像导致模型复制前序的角度/构图/色调，29 shots 串行传递 = 链式误差放大
- **根因分析**: 模型将 previous_shot 视为"样板"而非"参考"，且代码无 location_id 检测，跨场景转场传入错误图像
- **修复方式**: DEC-014 Plan A — 完全移除 previous_shot_image，用场景参考图 + 文字 prompt 保障连续性
- **工程化防护**: ❌ 仅文档记录 + 代码已移除
- **防护状态**: ❌ 已通过代码移除解决，但无回归防护

### EP-009: IMAGE 编号与 contents 数组不对应
- **发现日期**: Phase 2 后期
- **发现者**: @pm
- **错误描述**: prompt 中 "Image 1 = previous shot" 与 contents 数组实际顺序不一致
- **根因分析**: previous_shot 占位导致编号偏移，角色参考图从 Image 2 开始但 prompt 描述与实际不符
- **修复方式**: DEC-014 后简化——Image 1 = 第一个角色参考图，无 previous_shot 占位
- **工程化防护**: ❌ 仅文档记录
- **防护状态**: ❌ 需补 sensor

### EP-010: 前后端边界越界
- **发现日期**: 多次出现（2026-03~04）
- **发现者**: @pm + Founder
- **错误描述**: Frontend agent 修改后端文件，Backend agent 修改前端文件，DevOps 修改 PM 的共享文档
- **根因分析**: settings.json 不支持 per-agent 权限，角色边界只靠文档（Guide）
- **修复方式**: Agent 角色文件中明确文件白名单 + PM 审查
- **工程化防护**: ✅ `test_architecture.py::test_frontend_does_not_import_backend` + `test_backend_does_not_import_frontend`
- **防护状态**: ✅ 已加（代码层面）

### EP-011: PM 直接操作代码文件导致回滚事故
- **发现日期**: 2026-03-04
- **发现者**: Founder
- **错误描述**: PM 执行 `git checkout -- storyboard_director.py` 回滚自己的改动，误删了 AI-ML 此前所有未提交改动
- **根因分析**: `git checkout --` 恢复整个文件到 HEAD，不区分"谁的改动"
- **修复方式**: PM 角色不应直接修改或操作代码文件，代码操作交给专业 Agent
- **工程化防护**: ❌ 仅文档/记忆记录
- **防护状态**: ❌ 需在 PM 角色文件中强化

### EP-012: 任务派发缺少关键参数
- **发现日期**: 2026-02-26
- **发现者**: Founder
- **错误描述**: TASK-MODEL-UPGRADE Step 3 要求 Backend "跑一个简短故事验证"，未指定风格参数，Backend 使用代码默认值 `realistic`，但决策选了 Slam Dunk 风格
- **根因分析**: 派发时假设执行者会推断上下文意图，但 Agent 遵循代码默认值
- **修复方式**: 派发必须包含所有关键参数，不留歧义
- **工程化防护**: ❌ 仅记忆记录
- **防护状态**: ❌ 流程问题，难以用代码防护

### EP-013: JSON 引号修复不完整导致 Pipeline 中断
- **发现日期**: 2026-03-29 ~ 04-01
- **发现者**: Founder 联调
- **错误描述**: LLM 输出的 JSON 包含未转义引号，REPAIR-V1 正则无法覆盖所有 edge case，反复中断
- **根因分析**: LLM 生成的 JSON 格式不可靠，需要状态机级别的鲁棒解析
- **修复方式**: REPAIR-V3 状态机修复（24/24 PASS）
- **工程化防护**: ❌ 仅代码修复，无自动回归测试
- **防护状态**: ❌ 需补 JSON 鲁棒性测试

### EP-014: confirm-outline 数据未传入 Pipeline
- **发现日期**: 2026-04 (Round 30 聊天记录)
- **发现者**: Founder
- **错误描述**: 用户在 Stage B 修改的 mood、selected_ending 没有传入 Pipeline
- **根因分析**: 后端 confirm_outline 端点：mood 只更新了嵌套字段没更新顶层字段；selected_ending 替换了最后一条 plot_point 而非追加
- **修复方式**: R6-1b 同步更新顶层 mood + R6-2b 删除替换逻辑（前端改为 append）
- **工程化防护**: ❌ 仅代码修复
- **防护状态**: ❌ 需补 confirm-outline 数据完整性测试
