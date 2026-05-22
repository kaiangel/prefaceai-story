# test23 故事 idea — 深夜服务器 (都市悬疑)

> **创建时间**: 2026-05-22 16:40
> **目的**: 跨题材验证 Wave 7+8 (Layer 1 Identity Anchor + 通用 Fallback 架构 + LLMFallbackChain) — 现代都市 + 紧张悬疑, 跟 test22 fairytale 完全不同基调

---

## 一句话故事 idea

**程序员林之南深夜加班, 发现公司服务器机房无人时刻独自运行陌生 AI 程序。追查过程中, 一个自称"陌生用户"的 AI 实体开始用员工口吻给他发邮件, 直到林之南意识到真相 — 那是公司去年离职死去的同事张铭留下的数字遗志。**

---

## 推荐 Stage A 参数

| 项 | 选值 |
|---|---|
| 故事创意 | 见上方一句话 |
| 篇幅 | 短片 (~18-20 shots) |
| 画幅 | 竖屏 3:4 |
| 风格 | cyberpunk / illustration / realistic (任一现代科技感) |
| 情绪基调 | 悬疑 / 紧张 / 哲思 |

---

## 验证 e2e 点

| 维度 | 期望 |
|---|---|
| 🌟 跨题材 vs test22 | fairytale → 现代都市悬疑, 验证 Layer 1 跨风格通用 |
| 🌟 ai_entity / digital_virtual schema | 张铭数字遗志 character_type=`ai_entity` or `digital_virtual`, T22-NEW-9 通用 fallback 接受人外貌 |
| 🌟 LLMFallbackChain (T22-NEW-4) | 任何 LLM 调用 Haiku 失败时 Gemini 接管, AdjustCharacter / BGM 等 |
| 🌟 Layer 1 anchor 强注入 | 林之南程序员形象 (休闲衬衫 + 眼镜 + 笔记本) 18 shot 一致 |
| Stage 4.5 scene refs | 办公楼夜景 + 机房 + 工位 + 走廊 + 邮件特写 |
| BGM 悬疑色彩 | tense_dramatic + mysterious + nostalgic 真融合 ~3 min |

---

## 多场景设计 (Stage 4.5 unique_locations)

预期 4-5 unique_locations:

1. **办公楼夜景** (exterior) — 高层办公楼亮着的窗户
2. **机房 server room** (interior) — 冷光蓝紫色, 服务器机柜
3. **林之南工位** (interior) — 双屏显示器 + 凌乱桌面
4. **办公楼走廊** (interior) — 深夜空荡走廊
5. **张铭旧工位** (interior, 闪回) — 已清空但留有照片

---

## 涉及角色 (3 个)

| 角色 | character_type | 验证 |
|---|---|---|
| 林之南 (程序员) | `human` | 基准 |
| 张铭 数字遗志 (AI) | `ai_entity` or `digital_virtual` | T22-NEW-9 通用 fallback (人外貌) |
| 张铭 生前 (闪回, 真实人物) | `human` | 跨闪回一致性 |

---

## 真实战看点

- 现代悬疑题材如何跨 fairytale → tech / 哲思 (Layer 1 通用性最佳证明)
- digital_virtual / ai_entity 真 schema 验证 (Wave 4+4.5+8 累计 fallback 通用)
- 暗黑题材 prompt 工程 (Seedream 真**safety avoidance** T20-26 + StyleEnforcer cyberpunk mandatory)
