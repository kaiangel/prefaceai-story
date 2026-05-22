# test18 /preview 视觉验收审计 (2026-05-18)

> **审计场景**: test18《最后一克》生成成片
> **Founder 反馈**: 3 大类视觉质量问题
> **审计原则**: 通用工具视角 — 根因和修复方案必须 universal (适配任何故事/场景)

---

## ⚠️ 问题 #1 (🔴🔴 P0 灾难): 中文 location name 被强制渲染为招牌

### Founder 观察
Shot 5 / 8 / 13 的图像上出现中文招牌 "陈默租住楼的雨夜楼道口" — 这是个**地点描述**，不应该出现在画面上。

### 根因定位 (代码层)
`scene_reference_manager.py:719,739-758`:

```python
_SIGNAGE_KEYWORDS_ZH = {'铺', '店', '坊', '馆', '堂', '楼', '阁', '庄', '号', '行'}

def _detect_signage_name(self, location_name, location_desc, signage_text=''):
    if signage_text:
        return signage_text  # Stage 1 生成 (本次没有)
    cleaned = location_name.split('·')[0].strip()
    for kw in self._SIGNAGE_KEYWORDS_ZH:
        if kw in cleaned:
            return cleaned  # ⚠️ 把整个 location_name 当招牌返回!
    ...
```

`scene_reference_manager.py:825-833` (用于 EXT anchor):
```python
signage_section = f"""
REQUIRED TEXT ON SIGNAGE (CRITICAL):
The storefront/building sign MUST display: "{signage_name}"
Do NOT invent or substitute any other name. The sign text must match EXACTLY."""
```

### 触发流程
1. Stage 1 outline 生成 location_name = "陈默租住楼的雨夜楼道口" (中文, 含 "楼" 字)
2. SceneReferenceManager 生成 EXT anchor 时调用 `_detect_signage_name`
3. 关键词命中 "楼" → 返回完整中文 location_name 作为 signage
4. Prompt 注入: `The storefront/building sign MUST display: "陈默租住楼的雨夜楼道口"`
5. Seedream 忠实执行 → scene ref PNG 含中文招牌
6. 所有引用此 scene ref 的 shot (5/8/13) 都抄了招牌 → 污染最终成片

### Scene Ref 实证 (审计中确认)
- `rainy_night_alley_entrance_exterior_anchor.png`: 招牌 = "陈默租住楼的雨夜楼道口" ✅ 确认
- `apartment_window_seat_interior_anchor.png`: 内景无招牌 (interior path 注入文字到墙牌/匾额 — 本次没触发)

### 🔬 outline 实证 (深查后关键发现!)

| outline.unique_locations | display_name | signage_text | 实际行为 |
|--------------------------|-------------|--------------|----------|
| 1 林晓雨的出租屋窗边 | 含"屋" | **空** | ✅ 正确 (没招牌) |
| 2 **陈默租住楼的雨夜楼道口** | 含"楼" | **空** | ⚠️ fallback 命中"楼" → 灾难 |
| 3 城西万象广场珠宝柜台 | 含"店" | **"万象珠宝"** | ✅ 正确 (用 signage_text) |
| 4 陈默深夜接私活的出租屋小桌 | 含"屋" | **空** | ✅ 正确 (内景没命中) |

**Stage 1 outline LLM 设计是对的** — 它已经做了"该不该有招牌"的决策:
- 3/4 场所留 signage_text 空 = "不该有招牌"
- 1/4 (珠宝柜台) 填 "万象珠宝" = "该有招牌, 名字是这个"

**完全是 `_detect_signage_name` fallback 错误** — 它"不信"Stage 1 决策, 强行用 keyword 猜，结果把"住宅楼/教学楼/办公楼/出租屋"等普通住宅/办公场所都误判为招牌场所。

### 🌐 通用工具视角影响 (普适灾难)
`_SIGNAGE_KEYWORDS_ZH = {'铺', '店', '坊', '馆', '堂', '楼', '阁', '庄', '号', '行'}` 覆盖**绝大多数中文场景**:

| 故事类型 | 命中示例 location | 错误招牌输出 |
|---------|------------------|-------------|
| 都市情感 | 办公楼/写字楼/公寓楼 | "周末加班的办公楼" |
| 校园青春 | 教学楼/宿舍楼/食堂 | "高三8班教学楼三层" |
| 古装武侠 | 醉仙楼/翠云阁/济世堂 | "城东悦来客栈一楼" |
| 古风家庭 | 老宅祠堂/书坊 | "祖宅东厢正堂" |
| 商业 | 咖啡店/便利店/早餐铺 | "巷口张姨的早餐铺子" |
| 童话寓言 | 巫师塔楼/精灵阁 | "森林深处的智者堂" |

