# test24 故事 idea — 剑灵归鞘 (古风武侠)

> **创建时间**: 2026-05-22 16:45
> **目的**: 跨题材验证 Wave 7+8 (Layer 1 + 通用 Fallback + ink 水墨风格) — 古装武侠, 跟 test22 fairytale / test23 现代悬疑 完全不同基调

---

## 一句话故事 idea

**剑客顾飞云退隐山林十年。一日少女苏寒梅前来寻仇 — 父亲死于顾飞云剑下。决斗之际, 顾飞云的佩剑突然显出剑灵, 揭示当年真相: 苏父并非顾飞云所杀, 是嫁祸者持顾飞云遗剑灭口。苏寒梅泣不成声, 收剑入鞘, 与顾飞云结伴下山寻找真凶。**

---

## 推荐 Stage A 参数

| 项 | 选值 |
|---|---|
| 故事创意 | 见上方一句话 |
| 篇幅 | 短片 (~18-22 shots) |
| 画幅 | 竖屏 3:4 |
| 风格 | ink (中国水墨) / wuxia (武侠) / ghibli (吉卜力古风感) |
| 情绪基调 | 苍凉 / 悲悯 / 反转 / 武侠 |

---

## 验证 e2e 点

| 维度 | 期望 |
|---|---|
| 🌟 跨题材 vs test22/23 | 古装武侠, ink 水墨风, 三跨题材实战 (fairytale → 现代悬疑 → 古风武侠) |
| 🌟 supernatural / mythological schema (剑灵) | 剑灵 character_type=`supernatural` or `mythological`, T20-43 + T22-NEW-9 通用 fallback |
| 🌟 ink 水墨风格强注入 (StyleEnforcer) | 18+ shot 一致 ink/wuxia 风, 不漂 realistic/anime |
| 🌟 Layer 1 anchor (古装服饰) | 顾飞云 (灰布长袍 + 长须) + 苏寒梅 (素白衣裙 + 长剑) + 剑灵 (虚影 + 古剑光晕) 跨 shot 一致 |
| Stage 4.5 scene refs | 山林 + 茅屋 + 山道 + 决斗石台 + 远山远景 |
| BGM 古风武侠 | 古琴 + 箫 + 苍凉旋律 ~3 min |

---

## 多场景设计 (Stage 4.5 unique_locations)

预期 4-5 unique_locations:

1. **山林茅屋 (顾飞云隐居处)** — interior + exterior (茅屋内 + 茅屋外山景)
2. **山道松林** (exterior) — 苏寒梅上山
3. **决斗石台** (exterior) — 山巅平台 + 云海
4. **远山远景** (exterior) — 转场 + 闪回 + 下山
5. **剑客回忆 (闪回 江湖)** (exterior, 闪回) — 旧场景虚化

---

## 涉及角色 (3 个)

| 角色 | character_type | 验证 |
|---|---|---|
| 顾飞云 (退隐剑客, 中年) | `human` | 基准 |
| 苏寒梅 (少女, 复仇者) | `human` | 基准 |
| 剑灵 (古剑显灵) | `supernatural` or `mythological` | T20-43 + T22-NEW-9 fallback (虚影人形 + 古剑光晕) |

---

## 实战看点

- 三跨题材验证 (fairytale + 都市悬疑 + 古风武侠) — Layer 1 真**通用性铁律**
- ink 水墨风格 vs anime/cyberpunk/children_book (StyleEnforcer 80+ style 跨风格强注入)
- supernatural 剑灵真虚实结合 (人形 + 武器光晕)
- 武侠题材 BGM (古琴 + 箫 + 苍凉) vs test22 童话 vs test23 悬疑 — BGM mood 跨题材覆盖
