# AI-ML Agent - 给其他 Agent 的上下文

> 其他 Agent 查看此文件了解 AI-ML 的工作状态和 Prompt 约束
> **最后更新**: 2026-03-24

---

## 当前状态速览

```
状态: TASK-OUTLINE-LLM-FIX 第 1 项完成 (system prompt 设计)
       TASK-OUTLINE-PROMPT-UPGRADE 完成 (Stage 1 prompt 新增 5 个字段)
下一步: Backend 集成 system prompt → PM Review
```

---

## TASK-IMG-SAFETY-RETRY-AIML (2026-03-16) @PM @Backend

### 参考图安全改写 Prompt 工程 — 5 项交付物

**文件**: `app/prompts/prompt_safety_rewrite.py`

**交付物概览**:
1. **5 类新关键词** (74 词条): CROWD/ANIMAL/FIRE_SMOKE/CHILD_CONTEXT/REVEALING_CLOTHING
2. **SCENE_REF_REWRITE_PROMPT**: 场景参考图专用 LLM 改写模板
3. **CHAR_REF_REWRITE_PROMPT**: 角色参考图专用 LLM 改写模板
4. **_simplify_anchor_prompt() spec**: Backend 实现指引
5. **_build_anchor_prompt() 结构优化**: 建议 "No people" 前置

**@Backend 关键接口**:
- `from app.prompts.prompt_safety_rewrite import build_scene_ref_rewrite_prompt, build_char_ref_rewrite_prompt, apply_simple_replacements`
- L2 简化重试: `apply_simple_replacements(prompt)` 处理 CROWD/ANIMAL/FIRE_SMOKE + 前置 "No people"
- L3a 场景改写: `build_scene_ref_rewrite_prompt(prompt)` → 传给 PromptRewriter LLM
- L3b 角色改写: `build_char_ref_rewrite_prompt(prompt)` → 传给 PromptRewriter LLM

---

## Phase 3 T-H-AIML (2026-03-13) ✅ — @PM @Backend

### T-H-AIML [P2] 画面自然度 Haiku Prompt 设计

**交付物**: TEAM_CHAT 2026-03-13 18:30 中的 prompt 设计文档
**消费者**: @Backend T-H-Backend（将 prompt 集成到 shot_validator.py VALIDATION_PROMPT_BASE）

**设计要点**:
- 3 子维度: D1 ANATOMICAL + D2 PHYSICS + D3 SPATIAL
- 风格无关: 区分"生成失败"(flag) vs "艺术风格"(不flag)
- 可合并到现有 VALIDATION_PROMPT_BASE Q3 位置（零额外 API 调用）
- JSON 新增: `has_visual_unnaturalness` + `unnaturalness_details`
- max_tokens 建议 256→384
- ⚠️ Phase 1 仅日志不触发 FAIL; Phase 2 需 Haiku 准确率 > 90% 后启用

---

## Phase 1 T-E+T-F+T-G+T-C-AIML (2026-03-13) ✅ PM Code Review PASS — @PM @Backend

### T-E [P1] 背面/高角度角色一致性 — storyboard_director.py

**问题** (Shot_08): 背面拍摄角色服装颜色偏差（鼠尾草绿 T 恤偏白）
**修复**: Rule #10 BACK-VIEW/HIGH-ANGLE CHARACTER CONSISTENCY
- back-view/over-shoulder/bird's-eye/high-angle → REINFORCE 服装精确色名+类型 + 发色+发型
- 显式注明 "Even viewed from behind/above, must remain identifiable"
- 两处规则区（详细版 + 精简版）同步

### T-F [P1] off-screen 肢体接触规则 — storyboard_director.py

**问题** (Shot_03): "pulled by Xiaohe's grip off-screen left" 导致悬空手
**修复**: Rule #11 OFF-SCREEN CHARACTER PHYSICAL CONTACT (CRITICAL)
- FORBIDDEN: 可见角色与画外角色直接物理接触
- REQUIRED: 独立肢体语言暗示互动
- 不影响环境交互（开门、拿物品等）

### T-G [P1] 空间方向矛盾检测 — storyboard_director.py

**问题** (Shot_04): "trailing at the rear" 但镜头面向正面
**修复**: Rule #12 SPATIAL DIRECTION SELF-CONSISTENCY CHECK
- 镜头角度 + 动作 + 空间描述自洽验证
- 含 ❌ CONTRADICTORY / ✅ CONSISTENT 正反例

### T-C-AIML [P1] signage_text 字段 — story_outline_generator.py

**问题**: display_name 开发标签泄漏到场景参考图招牌
**修复**: unique_locations schema 新增 `signage_text` 字段 + 创作要点 #7
- signage_text = 店铺招牌真实文字（"李记桂花糕"），display_name = 开发标签（"李记桂花糕铺·外景"）
- Backend T-C-Backend 将改用 signage_text 作为招牌数据源

---

## Phase 1b T34+T37 (2026-03-12) @PM @Backend @Tester

