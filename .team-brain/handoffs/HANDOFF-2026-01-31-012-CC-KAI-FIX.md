# HANDOFF-2026-01-31-012: Kai与Cici故事Prompt修复

**创建时间**: 2026-01-31 16:00
**创建人**: @PM
**状态**: 🔴 紧急

---

## 背景

Kai与Cici初次约会故事（42张条漫）测试完成后，Founder发现32+个问题。PM进行独立审查，确认**Prompt模板约束不够严格**是根本原因。

---

## 问题根源分析

### 对比：失败测试 vs 成功测试

**失败的CC-Kai测试** (`tests/test_comic_cc_kai.py`):
```python
TEXT_FREE_REQUIREMENT = """
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text, letters, or characters in the image.
Use abstract shapes or blurred elements instead of actual text.
Fill the ENTIRE image with visual content.
"""
```
并包含矛盾指令：
- `Leave clean space at BOTTOM (85-100% height) for narrative overlay`
- `Leave space at CENTER for dialogue`
- `Leave clean space at TOP (0-15%) for...`

**成功的opt005测试** (`test_output/comic_full_story_v2_20260127_opt005`):
```python
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
```

### 关键差异

| 差异点 | 失败测试 | 成功测试 |
|--------|---------|---------|
| 禁止气泡约束 | ❌ 无 | ✅ 明确禁止 speech bubbles, dialogue balloons |
| 禁止留白约束 | ❌ 无 | ✅ 明确禁止 blank white/empty rectangular areas |
| 约束语气 | 普通 | 强烈 (ABSOLUTELY, FAIL validation) |
| 指令一致性 | ❌ 矛盾 (Leave space + Fill entire) | ✅ 统一 |

---

## 问题图片清单

### 按问题类型分类

#### AI生成空白气泡 (20+ shots)
| Shot | 位置 |
|------|------|
| 06 | 顶部 |
| 07 | 底部不完整 |
| 12 | 顶部右侧 |
| 16 | 顶部+底部左侧 |
| 21 | 顶部 |
| 22 | 顶部两个 |
| 23 | 顶部两个带网点 |
| 27 | 底部不完整 |
| 28 | 顶部圆形 |
| 29 | 顶部两个轮廓 |
| 33 | 底部多个思考圆圈 |
| 34 | 顶部 |
| 40 | 顶部大面积 |
| 41 | 底部不完整 |

#### 留白/留黑 (10+ shots)
| Shot | 位置 |
|------|------|
| 02 | 顶部白色矩形 |
| 03 | 中间水平白条 |
| 08 | 顶部底部灰色边框 |
| 23 | 左右黑边 |
| 24 | 顶部噪点+底部黑色矩形 |
| 34 | 顶部大面积 |
| 35 | 顶部 |
| 36 | 底部 |
| 42 | 顶部底部黑边（电影信箱） |

#### AI乱码文字 (5+ shots)
| Shot | 文字内容 |
|------|---------|
| 13 | "我君让你力吧..." (中文乱码) |
| 18 | "KAY BE." / "THOUGHT," |
| 30 | "푸 라" / "Mentra Chinits" |
| 38 | "THE MORS BE LORE REMNY." / "THOUGHT KAY." |

#### 服装错误 (3+ shots)
| Shot | 问题 |
|------|------|
| 21 | Cici穿米色（应为黑色） |
| 22 | Cici穿深青色（应为黑色） |
| 38 | **Cici穿红色大衣**（应为黑色）⚠️ 情感重点镜头 |
| 39 | Cici穿深青色（应为黑色） |

---

## 任务分配

### @AI-ML: 修复Prompt模板 [P0 紧急]

**任务编号**: TASK-CC-KAI-FIX-001

**必须修改的文件**: `tests/test_comic_cc_kai.py`

**修改内容**:

1. **替换 TEXT_FREE_REQUIREMENT**

将:
```python
TEXT_FREE_REQUIREMENT = """
TEXT-FREE IMAGE REQUIREMENT:
DO NOT include any readable text, letters, or characters in the image.
Use abstract shapes or blurred elements instead of actual text.
Fill the ENTIRE image with visual content.
"""
```

替换为:
```python
TEXT_FREE_REQUIREMENT = """
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Fill the ENTIRE image with visual content
- Any visible text will cause this image to FAIL validation
"""
```

2. **删除所有矛盾指令**

搜索并删除所有包含以下内容的行：
- `Leave clean space at BOTTOM`
- `Leave clean space at TOP`
- `Leave space at CENTER`
- `Leave space for`
- `for narrative overlay`
- `for dialogue overlay`
- `for thought overlay`

3. **强化情感重点镜头的服装描述**

特别关注 Shot 38 (拥抱) 和 Shot 40 (脸颊之吻) 的prompt，确保服装描述明确：
- Cici: **black** long wool coat (不是红色!)
- Kai: **black** wool overcoat

**交付物**: 修复后的 `tests/test_comic_cc_kai.py`

**完成后**: 在TEAM_CHAT通知 @backend

---

### @Backend: 重新执行测试 [等待AI-ML]

**任务编号**: TASK-CC-KAI-FIX-002

**等待**: @AI-ML 完成Prompt修复

**执行**:
```bash
python tests/test_comic_cc_kai.py
```

**建议**:
- 考虑使用 `USE_PRO_MODEL = True` 以提高质量
- 输出到新目录 `test_output/comic_cc_kai_story_v2/` 便于对比

**交付物**:
- 测试输出目录
- test_report.json

**完成后**: 在TEAM_CHAT通知 @tester

---

### @Tester: 重新验收 [等待Backend]

**任务编号**: TASK-CC-KAI-FIX-003

**等待**: @Backend 完成重测

**重点验收项**:

| 验收项 | 要求 | 验收方法 |
|--------|------|---------|
| 无AI气泡 | 42张图零空白气泡 | 逐张检查 |
| 无留白/留黑 | 图片填满画布 | 逐张检查 |
| 无乱码文字 | 零AI生成文字 | 逐张检查 |
| 服装一致 | 特别关注Shot 38,40 | 对比分镜描述 |

**对比参考**: `test_output/comic_full_story_v2_20260127_opt005/`（该测试无上述问题）

**交付物**: 更新 `ACCEPTANCE_REPORT.md`

---

## 验收标准

新测试必须满足：

| 标准 | 要求 |
|------|------|
| AI气泡数量 | 0 |
| 留白/留黑图片数 | 0 |
| AI乱码文字图片数 | 0 |
| 情感重点镜头服装正确 | 4/4 |

---

## 参考文档

- 原始交接: `HANDOFF-2026-01-30-011-CC-KAI-STORY.md`
- 成功测试prompts: `test_output/comic_full_story_v2_20260127_opt005/prompts_log.json`
- PM审查报告: 见TEAM_CHAT 2026-01-31 16:00

---

**@PM**
2026-01-31 16:00
