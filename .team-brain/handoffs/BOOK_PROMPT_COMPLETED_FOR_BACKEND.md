# 书籍解说 Prompt 已完成 - 请 Backend 编写测试脚本

> **From**: @AI-ML
> **To**: @Backend
> **Priority**: P1
> **Type**: Side Test 接续任务
> **Created**: 2026-01-15

---

## 任务概述

书籍解说视频的3个Prompt模板已全部完成，可以开始编写测试脚本验证整个流程。

---

## 已完成的工作

### 产出文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `app/prompts/book/book_outline_prompt.py` | 书籍要点提炼 (Stage 1) | ✅ 已完成 (你之前写的) |
| `app/prompts/book/book_narration_prompt.py` | 解说脚本生成 (Stage 2) | ✅ 已完成 |
| `app/prompts/book/book_storyboard_prompt.py` | 配图分镜 (Stage 3) | ✅ 已完成 |
| `app/prompts/book/__init__.py` | 模块导出 | ✅ 已完成 (你之前写的) |

### 设计要点

1. **概念可视化**
   - 每个Prompt都包含详细的"概念可视化"指令
   - 强调：抽象概念→具体场景，禁止文字/图表
   - 提供了大量好/坏示例

2. **英文约束**
   - `visual_concept` (Stage 1) - 英文
   - `visual_direction` (Stage 2) - 英文
   - `image_prompt` (Stage 3) - 英文
   - `narration_text` (Stage 2) - 中文 (用于TTS)

3. **风格一致性**
   - Stage 3 包含 `CONCEPT_VISUALIZATION_BLOCK` 强制指令
   - 支持多种风格：illustration, realistic, watercolor, ink, oil_painting, digital_art

---

## 需要你接手的工作

### 1. 编写测试脚本

建议位置：`tests/test_book_narration_experiment.py`

测试流程：
```
1. 调用 book_outline_prompt → LLM → 解析JSON
2. 调用 book_narration_prompt(outline) → LLM → 解析JSON
3. 调用 book_storyboard_prompt(narration) → LLM → 解析JSON
4. (可选) 调用 ImageGenerator 生成图片
```

### 2. 测试用例

每个Prompt文件末尾都有 `*_EXAMPLE_INPUT` 字典，可直接用于测试。

《人类简史》测试输入：
```python
BOOK_INPUT = {
    "title": "人类简史",
    "author": "尤瓦尔·赫拉利",
    "summary": """
《人类简史》讲述了人类从7万年前的认知革命到21世纪的科技革命的历程。

核心观点：
1. 认知革命：智人能够创造和相信虚构故事（神话、宗教、国家、货币），这是人类统治地球的关键
2. 农业革命是"史上最大骗局"：人类以为驯化了小麦，实际上是小麦驯化了人类
3. 帝国、货币、宗教是统一人类的三大力量
4. 科学革命：承认无知是进步的开始
5. 快乐悖论：物质进步不等于幸福增加
""",
    "target_duration": 180,  # 3分钟
    "style": "illustration"
}
```

### 3. 验收标准

- [ ] Stage 1 输出包含 5 个 key_insights，每个有英文 visual_concept
- [ ] Stage 2 输出包含 narration_segments，中文旁白 + 英文 visual_direction
- [ ] Stage 3 输出包含 shots，每个有完整英文 image_prompt
- [ ] image_prompt 中无中文字符
- [ ] image_prompt 中无文字/图表描述（如 "text showing...", "chart of..."）
- [ ] (可选) 生成的图片无明显文字元素

---

## 沟通群聊

请查看 `.team-brain/TEAM_CHAT.md` 了解讨论记录，完成后请在群聊中更新状态。

---

## 注意事项

1. **不影响主线**：这是Side Test，测试脚本放在单独文件
2. **使用Flash模型即可**：书籍解说不需要Pro模型的角色一致性能力
3. **先跑通再优化**：Prompt可能需要迭代，先验证流程

---

**有问题随时在群聊中@我。**
