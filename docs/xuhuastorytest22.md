# test22 故事 idea — 美人鱼公主 (fairytale)

> **创建时间**: 2026-05-21 20:50
> **目的**: 验证 Wave 5 全栈 (T21-NEW-2 aquatic schema fallback + T21-NEW-7 Stage 4.5 真预览 + 其他 4 修复)

---

## 一句话故事 idea

**年轻人鱼公主珊瑚偷游海面看人间, 暴风雨夜救起落水渔家少年阿海。为再见他, 她找海底女巫用歌声换一双腿, 失声后用贝壳口琴吹响那夜的歌, 阿海认出了她。**

---

## 推荐 Stage A 参数

| 项 | 真选值 |
|---|---|
| 故事创意 | 见上方一句话 |
| 故事篇幅 | 短片 (~18-19 shots) |
| 画幅 | 竖屏 3:4 |
| 风格 | fairytale / 儿童绘本 / 水彩 (任一童话感) |
| 情绪基调 | 温馨 / 浪漫 / 童话 |

---

## 真验证 e2e 点

| 维度 | 期望真值 |
|---|---|
| 🌟 T21-NEW-2 aquatic schema fallback | 珊瑚 character_type=`aquatic` + 人外貌字段 (hair_color/skin_tone) 真过 schema |
| 🌟 T20-43 mythological/supernatural | 海底女巫 character_type=mythological/supernatural, 人外貌 fallback 真过 |
| 🌟 T21-NEW-7 Stage 4.5 真预览 (核心新功能) | Stage 4 后跳 /scenes 真显示场景参考图卡片: 海底宫殿 + 暴风雨海面 + 沉船 + 海岸渔村 + 女巫洞穴 (8-10 张图) + 60s 倒计时 + 编辑 + 重生 + 确认 |
| T21-NEW-3 restart UX | progress 真 > 0 |
| T21-NEW-4 portrait cache-buster | 重生角色后浏览器自动 reload 真出图 |
| T21-NEW-5 文案 | "全身参考图" 不再 "角色参考图" |
| T21-NEW-6 image_preparation sub-stage | 不再卡 7 min, 真显示 sub-step 进度 |
| T20-46 fairytale 风格 | 3 角色 (珊瑚 + 阿海 + 女巫) 风格统一 |
| BGM mixed 6 mood | 童话色彩 BGM 真 3 min+ |
| 3:4 画幅 | 19 shots 全 1664×2218 |

---

## 多场景设计 (Stage 4.5 unique_locations)

预期 5-6 unique_locations:

1. **海底珊瑚宫殿** (interior + exterior)
2. **暴风雨海面 / 沉船甲板** (exterior)
3. **海底女巫洞穴** (interior)
4. **海岸沙滩** (exterior)
5. **渔村小屋** (interior + exterior)

每 location 2 张图 = ~10 张场景参考图 让用户在 /scenes 页面真预览。

---

## 涉及角色 (3 个, schema fallback 验证)

| 角色 | character_type | 真验证 |
|---|---|---|
| 珊瑚 (人鱼公主) | `aquatic` | T21-NEW-2 fallback (上半身人形) |
| 阿海 (渔家少年) | `human` | 基准 |
| 海底女巫 | `mythological` 或 `supernatural` | T20-43 fallback |