### T34 [P1] shot_size/angle 完整性 — storyboard_director.py

**问题** (P-R6): 早期 shot image_prompt 缺镜头信息（无 shot_size/angle 关键词）
**修复**:
- **Plan A**: CAMERA_INFORMATION_COMPLETENESS_RULE 常量 (3 条)，注入 `_build_scene_prompt()` SHOT TRANSITION 后
  - shot size in prompt + camera angle in prompt + natural integration
- **Plan B**: `_validate_storyboard()` 后验证
  - 检测 image_prompt 是否含 shot_size/angle 关键词（映射表匹配）
  - 缺失: 从 shot.camera 元数据构建 "low angle medium shot" 等自然短语，注入 prompt 开头
  - eye_level 不强制（最常见角度，省略合理）
  - 在 T29 off_screen_speaker 逻辑之后独立运行，不覆盖 T29

### T37 [P2] 称谓歧义消除规则 — screenplay_writer.py

**问题** (P-R9): "妈" 在多代际故事中可指代祖母/母亲/婶婶等多人
**修复**:
- T26 DIALOGUE NATURALNESS RULES 新增 Rule 5: KINSHIP ADDRESS CLARITY
- 多代际家庭: 角色间称谓从说话者视角明确无歧义
- 旁白同样需消歧（"林秀梅" 而非 "妈妈"，当多个女性长辈在场时）
- 引用 T32 CHARACTER RELATIONSHIPS 数据
- SHOULD 措辞，含 ❌/✅ 正反例

---

## Phase 1a T33+T35+T36 (2026-03-12) ✅ PM 审查 PASS

### T33 [P2] family_relationships 三角关系校验 — story_outline_generator.py
### T35 [P2] 多人空间锚定+比例 — storyboard_director.py
### T36 [P3] color_palette 英文化 — story_outline_generator.py

---

## Phase 1 T25+T26+T27 (2026-03-12) ✅ PM Code Review PASS
## Phase 1 T18+T19 (2026-03-11) ✅ PM PASS + R5 PASS

---

## 历史修复 (供参考)

### Step 7 T13+T14+T15 (2026-03-10) ✅ PM PASS
### Step 3 T10 (2026-03-09) ✅ PM PASS
### Step 1 T1+T2+T3 (2026-03-09) ✅ PM PASS

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
### 15. 参考图跨年龄风格统一 — 强化版: 显式引用 style_name + age-specific anchor (T19)
### 16. NB2 气泡 EXACTLY ONCE 去重指令
### 17. 同场景道具连续性: SHOULD maintain props across shots (T18)
### 18. Stage 1 标题校验: 标题角色称谓/性别匹配 characters_overview (T25)
### 19. Stage 3 对话自然度: 逻辑常识 + 主语明确 + 年龄匹配 + 口语化 (T26)
### 20. Stage 4 角色关系映射: text_overlay 使用正确称谓 (T27, 配合 T24 数据)
### 21. Stage 4 背景多样性: 同场景 3+ shots 变换背景焦点 (T27)
### 22. Stage 4 室内纵深: medium_shot + interior 必含前中后景纵深 (T27)
### 23. Stage 1 关系三角校验: family_relationships 代际一致性 + 配偶传递 (T33)
### 24. Stage 4 多人空间锚定: 3+角色人数声明+家具比例+环境交互+多层分布 (T35)
### 25. Stage 1 color_palette 英文: 色名必须英文 (T36)
### 26. Stage 4 镜头信息完整: image_prompt 含 shot_size/angle + 后验证注入 (T34)
### 27. Stage 3 称谓消歧: 多代际家庭称谓从说话者视角明确无歧义 (T37)
### 28. Stage 4 背面/高角度角色一致性: back-view/high-angle → REINFORCE 服装精确色名+发色 + 可识别性注明 (T-E)
### 29. Stage 4 off-screen 肢体接触禁止: 可见角色不描述与画外角色的直接物理接触, 改用独立肢体语言 (T-F)
### 30. Stage 4 空间方向自洽: camera_angle + 角色动作 + 空间描述需逻辑一致 (T-G)
### 31. Stage 1 signage_text 字段: unique_locations 招牌文字与 display_name 分离 (T-C-AIML)
### 32. ShotValidator 画面自然度: 3 子维度 (ANATOMICAL+PHYSICS+SPATIAL), 风格无关, Phase 1 仅日志 (T-H-AIML)
### 33. 参考图安全改写: CROWD/ANIMAL/FIRE_SMOKE/CHILD/REVEALING 5 类新关键词 + 场景/角色专用改写模板 (TASK-IMG-SAFETY-RETRY-AIML)

---

## 风格系统

15 种风格全部已升级场域式 + 缩略图已生成:
realistic, cartoon, pixar_3d, anime, ghibli, illustration, watercolor, children_book, manga, slam_dunk, korean_webtoon, oil_painting, cyberpunk, ink, pixel