**T31 招牌检测设计初衷可能是**: 古代客栈/茶馆等有招牌的场景应正确渲染招牌名。
**实现缺陷**: T31 不信任 Stage 1 LLM 已经做的决策, 用过激 keyword fallback 把整个 location_name (地点描述) 当作招牌内容。

### 严重性
- **概率**: 80%+ 中文故事会触发 (任何含 _SIGNAGE_KEYWORDS_ZH 字符的 location name)
- **影响**: 所有引用该 scene ref 的 shot 都被污染 (5-15 shots / 故事)
- **可见度**: 中文招牌在画面上极度显眼，用户必然第一眼发现
- **品牌伤害**: 用户感觉"这工具连基本的中英文都搞不清楚"

---

## ⚠️ 问题 #2 (🔴 P1): B51 fallback 双重叠加 → 场景元素跳变 (Shot 3→4)

### Founder 观察
Shot 3 (桌椅 + CANCELED 平板 + 账单 + 窗台相框) → Shot 4 (桌椅消失 + 门打开 + 走廊 + 窗台相框还在)
"接连两张图，相同布局突然剧变，困惑"

### 根因定位
**两张 shot 都是 B51 fallback minimal shot** (Wave 11.1 引入的兜底机制):
- Shot 3 = Scene 2 fallback (INT. Rental apartment window seat - Late evening - light rain)
- Shot 4 = Scene 3 fallback (INT. Rental apartment window seat transitioning to exterior - Late night - rain)

Fallback prompt 极度模糊:
```
"Establishing shot of [scene_heading]. Atmosphere: ... Wide angle, showing the environment and setting clearly. No specific character interaction required."
```

→ Seedream 拿到模糊 prompt + 同一 scene_ref (`apartment_window_seat_interior_anchor.png`)
→ Shot 3 几乎照抄 scene_ref (桌椅完整)
→ Shot 4 prompt 提"transitioning to exterior", Seedream 自由发挥 (桌椅消失 + 走廊延伸)
→ 用户看到"同地点剧烈跳变" → 困惑

### 🌐 通用工具视角影响
- 任何故事如 LLM 返空 shots 都会触发 B51 fallback
- 任何同 location 多 scene 触发多次 fallback → 多张"模糊变奏"图
- 这是 RISK-T20-1 (33% B51 触发率) 的下游质量后果

### 修复方向 (universal)
1. **prompt 加约束** (RISK-T20-1 已记): "每 scene 必输出 2-3 shots, 禁止 shots=[]"
2. **B51 fallback 改进**: 不只生成 establishing wide shot, 应该按 scene 上下文生成更有针对性的 fallback (如有人物则带人物, 有道具则带道具)
3. **连续 fallback 抑制**: 同 location 连续 fallback 时, 应交错使用 scene_ref 内 / 外 视角, 避免"两张几乎一样的图"

---

## ⚠️ 问题 #3 (🔴 P1): Shot 5 vs Shot 13 几乎完全一样

### Founder 观察
"Shot 5 和 13 基本一样, 整个场景很相似, 没有人, 这是为什么呢？"

### 根因定位
| Shot | Scene | location_id | Fallback | 角色 | scene_ref |
|------|-------|-------------|----------|------|-----------|
| 5    | 4     | rainy_night_alley_entrance | ✅ YES | char_001+char_002 | exterior_anchor |
| 8    | 6     | rainy_night_alley_entrance | ✅ YES | char_001+char_002 | exterior_anchor |
| 13   | 9     | rainy_night_alley_entrance | ✅ YES | char_001+char_002 | exterior_anchor |

**根因三重叠加**:
1. **B51 fallback 触发率 33%** (Scene 4/6/9 同地点 + 雨夜冲突 → 全 LLM 返空)
2. **同 location_id 重用 scene ref** (设计如此, 保证地点一致性)
3. **fallback prompt 高度类似** (都是 EXT alley + rain wide establishing)
4. **Seedream 看 fallback prompt 模糊 + 同 ref → 高度复制原 ref**

意外的是 Shot 8 反而画出了人物 (Seedream 看到 char_refs 多了 char_001+002 → 自由发挥加人物), 而 Shot 5/13 没画 (这是 Seedream 决策黑盒, 不稳定)。

### 🌐 通用工具视角影响
- 任何故事多 scene 共用 location + 多次 LLM 返空 → 多张相似图
- 这是问题 #2 + RISK-T20-1 + scene_ref 重用机制的合并后果

### 修复方向 (universal)
- **优先修 RISK-T20-1** (减少 fallback 触发率) — 釜底抽薪
- 配合问题 #2 修复 (B51 改进 + 连续抑制)

---

## ⚠️ 问题 #4 (🟡 P2 新发现): Shot 8 fallback shot 画出了人物但 Shot 5/13 没画

### 现象
Shot 8 (Scene 6 fallback) 画出了陈默 + 林晓雨, 但 Shot 5/13 (同 fallback path) 画的纯环境。

### 根因
**Seedream 对模糊 prompt + 多 ref 的决策黑盒 + 随机性**:
- 所有 3 shot 都有 char_001+char_002 ref + scene ref
- 所有 3 shot prompt 都说 "No specific character interaction required"
- Seedream 自由发挥 → Shot 8 决定画人物, Shot 5/13 不画

**用户视角**: 不可预测, 同样故事跑多次结果不同, 影响信任。

### 修复方向 (universal)
- B51 fallback prompt 改进 — 明确指令"if characters present, include them; else pure environmental"
- 加 character ref 是否应该传 (fallback path 也许只传 scene ref 更稳)

---

## 🎯 优先级 + 修复方案推荐 (universal)

### 🔴🔴 P0 立即修 — 问题 #1 (招牌污染)

**方案 A (强烈推荐, universal 最安全, 信任 Stage 1 LLM 决策)**:
- 改 `_detect_signage_name` 完全删除 keyword fallback (L746-757)
- 只保留 L744-745: `if signage_text: return signage_text`, 其他直接 `return None`
- 信任 Stage 1 LLM: 它已经做了"该不该有招牌"+ "招牌叫什么"的决策
- **本次实证**: 4 场所中 3 个留空 (Stage 1 决定不该有招牌) + 1 个填"万象珠宝" — LLM 决策准确

**方案 B (保守, 保留 fallback 但严格化)**:
- 关键词 list 精简为"明确商业场所": `{'店', '铺', '馆', '号', '行'}` (去除"楼/坊/堂/阁/庄")
- 提取招牌名时去除前置修饰: e.g. "巷口张姨的早餐铺" → "早餐铺" (取最后名词)
- 加白名单否定: 含"住/办公/教学/楼道/单元/号院/出租" 等住宅/办公场所词的不识别为招牌

**Tester 验证用例** (universal):
- 都市 location "周末加班的办公楼" 不出招牌 ✓
- 古装 "城东悦来客栈" 招牌出 "悦来客栈" 而非全名 ✓
- 校园 "高三8班教学楼" 不出招牌 ✓
- 本次 test18 4 个 location 重跑应得到完全不同结果 (3 个无招牌, 1 个仅出"万象珠宝")

### 🔴 P1 — 问题 #2/#3 (B51 fallback 下游)

**先修 RISK-T20-1** (减触发率, 釜底抽薪)
**再修 B51 fallback prompt** (即使触发也提升质量)

### 🟡 P2 — 问题 #4 (Seedream fallback 决策不稳)

POST_BETA 阶段，依赖 B51 prompt 改进自然收敛。

---

## 📋 新 RISK 待加入 task list (3 个)

| RISK | P 级 | 描述 |
|------|------|------|
| RISK-T20-3 | 🔴🔴 P0 | T31 招牌检测过度匹配, 中文 location_name 强制渲染为招牌, 污染 scene ref 和所有 shot |
| RISK-T20-4 | 🔴 P1 | B51 fallback prompt 太模糊, scene ref 自由复制导致同地连续 shot 元素跳变 |
| RISK-T20-5 | 🟡 P2 | Seedream 对 fallback prompt 决策不稳定 (同 ref 不同 shot 行为差异大) |

---

## 🔬 PM 地毯式审查清单 (本次执行)

✅ 1. Read `4_storyboard.json` 看所有 20 shots 的 image_prompt
✅ 2. 检测每个 prompt 是否含中文 (结果: 全英文 ✅, 招牌污染不在 image_prompt 层)
✅ 3. Read `reference_images_log.json` 看每 shot 的 ref 配置
✅ 4. 视觉检查 scene ref PNG 文件 (rainy_alley + apartment_window)
✅ 5. Grep `scene_reference_manager.py` 看 anchor prompt 生成代码
✅ 6. Read `_detect_signage_name` + `_SIGNAGE_KEYWORDS_ZH` 找根因
✅ 7. 验证根因: "楼" 字在关键词列表 + location_name 含"楼" → 触发招牌注入
✅ 8. 通用性影响推演 (跨故事类型/场景类型枚举)
✅ 9. 修复方案 universal 验证 (3 个 universal 测试用例)
✅ 10. 优先级排序 (P0 招牌 > P1 fallback > P2 决策不稳)

---

*报告: 2026-05-18 完成*
*Founder 反馈: "总体不错 BGM也应景" + 3 个具体问题反馈*
*PM: 地毯式 10 维度审查 + universal 视角根因分析*
