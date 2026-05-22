# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## 📊 真**当前剩余 task** (5/22 15:20 cleanup)

### 🔴 P0 (内测启动卡点) — **0 个** ✅ Wave 7+8 已全修

### 🟡 P2 (内测后/不阻塞)
- **TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED** — test_status_authoritative 综合跑 mock 污染 (生产 0 影响, Wave 9+ 修)

### 🔮 长期 (memory 待办)
- `project_mysql_migration.md` — 生产 MySQL 迁移 (Ben 决定时机, Phase 6+)
- `project_schema_humanoid_fallback_remaining.md` — Wave 8 T22-NEW-9 真**已根治**, memory 可标 ✅
- `project_confirm_outline_not_wired.md` — Wave 8 T22-NEW-8 验证 **已实现** (5/22 PM 漏核 memory, memory 可删 or 标 ✅)

---

## ✅ COMPLETED 汇总 (Wave 1-8, 5/19-22)

### Wave 1+2+Round 3 (T20 全 P0/P1 fix, 5/20 17:20-19:41) ✅ 11 task
- T20-43/44/45/46/47/47-fix/48/49/50/50b/50-fix-2

### Wave 3 (3 P3 long-tail, 5/20 19:50) ✅ 3 task
- T20-51 BGM meta-prompt 路径 / T20-52 test isolation / T20-53 SQLAlchemy pool

### Wave 4+4.5 (T21-NEW-1+2 humanoid fallback, 5/20-21) ✅ 2 task
- T21-NEW-1 (8 type) + T21-NEW-2 (5 type wave2)

### Wave 5 Backend (T21-NEW-3/4/5/6/7, 5/21 19:25-22:30, Opus 4.7 xhigh) ✅ 5 task
- T21-NEW-3 restart UX / T21-NEW-4 cache-buster / T21-NEW-5 文案 / T21-NEW-6 sub-stage / T21-NEW-7 Stage 4.5 (DEC-047 + STATUS_API_CONTRACT v1.4 + Alembic 006)

### Wave II Frontend (T21-NEW-7 SceneRefsPreview, 5/21 22:40, Opus 4.7 xhigh) ✅
- 6 frontend 文件 / 14/14 useETA / 0 errors

### Wave 6 Layer 1 (T22-NEW-3 长期治本, 5/22 早间, 306 PASS) ✅
- AI-ML M1 spec 837 行 + M2-M5 round 1+2 (74/74)
- Backend inject + validator + image_generator wire (127/127)
- Tester baseline (105/105)

### Wave 7 (T22-NEW-7/4/6 + T22-NEW-2 + T22-NEW-5 frontend, 5/22 下午, 321 PASS) ✅
- T22-NEW-7 P0 chars=0 (ID format mismatch 真根因)
- T22-NEW-4 P0 三层 fallback (Haiku→Gemini→Sonnet)
- T22-NEW-6 P2 location wire
- T22-NEW-2 P2 SceneRefsPreview 智能展示
- T22-NEW-5 frontend (R4-2 砍 frontend 5 文件)

### Wave 8 (T22-NEW-9 + T22-NEW-8 + T22-NEW-5 backend, 5/22 15:00-15:20) ✅
- T22-NEW-9 P2 通用 fallback 架构 (229 PASS, 19→4 entries)
- T22-NEW-8 P2 confirm-outline 真**已实现 0 改动** (PM 漏核 memory)
- T22-NEW-5 backend (R4-2 wait loop 移除 + STATUS_API_CONTRACT v1.5)

**Wave 1-8 总修复**: 30+ task, 786+ test PASS, KEY_LEARNINGS #44-56 沉淀

---

## 📋 当前待处理 (历史 task 详情, 保留作记录)

### [2026-05-20 18:58] 🔴🔴 TASK-T20-47-FIX — P0 SONNET_MODEL ID 写错 100% fail-open (Founder 新 test20 实证 + Wave 2 PM 审查漏抓)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-47-fix `shot_validator.py:L184` SONNET_MODEL = `"claude-sonnet-4-6-20251101"` ❌ Anthropic 404 NotFoundError, 真实 ID `"claude-sonnet-4-6"` 无日期后缀. 导致 100% shot validation fail-open, 20 张图都没经过 LLM 质量验证 | 🔴🔴 **P0** | Backend round 3 (Sonnet 4.6 xhigh) | 🟡 **派工中 (5/20 19:00, agent a6964fac31009ea4b 后台跑)** |

**Founder 新 test20 实测**: Stage 5 shot generation 阶段, ShotValidator 100% 404 fail-open, 告警 "fail-open 率告警: 5/5 = 100.0% > 30% 阈值"。Anthropic 返回 `'model: claude-sonnet-4-6-20251101'` not found.

**真根因**: T20-47 Wave 2 Backend agent round 1 凭印象写 model name 加日期后缀 (跟 Haiku 4.5 `-20251001` 类比), 实际 Sonnet 4.6 真实 ID 是 `claude-sonnet-4-6` 无日期后缀 (按 CLAUDE.md memory)。

**PM 审查漏抓**: Wave 2 round 2 PM 审查只 grep 验证 `SONNET_MODEL` 字符串存在 + pytest 通过, 没真 mock Anthropic API 调用看 model ID 是否被 Anthropic 接受。pytest mock 用了 fake Anthropic client, 没触发真 404。

**修复 (Backend round 3 已派)**:
1. `app/services/shot_validator.py:L184` SONNET_MODEL 改 `"claude-sonnet-4-6"`
2. 同步检查 HAIKU_MODEL 真值 (期望 `claude-haiku-4-5-20251001`)
3. pytest 新增真 mock Anthropic API call test (不只 grep 字符串)
4. **不重启 backend** — 等 Founder 当前 Pipeline 完成 + PM 手动重启

---

### [2026-05-20 18:58] 🔴🔴 TASK-T20-50-FIX-2 — P0 save_all_references 覆盖 portrait (T20-50 修复绕过)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-50-fix-2 `reference_image_manager.py:L777-803` `save_all_references()` 无条件 image.save 覆盖 portrait, 绕过 T20-50 _gen_one_char_ref 的 skip_portrait 修复 → Founder 重生的 portrait 仍被 image_preparation 阶段覆盖 | 🔴🔴 **P0** | Backend round 3 (Sonnet 4.6 xhigh) | 🟡 **派工中 (5/20 19:00, agent a6964fac31009ea4b 后台跑)** |

**Founder 新 test20 实测证据**:
- 18:47:13 Founder 重生 char_003 portrait (绿色制服) size = 2372998
- 18:56 image_preparation 阶段后 char_003 portrait size = **2896955** (~500KB 不同, 真换内容)
- Pipeline log 写"老刘 portrait 已存在, 信任用户操作 (no regen)", 但文件实际被覆盖

**真根因**:
T20-50 round 1 修了 `pipeline_orchestrator.py:_gen_one_char_ref` 的 `_skip_portrait_local=True` (不调 Seedream 生 portrait), 但**没改 ReferenceImageManager.save_all_references**:
```python
# reference_image_manager.py:L777-803 真根因
def save_all_references(self, output_dir):
    for char_id, char_refs in self.character_references.items():
        for ref_type, image in char_refs.items():
            file_path = os.path.join(output_dir, f"{char_id}_{ref_type}.png")
            image.save(file_path)  # ❌ 无条件覆盖, 包括 portrait
```

`_gen_one_char_ref` 即使 skip_portrait, ReferenceImageManager 内部的 `character_references[char_id]['portrait']` in-memory dict 可能仍含 portrait entry (从 disk reload 后的 PIL Image), `save_all_references` 一统写盘. **更严重**: 如果 `generate_character_multi_refs(seed_image=portrait, skip_portrait=True)` 内部生成 fullbody 时把 fullbody 临时图覆盖了 in-memory portrait entry, save_all 写盘时就把 fullbody-like 内容写到 portrait 文件 → size 大幅变化 (符合 2372998→2896955 现象).

**修复方案 A (Backend round 3 已派, 最少改动)**:
```python
def save_all_references(self, output_dir):
    saved = {}
    for char_id, char_refs in self.character_references.items():
        saved[char_id] = {}
        for ref_type, image in char_refs.items():
            file_path = os.path.join(output_dir, f"{char_id}_{ref_type}.png")
            if os.path.exists(file_path):
                # T20-50 KEY_LEARNINGS #46: 文件已存在, 信任用户操作, 不覆盖
                logger.info(f"[ReferenceImageManager] {char_id}_{ref_type}.png 已存在, 信任不覆盖")
                saved[char_id][ref_type] = file_path
            else:
                image.save(file_path)
                saved[char_id][ref_type] = file_path
    return saved
```

**等价铁律 (KEY_LEARNINGS #46 升级)**: 用户操作 = 真相, **Pipeline 任何层** (`_gen_one_char_ref` + `save_all_references` + 任何其他下游) 都不能覆盖用户的 disk 文件. T20-50 round 1 只防一个层, round 3 需要防所有写盘点。

**这是"修了一半"第 7 次重演** (链条: #30/#39/#40/#43/#45/#48/本次)

---

### [2026-05-20 16:50] 🔴🔴 TASK-T20-50-FRESHNESS-CHECK-BUG — P0 用户重生角色白做 (Founder test20 实证)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-50 `pipeline_orchestrator.py:L1071` freshness check 算法 bug: `_portrait_fresh = _portrait_mtime > _char_ts + 30` 把"刚重生的"判为"陈旧"导致 Pipeline 重新生成覆盖 → 用户重生角色等于没用 | 🔴🔴 **P0** | Backend (Sonnet 4.6 xhigh) | ✅ **COMPLETED 5/20 17:20** (PID 68942, pytest 5/5 + 353/353 regression PASS) |

**Founder 发现路径**: test20 在 /characters 页重生陈婶 (gothic 成功) → 确认角色 → Stage 5 完成后看 27 shot, 陈婶又变回 realistic. PM 地毯式追查发现 character_refs/char_003_portrait.png mtime = 15:59 (Pipeline 阶段) 而非 15:46 (Founder 重生时刻).

**真根因 (代码层面)**:
```python
# pipeline_orchestrator.py:L1063-1075
_portrait_mtime = os.path.getmtime(_portrait_path)
_char_updated_at_str = char.get("updated_at")
_portrait_fresh = True
if _char_updated_at_str:
    _char_dt = datetime.fromisoformat(_char_updated_at_str.replace("Z", "+00:00"))
    _char_ts = _char_dt.timestamp()
    _portrait_fresh = _portrait_mtime > (_char_ts + 30)  # ❌ BUG 在这里
if _portrait_fresh:
    _skip_portrait_local = True  # 跳过重生
```

`+30` buffer 要求 portrait 文件 mtime 比 char.updated_at 晚 30 秒以上才算"新鲜"。但 RegeneratePortrait 端点 (B57) 在同一时刻 (T₀) 同时:
1. 生成新 portrait → 文件 mtime = T₀
2. 更新 DB char.updated_at = T₀

T₀ > T₀ + 30 = **False** → 算"陈旧" → Pipeline 重新生成 portrait, 覆盖 Founder 重生的版本

**为什么林深 / 镜中人 Founder 没发现?**
char_001 / char_002 没在 /characters 重生过, updated_at = 初次生成时间 (15:39)。Pipeline 15:59 重生用同样 CharacterDesigner 描述, 生成结果跟初次很相似 (LLM 给的描述一致 → Seedream 生成相近图)。Founder 视觉上看不出。陈婶因为重生改了 gothic 风格 ≠ CharacterDesigner 原始描述 → Pipeline 重生时又按原描述生 realistic 版 → Founder 一眼发现不一致。

**等价说**: 这是个**系统级 bug**, 影响所有角色, 只有 Founder 主动重生 + 风格大改时才显形。其他用户重生角色都白做了。

**修复方案 (Founder 2026-05-20 16:55 选定方案 A — 信任用户操作)**:

**核心铁律**: **用户在 /characters 页操作的产物 = 真相, Pipeline 不准二次裁判**。

```
正确逻辑:
  Stage 2 完成 → 3 角色自动生 portrait + fullbody
  用户在 /characters 页:
    ① 不动 → 用 Stage 2 版本 ✅
    ② 重生 portrait → 同步重生 fullbody (B57) → 锁定 ✅
    ③ 调整描述但没点重生 → 用现有 portrait (信任用户操作)
  用户确认角色 → Pipeline 进 Stage 5:
    ★ 永远信任 character_refs/ 里现有文件
    ★ 只在文件不存在时补生
    ★ 绝不基于 mtime/updated_at/freshness check 自检覆盖
```

**代码改动 (`pipeline_orchestrator.py:L1057-1099`)**:

```python
# 旧 (BUG): freshness check 算法 ~20 行
_portrait_seed_local = None
_skip_portrait_local = False
_portrait_path = os.path.join(_char_refs_dir_stage5, f"{char_id}_portrait.png")
if os.path.exists(_portrait_path):
    try:
        _portrait_mtime = os.path.getmtime(_portrait_path)
        _char_updated_at_str = char.get("updated_at")
        _portrait_fresh = True
        if _char_updated_at_str:
            from datetime import timezone
            _char_dt = datetime.fromisoformat(_char_updated_at_str.replace("Z", "+00:00"))
            _char_ts = _char_dt.timestamp()
            _portrait_fresh = _portrait_mtime > (_char_ts + 30)  # ❌ BUG
        if _portrait_fresh:
            from PIL import Image as _PilImage
            _portrait_seed_local = _PilImage.open(_portrait_path).convert("RGB")
            _skip_portrait_local = True
    except Exception as _fe:
        logger.warning(...)

# 新 (方案 A): 文件存在即信任, 永不覆盖
_portrait_seed_local = None
_skip_portrait_local = False
_portrait_path = os.path.join(_char_refs_dir_stage5, f"{char_id}_portrait.png")
if os.path.exists(_portrait_path):
    try:
        from PIL import Image as _PilImage
        _portrait_seed_local = _PilImage.open(_portrait_path).convert("RGB")
        _skip_portrait_local = True
        logger.info(f"[Pipeline] {char_name} portrait 已存在, 信任用户操作 (no regen)")
    except Exception as _fe:
        logger.warning(f"[Pipeline] 读取 {char_id} portrait 失败, 重新生成: {_fe}")
        _portrait_seed_local = None
        _skip_portrait_local = False
```

同样逻辑应用到 fullbody (如果有类似 freshness check 也去掉)。

**adjust_character endpoint 的责任** (T20-50 不管, 单独审查):
- 如果用户在 /characters 页"调整描述", endpoint 必须立刻重生 portrait+fullbody 文件
- 不能依赖 Pipeline 兜底
- 待 Backend 审查 `app/api/projects.py` adjust_character endpoint 真行为

**验收**:
1. 跑 test 重生陈婶 portrait → Stage 5 看 backend.log 出现 "portrait 已存在, 信任用户操作 (no regen)" ✅
2. 27 shot 里陈婶 = /characters 页确认的版本 (gothic) ✅
3. pytest 新单测验证: `if file exists → skip = True; if file missing → generate`
4. character_consistency_regression 回归不退化
5. **跨题材测试**: test21 跑通 + 1 个 fairytale 跑通 (确认其他角色重生场景也 OK)

**这是"修了一半" 链条第 5 次重演** (#30/#39/#40/#43/本次): B57 修了"同步重生 fullbody + DB updated_at" 但没改 freshness check 算法, 导致重生流程白做。

**KEY_LEARNINGS #45 + #46 已加**: B57 设计原则错误。设计任何"用户编辑入口"必须画完整数据流图。

---

### [2026-05-20 16:55] 🔴 TASK-T20-46-CHARACTER-STYLE-CONSISTENCY — 角色风格统一 (test20 林深 anime/陈婶 realistic 不一致)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-46 CharacterDesigner LLM 输出角色描述具体性差异巨大 → Seedream 风格自由发挥 → 3 角色风格不统一 (林深 anime / 镜中人 gothic ✅ / 陈婶 realistic) | 🔴 P1 | AI-ML + Backend wire | ✅ **COMPLETED 5/20 17:34** (AI-ML STYLE_INFUSION_RULES 47/47 PASS + Backend wire pipeline_orchestrator.py L561-564 11/11 PASS + Backend 重启 PID 71758, 真 e2e 验证待 Founder 重跑 test20) |

**Founder 实测**: test20 选 gothic 风格, 但生成的 3 角色 portrait 风格完全不同:
- 林深: 二次元/anime 偏漫画 (描述"28岁程序员戴眼镜深蓝卫衣"过于普通 → Seedream 给 anime 审美默认)
- 镜中人: ✅ gothic dark romantic (描述"面容模糊苍白双眼空洞"本身抽象风格化)
- 陈婶: ❌ 真人写实照片 (描述"60岁老妇人头发花白暗红色睡袍"过度写实化 → Seedream 偏 realistic)

**真根因**: StyleEnforcer 真调了 (`reference_image_manager.py:L378+L586`), gothic mandatory keywords 也注入了, 但 CharacterDesigner LLM 输出的具象人物描述"权重过大"反向压过风格指令, Seedream 按描述具体性自由发挥。

**修复方向**: AI-ML 改 CharacterDesigner prompt 让 LLM 输出 character 描述时**强制带 style hint**:

```
旧: "60岁老妇人, 头发花白, 暗红色睡袍"
新: "60-year-old woman drawn in gothic dark romantic style, pale gaunt face,
     ash-gray hair with silver streaks, deep blood-red gothic-cut robe with lace trim,
     hollow eyes ringed in shadow"
```

具体改动:
1. `app/prompts/character_design_prompts.py` 加 STYLE_INFUSION_RULES section
2. CharacterDesigner Stage 2 Sonnet prompt 强约束: "每个 character 的 physical + clothing 描述必须以 'drawn in {style_name} style' 开头, 后续每个字段加 style-aligned 形容词"
3. 不同 style preset 给不同 modifier 词典 (gothic: pale/gaunt/ash-gray; anime: bright/expressive; realistic: natural/proportional)

**验收**:
- 重跑 test20 (gothic), 3 角色 portrait 风格统一 (≥ 4/5 视觉一致性)
- test21 (scifi) + 1 fairytale 跨题材验证不退化
- 不影响角色一致性 (跨 shot 同角色仍一致)

---

### [2026-05-20 16:55] 🟡 TASK-T20-47-ANTHROPIC-529-FALLBACK — ShotValidator 备用模型 fallback (Anthropic 大范围过载)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-47 Anthropic 服务过载 → ShotValidator 4/4 retry 全 529 → fail-open 放行 (test20 13/27 = 48% shot 验证跳过) | 🟡 P2 | Backend (Sonnet 4.6 high) | ✅ **COMPLETED 5/20 18:25** (Wave 2 全闭环) |

**Founder 实测**: test20 image_generation 阶段, Anthropic 区域性过载, ShotValidator 调 Sonnet 4.6 验证 shot 描述时, 27 shot 中 13 个 4 次 retry 全 529, T20-14 fail-open 放行 (skipped_count=13)。

**影响**:
- 48% shot 没经过 LLM 质量验证就交付 (Shot 16 anatomy 是少数验证到的)
- 其他 12+ 张 fail-open shot 可能有 hallucination 但没被发现 (Founder 翻 /preview 才能 visual check)
- 用户体验: Anthropic 偶发过载导致质量验证形同虚设

**修复方向**:
1. **降级 fallback**: Sonnet 4.6 全 529 → 切 Haiku 4.5 (更低 throughput, 但通常不过载) → Haiku 也过载 → fail-open
2. **增加 retry 次数**: 4 → 8 (拉长总等待时间, 给 Anthropic 恢复时间)
3. **监控 fail-open 率**: > 30% 时记 ERROR + 告警 (DevOps), 让运维知道"今天 Anthropic 不稳"
4. **可选**: 切换 provider (OpenAI / Gemini 等) 做 ShotValidator 备份, 但成本不一定划算

**验收**:
- 模拟 Anthropic 529 (mock 测试), ShotValidator 真切 Haiku 4.5
- Haiku 也 fail → fail-open, log 标 reason=ALL_PROVIDERS_OVERLOADED
- 跑 test 验证不退化

**长期愿景**: 任何外部 LLM 调用都应有 fallback chain, 不能单点依赖 Anthropic Sonnet 4.6。

---

### [2026-05-20 16:55] 🟡 TASK-T20-48-SHOT-ANATOMY-AUTO-REGEN — Shot anatomy issue 自动重生 (test20 Shot 16 4 只手)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-48 Seedream hallucination 画 4 只手 (Shot 16), T17 ShotValidator 抓到但仅警告级 ⚠️ 不强制重生 → 用户看到畸形画面 | 🟡 P2 | AI-ML (Sonnet 4.6 high) + Backend | ✅ **COMPLETED 5/20 18:25** (Wave 2 全闭环) |

**Founder 实测**: test20 Shot 16 anatomy_issue: "4 hands visible (normal humans have 2 hands)" + "4 arms visible". Pipeline 接受这张图, 不重生。

**真根因**: Seedream 大模型常见 anatomy hallucination, 不是 prompt 错 (prompt_quality_report.md 显示 Shot 16 prompt 1158 字符通过 3 大检查)。但 ShotValidator T17 设计是 ⚠️ 警告级, 不触发自动重生 (设计原意可能是"不让 Pipeline 死循环"但牺牲了用户体验)。

**修复方向**:
1. **升级 anatomy_issue 为 ERROR + 触发自动重生** (最多 2 次), 否则记 partial_failure
2. **prompt 端预防**: AI-ML 在 storyboard_prompts.py 加 hard constraint "anatomically accurate, exactly 2 hands, exactly 2 arms, normal proportions" 强制词
3. **frontend /preview 显示警告 badge**: shot 卡片右上角红色"⚠️ 检测到 anatomy 问题"标记 + 一键重生按钮提示

**验收**:
- Mock anatomy_issue 触发 → ShotValidator auto-regen → 二次重生成功 → Pipeline 接受
- 跑 test 不退化
- /preview anatomy 警告 badge 真显示

---

### [2026-05-21 22:00] 🔴🔴🔴 TASK-T22-NEW-3-CHARACTER-SCHEMA-FORCE-INJECTION — Stage 4 LLM 真**全 character physical 字段自由发挥**, 真通用性 P0 灾难 (Founder 5/21 test22 实测发现, 真历史长期违反 CLAUDE.md "产品生命线" 铁律)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T22-NEW-3 Founder 实测 test22 fairytale shot 9-14 (6 张): 珊瑚 char_001 真 schema `hair_color="deep sea-green with teal highlights"`, portrait 真渲染**粉红长卷发** (Seedream 自由发挥), 但 Stage 4 LLM 真生 shot prompt 写 `"dark hair"` (全 6 shot) — 真完全忽略 char_001 schema. 真 CLAUDE.md 角色一致性"产品生命线" P0 违反! Shot 11/13 还真"3D Pixar 写实"漂移 (StyleEnforcer 真没强对 children_book 水彩) | 🔴🔴 **P0 (产品生命线)** | AI-ML (storyboard_prompts.py + storyboard_director.py) | ⏳ 待派工 |

**真三层不一致 (实证)**:
- Layer A: Stage 2 schema `hair_color="sea-green"` ≠ Portrait 渲染 "**粉红色**" (Seedream 自由发挥)
- Layer B: Portrait 真"粉红色" ≠ Stage 4 shot prompt "**dark hair**" (LLM 完全忽略 character data)
- Layer C: Shot 11/13 真"3D Pixar 风格漂移" (StyleEnforcer 真没强对到 image_prompt)

**真证据 (shot 9-14 全 grep)**: prompt 真含 "dark hair" 全 6 shot. 真"珊瑚角"装饰真消失 5 shot (10-14).

**真根因**:
- `app/services/storyboard_director.py` L229 真**0 注入** char physical 到 image_prompt
- `app/prompts/storyboard_prompts.py` L904 真"建议" LLM 用 `[hair_color]` 模板替换, 但 LLM 真自由发挥, 真没强制读 character data

**修复方向** (AI-ML 真大改):
- 改 storyboard_prompts.py: 真**强制注入** character 完整 physical (hair_color/hair_style/distinctive_marks) 到 LLM context, **明确 SHALL NOT 自由发挥**
- 真考虑预处理 image_prompt — 自动 inject character signature line (e.g., "Coral: deep sea-green long flowing hair with pearl pins, oval face, mermaid tail...")
- StyleEnforcer 真强对 children_book mandatory keywords 到每个 shot prompt 开头 (T20-46 already 做但显然 shot 11/13 还漂)

**测试范围**: 跨题材 (cyberpunk/fairytale/scifi) shot prompt 真含 "{真 hair_color}" 一致性

**不阻塞内测? 真阻塞内测!** 角色一致性是 CLAUDE.md "产品生命线", 用户看到自家美人鱼黑发会感觉不专业

---

### 🚨 真通用性扩展 (Founder 5/21 22:00 提醒"通用性角度")

**真深度 grep 20/20 shot 真 hair 描述统计**:
- 0 shot 真用对珊瑚 schema "sea-green" hair
- Shot 8-14: 真写 "dark hair" (7 shot 真错)
- Shot 1-7, 15-20: 真空 (13 shot 真省略)
- **真 100% miss** — CLAUDE.md "每个 shot prompt 必须包含完整角色外观描述" 真长期违反

**真不止 hair_color, 真全 physical 自由发挥**:
- face_shape / eye_color / skin_tone / distinctive_marks (鱼尾鳞片) 真全自由发挥
- 不止 char_001 真 — char_002 ash_blonde 真也漂 (portrait 银白), char_003 silver-white 真未验

**真跨题材普遍性 (假设, 真历史 P0)**:
- test21 cyberpunk (小爱/陈远/林博士) 真可能同样
- test20 horror gothic (林深/陈婶/老刘) 真可能同样
- 真"用户没注意"因为 Seedream portrait reference 一致性 真掩盖了 prompt 描述错位

**真 PM 推荐方案 A+B 组合 (~8h)**:
1. **Backend post-process 强注入** (~2h): Stage 4 LLM 生成 image_prompt 后, 真**自动注入 [CHARACTER REGISTRY]** block 到 prompt 开头 (3 角色完整 physical signature), 真覆盖 LLM 自由发挥, 真**绕过 LLM 修复**
2. **AI-ML 升级 storyboard_prompts.py L904** (~3h): "建议性" → "**MUST**" 强制 + few-shot examples + 真禁止 dark/black/generic 通用词
3. **ShotValidator + Tester 跨题材 regression** (~3h): 加 prompt vs schema validation + 跑 test19-22 全 grep 验证

---

### 🚨🚨 真**通用故事角度** 升级 (Founder 5/21 22:05 提醒"通用故事, 不是修一个/一类")

**真根本性 problem (LLM-generated visual narrative 通用)**:
- LLM 真"创意能力" vs 真"严格一致性" 张力 — LLM 真乐于"换汤换药"
- "建议性 prompt hint" 真永远被 LLM 创意绕过 — 真这是 LLM 本质
- 真同问题出现在 Midjourney/Sora/Runway 等所有 LLM-generated visual content 工具

**真通用性扩展** (不止 character, 真所有 stable identity 层):
| 应该固定 Anchor | LLM 自由发挥 | 真同类问题 |
|---|---|---|
| character physical (hair/face/skin/marks) | "dark/blonde" generic | ✅ 已发现 |
| character clothing core (signature 服饰) | 不一定固定 | 🚨 待验 |
| location identity ("magic forest" 真什么光/季节?) | 真自由 | 🚨 同样问题 |
| props signature (shell harmonica 真什么样?) | 真自由 | 🚨 同样问题 |
| style mandatory (children_book 必须水彩) | shot 11/13 漂 3D Pixar | ✅ 已发现 |
| time_of_day / lighting continuity | 真自由 | 🚨 可能漂 |

**真普遍性**: 19 character_types × 80+ styles × 任意题材 × N shots — **真每个故事都面对**, 不是 fairytale 特例

**真根因深定位** (产品架构层):
1. Pipeline 真**无 Identity Anchor 框架** 接入 (CLAUDE.md 真提到 docs/CHARACTER_IDENTITY_FRAMEWORK.md v1.0 真未实施)
2. 真**信息传递衰减** (Stage 2 → 4 → 5 真每跳丢一层 fidelity)
3. 真**创意 vs 一致** 真无 separation of concerns (LLM 真同时管, 真应该 LLM 管创意 + Backend 管一致)
4. 真**无 cross-stage validation** (ShotValidator 真验 image vs prompt, 真不验 prompt vs schema)

**真通用解决方案 (3 层架构)**:

#### Layer 1: **Identity Anchor Framework 接入** (长期治本, 1-2 day)
- 真实施 `docs/CHARACTER_IDENTITY_FRAMEWORK.md v1.0`
- 真分离固定层 (hair_color/face_shape/distinctive_marks/clothing_core) vs 变化层 (pose/expression/camera/emotion)
- 通用所有 19 character_types

#### Layer 2: **Backend Post-process 强注入** (短期 hotfix, 2-3h, 真绕过 LLM)
Stage 4 LLM 生成 image_prompt 后, 真自动 prepend:
```
[CHARACTER IDENTITY ANCHORS — MUST APPEAR AS DESCRIBED]
char_001: deep sea-green long flowing hair (past waist, pearl pins), iridescent fair skin, vivid ocean blue almond eyes
char_002: ash-blonde short hair, sun-tanned skin
char_003: silver-white spiraling long hair, lavender-pale skin

[STYLE MANDATORY]
children_book watercolor: soft pastel, hand-drawn texture, NO 3D Pixar, NO realistic rendering

[SCENE]
{LLM 真生成 image_prompt — 创意允许但 anchor 不可改}
```
- 真通用全 character_type / 全 style / 真覆盖 100% LLM 自由发挥盲点

#### Layer 3: **跨题材 baseline regression** (持续, ~1h/题材)
- 真测 19 character_types × 随机 5 styles
- 真验证 shot prompt 100% 含 character schema 关键字
- 真发现 long-tail 问题 (props/location/time_of_day 漂)

**真历史 P0 长期违反**: test19-22 真所有 e2e 都可能有此 100% miss 问题, 用户没注意因为 Seedream portrait reference 一致性掩盖了 prompt 描述错位

**Founder 决策 (2026-05-21 22:55 真选 Layer 1 长期架构治本)**: 真**不走** Layer 2 hotfix patch, 真选 **Layer 1 Identity Anchor Framework v1.0 真根治**. 真理由: 跨 19 character_types × 80+ styles × 任意题材, hotfix patch 真治不了根 — 必须真**架构层 separation of concerns** (LLM 真管创意 + Backend 真管一致). 真内测延后等架构改造完成

**Layer 1 真实施计划 (~1-2 day, 真根治, Wave 6 长期架构 task)**:
1. **Identity Anchor Framework v1.0 真接入** (`docs/CHARACTER_IDENTITY_FRAMEWORK.md` 真早写好真未实施)
   - 真分离 **Identity Anchors** (hair/face/skin/marks/clothing_core/style_signature/location_signature/props_signature/time_continuity) vs **Narrative Variables** (pose/expression/camera/emotion/interaction)
   - 真所有 19 character_types / 80+ styles / 任意题材 真统一框架
2. **Backend post-process 强注入** (架构层, 真绕过 LLM 决策, 不是 hotfix)
   - Stage 4 LLM 真生 image_prompt 后, 真自动 prepend [IDENTITY ANCHORS] block + [SCENE] block
   - 真覆盖 character / style / location / props / time 真 5 维度 anchor
3. **Validation 层升级** (ShotValidator + PromptValidator 新加)
   - 真 prompt vs schema validation (新增, 在生图前真验)
   - 真 image vs prompt validation (已有, T20-47)
4. **跨题材 baseline regression** (真持续 CI 防退化)
   - 真 19 character_types × 真随机 5 styles 真 baseline test
   - 真 grep shot prompts 100% 含 character schema 关键字
5. **架构文档** + **DEC-048 决策记录** + **STATUS_API_CONTRACT v1.5 真升级**

**真不影响内测启动? 真影响** — Founder 真接受真延后等真根治, 不"先解锁"

---

### [2026-05-21 21:27] 🟡 TASK-T22-NEW-2-SCENE-CARDS-SMART-DISPLAY — SceneRefsPreview 卡片真智能展示 (Founder 5/22 **第 2 次**实测, 升级 P3→P2)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T22-NEW-2 Founder 实测 test22 fairytale 真**第 2 次**遇到 (5/21 + 5/22): SceneReferenceManager 按场景语义判断 — 海底宫殿/海面/洞穴/沙滩 天然只有 interior or exterior (DEC-014/DEC-009 by-design 智能), 渔村两者都有. 但 frontend SceneRefsPreview 默认显示 2 槽位 (interior + exterior) "外景未生成"占位, 让用户**误以为"缺失"** | 🟡 **P2 升级** (Founder 5/22 第 2 次抓到, UX 视觉空洞 + 心理负担) | Frontend (StageC.tsx SceneRefsPreview) | ⏳ Wave 6+ 待派 |

**Founder 5/22 13:44 原话**: "这里还是有如图这样的有内景没有外景或者有外景没有内景的情况, 我知道符合逻辑, 但要记下来, 前端的 UX 可以做的更好"

**Founder 原话**: "场景1没有外景, 2没有内景, 3没有外景, 4没有内景, 5内外都有, 看看是不是正常正确的"

**真根因**: backend 真按 by-design (海底/洞穴 only interior, 海面/沙滩 only exterior), 但 frontend 真假设每 location 都有 2 张图

**修复方向**:
- 卡片真判断 `interior_url` / `exterior_url` 是否真存在
- 只显示真有的图
- 加文字标签 "(海底场景, 无外景)" / "(开放外景, 无室内)" 等真合理提示
- 不要默认 2 空槽位让用户以为有缺失

**不阻塞内测**: 真功能正确, 只是 UX 视觉问题, 用户操作流程不受影响

---

### [2026-05-21 22:35] 🟡 TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED — test_status_authoritative + test_t21_digital_virtual_fallback 综合跑某些组合 27 errors + 4 fail (Backend Wave 5 报告发现, 跟 T20-52 同款 mock state 污染)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T22-NEW-1 Backend Opus 4.7 Wave 5 报告: pre-existing T20-52 同款 isolation bug 持续 (test_status_authoritative 综合跑 T21 系列时 27 errors + 4 fail, 单跑都 PASS). 跟 T20-52 同款 mock state 污染, 生产代码 0 bug, 仅 test infra 问题 | 🟢 P3 long-tail (不阻塞内测, Wave 6 修) | Backend (test isolation, 镜像 T20-52 用 importlib.spec_from_file_location 同款) | ⏳ Wave 6 待派 (内测 1-2 周后) |

**修复方向**: 镜像 T20-52 修法 — tests/test_status_authoritative + tests/test_t21_digital_virtual_fallback 各加 autouse fixture + importlib.spec_from_file_location 隔离 mock state

**不阻塞内测**: 生产代码 0 bug, 单跑全 PASS, 只在综合跑某些组合下 fail

---

### [2026-05-21 18:25] 🟢 TASK-T21-NEW-3/4/5/6/7 — Wave 5 Backend 全 5 task 完成 ✅ (Opus 4.7 + thinking xhigh)

| Task | 状态 |
|---|---|
| T21-NEW-3 restart progress/ETA reset | ✅ **COMPLETED Backend 5/21 22:30** (chapters.py restart 真重算 progress + ETA, 5/5 PASS) |
| T21-NEW-4 portrait cache-buster | ✅ **COMPLETED Backend 5/21 22:30** (AdjustCharacter + RegeneratePortrait + characters_json 同步, 4/4 PASS) |
| T21-NEW-5 stage_message 全身参考图 | ✅ **COMPLETED Backend 5/21 22:30** (KEY_LEARNINGS #46 同源, 2/2 PASS) |
| **T21-NEW-7 Backend** | ✅ **COMPLETED Backend 5/21 22:30** (Stage 4.5 ~180 行 + R4-3 1800s 闸门 + 3 endpoint + STATUS_API_CONTRACT v1.4 + DEC-047 + Alembic 006 + 9 ui_phase 状态机 + DEC-014/DEC-009 一致性保留, 24/24 PASS) |
| T21-NEW-6 sub-stage messages | ✅ **COMPLETED Backend 5/21 22:30** (sub_progress_callback 4 参数 + ≥5 sub-step UPDATE, 6/6 PASS) |
| **T21-NEW-7 Frontend** | ⏳ Wave II 待启 (Backend 完成, Frontend 用真 API contract v1.4 镜像 characters 真改造) |

**PM 9+10 Layer 地毯式审查全过 5/21 22:35** ✅ — KEY_LEARNINGS #47/#48/#49 + Ben 5/13 + carpet_review 全过, 0 越权, 真完整闭环

**Pre-existing T20-52 isolation bug 持续** (test_status_authoritative 综合跑某些组合下 fail, 单跑 PASS, 不阻塞内测, 后续 Wave 修)

**Backend 未重启** — 等 Frontend Wave II 完成 + Alembic 006 真跑 + 一起重启 (避免重复)

---

### [2026-05-21 18:25] 🔴 TASK-T21-NEW-7-SCENE-IMAGE-CONFIRM-PAGE (历史派工记录, Backend 已完成 Wave I)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-7 Founder 决: 情节确认大纲已有, scenes 页面应做真"场景视觉确认" — 等场景参考图 (interior + exterior) 生成后, frontend 显示场景参考图卡片让用户查看/修改/重生/确认/60s 倒计时. 跟 characters 页面同款对偶设计 | 🔴 P0 (内测前必修, 真功能升级) | Backend ✅ + Frontend ⏳ | 🟡 **Wave I Backend ✅ 5/21 22:30 + Wave II Frontend 待派** |

**Founder 原话**: "情节确认其实在大纲环节就有了 如果选B（改文案）这样是不是重复了 能不能走和角色参考图预览一样的逻辑 等场景参考图生成后显示在前端scenes页面，可以让用户查看、修改、重新生成、确认等等，也有倒计时60s"

### 真架构改动 (方案 D)

**Backend Pipeline 架构** (`app/services/pipeline_orchestrator.py`):
- Stage 4 完成 → **新 Stage 4.5 `scene_image_preparation`** (单独生成场景参考图 interior + exterior, 然后等用户确认)
- Stage 4.5 完成 → 用户确认 → Stage 5 shots

**新 3 endpoint** (`app/api/chapters.py`):
- `GET /chapters/{n}/scene-references` 返回所有场景参考图 (location_id + interior_url + exterior_url + description_zh + atmosphere/time_of_day/lighting_condition)
- `POST /chapters/{n}/scenes/{location_id}/regenerate-reference` 重生单个场景参考图 (支持 interior/exterior 单独重生 + adjust 文字描述)
- `POST /chapters/{n}/confirm-scene-references` 确认场景参考图继续 Stage 5

**STATUS_API_CONTRACT v1.3 → v1.4** (`.team-brain/contracts/STATUS_API_CONTRACT.md`):
- 新增 `ui_phase = "scene_references_review"` (Stage 4.5 后)
- 新增 `scene_references_ready` boolean field
- Ben 5/13 backend authoritative + frontend 派生协议保留

**Frontend StageC 大改** (`frontend/src/components/create/StageC.tsx`):
- scenes 页面真改造: 显示场景参考图卡片 (跟 character 卡片同款)
- 每个 location 显示 interior + exterior 2 张图
- 编辑文字描述 + "重生" 按钮 (调 POST regenerate-reference)
- 60s 倒计时 (跟 characters 页面同款)
- "确认场景继续" 按钮 (调 POST confirm-scene-references)

### Wave 派工

| Wave | Agent | Task | 时间 |
|---|---|---|---|
| Wave I | Backend Sonnet 4.6 xhigh | T21-NEW-3 + T21-NEW-4 + T21-NEW-5 + T21-NEW-6 + T21-NEW-7 Backend | ~3h |
| Wave II | Frontend Sonnet 4.6 xhigh | T21-NEW-7 Frontend (用真 API contract v1.4) | ~1.5h |
| Wave III | PM 40+ 维度审查 + 重启 + Founder e2e test22 fairytale 美人鱼 (aquatic schema fallback T21-NEW-2 实证) | - | ~30 min |

### 影响

- **DEC-XXX 新决策**: Stage 4.5 scene_image_preparation 引入 (类似 character_design 之后的等待确认)
- **DEC-014 / DEC-009**: 场景一致性 (interior/exterior 关联) 真保留, 不影响
- **Ben 5/13 protocol**: STATUS_API_CONTRACT v1.4 升级, Ben 看新契约

---



**真根因**: Stage 3 screenplay.json 每个 scene 含:
- `scene_heading` (英文 location, e.g., "INT. Virtual call center - 2045 night shift")
- `description` (中文情节摘要, e.g., "2045年。小爱今日完成第800通通话")
- `location_id` / `atmosphere` / `time_of_day` / `lighting_condition` (场景属性, 当前没显示)
- `action_beats` (情节节拍)

Frontend `StageC.tsx:1815` 显示 `scene.description` (情节) + placeholder "描述你想要的场景氛围" — 文案错位

**对照 CLAUDE.md 用户旅程 Stage B 设计**: 这个页面真做的是"**情节走向**"确认 (CLAUDE.md L307: "情节走向 列表展示, 可拖拽调整/删除/新增"), 不是场景设定确认。

**修复方向 (3 方案)**:
- **🟢 方案 B 简单 (推荐)**: Frontend 改文案 — 页面标题 "场景确认" → "情节确认", placeholder "描述你想要的场景氛围" → "调整情节走向". 零功能改, 零数据改. (~5 min)
- 🟡 方案 C 双显示: 上半显示场景属性 (location_id_zh + atmosphere 只读), 下半情节可编辑
- 🔴 方案 A 真"场景"功能: 让用户真改场景属性 (Frontend + Backend + AI-ML 协作), Pipeline 重新生 image_prompt 用新场景

**Founder 选哪个?** PM 推荐 B (符合 CLAUDE.md Stage B 设计)。

---

### [2026-05-21 17:03] 🔴 TASK-T21-NEW-6-IMAGE-PREPARATION-SUBSTAGE-UX — image_preparation 阶段 stage_message 卡几分钟没动, 用户以为有错误没耐心 (Founder 实测 5/21 16:54-17:01, ~7 min 无细化)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-6 image_preparation stage 真子环节 (fullbody 生成 + 场景参考图 interior+exterior anchor + shots refs 组装 + shots dispatch) frontend stage_message 没细化, 用户卡几分钟看到一样文案以为有错误或没动. Founder 实测 5/21 progress 65%→75% 期间 stage_message 一直 "角色参考图 3/3 完成 (陈远)" 几分钟没变 → "开始绘制画面..." 又卡几分钟 | 🔴 P1 (UX 内测前必须修) | Backend (stage_message 细化) + Frontend (展示) | ⏳ 待派工 |

**Founder 原话**: "前端在确认场景后一些细节环节还需要 UX 的细化 否则用户一直觉得怎么进度条都不动 会以为有错误或者什么 然后没耐心 不知道到底发生了什么"

**真根因**: backend pipeline_orchestrator.py image_preparation stage 内部多个 sub-steps 没 update job.stage_message, 全用同一文案

**修复方向**: 
- Backend: 加 sub-stage stage_message:
  - "生成 fullbody 参考图 X/3 (角色名)..."
  - "生成场景参考图 (interior 1/4: 客服中心) ..."  
  - "生成场景参考图 (exterior 1/2: 神经研究所外景) ..."
  - "准备分镜引用映射..."
  - "调度 Shot 生成 (X/19)..."
- Frontend: 不用改 (stage_message 直接显示 backend 真值)

**Founder 决策**: 内测前必须修 — UX 耐心阈值是真痛点, 不修内测用户会以为产品卡死

---

### [2026-05-21 16:55] 🟡 TASK-T21-NEW-5-STAGE5-UX-TEXT-PORTRAIT-VS-FULLBODY — Stage 5 image_preparation 文案"角色参考图"模糊, 用户误以为 portrait 重生 (实际 fullbody 重生, T20-50 遵守)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-5 Founder 实测 5/21 16:54 Stage 5 image_preparation 阶段 frontend stage_message 显示"角色参考图 1/3 完成 (林博士)"。Founder 警觉以为 Pipeline 重复生成 portrait (违反 T20-50 用户操作=真相). 真实情况: portrait 真没动 (3/3 "信任用户操作 no regen"), 实际是 fullbody 真生成 (期望). 文案模糊导致误解 | 🟡 P2 (UX 文案, 不阻塞) | Frontend + Backend (stage_message 文本) | ⏳ 待派工 |

**真根因**: backend `image_preparation` stage_message 用"角色参考图", 但实际 portrait + fullbody 都叫"参考图"。需要明确区分:
- portrait = "角色头像/肖像" (信任不重生)
- fullbody = "角色全身参考图" (Stage 5 真生成)

**修复方向**: 
- Backend `pipeline_orchestrator.py` Stage 5 stage_message 改 "全身参考图 X/3 完成 ({角色名})" 或 "角色 fullbody 参考图 X/3 完成"
- Frontend 不需改 (stage_message 直接显示 backend 真值)

**Founder 警觉点**: T20-50 KEY_LEARNINGS #46 "用户操作=真相" 是 Founder 设计铁律, 任何文案让用户怀疑都是 P2 真问题

---

### [2026-05-21 16:40] 🟡 TASK-T21-NEW-4-PORTRAIT-CACHE-BUSTER — AdjustCharacter 重生 portrait 后 frontend 浏览器 cache 旧 404, 图片显示"加载失败"

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-4 Founder 实测 5/21 16:31 char_001 小爱 portrait Seedream IncompleteRead 失败 → 16:37 点"重新生成" → 16:38 Seedream 真重生成功 PNG 2.28MB → 但 frontend `<img>` 同一 URL 拿到浏览器 cache 旧 404, 显示"图片加载失败"。后端 curl /static 真返回 200, DB UPDATE characters_json 真完成 | 🟡 P1 (UX, 不阻塞 - 硬刷新解锁) | Frontend | ⏳ 待派工 |

**真根因**: AdjustCharacter 重生 portrait 后, portrait_url 字段不变 (`/static/.../char_001_portrait.png` 仍同 URL), 浏览器 cache 之前的 404 状态, 不重新请求

**修复方向** (镜像现有 cache-buster 模式):
- Backend: portrait_url 加 `?v={updated_at_epoch}` 后缀, 重生时 epoch 变, URL 变
- Frontend: `<img src={portrait_url}?v={updated_at}>` 或用 `key={updated_at}` 让 React 重新 mount img

**Workaround**: Founder 硬刷新 (Cmd+Shift+R) 立即解锁

**Founder 决策**: 不阻塞 e2e cyberpunk 验证, 内测前/启动后修都行

---

### [2026-05-21 16:30] 🟡 TASK-T21-NEW-3-RESTART-UX-ETA-PROGRESS-FIX — 原地重启后 frontend progress/ETA 显示卡死 0% / 27 min (Founder 实测 5/21 16:26-16:31)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-3 Founder 点 test21 (project 49a0a874) restart-from-failed-stage 后, Pipeline 真在跑 (Stage 2 16:28 完成, portrait 16:31 完成), 但 frontend `/generating` 页面 progress 一直显示 **0%** + ETA 一直显示 **27 min**. 不阻塞 Pipeline 生成 (Founder 跳到 /characters 页 OK), 只是 UX 错觉以为没动 | 🟡 P1 (UX, 不阻塞内测) | Backend + Frontend | ⏳ 待派工 (Founder 5/21 16:32 决"之后修") |

**真根因假设** (待 Backend agent 诊断):
- restart-from-failed-stage L2953-3090 endpoint 重置 chapter.status='pending' + 新建 GenerationJob (`job_manager.create_job`), 但**新 job.progress 字段可能初始化为 0 + 后续 progress_callback 写入时机或值有问题**
- chapters.py:L616 status response 真 path `progress=job.progress`, job.progress=0 → frontend 显示 0%
- ETA 27 min = job.estimated_seconds 默认值, 没动态更新

**修复方向**: Backend 查 job_manager.create_job + progress_callback 重启后真行为 + restart 时是否正确 init progress; Frontend 验证 useETA hook 在 restart 后是否 reset isBackendAuthoritative 状态

**Founder 决策**: "之后修" — 不阻塞 e2e cyberpunk 验证, 内测前/启动后修都行

---

### [2026-05-21 21:15] 🔴 TASK-T21-NEW-2-HUMANOID-FALLBACK-WAVE-2 — 5 type 待补 fallback (PM 19 type 地毯式分析发现, Founder 批准立即派)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-2 PM 19 type 地毯式分析发现, 除 T20-43 (4 type) + T21-NEW-1 (8 type) 已修共 12 type 外, 还有 5 type 可能呈人形 (aquatic 美人鱼 / anthropomorphic_animal 狼人 / object 钟先生 / plant 树精 / insect 蝴蝶仙子). Founder 决方案 A 立即派, 一起重启 1 次 | 🔴 P0 | Backend (Sonnet 4.6 xhigh) | ✅ **COMPLETED 5/21 21:50** (Wave 4.5, pipeline_schemas.py L236-268 5 type fallback + anthropomorphic_animal 2 group AND 特殊 + tests/test_t21_new_2_humanoid_fallback_wave2.py 16/16 PASS, T21-NEW-1 25/25 + T20-43 26/26 不退化, PM 自跑 pytest verify + 9 Layer 地毯式审查全过) |

**真根因**: schema 强 type 化 vs 通用性矛盾 (项目记忆 project_schema_humanoid_fallback_remaining.md 已记)。anthropomorphic_animal 字面就是"动物拟人化", aquatic 美人鱼必给上半身人外貌。

**修复方向**: 4 type (aquatic/object/plant/insect) 镜像 T21-NEW-1 同款合并 group OR fallback; anthropomorphic_animal 特殊处理保留 2 group AND, 加人外貌到 group 2 (狼人必须有 species + 半人形外貌)。

**测试**: 新建 test_t21_new_2_humanoid_fallback_wave2.py 15+ 测试, T20-43 + T21-NEW-1 不退化。

**阻塞**: Wave 4.5 完成后 PM 审查 → 重启 → 通知 Founder 点 test21 原地重启 → e2e cyberpunk + scifi + 5 待修 type 同时验证。

---

### [2026-05-20 20:30] 🟢 TASK-T21-NEW-1-DIGITAL-VIRTUAL-SCHEMA-FALLBACK — test21 Stage 2 Schema 验证失败, T20-43 hotfix 漏修 5 类 non-human humanoid type (P0 阻塞 test21)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T21-NEW-1 test21 scifi 题材 LLM 给小爱 character_type=`digital_virtual` + 15 个人类外貌字段, schema 拒因 `[digital_type OR base_form]` 强制. T20-43 Wave 1 hotfix 只修 4 种 supernatural humanoid type, 漏了 digital_virtual + robot + hybrid + alien + elemental + concept_personified + giant + miniature 共 8 种可能呈人形 type | 🔴 P0 | Backend (Sonnet 4.6 xhigh) | ✅ **COMPLETED 5/20 21:01** (Wave 4, pipeline_schemas.py L226-252 8 type fallback + tests/test_t21_digital_virtual_fallback.py 25 PASS + T20-43 26 不退化, PM 自跑 pytest verify + 9 Layer 地毯式审查全过) |

**真根因**: `pipeline_schemas.py:L242 'digital_virtual': [('digital_type', 'base_form')]` 缺人类外貌 fallback。

**修复方向**: 镜像 T20-43 DEC-043 hotfix 给 8 种 non-human humanoid type 加 `hair_color, skin_tone, face_shape` OR fallback。

**测试**: 跑 test_t20_43 不退化 + 新建 test_t21_digital_virtual_fallback.py 验证 8 type + 综合 pytest 不退化。

**阻塞**: test21 Founder 点"原地重启"前必须修完 + Backend 重启加载。

**Backend 完成后 PM 40+ 维度审查 → Founder 点原地重启 → Stage 2 续跑。

---

### [2026-05-20 18:25] 🟢 TASK-T20-52-T20-47-TEST-ISOLATION — T20-47 测试 isolation 问题修复 (Wave 2 PM 审查发现, P3)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-52 综合 pytest 跑顺序 (T20-43→44→45→46→47→...) 时, T20-47 19 个测试中 13 个 fail (前面 test 污染 mock state). 单跑 T20-47 19/19 PASS, 生产代码无 bug — 仅 test infra 问题 | 🟢 P3 | Backend (test isolation) | ✅ **COMPLETED 5/20 20:05** (Wave 3, tests/test_t20_47 + test_t20_50_fix_round3 各加 autouse fixture + importlib.spec_from_file_location 隔离 mock state, 综合跑 162 PASS 0 FAIL, 单跑 T20-47 19/19 不退化) |

**Founder 实测**: 不影响, 单跑 T20-47 19/19 PASS, 生产 shot_validator.py 真接通 (Sonnet + Haiku fallback). 这是测试基础设施 isolation 问题。

**修复方向**: T20-47 测试在 setup/teardown 加 mock state 隔离 (重置 sys.modules / `importlib.reload(shot_validator)` 等). 长期 test infra 改进.

**不阻塞内测**: 生产代码 OK, e2e 验证只依赖 Founder 手动重跑 test20/test21.

---

### [2026-05-20 17:45] 🟢 TASK-T20-51-BGM-META-PROMPT-PATH-REFACTOR — BGM meta-prompt hardcoded 在 test_output 路径需重构 (PM 5+ 维度审查 Wave 1 发现, P3)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-51 BGM meta-prompt 路径 hardcoded 在 `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md` 是项目历史遗留, 生产部署必须 ship 这个 test_output 目录, 不符合代码规范 | 🟢 P3 | Backend | ✅ **COMPLETED 5/20 20:00** (Wave 3, meta_mixed_v3_quote_picking.md + meta_en_v2.md 迁 app/prompts/bgm/, music_generation_service.py META_PROMPT_DIR 改新路径, diff 100% 一致, 旧 test_output 文件保留不删, 9 单测 PASS) |

**背景**: 2026-05-20 PM 整体 Wave 1 审查时 grep 发现 `music_generation_service.py:L60-65` 引用 `test_output/manualtest/...` 路径加载 BGM Haiku meta-prompt:
```python
META_PROMPT_DIR = "test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts"
PROMPT_FILES = {"mixed": "meta_mixed_v3_quote_picking.md"}
```

**风险**: 生产 deployment 必须 ship 这个 test_output 目录, 否则 BGM 生成失败 (路径不存在)。test_output 通常是 .gitignore 排除的开发产物, 不应在生产路径。

**修复方向**: Backend 把 meta_mixed_v3_quote_picking.md 迁到 `app/prompts/bgm/`, AI-ML 同步改 META_PROMPT_DIR 引用。属于代码规范重构, 不影响功能。

**不阻塞内测**: 当前 test_output 目录存在, BGM 能正常加载。重构是长期 deployment 卫生问题。

---

### [2026-05-20 17:45] 🟢 TASK-T20-50b-ADJUST-CHARACTER-AUDIT — adjust_character endpoint 真行为审查 (T20-50 KEY_LEARNINGS #46 后续)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-50b 用户在 /characters 页"调整描述"如果走 adjust_character endpoint, endpoint 必须立即重生 portrait+fullbody (不能依赖 Pipeline 兜底, 因为 T20-50 已删 freshness check) | 🟡 P2 | Backend (Sonnet 4.6 xhigh) | ✅ **COMPLETED 5/20 18:12** (Wave 2 Backend round 1 审查: app/api/projects.py adjust_character endpoint 已正确实现 KEY_LEARNINGS #46 — 每次调用真触发 portrait 重生 + B57 cascade fullbody, 16 新单测验证完整链路, 无需额外代码改动) |

**背景**: KEY_LEARNINGS #46 (Founder 5/20 16:55 拍板) "用户操作产物 = 真相, Pipeline 不准二次裁判". T20-50 移除 Pipeline freshness check 后, 如果 adjust_character endpoint 没真重生 portrait, 用户改了描述但 portrait 还是旧的, Stage 5 直接用旧 portrait → 描述跟图不一致。

**修复方向**: 审查 `app/api/projects.py` adjust_character endpoint 真行为:
1. 改 description 后是否真重生 portrait + fullbody?
2. 如果没, 加 RegeneratePortrait 内部调用确保同步重生
3. pytest 验证: 改 description → portrait 文件 mtime 立即更新

**不阻塞内测**: 当前用户主要操作是"重生 portrait"按钮 (B57 已完整), "调整描述"功能可能少用。但应 Wave 2 审查避免坑用户。

---

### [2026-05-20 16:55] 🟢 TASK-T20-49-OUTLINE-VALIDATOR-PREVENTION — Stage 1 outline validator 4 警告预防 (Stage 3 已自愈但应改 prompt 预防)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-49 Outline validator 抓到 4 条警告: plot_points 缺 climax / inciting_incident+first_turn beat 标签重复 / 2 角色 emotional_journey 与节拍不符 | 🟢 P3 | AI-ML (Sonnet 4.6 high) | ✅ **COMPLETED 5/20 18:25** (Wave 2 全闭环) |

**Founder 实测**: test20 outline 出来后弹"大纲存在以下提示" 4 条警告, Founder 点"知悉并继续", Stage 3 ScreenplayWriter LLM 实际自愈了 (Scene 11 完美高潮反转, 补回 climax)。

**真根因**: Stage 1 StoryOutlineGenerator prompt 没强约束:
- plot_points[-1] 必须是 climax/resolution 节拍
- beat_tag 不允许重复 (inciting_incident_a / inciting_incident_b 区分)
- emotional_journey 描述必须跟 plot_points 出场次数+情绪递进对应

**修复方向**: AI-ML 改 `app/prompts/story_outline_prompts.py` 加 prompt 后置 validator self-check:
1. 输出 outline 后让 LLM 自检 4 条规则, 不满足重写
2. plot_points 节拍 schema 加 enum: ['hook', 'inciting_incident', 'first_turn', 'midpoint', 'second_turn', 'climax', 'resolution']
3. beat_tag 重复时强制加 _a/_b 后缀

**不阻塞内测**: Stage 3 LLM 真自愈, 但每次依赖 Stage 3 容错不稳定, 长期应该 Stage 1 一次输出对。

---

---

### [2026-05-20 16:30] TASK-T20-45-BGM-PROMPT-DURATION-CONTROL — Mureka BGM 时长由 prompt 内容控制, 暗黑题材 prompt 含"短促/停顿"暗示词导致 40s (Founder test20 实证, PM 地毯式深挖纠正)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-45 暗黑/恐怖题材 BGM prompt 含 "Long silences/suddenly stops/No resolution/question hanging" 等"收尾感强"语义 → Mureka 推断短曲 → 40s 不到 (其他题材 2-3 分钟) | 🟡 P2 | AI-ML | ✅ **COMPLETED 5/20 17:30** (BGM Haiku meta-prompt TARGET DURATION CONSTRAINTS + music_generation_service.py Step 5a-2 duration linter 37/37 PASS, 真 e2e 验证待 Founder 重跑 test20) |

**纠正背景**: PM 第一轮诊断错误为"Mureka payload 缺 duration 参数"。Founder 反驳后地毯式深挖发现:
1. ✅ 历史 BGM (4/23/27/28, 5/9/11/13/14/19) 全部 2-3 分钟, payload **一直是** `{"model": "auto", "n": 1, "prompt": prompt}` 没 duration
2. ✅ Mureka API v1 文档真实参数: account / prompt / title / ref_id / model / async / replyUrl / replyRef — **没有 duration / length 字段**
3. ✅ 文档明确: "Generated songs can be up to 5 minutes long depending on your prompt" — **时长完全由 prompt 内容控制**

**真根因 (test20 实证)**:
本次 horror C2 cluster BGM prompt 含大量"短促/停顿"语义:
```
Long silences that last one beat too long.
A muffled pulse that builds, builds — then suddenly stops.
No resolution.
A question hanging. No answer.
```
Mureka 模型解读为"短曲" → 40s。

之前 romance/热血/悬疑/亲情 都没这种"收尾感强"词汇 (那些 prompt 写"sustained / continuous / building / unfolding" 等) → Mureka 输出 2-3 分钟。

**修复 (AI-ML prompt 工程层)**:
1. 改 `app/prompts/bgm_meta_prompt.py` (或对应 Haiku 生成 BGM prompt 的 meta-prompt 文件) — 加入硬约束:
   ```
   TARGET DURATION: ~3 minutes (180s) sustained development.
   AVOID writing "silences as primary motif" / "sudden stops" / "no resolution" / "question hanging" as core descriptors.
   Even for horror/gothic clusters, frame the tension as **CONTINUOUS / SUSTAINED / EXTENDED** rather than punctuated by terminations.
   E.g. horror = "sustained dread", "extended unease", "continuous tension building toward climax" (NOT "silences interrupted by stops").
   ```
2. 加 BGM linter 规则: 检测 prompt 含 ≥ 2 个"短促/收尾"暗示词 → warn + 自动 rewrite

**长期愿景**: 5 维 prompt 体系 (画面/对话/旁白/标点/BGM) 都不能因题材黑暗而导致时长/质量下降, 必须用"sustained / extended" 框架表达紧张感。

**验收**:
- 跑 test20 重生 BGM (prompt 改后), 时长 ≥ 150s
- 跑 test21 (scifi) + test19 (suspense) + 1 个 horror 测试不退化
- BGM linter 自动 reject "silences + suddenly stops + no resolution" 三联词

**KEY_LEARNINGS 待加 #44**: "PM 第一轮表象诊断错误 — Mureka payload 缺 duration", 实际真根因是 prompt 内容控制时长 (Mureka API 没 duration 字段)。Founder 反驳"之前 BGM 2-3 分钟为什么这次 36s"才让 PM 真深挖。教训: 任何 API 参数假设, 必须先查官方文档 + 看历史数据 (历史成功为什么这次失败)。

---

### [2026-05-20 16:05] TASK-T20-44-ETA-FRONTEND-BACKEND-ALIGN — 前后端 ETA 联动对齐 (Founder test20 实证)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-44 前后端 ETA 严重不对齐（backend 真值 790s, frontend 显示 3min ≈ 4x 低估）+ shots_completed 字段滞后写库（log 显示 5 张完成, API 仍报 3 张） | 🟡 P1 | Frontend + Backend 协作 | ✅ **COMPLETED 5/20 18:10** (全栈闭环: Backend chapters.py BGM 阶段不重置 21/21 + STATUS_API_CONTRACT v1.3 + Frontend useETA.ts isBackendAuthoritative bypass smoothing + StageC isPostImageGen guard, 9/9 jest PASS + tsc/build 0 errors) |

**背景**: 2026-05-20 Founder 跑 test20 image_generation 阶段实测：
- Backend `/status` API 返 `estimated_remaining_seconds=790s` (13min) + `shots_completed=3` 
- 实际 backend.log 显示 5 张 shot 已生成 (Shot 1/2/4/5/7 ✅)
- Frontend 显示"预计还需约 3 分钟" — 4x 低估真值

**Founder 提醒**: "ETA 这点还是要记下来 前后端的 ETA 要尽可能每个环节节点都联动对齐起来"

**两个独立 bug**:
1. **shots_completed 字段滞后**: backend.log 5 张完成时, status API 仍报 3 张 — 写库时机延迟（可能只在 ShotValidator pass 后才 increment, fail-open 路径漏 increment）
2. **Frontend ETA 渲染错位**: backend ETA 790s 真值, frontend 显示 "3 分钟" — 可能 frontend hardcoded 通用文案, 没真用 `estimated_remaining_seconds` 渲染

**修复方向**:
- Backend: 检查 `shots_completed` increment 时机, 在 SeedreamGenerator 成功后立即 +1 (无论 ShotValidator 是否 fail-open)
- Frontend: 检查 ETA 显示逻辑（StageC/useETA.ts）, 真用 `status.estimated_remaining_seconds` 渲染, 不要 hardcoded 假估值
- 5 个环节节点 ETA 都对齐: outline / character_design / screenplay / storyboard / image_generation

**长期愿景**: 前后端每个 stage 节点 ETA 公式统一, 真值同步, 不再"前后端各算各的"（KEY_LEARNINGS #33 类问题, ETA 失真是 test15 47% bug 之一根因）

**验收**:
- 5 stage 节点 frontend / backend ETA 偏差 ≤ 10%
- shots_completed 写库 ≤ 1s 滞后于 SeedreamGenerator 成功

**依赖**: 无, 跟 Wave 4 T20-13 STATUS_API_CONTRACT v1.1 / T20-9.v3 ETA 算法工作平行

---

### [2026-05-20 15:35] TASK-T20-43-PROMPT-SUPPLEMENT — CharacterDesigner prompt 补强 4 种人形 type (KEY_LEARNINGS #43 长期修)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-43 prompt 端补强（supernatural/undead/mythological/fantasy_creature 优先填 being_type/undead_type/creature_type，否则补完整人类外貌字段） | 🟡 P2 | AI-ML (Sonnet 4.6 high) | ✅ **COMPLETED 5/20 18:25** (Wave 2 全闭环) |

**背景**: 2026-05-20 test20 镜中人 char_002 Stage 2 schema fail（character_type=supernatural + 完整人类外貌字段，但 schema 要求 being_type/base_form）。Backend 已 hotfix `pipeline_schemas.py` 让 schema 端接受人类外貌字段（KEY_LEARNINGS #43）。

**长期修**: AI-ML 在 CharacterDesigner prompt 文件（`app/prompts/character_design_prompts.py` 或对应文件）增加规则：选 `supernatural / undead / mythological / fantasy_creature` 这 4 种 character_type 时：
1. **优先**填该 type 的种族字段（being_type / undead_type / creature_type / base_form / original_form 等）
2. 如选"呈人形"配置（鬼 / 魂 / 镜中人 / 山神 / 仙人 / 妖等），**额外**补完整人类外貌字段（hair_color / skin_tone / face_shape / eye_color 等）
3. 不接受"只给人类外貌字段、不给 type 种族字段"的 minimal 输出（schema 虽兜底，但语义不准）

**不阻塞**: 当前 schema 已兜底，test20 可以继续跑通。这是补强 prompt 让 LLM 输出更语义化（既有"人形"又有"超自然身份"）。

**依赖**: 无（pipeline_schemas.py hotfix 已生效）

**验收**:
- 跑 test20（horror 镜中人） + test21（scifi AI）+ 任意 fairytale（仙人/山神）3 个题材测试
- 镜中人/类似角色的 physical 应同时含 being_type + hair_color 等
- pytest 不退化（5 个全 PASS）

---

## ✅ Wave 14 全闭环（2026-05-15 18:00, 4 RISK 全修, 含 Founder 发现 5 角色画成人类 真根因)

### Wave 14 战果 (4 RISK 全修, 5 agent 并行 ~2h)

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| ✅ #24 T19-6 P0 灾难 anthropomorphic_animal | character_types.py L37/L429 + character_prompt_builder.py L31/L343 + character_designer.py + reference_image_manager.py 4 处 | AI-ML Sonnet xhigh | 14 单测 + b58 7 regression PASS |
| ✅ #26 T19-8 P0 B51 fallback 6 中文来源 | storyboard_director.py L328-1040 (_extract_english_from_field + name_en + clothing 英文化 + prompt 铁律) | Backend #1 Sonnet xhigh | 20 新单测 + 50 regression PASS |
| ✅ #23 T19-5 P1 BGM dict/str 双修 | story_music_extractor.py L419-431 visual_tone + L491-511 atmosphere isinstance 三分支 | Backend #2 Sonnet xhigh | 15 新单测 + 152 regression PASS |
| ✅ #25 T19-7 P1 IMAGE_TOO_LARGE | shot_validator.py L52 target **4.5MB→3.5MB** (Wave 11.4 错 target, 没考虑 base64 33% 膨胀) + resize 优先 | Backend #3 Sonnet xhigh | 9 新单测 + 9 regression PASS |

### 真根因发现 (深度审查抓出)

1. **anthropomorphic_animal 类型完全无映射** (PM + Explore agent 5 维度审查发现): character_types.py 枚举不存在 → CHARACTER_TYPE_DECLARATIONS 没映射 → CharacterPromptBuilder fallback 到 description 字符串 → LLM 自由解释成 "young woman" → 5 动物全画成人
2. **B51 fallback 6 中文来源** (Backend #1 深挖): 不只 atmosphere/scene_heading, 还有 characters.name 中文 / clothing 中文 / action_beats 中文 / narration 中文 — Wave 12+13 只修 2/6 → Wave 14 修全部 6
3. **IMAGE_TOO_LARGE 真根因**: Wave 11.4 设 4.5MB binary target, 但 base64 编码膨胀 ~33% → 6MB > 5MB Anthropic 限制 → Wave 14 改 3.5MB binary (base64 ~4.65MB safe)

### PM 8 维度地毯式审查全过

- 代码改动 + **完整调用链路** (anthropomorphic_animal 在 5 文件接通 / _extract_english_from_field 真接通 / isinstance 防御真接通) + py_compile 7 文件 + pytest **319/319 PASS** + 0 越权 + Backend 重启 (新 PID 10553) + Frontend HTTP 200 + 死代码检查 + 5 维度日志 0 新增异常

### 26 RISK 战果总览 (Wave 11+12+13+14)

```
✅ Completed (22 内测前修):
  Wave 11.x: #1/#2/#3/#4/#5/#6/#9/#10/#11/#12/#15/#16 (12)
  Wave 12:   #7/#18/#19/#20 (4)
  Wave 13:   #21/#22 (2)
  Wave 14:   #23/#24/#25/#26 (4)

⏳ Pending (5):
  POST_BETA 4: #8/#13/#14/#17
  POST_BETA 1 (新): #27 RISK-T19-9 P3 emotional_arc dict/str (Backend #2 bonus 发现)
```

### Bonus 发现 (待 Founder 决策)

- Backend #2 audit 时发现 `story_music_extractor.py L444 emotional_arc` 同样 dict 假设 (test19 实测是 dict 没触发, 但理论风险)
- PM 已加 task #27 RISK-T19-9 P3 (POST_BETA 内测后修)

### 内测就绪度: A (升级! 22 RISK 修, 5 待修都不阻塞)

### 待 Founder

- ⏳ 重新 e2e 测 test20 (新 chapter / 新 project) 验证 Wave 14:
  - 5 角色画成动物 (anthropomorphic_animal 真接通!)
  - Stage 4 0 fallback (B51 6 中文来源全修)
  - BGM 真生成 (dict/str 双修)
  - ShotValidator 真验证 (5.7MB 压成 3.5MB)

---

## ✅ Wave 12 + Wave 13 全闭环（2026-05-15 16:42, 6 RISK 全修, 等 Founder 第三次 e2e 实测）

### Wave 13 战果 (RISK-T19-3 P1 + RISK-T19-4 P0)

| RISK | 文件 | 修复证据 |
|---|---|---|
| ✅ T19-4 P0 (Backend) | `screenplay_writer.py` L545/561+L1116/1130 + `storyboard_director.py` L686 | scene_heading ENGLISH ONLY 约束 (8 处 ENGLISH ONLY) + fallback _contains_chinese 检测替换 "Scene {id}" |
| ✅ T19-3 P1 (Frontend) | `StageC.tsx` L170-171/324-327/449-468/109-113 | live ref 替代 mount-time snapshot + subtitle 全 stage 统一 + 真根因 3 层 bug 修复 |

### Wave 12 战果 (4 RISK 全闭环 + 1 漏修 → Wave 13 补)

| RISK | 文件 | 修复证据 |
|---|---|---|
| ✅ T19-1 P0 atmosphere 真根因 (1/2 修, 漏 scene_heading) | screenplay_writer.py + storyboard_director.py | atmosphere ENGLISH ONLY + _atmosphere_to_str 防御中文 |
| ✅ T17-8 P0 原地重启 | chapters.py L2618-2766 + pipeline_orchestrator.py L320-393 | POST /restart-from-failed-stage + start_from_stage 参数 + 跳过 R4-1/R4-2 |
| ✅ T19-2 P1 friendly UI | StageC.tsx L78-1220 | "生成遇到问题" + 折叠技术详情 + 原地重启主按钮 |
| ✅ T17-7 P2 升级 后台按钮扩展 | StageC.tsx L1144 | text-gen + storyboard 阶段也显示 |

### PM 5 维度地毯式审查 (8 维度全过)

代码改动 + **完整调用链路** (_contains_chinese atmosphere+scene_heading 双调用 / generationProgressRef live ref 真守卫 / scene_heading_safe 真拼装) + py_compile 2 文件 + **261/261 PASS** + 0 越权 + Backend 重启 + Frontend clean rebuild + **死代码检查** (initialProgressRef 0 引用)

### 18 RISK 战果总览 (Wave 11+12+13)

```
✅ Completed (18 内测前必修):
  Wave 11.x: #1/#2/#3/#4/#5/#6/#9/#10/#11/#12/#15/#16 (12)
  Wave 12:   #7/#18/#19/#20 (4)
  Wave 13:   #21/#22 (2)

⏳ POST_BETA (4 内测后做): #8/#13/#14/#17
```

### test19 e2e 实证关注 (Founder 即将第三次原地重启)

```
[预期 Wave 13 全胜利]
[1] Stage 4 LLM 输出 atmosphere 全英文 (Wave 12 prompt 约束)
[2] Stage 4 LLM 输出 scene_heading 全英文 (Wave 13 prompt 约束)
[3] 即使 LLM 失败 fallback → atmosphere 跳过中文 (Wave 12) + scene_heading 替换 "Scene {id}" (Wave 13)
[4] fallback_image_prompt 100% 英文 → Schema 验证 ✅
[5] frontend storyboard 阶段 progress 真显示 (Wave 13 修)
[6] 不再 0% 卡 6 min ✅
```

---

## 🟡 RISK-T17-7 升级 P2 — "后台生成"按钮扩展到所有耗时阶段（2026-05-15 15:10 test19 实测 PM 误判修正）

### 真根因发现 (test19 5/15 15:09 Founder 实测 + PM 深度 grep 验证)

**PM 5/14 16:00 audit 误判**:
- ❌ 错误结论: "PENDING 复盘删条目" (PM 以为前端早实现按钮)
- 误判依据: test18 时 Founder 看到按钮 → PM 以为按钮一直存在所有 stage

**test19 5/15 15:09 实测发现**:
- Founder 在 `stage=storyboard` (44% 进度) 反馈: "仍然还没看到'后台生成 去做别的'的前端UI"
- PM grep frontend StageC.tsx 找到 **L1087 注释明确**:
  ```typescript
  // RISK-T15-1 fix: "后台生成" button shown ONLY during shot-gen phase.
  ```

### 完整影响范围

| Stage | 现状 (RISK-T15-1 fix 老设计) | 是否显示按钮 | 实际耗时 |
|---|---|---|---|
| outline / character_design / character_ready | - | ❌ 不显示 | ~5 min |
| screenplay / scenes_ready | - | ❌ 不显示 | ~5 min |
| **storyboard** (test19 Founder 实测发现) | shot-gen ≠ storyboard | ❌ **不显示** | ~3-4 min |
| **image_preparation** | shot-gen ≠ image_preparation | ❌ **不显示** | ~3 min |
| image_generation | ✅ 这就是 "shot-gen phase" | ✅ 显示 | ~15-20 min |
| **bgm** | shot-gen ≠ bgm | ❌ **不显示** | ~1 min |

**用户体验问题**: 前 ~10-15 min 的 Pipeline 阶段 (storyboard + image_preparation) 用户必须守着, 不能"后台去做别的". 只在 image_generation 阶段才能后台。

### 修复方向

**Frontend StageC.tsx L1087 附近**: 修改按钮显示条件

**当前条件** (推测):
```typescript
{ui_phase === 'shot_generating' && <BackgroundGenerationButton />}
```

**期望条件** (Wave 12):
```typescript
{['storyboard_running', 'shot_generating', 'bgm_running'].includes(ui_phase) && <BackgroundGenerationButton />}
// 或者
{['storyboard', 'image_preparation', 'image_generation', 'bgm'].includes(stage) && <BackgroundGenerationButton />}
```

### Wave 12 派活

- **派给**: Frontend Sonnet xhigh
- **估时**: 30 min (含 5 维度审查 + 单测)
- **触发**: **内测前必修** (Founder 体验明确要求, P2 升级)
- **task ID**: #7 (已 TaskUpdate 升级 P2 + 详细 description)

### PM audit 教训

**第 19 条经验** (写入 KEY_LEARNINGS): "PM audit '已实现' 判断必须实测验证, 不能基于历史快照推断"
- PM 5/14 audit 看 PENDING 列表, 假设 RISK-T17-7 是"PM 想象但前端早实现" → 列入 POST_BETA 复盘删
- 实际真相: 前端实现了按钮, 但**只在 shot-gen 阶段** (RISK-T15-1 老 fix 限制), PM 没追代码
- 教训: "已实现" 判断必须 **grep 代码 + 看条件分支**, 不能仅基于"用户曾看到过"推断

---

## ✅ Wave 11.x + RISK-NEW-1/2 真彻底全闭环（2026-05-14 23:30 / 7 agent / 12 RISK 全修 / 内测就绪度 A）

### Wave 11.x 整体状态

| Wave | RISK | 状态 |
|---|---|---|
| 11.1 (P0+P1, 17:30) | T18-F + T17-9 + T18-H | ✅ |
| 11.2 (P1, 19:30) | T18-G + T18-E + StageC | ✅ |
| 11.3 (P1, 20:30) | T17-5 4 步全闭环 (job_manager + chapters 集成 + useETA + StageC 集成) | ✅ |
| 11.4 (P2, 22:30) | T18-A + T18-B + T18-D (含 SeedreamMetrics 死代码补漏) | ✅ |
| 11.4 timeout (22:35) | SEEDREAM_TIMEOUT_SEC 180→210 | ✅ |
| Pre-内测 audit (23:00) | 找到 3 新 RISK (PM 漏检) | ✅ |
| RISK-NEW-2 (23:30) | IMAGE_GENERATION_TIMEOUT 配置统一 | ✅ |
| RISK-NEW-1 (23:30) | actual_elapsed_sec 11 消费点 + sanity check | ✅ |

### 12 RISK 战果

| ID | 优先级 | RISK | 文件 |
|---|---|---|---|
| ✅ #10 | 🔴 P0 | T18-F (Shot 重生角色一致性) | chapters.py L1878-1890 |
| ✅ #3 | 🔴 P0 | T17-9 (R7-3 portrait_ref) | projects.py L1288-1309 |
| ✅ #12 | 🟡 P1 | T18-H (ShotValidator 5MB) | shot_validator.py |
| ✅ #11 | 🟡 P1 | T18-G (404 风暴 41 次) | chapters.py L415/L568 |
| ✅ #1 | 🟡 P1 | T18-E (/preview API 空) | projects.py L1556 (新增) |
| ✅ #2 | 🟡 P1 | T17-5 (ETA 4 步) | job_manager.py + chapters.py + useETA.ts + StageC.tsx |
| ✅ #4 | 🟢 P2 | T18-A (progress per-shot) | pipeline_orchestrator.py L1272+L1334 |
| ✅ #5 | 🟢 P2 | T18-B (Seedream 长尾调研) | SEEDREAM_LONGTAIL_RESEARCH.md (290 行) |
| ✅ #6 | 🟢 P2 | T18-D (失败率监控) | seedream_metrics.py + seedream_generator.py 6 调用点 |
| ✅ #15 | 🆕 P2 | RISK-NEW-2 (timeout 统一) | config.py L33 + seedream_generator.py L103 |
| ✅ #16 | 🆕 P3 | RISK-NEW-1 (actual_elapsed 消费) | useETA.ts + StageC.tsx + CreateContent.tsx 11 消费点 |
| ✅ #9 | - | 监测 Shot 8 重生 | (审查任务) |

### POST_BETA (4 RISK 内测后做, 不能遗漏!)

| ID | RISK | 触发 |
|---|---|---|
| #7 | T17-7 后台按钮 PENDING 复盘 | 内测后 PM 5 min |
| #8 | T17-1 markdown JSON 全调用点排查 | 内测后 Backend 1h |
| #13 | T18-I IncompleteRead 24 次监控 dashboard | 内测后 Backend/DevOps 2-3h |
| #14 | T18-J Sync Anthropic → AsyncAnthropic | 内测后 Backend Opus 4-6h |
| - | RISK-NEW-3 alembic 验证 | Ben VPS 部署时验 |

### PM 5 维度地毯式审查 (10 维度全过)

代码改动 + 完整调用链路 (11 actual_elapsed + 6 SeedreamMetrics) + py_compile + **207/207 PASS** + 0 越权 + Backend 重启 + Frontend clean rebuild + progress 三件套 + timeout 统一 + 死字段消除 + 死代码消除

### 服务状态

- Backend (PID 78277) → **已停** (Founder 5/14 21:02 决定明天再测)
- Frontend (PID 78392) → **已停**
- 0 残留, ports 8000+3000 free
- task list: 12 completed + 4 POST_BETA pending

### 待 Founder

⏳ **Founder 明天 e2e 实测** test19 同 idea (杭州梅雨季) 验证 12 RISK 全修复 + 9 个观察点

---

## ✅ Wave 11 + Wave 11.4 全闭环（2026-05-14 22:30 / 5 agent / 8 RISK 全修 / PM 地毯式审查通过）

### 战果总览

| Wave | RISK | 状态 |
|---|---|---|
| 11.1 | T18-F + T17-9 + T18-H | ✅ 全闭环 (16:40-17:30) |
| 11.2 | T18-G + T18-E + StageC 配套 | ✅ 全闭环 (17:35-19:30) |
| 11.3 | T17-5 backend ETA + chapters 集成 + useETA hook + StageC 集成 | ✅ 全闭环 (19:00-20:30) |
| 11.4 | T18-A + T18-B + T18-D | ✅ 全闭环 (20:30-22:30, 含 SeedreamMetrics 死代码补漏) |

### Wave 11.4 战果

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| ✅ T18-A P2 (progress per-shot) | `pipeline_orchestrator.py` L1272 + L1334 (公式 75 + int(20 * _done / _total_shots)) | Backend #5 | 19 新单测 + 135 regression PASS |
| ✅ T18-B P2 (Seedream 长尾调研) | 新建 `.team-brain/analysis/SEEDREAM_LONGTAIL_RESEARCH.md` (290 行) | Backend #6 | 11 段完整调研 |
| ✅ T18-D P2 (失败率监控 + retry 评估) | 新建 `seedream_metrics.py` + `seedream_generator.py` 6 调用点接通 | Backend #6 + 补漏 Backend | 30 + 191 PASS |

### Wave 11.3 收尾战果

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| ✅ T17-5 ETA 集成 backend | `chapters.py` L356-367 + `schemas/chapter.py` L40 (actual_elapsed_sec 字段) | Backend #3 | 154 regression PASS |
| ✅ T17-5 ETA 集成 frontend | `StageC.tsx` L12 + L269-295 + L988-993 (集成 useETA hook 替换 estimatedMinutes IIFE) | Frontend #2 接力 | npm build 0 errors |

### PM 地毯式审查 (8 维度全过)

1. ✅ 代码改动 (Read 5 文件改动行号)
2. ✅ 完整调用链路 (useETA 真在 StageC / progress per-shot 真接 callback / SeedreamMetrics 真 6 调用点)
3. ✅ py_compile 5 文件
4. ✅ pytest 单测 191 全 PASS
5. ✅ 0 越权
6. ✅ Backend 重启 (新 PID HTTP 200 含全改动)
7. ✅ progress 三件套真更新
8. ✅ **死代码检查抓出 SeedreamMetrics 死代码 + 补漏闭环** (Wave 1.1 教训没重演!)

### Backend #6 待 Founder 决策

1. **SEEDREAM_TIMEOUT_SEC 180s → 210s** (一行改动, 防 177s long-tail 偶发超时)

---

## ✅ Wave 11.2 + 11.3 代码层全完成（2026-05-14 19:30 / 4 agent / 等 PM 收尾审查 + 集成）

### Wave 11.2 战果

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| ✅ T18-G P1 (404 风暴) | `app/api/chapters.py` L415-446 + L568-574 | Backend #1 | 22 单测 PASS |
| ✅ T18-E P1 (preview API 空) | `app/api/projects.py` L1556-1660 (新增 endpoint) | Backend #1 (顺序) | 134 regression PASS |
| ✅ T18-G 配套 (frontend) | `lib/api.ts` + `StageC.tsx` + `CreateContent.tsx` | Frontend #1 | npm build 0 errors |

### Wave 11.3 战果

| RISK | 文件 | Agent | 验证 |
|---|---|---|---|
| ✅ T17-5 P1 ETA backend | `app/services/job_manager.py` L18-148 + L375-395 + L411-428 | Backend #2 | 50 单测 PASS |
| ⏳ T17-5 配套 (frontend, 部分完成) | `frontend/src/hooks/useETA.ts` (新建) + `CreateContent.tsx` L1409-1428 | Frontend #2 | hook 完成, **StageC 集成等接力** |

### 待 PM 收尾

1. **PM 5 维度地毯式审查 4 agent** (重读 TEAM_CHAT + Read 改动文件 + 验调用链路 + 验 pytest + 验 0 越权)
2. **派 Backend #3 mini agent 集成 chapters.py status response ETA 字段** (Backend #2 paste 的 snippet)
3. **派 Frontend #2 接力 StageC.tsx 集成 useETA hook** (使用方式 paste 已留)
4. **重启服务**: backend + frontend
5. **标 task #11/#1/#2 completed**
6. **Wave 11.4 派活时机决策** (T18-A + T18-B + T18-D, 估 3-4h)

---

## ✅ Wave 11.1 已闭环（2026-05-14 16:45 Backend × 2 并行 / PM 地毯式审查通过）

### Wave 11.1 战果 — 3 P0/P1 RISK 全修

| RISK | 文件 | 行号 | Backend agent | 状态 |
|---|---|---|---|---|
| 🔴 T18-F P0 | `app/api/chapters.py` regenerate_shot | L1878-1890 | #1 (Sonnet 4.6 xhigh) | ✅ |
| 🔴 T17-9 P0 | `app/api/projects.py` adjust_character | L1288-1309 | #1 (顺序) | ✅ |
| 🟡 T18-H P1 | `app/services/shot_validator.py` 5MB 压缩 + 日志 | L37-50/L304/L461-474 | #2 (Sonnet 4.6 xhigh, 并行) | ✅ |

### PM 地毯式审查 (5 维度全验证)

| 维度 | 验证 | 结果 |
|---|---|---|
| 1. 代码改动 | Read 3 个文件改动行号 | ✅ 真改对 |
| 2. 调用链路 | regenerate_shot endpoint chapters.py L1731 真注册 / _compress_for_claude L304 真接通 / projects.py L1288 真传 portrait_ref | ✅ 完整闭环 |
| 3. py_compile | 3 文件 | ✅ PASS |
| 4. pytest 单测 | ShotValidator 9/9 + atmosphere 10/10 + b58 7/7 + shot_regenerate_persistence 9/9 + 82 regression | ✅ 全 PASS |
| 5. 0 越权 | git status 只改 backend-progress + chapters.py + projects.py + shot_validator.py + 新建 test_shot_validator_compression.py | ✅ |
| 6. Backend 重启 | 老 PID 63583 → 新 PID 70144 含 Wave 11.1 改动 | ✅ HTTP 200 |
| 7. progress 三件套 | backend-progress 三件套 5/14 16:39 modified + 内容完整 | ✅ |
| 8. character_consistency_regression | 是脚本非 pytest, collected 0 items 正常 (要 e2e 真 API), Backend agent 判断免跑合理 | ⚠️ 待 Founder e2e 实证 |

### 验收标准

- ✅ T18-F: regenerate_shot 改完后, 后端 log 应显示 char_refs=2 (portrait + fullbody)
- ✅ T17-9: adjust_character 真传 portrait_ref 参数
- ✅ T18-H: ShotValidator 真压缩 + reason="API_ERROR_SKIPPED"/"IMAGE_TOO_LARGE_SKIPPED" + skipped_count metric
- ✅ pytest 全过 (含 regression)
- ✅ Backend 重启含改动
- ⏳ Founder 手动 e2e 验证 (Shot 重生 + character adjust + 5MB+ shot 真验证)

### Wave 11.1 总结

- 3 RISK / 2 Backend agent 并行 / ~1h 完成 (16:40 派工 → 17:30 完工 + PM 审查)
- 0 文件冲突 (chapters.py + projects.py 同 Backend #1, shot_validator.py Backend #2)
- 100% 文档闭环 (Backend agent 不直接 Edit 共享文档, paste 给 PM 代写)
- Founder 5/14 17:00 修正"Shot 8 只 1 个人物 char_refs=1 合理 + 必须 portrait+fullbody 两张" 已落实

### 下一步

- ⏳ 等 Founder 手动 e2e 验证 + 决策 Wave 11.2 派活时机
- Wave 11.2: T18-G + T18-E + StageC 配套 (Backend + Frontend 并行)

---

## 🔴🟡🟢 Wave 11 RISK 全清单（2026-05-14 16:35 PM 地毯式 audit 后写）

> **决策**: Founder 5/14 16:30 拍板 Wave 11 P0+P1+P2 都做（内测前），P3 内测后做（不能遗漏）
> **完整 audit 报告**: `.team-brain/analysis/TEST16-18_DEEP_AUDIT_2026-05-14.md`
> **Wave 11 派活计划 + POST_BETA**: `.team-brain/analysis/WAVE11_PLAN_AND_POST_BETA_RISKS.md`

### Wave 11.1 — P0 角色一致性 + P1 ShotValidator (派活中)

| ID | 优先级 | RISK | 文件 | 派给 |
|---|---|---|---|---|
| #10 | 🔴 P0 | T18-F: regenerate_shot 传 portrait + fullbody | `app/api/projects.py` regenerate_shot endpoint | Backend Sonnet xhigh #1 |
| #3 | 🔴 P0 | T17-9: adjust_character R7-3 传 portrait_ref | `app/api/projects.py` L1278-1293 | 同 Backend #1 (顺序) |
| #12 | 🟡 P1 | T18-H: ShotValidator 5MB+ 图片直接跳过 | `app/services/shot_validator.py` | Backend Sonnet xhigh #2 (并行) |

### Wave 11.2 — P1 数据契约 (待 Wave 11.1 完)

| ID | 优先级 | RISK | 文件 | 派给 |
|---|---|---|---|---|
| #11 | 🟡 P1 | T18-G: /chapters/{id}/story|storyboard 404 风暴 41 次 | `app/api/chapters.py` 加 endpoint or 改 by-design 404 | Backend Sonnet xhigh |
| #1 | 🟡 P1 | T18-E: /preview API 接口空数据 | `app/api/projects.py` 或 chapters.py | 同 Backend (等 Wave 11.1 projects.py 改完) |
| #11 配套 | 🟡 P1 | StageC 调用 endpoint 修复 | `frontend/src/components/create/StageC.tsx` | Frontend Sonnet xhigh 并行 |

### Wave 11.3 — P1 ETA 全面深挖 (Founder 明确要求)

| ID | 优先级 | RISK | 文件 | 派给 |
|---|---|---|---|---|
| #2 | 🟡 P1 | T17-5: ETA 算法 + status response | `app/services/job_manager.py` + `app/api/chapters.py` | Backend Sonnet xhigh |
| #2 配套 | 🟡 P1 | Frontend ETA hook + stage 切换 reset | `frontend/src/.../useETA.ts` (假设) | Frontend Sonnet xhigh 并行 |

### Wave 11.4 — P2 性能 + 监控 (内测前优化)

| ID | 优先级 | RISK | 文件 | 派给 |
|---|---|---|---|---|
| #4 | 🟢 P2 | T18-A: progress per-shot 增量 | `app/services/pipeline_orchestrator.py` | Backend Sonnet xhigh |
| #5 | 🟢 P2 | T18-B: Seedream 长尾 150-180s 调研 | (调研为主) | Backend Sonnet xhigh |
| #6 | 🟢 P2 | T18-D: Seedream 失败率监控 + 4 retry 阈值评估 | (统计 + dashboard) | Backend Sonnet xhigh |

---

## 🔵 POST_BETA 内测后必修 RISK 清单（不能遗漏！）

> ⚠️ **Founder 5/14 16:35 强调**: 内测后做的 RISK 必须明确记下不能遗漏

| ID | RISK | 文件 | 派给 | 触发 |
|---|---|---|---|---|
| #7 | T17-7: 后台按钮已存在 — 复盘 PENDING | (PM 自做删条目) | PM | 内测启动后 |
| #8 | T17-1: markdown JSON 解析全调用点排查 | grep `_strip_markdown_json_fence` 调用点 | Backend Sonnet xhigh | 内测后 |
| #13 | T18-I: Seedream IncompleteRead 24 次监控 | (监控 + dashboard) | Backend / DevOps | 内测后建立基线 |
| #14 | T18-J: Sync Anthropic 阻塞 event loop | character_designer / screenplay_writer / storyboard_director Sync → AsyncAnthropic | Backend Opus xhigh | 内测后扩大用户量前 |

---

### ✅ RISK-T17-6 — P0 CRITICAL 已修（2026-05-14 14:51 Backend Sonnet 4.6 xhigh / Wave 10.1）

| 字段 | 内容 |
|------|------|
| **修复** | `app/services/storyboard_director.py` L323-341 + L654 + L658 — 新增 `_atmosphere_to_str()` helper + L654 转换 + L658 安全拼接 |
| **验证** | test_atmosphere_dict_compat.py 10/10 PASS + regression 63/63 PASS + py_compile PASS + 0 越权 |
| **状态** | ✅ 已修，backend 已重启 PID 63583 含改动。test17 chapter 已 failed 无法原地重启 → Founder 跑 test18 新 project 验证 |

---

### 🟡 RISK-T17-9 — P2：Wave 10 RISK-T16-2 修了一半，projects.py R7-3 调用时没传 portrait_ref（2026-05-14 15:15 test18 复盘 + Founder 反馈"角度有点点不一样")

| 字段 | 内容 |
|------|------|
| **现象** | test18 Founder 调晓桐发型"丸子头→马尾辫"后 R7-3 重生，反馈"identity 还很像 + 角度有点点不一样" |
| **真根因 (按 KEY_LEARNINGS "signature 加参数 ≠ 参数被传值" 教训)** | Wave 10 P2 Backend agent 改了 `reference_image_manager.py` L107 让 portrait 重生支持 portrait_ref 参数 ✅，但 `projects.py` L1288-1293 adjust endpoint 调用 generate_character_reference 时**没传** portrait_ref → 修复入口失效 |
| **代码证据 projects.py L1288-1293** | `_portrait_result = await _ref_manager.generate_character_reference(character=updated_char, project_style=..., image_generator=..., ref_type="portrait")` — 4 参数无 portrait_ref |
| **效果** | Seedream 完全靠 prompt 文本重新生成 portrait → identity 大致保持（character description 完整描述脸/发型）+ **角度/表情/微细节有变化**（没 ref image 锁定 ground truth）|
| **修复 (5-10 行)** | `projects.py` L1278-1293 R7-3 之前先 read existing portrait 文件 → 转 PIL.Image → 传给 generate_character_reference 作 portrait_ref:<br>```python<br>_existing_portrait_path = _os.path.join(_char_refs_dir, f"{char_id}_portrait.png")<br>_existing_portrait_pil = None<br>if _os.path.exists(_existing_portrait_path):<br>    from PIL import Image as _PilImage<br>    _existing_portrait_pil = _PilImage.open(_existing_portrait_path).convert("RGB")<br>_portrait_result = await _ref_manager.generate_character_reference(..., portrait_ref=_existing_portrait_pil)<br>``` |
| **Wave 10 审查教训** | PM 之前 Wave 10 审查时光看 reference_image_manager.py L107 改了 + 单测 PASS，没追到 chapters/projects.py 调用是否真传参数。**完整调用链路: 函数定义 → 调用点 → 参数传递 → 数据流向 → 消费点 — 每一环都查** |
| **派发** | Backend Sonnet xhigh ~15 min — Wave 11 / 测试通过后修 |
| **状态** | 🟡 P2，不阻塞 e2e（identity 还是很像，只是角度微变）|

---

### 🔴 RISK-T17-8 — P1：Pipeline 失败后无"原地重启从失败 stage 重跑"机制，必须重新创建 project（2026-05-14 14:55 test17 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | test17 Pipeline Stage 4 失败 (RISK-T17-6 atmosphere TypeError) → backend 写 chapter.status="failed" → Founder 点 frontend "返回重试" 按钮但**没真重启 Pipeline** |
| **frontend 真行为** | StageD.tsx L95 `router.push("/create")` 跳回 Stage A 重新创建项目；StageC.tsx L1115 dispatch SET_STAGE 仅 UI 状态切换 — 都**没调 backend restart endpoint** |
| **影响** | 用户必须重新创建项目 + 浪费 outline + characters + scenes (~10 min Pipeline 工作 + ~$0.20 LLM 成本) |
| **修复方向** | (a) Backend 加 `POST /chapters/{n}/restart` endpoint: 重置 chapter.status="processing" + 从失败 stage 重跑 Pipeline; (b) Frontend StageD failed UI 加 "重启 Pipeline" 按钮 (区别于 "重新创建") + 调 backend restart endpoint |
| **派发** | Backend + Frontend Sonnet xhigh ~1h — Wave 11 / 测试通过后修 |

---

### 🔴🔴🔴 RISK-T17-6 (历史条目) — P0 CRITICAL：storyboard_director.py 假设 atmosphere=str 但 LLM 输出 dict，Stage 4 TypeError 失败（2026-05-14 14:44 test17 实证）

| 字段 | 内容 |
|------|------|
| **现象** | test17 Stage 4 跑到 Scene 5/6 时报 `TypeError: can only concatenate str (not "dict") to str` at storyboard_director.py L635 `'Atmosphere: ' + atmosphere + '. '` |
| **真根因** | (a) Stage 3 LLM (Claude Sonnet 4.6) 输出的 `atmosphere` 字段是 **dict** 含 `{mood, sound_design_hint, temperature_feel}` 3 keys；(b) Backend `storyboard_director.py` L635 写死按 `str + atmosphere + '.'` 拼接，dict 不能 + str → TypeError |
| **为什么 test16 没崩** | test16 B58 完全替换丢失 atmosphere 字段 → Stage 4 用空 str → 不触发 |
| **为什么 test17 才崩** | Wave 10 T16-4 B58 merge **完美保留 atmosphere (dict)** → Stage 4 真用 dict → 触发 TypeError |
| **意外暴露** | Wave 10 T16-4 修复**正确**，但 merge 保留完整字段后**意外暴露之前 storyboard_director.py 的隐藏 bug**（schema 演化问题）|
| **修复 (1 行)** | `storyboard_director.py` L635 + grep 同文件其他 atmosphere 拼接处加 `_atmosphere_to_str()` 容错: `if isinstance(atm, dict): return atm.get('mood', json.dumps(atm))`; if str: return atm |
| **不要点"返回重试"** | 重新跑 Pipeline LLM 仍输出 dict atmosphere → 仍 TypeError 失败循环 |
| **救场方案** | (a) 派 Backend Sonnet xhigh 修 5 min；(b) PM 重启 backend；(c) Founder 点 "返回重试" → Pipeline 从 R4-2 自动重跑 Stage 4（chapter.scenes_json 已含完整 10 scenes）→ 这次容错成功 |
| **派发** | Backend Sonnet xhigh ~10 min — 立即派 |

---

### 🟡 RISK-T17-7 — P1 UX：Pipeline 跑中"后台生成 去做别的"按钮没显示（2026-05-14 14:44 Founder test17 反馈）

| 字段 | 内容 |
|------|------|
| **现象** | test17 Pipeline 进入 Stage 4 (storyboard_running) Founder 期待"后台生成"按钮显示但**没看到** |
| **设计意图** | 按 RISK-T15-1 修复后规则: subPhase=shot-gen 时显示。但 Pipeline 当前 stage=storyboard → ui_phase=storyboard_running → frontend subPhase 派生为 shot-gen 还是 text-gen? |
| **可能根因** | Wave 9 P2 frontend subPhase 派生映射: `storyboard_running → shot-gen 或 text-gen?` (Backend agent Wave 9 P2 paste 写"看你设计")。如果是 text-gen → 不显示按钮 |
| **修复** | 确认设计意图: storyboard_running 阶段应是 shot-gen (用户已 confirm scenes 已过 2 检查点) → frontend subPhase 派生映射 storyboard_running → shot-gen |
| **派发** | Frontend Sonnet xhigh ~10 min — Wave 11 / Pipeline 跑通后修 |

---

### 🟡 RISK-T17-5 — P1：Wave 10 ETA 修复不彻底，stage 切换时 frontend ETA 仍压到极小（2026-05-14 14:38 test17 实证）

| 字段 | 内容 |
|------|------|
| **现象** | test17 stage=screenplay (Stage 3 跑中) backend ETA = 1379s (23 min)，但 frontend 显示 **1 分钟**，差 22 min |
| **Wave 10 双修都未生效** | (a) T16-1 Backend ETA 实时折算 — backend ETA 全程仍 1379s 没变；(b) T15-7 Frontend lastStageRef reset on stage change — stage 已切到 screenplay 但 frontend ETA 仍 1 min |
| **真根因可能** | (a) Wave 10 P2 Backend agent 改的是 `stage_progress` (job_manager L296-313)，不是 `job.estimated_seconds` 字段，所以 status response 的 `estimated_remaining_seconds` 没真折算；(b) Frontend lastStageRef useEffect (StageC L187-247) reset 逻辑可能没真触发 — hot reload 后 component 没 unmount 重 mount |
| **影响** | P1 UX — 用户体感 ETA 不准（1 min 实际还要 22 min）|
| **修复方向** | (a) Backend 真改 `job.estimated_seconds` 字段实时折算 (而非 `stage_progress` 中间变量)；(b) Frontend verify lastStageRef useEffect 真触发 — 加 console.log 跟踪 stage 变化时 reset 是否真执行 |
| **派发** | Backend + Frontend Sonnet xhigh ~30 min — Wave 11 / 测试通过后修 |

---

### 🟡 RISK-T17-4 — 验证方法待补：T16-2 修复"identity 不漂移"无法精确对比（2026-05-14 14:37 Founder 反馈）

| 字段 | 内容 |
|------|------|
| **现象** | test17 Founder 调 char_002 "粉色书包→米黄色书包" → R7-3 重生 portrait + B57 同步重生 fullbody。新 portrait 出来后 Founder 反馈 "好像没怎么变"，但**没法精确对比**（之前的 portrait 没截图，Founder 凭印象判断） |
| **影响** | RISK-T16-2 (Wave 10 P2 修复) 暂时**无法精确验证**是否真生效 — 需要下次测试时 Founder 先截图原 portrait 再调整 → 重生后视觉对比 |
| **下次测试方法** | (a) Stage 2 portrait 完成后 Founder 截图所有 3 角色 portrait（保留对照）；(b) 调整某 1 角色（如换发色/服装/配饰）→ 等 R7-3 + B57 完成；(c) 截图新 portrait + 跟原版对比（脸型/发型/眼睛/皮肤是否一致 + 调整字段是否真改）|
| **派发** | Founder + PM 下次 test 时执行 — 不需 spawn agent |
| **状态** | 🟡 待 test18 (或下次测试) Founder 截图对比验证 |

---

### 🟡 RISK-T17-3 — P1 性能：Wave 10 T14-10 并行化只改 image_preparation 阶段，UX-1 portrait 阶段仍串行（2026-05-14 14:31 test17 实证发现）

| 字段 | 内容 |
|------|------|
| **现象** | test17 UX-1 portrait 阶段时序: 14:28:02 启动第 1 张 → 14:29:03 完成 (60s) → 14:29:51 第 2 张 (+48s) → 14:31:12 第 3 张 (+81s) = **串行** |
| **真根因** | Wave 10 Backend Phase 2 agent 改 `pipeline_orchestrator.py` L925-1010 加 `asyncio.Semaphore(3)` + `asyncio.gather`，但**只改了 image_preparation 阶段（fullbody）**，没改 UX-1 阶段 (L499-503) |
| **影响** | UX-1 portrait 阶段仍 ~3 min 串行（不是预期 ~50s 并行）|
| **设计权衡** | UX-1 设计是 "让用户尽快看到角色卡" → 等用户 R4-1 confirm → 进 image_preparation 真并行做 fullbody。但理论上 UX-1 也可并行（让用户看到第 1 张更快，然后再看到 2/3）|
| **修复** | `pipeline_orchestrator.py` L499-544 UX-1 portrait 循环也改 asyncio.gather + Semaphore(3) |
| **Verify**: image_preparation 阶段（你确认角色 + scenes 后）真并行需观察 backend log | - |
| **派发** | Backend Sonnet xhigh ~30 min — Wave 11 / 测试通过后修（与 RISK-T17-1/2 + 历史 P2 一起）|

---

### 🟡 RISK-T17-2 — P2：Stage 1 LLM 输出 plot_points 缺 beat_type 字段，导致一致性检查器误报"缺高潮/结局"（2026-05-14 14:30 PM 深挖发现）

| 字段 | 内容 |
|------|------|
| **现象** | test17 1_outline.json 真实 plot_points 数 = 10 个，**叙事完整含高潮（"上来叔叔今天派我替他送你"）+ 结局（黄色绢花泪水混晨雨）**。但所有 plot_points 的 `beat_type` 字段都是 **None**。LLM 一致性检查器按 beat_type 统计 → 误报"缺 climax / resolution" |
| **真相** | 大纲叙事**完整无缺**！只是 schema 字段缺失误导一致性检查器 |
| **不影响成片** | Stage 3 ScreenplayWriter + Stage 4 StoryboardDirector 用 `plot_point.description` 文本生成 scenes，基于完整叙事 → 最终成片含完整高潮 + 结局 |
| **根因** | (a) Stage 1 LLM prompt 可能没强制要求 plot_points 填 beat_type 字段；或 (b) Stage 1 schema 模板把 beat_type 设为可选导致 LLM 全省略 |
| **修复方向** | (a) Stage 1 prompt 强制要求 plot_points 含 beat_type ∈ {inciting_incident, first_turn, midpoint, climax, resolution}; (b) 或 Stage 1 后置一个 post-process 根据 plot_point 顺序自动派生 beat_type (第 1 个 = inciting_incident, 最后 1 个 = resolution, 中间按位置分配) |
| **派发** | AI-ML Sonnet xhigh ~30 min — Wave 11 / 测试通过后处理 |

**关联 RISK-T17-1**: T17-1 是 fallback OK，T17-2 是真根因。两者一起修可让 inconsistency_warnings banner 真显示给用户 + 真不再误报。

---

### 🟡 RISK-T17-1 — P2：T16-8 markdown fence strip 修复不彻底，仍有其他 JSON 解析失败场景（2026-05-14 14:26 test17 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | test17 ConfirmOutline 14:26:28 仍触发 `UX-2: 一致性检查 JSON 解析失败（非阻塞），fallback OK: text={"warnings": ["情节节拍不完整...缺少 climax（高潮）、resolution（结局）...` |
| **关键观察** | 这次 LLM 返的**不是** markdown 包裹（T16-8 修过那个）— 是**纯 JSON 文本但解析失败** |
| **可能根因** | (a) LLM 输出超长被截断（看 log 显示 text 末尾是 `... resolution（结局）` 不完整）; (b) JSON 中含中文括号 `（高潮）` 在某些场景导致解析失败; (c) JSON 嵌套深 + 引号未转义 |
| **影响** | P2 — fallback OK 不阻塞 Pipeline（Wave 9 T15-11 + Wave 10 T16-8 都是 fallback 设计），但 inconsistency_warnings banner 仍永远不显示给用户 |
| **修复方向** | (a) Backend 加更强 JSON parser: 先 try json.loads → fail → try ast.literal_eval → fail → regex 提取 `{...}` 区段重试; (b) 或让 LLM 输出 JSON 时降低复杂度（不嵌套中文）|
| **派发** | Backend Sonnet xhigh ~30 min — Wave 11 / 测试通过后处理 |

---

## ✅ Wave 10 全闭环（2026-05-14 11:42）— Test16 暴露的 10 个 RISK 全修

> **完成时间**: 5/14 11:00 派工 → 11:42 PM 全员审查通过（实际 ~1h 完成 vs 预估 2h，**快 2 倍**）
> **战果**: 9 P0/P1/P2 + 1 顺解 = 10 RISK 全闭环 + 93 单测 PASS + 0 越权 + 角色一致性 regression 0 fail
> **Ben 建议 Wave 10 实践**: Backend 改契约 → PM 同时 spawn Frontend 同步修配套（DEC-030 Ben 方案 A 深化）

| Phase | Agent | RISK | 状态 |
|---|---|---|---|
| Phase 1A | Backend Sonnet xhigh | T16-4 (B58 merge) + T16-6 (status failed) + T16-8 (markdown strip) + T16-10 (顺解) | ✅ 21 单测 |
| Phase 1B | Frontend Sonnet xhigh | T16-4 配套 (PreviewScene 透传) + T16-7 (StageD failed UI) + T16-9 (文案) + T16-3 (网络 retry) | ✅ hot reload |
| Phase 2 | Backend Sonnet xhigh | T16-1 (ETA 实时) + T16-2 (R7-3 ref) + T16-5 (storyboard_ready 严格) + T15-5 (skip_portrait 已存在) + **T14-10 (DEC-029 参考图 3 路并行化)** | ✅ 12 单测 |

**剩余**: 仅 T15-15 (PM verify GC 兜底)

> 详见 TEAM_CHAT [2026-05-14 11:18-11:42] Wave 10 完成 + 审查段 + `.team-brain/contracts/STATUS_API_CONTRACT.md`

---

### ✅ RISK-T16-10 — P1 已修（2026-05-14 11:18 顺解 T16-4 / Wave 10 Phase 1A）

| 字段 | 内容 |
|------|------|
| **顺解** | T16-4 修后 chapter.scenes_json 不再被简化 → GET /story 自动返完整 scenes（含 action_beats）|
| **状态** | ✅ 顺解，待 test17 e2e 验证 |

---

### 🟡 RISK-T16-10 (历史条目) — P1：GET /story endpoint 返简化版 scenes (4 字段)，frontend 看不到 LLM 完整 scene 数据（2026-05-14 PM 审查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Founder 在 /scenes 看到的 scene 卡片只 4 字段 (id/name/description/description_zh)，但 Stage 3 LLM 真生成的 scene 含 10+ 字段（含 action_beats / scene_id / scene_heading / location_id / time_of_day / weather / atmosphere）|
| **根因** | `app/api/chapters.py` GET /story endpoint serialize 时对 scenes 做了简化，只返 4 字段。`stage_results.screenplay.scenes` 也是简化版，只 frontend 用 |
| **影响** | (a) 用户无法 review/编辑 action_beats 等关键剧本数据；(b) frontend POST modified_scenes 时只能传 4 字段；(c) 配合 RISK-T16-4 (B58 完全替换) → action_beats 丢失 → Stage 4 失败 |
| **修复** | Backend GET /story endpoint 返完整 scenes（保留所有 LLM 字段，frontend 可选只展示部分但保留完整 payload）|
| **派发** | Backend Sonnet xhigh ~15 min — Wave 10 Phase 1 |

---

### 🟡 RISK-T16-9 — P1 UX：字幕"场景确认环节，你可以修改每个场景的氛围描述"误导用户去点修改触发 T16-4（2026-05-14 PM 审查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Founder 看到字幕 "场景确认环节，你可以修改每个场景的氛围描述" → 象征性点修改让倒计时消失 → 触发 T16-4 frontend POST 简化 modified_scenes → Pipeline 失败 |
| **根因** | `frontend/src/components/create/StageC.tsx:52` 字幕诱导用户去点编辑，但实际点编辑会触发 RISK-T16-4 bug |
| **修复** | 改文案为"场景已生成，请确认是否符合预期" 或类似不诱导编辑（等 T16-4 修后可改回鼓励编辑）|
| **派发** | Frontend Sonnet xhigh ~10 min — Wave 10 Phase 1 |

---

### 🟡 RISK-T16-8 — P2：UX-2 ConfirmOutline JSON markdown 包裹解析失败 fallback OK (test15+test16 重复)（2026-05-14 PM 审查再次发现）

| 字段 | 内容 |
|------|------|
| **现象** | test15 + test16 都触发 `[ConfirmOutline] UX-2: 一致性检查 JSON 解析失败（非阻塞），fallback OK: text=` ```json` `LLM 返回 markdown 代码块包裹的 JSON，backend 解析器没剥 fence |
| **影响** | inconsistency_warnings banner 永远不显示（即使 LLM 真检测到不一致）|
| **修复** | Backend ConfirmOutline JSON parser 先 strip ` ```json ... ``` ` markdown fence 再 parse |
| **派发** | Backend Sonnet xhigh ~10 min — Wave 10 Phase 1 |

---

### 🟡 RISK-T16-7 — P1 UX：Pipeline 失败时 frontend /preview 一片黑没错误提示（2026-05-14 PM 审查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Pipeline Stage 4 失败 → frontend 跳 /preview 一片黑 + client.log "[StageD] currentShot is null — shots.length=0"。用户不知道发生了什么 |
| **根因** | Frontend StageD 没有 failed state UI — 只判断 `shots.length` 没数据时显示空白，没读 status.error 显示真实错误信息 |
| **修复** | Frontend StageD 加 failed state UI: 当 status="failed" 或 storyboard 空时显示错误信息 + "重新生成" 按钮 |
| **派发** | Frontend Sonnet xhigh ~20 min — Wave 10 Phase 1 |

---

### 🔴 RISK-T16-6 — P0：Pipeline 失败但 chapter.status 错标 completed（2026-05-14 PM 审查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Pipeline Stage 4 失败 → JobManager 标 ✅ 完成 + chapter.status="completed" + ui_phase="completed"。但 success=False + storyboard_json="{}" 空 |
| **根因** | `app/services/pipeline_orchestrator.py` 失败 path return success=False 但 chapter.status 写入路径没对 success=False 处理 → 走默认 "completed" 路径 |
| **影响** | (a) frontend 误判 Pipeline 完成 → 跳 /preview 一片黑；(b) status API 返 ui_phase=completed 不准 |
| **修复** | Pipeline 失败时 chapter.status 写 "failed" + chapter.error_message 写 error 详情 |
| **派发** | Backend Sonnet xhigh ~20 min — Wave 10 Phase 1 |

---

### 🟡 RISK-T16-5 — P2：storyboard_ready=true 但 storyboard_json="{}" 错判（2026-05-14 PM 审查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Pipeline 失败后 backend status 返 storyboard_ready=true 但 storyboard_json="{}" 空对象 |
| **根因** | `app/api/chapters.py` _derive_ui_phase + _build_hydrate_hints 判断 `bool(chapter.storyboard_json)` 简单非 NULL，没判 shots 数 > 0 |
| **修复** | 改判 `len(json.loads(chapter.storyboard_json).get("shots", [])) > 0` |
| **派发** | Backend Sonnet xhigh ~10 min — Wave 10 Phase 2（合并 T16-1/2 一起做）|

---

### 🔴🔴🔴 RISK-T16-4 — P0 CRITICAL：ConfirmScenes B58 用 modified_scenes 完全替换 scenes_json，丢失 action_beats 等关键字段，Stage 4 无 shots 失败（2026-05-14 10:44 Founder test16 实证 Pipeline 完全 fail）

| 字段 | 内容 |
|------|------|
| **现象** | test16 Founder 在 /scenes 象征性点修改让倒计时消失 → 点确认场景 → frontend POST modified_scenes (只含 4 字段 `['id', 'name', 'description', 'description_zh']`) → Backend B58 用 `json.dumps(payload.modified_scenes)` **完全替换** chapter.scenes_json → action_beats 全丢 → Stage 4 StoryboardDirector "无法生成任何 shots（所有 scene 无 action_beats）" → ❌ Pipeline 失败 → status 错标 completed + storyboard_json={} 空 → Founder 跳 /preview 一片黑 |
| **根因 (a) Frontend** | `frontend/src/components/create/StageC.tsx` 中 ScenePreview 组件**只渲染 4 字段** (id/name/description/description_zh) 给用户编辑，POST 时也只传这 4 字段。**Stage 3 LLM 真输出的字段**: scene_id/scene_heading/plot_point/location_id/time_of_day/weather/lighting_condition/atmosphere/**action_beats**/narration/characters_in_scene 等 10+ 字段 |
| **根因 (b) Backend** | `app/api/projects.py` L766 `chapter.scenes_json = json.dumps(payload.modified_scenes)` **完全替换** 而非 **merge**。即使 frontend 漏传字段，backend 应该 merge 保留未传的字段（如 action_beats）|
| **影响** | 🔴🔴🔴 **P0 CRITICAL** — 任何用户在 /scenes 点确认（**即使不修改也会触发**因为 frontend 总是 POST modified_scenes）→ Pipeline 必失败 → 完整 e2e 体验破坏 |
| **真根因诊断** | PM 5/14 10:44 实证 chapter.scenes_json 当前只 `['id', 'name', 'description', 'description_zh']` 4 字段。Stage 3 LLM 完整输出含 22 action_beats（在 full_script error JSON 里看到） |
| **修复 (双修)** | (a) Backend B58 改 **merge** 而非 replace: 读 chapter.scenes_json 现有数据 → 用 modified_scenes 的字段覆盖（仅覆盖用户改的字段，保留未改字段如 action_beats）；(b) Frontend ScenePreview POST 时**保留完整 scene 数据**透传，即使不展示也保留 |
| **救场方案** | 选项 A: 修后重跑 test17（30 min）；选项 B: PM 手动从 full_script error JSON 提取完整 scene_data → 写回 chapter.scenes_json → 重启 Pipeline 从 Stage 4（10 min，不浪费已生成的 outline+characters）|
| **派发 (修复)** | Backend Sonnet xhigh ~30 min + Frontend Sonnet xhigh ~30 min — **必须立即修，否则任何 e2e 都会失败** |

---

### 🟡 RISK-T16-3 — P1：frontend 网络断时显示"生成遇到问题"假错误，网络恢复后不自动 retry（2026-05-14 10:41 Founder test16 现场实证）

| 字段 | 内容 |
|------|------|
| **现象** | test16 10:36:53 Founder 网络短暂断开 → frontend status poll fetch failed (`TypeError: Failed to fetch`) → frontend 显示**假错误页 "生成遇到问题，正在编写分场剧本... [返回重试]"**。但 backend Pipeline **完全健康**，10:39:14 已完成 Stage 3，10:41 已切到 ui_phase=scene_review 等用户确认 |
| **真相** | backend 一直在跑（Stage 3 4.4min 完成 + scenes 11 个写入 DB），frontend 是"假阳性"错误显示。Founder 差点点"返回重试"会重新跑 5 min |
| **根因** | frontend status poller 网络失败一次就 dispatch 错误状态，未实现"网络恢复后自动 retry"的容错。也可能是 React error boundary 把 NETWORK error 误判为 generation error |
| **修复方向** | (a) status poller 加 exponential backoff retry (3 次, max 30s)；(b) 区分 NETWORK error vs Pipeline failed，仅 backend 真返 status="failed" 才显示错误页；(c) 网络恢复事件监听 (`window.addEventListener("online", retry)`) |
| **影响** | 🟡 P1 UX — 用户看到假错误差点点重试浪费 backend 工作 + 体感产品不可靠 |
| **临时 workaround** | 用户刷新页面（Cmd+R）让 frontend 重新 hydrate，拿到最新 status |
| **派发** | Frontend Sonnet xhigh ~30 min — Wave 8.x test16 跑通后修 |

---

### 🟡 RISK-T16-2 — P2：R7-3 portrait 重生不传原 portrait 作 ref，character identity 漂移（2026-05-14 10:33 Founder test16 实证）

| 字段 | 内容 |
|------|------|
| **现象** | test16 char_002 (小桐) 调整服装 "换成穿粉色雨衣" → R7-3 重生 portrait → **脸型/发型/服装都变了**（不只是服装变）。Founder 现场实证 "感觉人物变了 服装也变了 都变了" |
| **根因** | `app/services/reference_image_manager.py` L107-117: `if ref_type == 'portrait': reference_images = None  # 肖像不需要参考图`。R7-3 portrait 重生时**不传原 portrait 作 ref**，完全靠 prompt 文本（含 character 完整描述）让 Seedream 重新画 → identity 漂移 |
| **B57 不受影响** | B57 fullbody 重生**用新 portrait 作 ref**（保 portrait→fullbody 一致），但 portrait 自身已漂移 → fullbody 也跟漂移后的 portrait 一致 = 整体漂移 |
| **修复方向** | 改 `reference_image_manager.py` L107: `if ref_type == 'portrait': reference_images = [portrait_ref] if portrait_ref else None` — 让 R7-3 重生 portrait 时也用原 portrait 作 ref（保 identity）+ prompt 调整指定字段（衣服/发色）|
| **设计权衡** | 当前机制是 portrait 完全靠 prompt 文本生成（**不依赖**任何 ref）— 这是 first-time 生成的合理设计；但 regenerate 场景应该 reuse 原 portrait 作 ref 保 identity |
| **优先级** | P2 — Founder 现场说"不是最大的问题，可以之后改进优化修复" |
| **派发** | Backend Sonnet xhigh ~30 min — Wave 8.x test16 跑通后一起做（可与 RISK-T14-10 参考图并行化 + RISK-T15-5 + RISK-T16-1 ETA 一起 PR）|

---

### 🟡 RISK-T16-1 — P2：Backend ETA stage 内不刷新，frontend guard 下降速度跟真实进度脱节（2026-05-14 10:30 Founder test16 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | test16 stage=character_design progress=6% 时 backend ETA = 1439s (24 min)，全程没变；frontend monotonicity guard 持续下降导致显示从 18 → 16 → 15 min（每 30s 下降 ~0.4 min），体感"ETA 跳得快不太对" |
| **数据** | backend 24 min (stale) vs frontend 15 min, 差值 -9 min |
| **根因** | (a) backend `estimate_remaining` 在 Pipeline 启动时算一次就锁定 `job.estimated_seconds`，stage 内不刷新；(b) frontend UX-7 guard 持续每 2s -1.6s 下降，与真实进度脱节 |
| **比 test15 已好** | test15 backend 350s vs frontend "1 分钟"（压成 0）；test16 没压成 0，但仍体感不准 |
| **修复方向** | (a) backend `estimate_remaining` 根据 progress 实时折算（不再 lock）；(b) 或者 frontend guard 速率跟随 progress 而非固定每 poll -1.6s |
| **派发** | Backend Sonnet xhigh ~30 min — Wave 8.x test16 跑通后一起做 |

---

## ✅ Wave 9 / DEC-030 全闭环（2026-05-13 21:25，Ben 方案 A 架构改造）— Test15 13 真 RISK 修 11 (84.6%)

| Phase | Agent | RISK | 状态 |
|---|---|---|---|
| Phase 0 (19:30) | Frontend Sonnet | T15-1, T15-2 | ✅ |
| Phase 1 (20:30) | Backend Sonnet | T15-12, T15-13 | ✅ 9 单测 |
| Phase 3 (20:42) | AI-ML + Frontend + Backend | T15-10, T15-11, T15-14 | ✅ 24 单测 |
| Phase 2 Wave 9 (21:00-21:21) | Backend + DevOps + Frontend Opus | T15-3, T15-7, T15-8, T15-9 顺解 | ✅ 44 单测 + npm build 0 errors |

**剩余**: T15-5 (Wave 8.x), T15-15 (PM verify)
**撤销**: T15-4 (设计正确), T15-6 (indoor only)

---

### 🟡 RISK-T15-5 — P2：image_preparation 阶段重新生成 portrait（应该 skip）

| 字段 | 内容 |
|------|------|
| **派发** | Wave 8.x 合并到 T14-10 参考图并行化 Backend Sonnet xhigh ~45 min |

---

### 🟡 RISK-T15-15 — P3：Shot 6/11/16/21 GC 兜底是否 by-design

| 字段 | 内容 |
|------|------|
| **现象** | test15 Stage 5 启动时 Shot 6/11/16/21 (每 5 张一个) 触发 "Pipeline GC 兜底" |
| **派发** | PM verify ~10 min（看 pipeline_orchestrator.py GC 注释判断是否真 bug） |

---

### 🔴🔴 RISK-T15-2 — P0 CRITICAL：scenes checkpoint 被 createUrl reconcile 完全绕过（2026-05-13 19:22 Founder test15 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | Founder test15 实测：19:22:23 点确认角色 → router.replace('/scenes') → 19:22:43 frontend 自动把用户**踢回 /generating** → 显示 "正在编写分场剧本... 11%"。永远不会自动跳回 /scenes，scenes checkpoint 完全跳过。test15 e2e 卡死 |
| **根因（精确）** | `frontend/src/lib/createUrl.ts:118-125` POST_CHAR_STAGES 包含 `screenplay` + `storyboard`，但这两个 stage scenes 数据**还在生成中**。L242-246 reconcile 逻辑认为 "backend past character_ready → scenes checkpoint 不再 actionable" → 返 'generating' → 用户被踢 |
| **业务影响** | scenes_ready 触发时 backendStage='storyboard' (in POST_CHAR_STAGES) → frontend 永远不会跳回 /scenes → 用户看不到场景列表 + 60s 倒计时 + 确认按钮 → 直接进 shot-gen → e2e 失败 |
| **修复（1 行）** | 移除 POST_CHAR_STAGES 的 `screenplay` + `storyboard`：<br>`const POST_CHAR_STAGES = new Set(["image_preparation", "image_generation", "bgm", "completed"]);` |
| **正确语义** | "POST_CHAR" 应理解为 "scenes 已确认完毕"，而 screenplay/storyboard 是 scenes 数据**正在生成**，不是已过 |
| **验证** | hot reload 后等 storyboard 完成 → frontend Watcher 应自动跳 /scenes（CreateContent.tsx scenes_ready watcher） + 用户看到场景列表 |
| **派发** | Frontend Sonnet xhigh ~10 min（必须立即派 — 否则 test15 e2e 卡死） |
| **顺便** | 同时修 RISK-T15-1（后台按钮 + subtitle 文案）— 一次 PR 双修 |

---

### ✅ RISK-T15-13 — P0 已修（2026-05-13 21:00 Backend Sonnet 4.6 xhigh）

| 字段 | 内容 |
|------|------|
| **修复** | `chapters.py` L1771 + L1829-1860（regenerate 双修 PR-A 一起修）|
| **改动** | (a) generate_shot_image_phase2_safe() 加 project_id=project.id 参数 → 透传到 seedream_generator log_api_cost；(b) 成功后回写 5_image_results.json (success=True, error=None, image_path/url/time 更新, try/except 非阻塞) |
| **验证** | 9/9 单测 PASS + 完整调用链路 9 层接通 + 0 越权 + PM 5/13 21:05 审查通过 |
| **状态** | ✅ 已修，待 backend 重启 + e2e verify |

---

### ✅ RISK-T15-12 — P0 已修（2026-05-13 21:00 Backend Sonnet 4.6 xhigh）

| 字段 | 内容 |
|------|------|
| **修复** | `chapters.py` L1862-1885（regenerate 双修 PR-A 一起修）|
| **改动** | select 最新 GenerationJob → failed_shot_count = max(0, count - 1)（防重复重生扣负数）→ partial_failure = (count > 0) → db.add + commit (try/except 非阻塞) |
| **验证** | 单测覆盖防负数 + happy path + DB 更新 PASS |
| **状态** | ✅ 已修，待 backend 重启 + e2e verify |

---

### 🔴 RISK-T15-12 — 已修，旧条目保留供历史参考

| 字段 | 内容 |
|------|------|
| **现象** | test15 Founder 在 /preview 点 Shot 22 重生 → 19:59:27 Seedream ✅ 成功 → shot_22.png 写入 images/（23 张全） → 但 status API 仍返 failed_shot_count=1, partial_failure=True |
| **影响** | Frontend /preview 一直显示 "22/23 张生成成功，1 张未生成"，即使实际 23/23 ✅。用户体感"我重生了但系统不认账" = bad UX |
| **根因** | `app/api/chapters.py` shot regenerate endpoint（如 /shots/{shot_id}/regenerate）成功后没更新 chapter_generation_jobs.failed_shot_count 字段 + 没重新评估 partial_failure |
| **修复方向** | regenerate endpoint 成功 path：`job.failed_shot_count -= 1; job.partial_failure = (job.failed_shot_count > 0)` + commit DB |
| **派发** | Backend Sonnet xhigh ~15 min |

---

### ✅ RISK-T15-9 — P2 已修（2026-05-13 21:00 Backend Opus 4.7 Wave 9 P2 顺解）

| 字段 | 内容 |
|------|------|
| **修复** | `pipeline_orchestrator.py` L1278-1284 + L1365-1372 Stage 5 单 shot 失败 path 调 `increment_failed_shot_count(job_id)` |
| **链路** | `chapters.py` → `job_manager.run_story_generation_task` → `pipeline.run(job_id=job_id)` → Stage 5 fail path → `increment_failed_shot_count` → DB commit |
| **验证** | 44 单测 PASS + 完整调用链路 9 层 verify + curl status 实测 ui_phase/failed_shot_count 同步 |
| **状态** | ✅ 已修，Wave 9 P2 Backend 顺解 |

---

### ✅ RISK-T15-8 — P0 UX 已修（2026-05-13 21:00 Backend Opus 4.7 Wave 9 P2 顺解）

| 字段 | 内容 |
|------|------|
| **修复** | `chapters.py` status response 新增 `ui_phase` + `characters_confirmed` + `scenes_confirmed` + `hydrate_hints` 字段，frontend subPhase 可直接派生 |
| **验证** | curl 实测 status response 含 6 新字段 ✅，等 Wave 9 P2 Frontend agent 改 createUrl/StageC 真派生 |
| **状态** | ✅ Backend 端已修，待 Frontend 派生（Wave 9 P2 Frontend agent spawn 中）|

---

### ✅ RISK-T15-7 — P1 UX 已修（2026-05-13 21:00 Backend Opus 4.7 Wave 9 P2 顺解）

| 字段 | 内容 |
|------|------|
| **修复** | Backend 保持 ETA 计算 + status response 含 `stage` 字段；frontend Wave 9 P2 改 createUrl/StageC 监听 stage 变化时重置 ref |
| **状态** | ✅ Backend 端就绪，待 Frontend Wave 9 P2 改 ETA guard |

---

### ✅ RISK-T15-3 — P0 CRITICAL 已修（2026-05-13 21:00 Backend Opus 4.7 Wave 9 P2 顺解）

| 字段 | 内容 |
|------|------|
| **修复** | `chapters.py` GET /story endpoint 顺序调整：优先检查 `chapter.scenes_json` 非空，有就直接返 200 + scenes 数据（即使 chapter.status 还是 "generating_story"）|
| **代码** | L395-430，含完整 RISK-T15-3 注释 + 永久治本 |
| **验证** | curl GET /story 实测 test15 项目返 scenes(11) + characters ✅ |
| **状态** | ✅ 已修，永久治本（不再需要 PM curl 强制 unblock R4-2）|

---

### 🟡 RISK-T15-9 (历史条目) — 已被上方 ✅ 取代（2026-05-13 19:54 monitor 触发，PM 19:57 修正）

| 字段 | 内容 |
|------|------|
| **现象** | test15 Shot 22 经 4 次 IncompleteRead retry 后最终 ERROR `❌ Shot 22 失败: IncompleteRead(450040 bytes read, 450 more expected)`，但 backend status API 返：failed_shot_count=0, partial_failure=False, msg="已生成 23/23 张图像..." — **数据撒谎** |
| **真实状态** | disk images/ 实际只有 22 张 (无 shot_22.png)，Pipeline 内存计数器以为 23 张全成功 |
| **根因** | `image_generator.py` 或 `seedream_generator.py` retry exhausted 后的 final ERROR 没传到 R5 image_results 列表，pipeline_orchestrator 统计时漏算 |
| **业务影响** | 🔴 P0 — (a) 用户在 /preview 看到成片缺 1 帧；(b) BGM 用 22 张对齐但音频按 23 张算，时间轴错；(c) failed_shot_count 永远 = 0 → frontend 不显示"重生失败 shot"按钮 |
| **修复方向** | (a) seedream_generator final ERROR path 必须 raise exception 给上游；(b) pipeline_orchestrator R5 image_results 处理 try/except，捕获后 += failed_shot_count；(c) frontend /preview 加"补生失败 shot"按钮 |
| **派发** | Backend Sonnet xhigh ~30 min（紧急修，下次测试前必须修） |

---

### 🟡 RISK-T15-10 — P1 性能：Shot 21 在 retry 过程中被重复生成（2026-05-13 19:54 monitor + PM 自查发现）

| 字段 | 内容 |
|------|------|
| **现象** | log 显示 Shot 21 ✅ 生成成功 两次：19:53:37 (43.77s) + 19:54:23 (42.27s)。浪费 1 次 Seedream call ($0.03) |
| **可能根因** | (a) IncompleteRead retry 触发新 fetch，但前一个 fetch 也并行完成；(b) 或 race condition：retry 任务和原任务同时返回成功；(c) 或 asyncio.gather 处理重复 task |
| **影响** | P1 — 不影响功能（重复生成不会污染数据），但浪费成本 + 可能 race write file 覆盖 |
| **派发** | Backend 调查 ~20 min — 可能与 RISK-T15-9 是同一 retry 机制问题 |

---

### 🔴 RISK-T15-8 — P0 UX：generationSubPhase 不监听 backend scenes_confirmed 字段（2026-05-13 19:46 Founder test15 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | image_generation 阶段（属于 shot-gen），按 RISK-T15-1 修复后逻辑应显示"后台生成"按钮，但 Founder 看不到 |
| **根因** | frontend `generationSubPhase` 只通过 user click handlers 切换（handleConfirmCharacters / handleConfirmScenes 内 dispatch `SET_GENERATION_SUB_PHASE: "shot-gen"`）。当 PM 直接 POST /confirm-scenes 绕过 frontend handler 时，subPhase 不变 → 后台按钮不显示。**深层**：subPhase 应该是 backend authoritative state 的派生（监听 status.scenes_confirmed 字段），不是 user action 触发的 |
| **修复方向** | Frontend 加 useEffect 监听 backend status.scenes_confirmed: 当 true 时 dispatch 切 subPhase = "shot-gen"；同样 status.characters_confirmed=true 时切 char-preview |
| **影响** | 🔴 P0 — 用户错过"后台生成"按钮 + 此 bug 不只是 PM unblock 场景触发，**任何 frontend handler 异常 + 刷新页面 + state 丢失场景都会触发** |
| **派发** | Frontend Sonnet xhigh ~20 min（subPhase 改造为 backend-authoritative） |

---

### ✅ RISK-T15-14 — P2 已修（2026-05-13 21:30 Backend Sonnet 4.6 xhigh）

| 字段 | 内容 |
|------|------|
| **修复** | `app/services/storyboard_director.py` (a) prompt 强化 REQUIRED FIELDS (L1116-1130) (b) JSON 示例 3 字段 (c) post-process fallback (L1625 后 ~50 行) |
| **改动** | shot_type / camera_angle / characters_in_scene 三字段：prompt 强约束 "NEVER leave blank or null" + 8/9-key 映射表 fallback + characters_in_scene 优先从 character_direction.characters_visible 派生 |
| **验证** | 13/13 单测 PASS + 既有 5 规则常量保留 + py_compile PASS + 0 越权 |
| **状态** | ✅ 已修，待 test16 e2e 验证 |

---

### ✅ RISK-T15-11 — P2 已修（2026-05-13 21:25 Frontend Sonnet 4.6 xhigh）

| 字段 | 内容 |
|------|------|
| **修复** | `frontend/src/app/layout.tsx` L83-175 (a) window.onerror 加 JS error stack 捕获 (b) addEventListener('error') 加 if(e.error) 守卫防双重 + 提取 MediaError.code (c) unhandledrejection 智能处理 Error/Event |
| **bonus 发现** | test15 那条 "Unknown error" 是 BGM `<audio>` 元素播放失败（MediaError），不是 JS 异常。修复后下次出现会显示 `audio src=... MediaError.code=4` |
| **验证** | npm build 0 errors / 20 routes ✅ + frontend 重启后 5 routes 200 |
| **状态** | ✅ 已修，待 PM e2e DevTools verify |

---

### ✅ RISK-T15-10 — P1 已修（2026-05-13 21:18 AI-ML Opus 4.7 xhigh）

| 字段 | 内容 |
|------|------|
| **修复** | `app/prompts/storyboard_prompts.py` 新建 OFF_SCREEN_SOUND_HANDLING_RULES (5210 字符) + `app/services/storyboard_director.py` import + Rule 6 强化 + 两个 prompt build 路径注入 |
| **改动** | THE GOLDEN RULE + 9 中文 cue 表 + 3 BAD/GOOD 对比（含 canonical 范例）+ 5 环境锚点 + 6 forbidden 黑名单 + 6 步 decision checklist |
| **验证** | 11/11 单测 PASS + 架构 regression 7/7 PASS + py_compile clean + 0 越权 |
| **状态** | ✅ 已修，待 test16 e2e Shot 21 类 case 验证 |

---

### 🟡 RISK-T15-7 — P1 UX：Frontend ETA 计算被 UX-7 monotonicity guard 过激压缩（2026-05-13 19:46 Founder test15 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | Frontend 显示 "预计还需约 1 分钟"，但 backend 真实 estimated_remaining_seconds=350 ≈ 5.8 min。**Founder 体感时间不准**，影响信任度 |
| **根因** | `frontend/src/components/create/StageC.tsx:257-262` UX-7 monotonicity guard 强制 ETA 永远不上调（每 2s poll 至少下降 1.6s）。Pipeline 经过多阶段切换（screenplay→storyboard→image_prep→image_gen），backend 真实 ETA 会按新 stage duration 上调，但 guard 阻止 → ETA ref 被人为压缩到极小值 |
| **设计错误** | UX-7 guard 假设 backend ETA 单调下降，但 backend 阶段切换时 ETA 会合理跳变（如 R4-2 解锁后 ETA 重置为新阶段总时长）|
| **修复方向** | (a) 监听 backendStage 字段，stage 切换时重置 lastEtaSecondsRef，让新 stage 的 ETA 自然显示；(b) 或者 guard 只在同一 stage 内生效；(c) 或者放宽：允许 ETA 上调但限制最大上调幅度（如 +2 min/poll）|
| **影响** | 🟡 P1 UX — 不阻塞功能，但用户看到 "1 分钟" 实际还要 5-6 min = 体感被骗 |
| **派发** | Frontend Sonnet xhigh ~15 min（test15 e2e 跑完后修）|

---

### 🟡 RISK-T15-6 — P2 优化：scene_refs 只生成 4 张（应是 8 张 interior+exterior）（2026-05-13 19:43 PM 自查发现）

| 字段 | 内容 |
|------|------|
| **现象** | test15 image_preparation 阶段 scene_refs/ 只有 4 张（4 location），不是预期的 8 张 (4 location × interior + exterior) |
| **可能根因** | (a) SceneReferenceManager 只生成 1 视角而非 interior+exterior 都生成；(b) 或者 location 没区分 interior/exterior 类型；(c) 或者 11 个 screenplay scenes 合并到 4 unique location，每个只取 1 视角 |
| **影响** | shots 生成时少了 50% scene refs，可能影响场景一致性。但当前 sanitize_attempts=0 全过，影响不显著 |
| **优先级** | P2，需要派 Backend Sonnet xhigh 调查 + 决定是否改回 8 张 |

---

### 🟡 RISK-T15-5 — P2 优化：image_preparation 阶段重新生成 portrait（应该 skip）（2026-05-13 19:41 PM 自查发现）

| 字段 | 内容 |
|------|------|
| **现象** | UX-1 阶段已生成 3 portrait，B57 重生 char_001。image_preparation 阶段又跑了 6 次 Seedream call（应是 3 次 fullbody，但实际跑了 portrait+fullbody = 6 张）|
| **根因** | `pipeline_orchestrator.py:966 generate_character_multi_refs(skip_portrait=False)` 没传 skip_portrait=True，导致 portrait 被重复生成 |
| **影响** | 浪费 ~$0.09（3 张 portrait × $0.03）+ ~1.5 min 时间 |
| **优先级** | P2，Wave 8 RISK-T14-10 参考图并行化时一并修 |

---

### ❌ RISK-T15-4 — 撤销（2026-05-13 20:15 Founder 澄清设计意图）

| 字段 | 内容 |
|------|------|
| **撤销原因** | Founder 5/13 20:15 澄清："用户已经可以看大纲和情节、角色、场景，这应该就够了，storyboard review 价值在哪？" |
| **CLAUDE.md 设计原则验证** | "用户关心的是讲什么故事，不是怎么拍" + "Phase 2-4（系统自动）：分场剧本、分镜脚本、旁白文案 — 系统自动完成，不打断用户" |
| **结论** | Storyboard (4_storyboard.json) 是分镜层（怎么拍 — 镜头/构图/光线），与 Scenes (3_screenplay.json) 叙事层（讲什么）不同。按 Founder 设计意图，**storyboard 不让用户 review = 设计正确**。/preview 阶段单 shot 重生 + 删除 + 编辑功能已提供事后修改权 |
| **行动** | 不派发，原方向无效 |

---

### 🔴 RISK-T15-3 — P0 CRITICAL：scenes_ready 阶段 frontend hydrate /storyboard 永远 404（2026-05-13 19:30 Founder test15 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | Backend Pipeline R4-2 在 Stage 3 后立即等待用户确认（**不跑 Stage 4**），但 frontend /scenes 页面 hydrate /storyboard endpoint（Stage 4 后才有数据）→ 永远 404 → 用户看 "场景还在生成中" 转圈 |
| **临时 unblock** | PM 直接 POST /confirm-scenes 强制解 R4-2，Stage 4 启动跑 |
| **永久修复方向** | (a) Backend GET /story 在 scenes_ready 阶段返回 3_screenplay.json 的 scenes；(b) 或新加 GET /screenplay endpoint；(c) Frontend /scenes 页面 hydrate 改用上者 |
| **派发** | Backend + Frontend Sonnet xhigh ~30 min（与 RISK-T15-4 一并修）|

---

### 🔴 RISK-T15-1 — P0 UX：/generating 在 text-gen 阶段错误显示"后台生成"按钮（2026-05-13 19:14 Founder test15 现场发现）

| 字段 | 内容 |
|------|------|
| **现象** | Founder test15 实测：刚点确认大纲 → 跳 `/generating`（character_design 阶段）→ 看到"后台生成，去做别的"按钮 |
| **设计意图（Founder 当场澄清）** | "我的意思是**角色和场景都要确认后**才有这个功能 现在用户不可以去做别的"。即只有 scenes_confirmed 之后（shot-gen 阶段）才显示 |
| **根因** | `StageC.tsx:943` 渲染条件 `(generationSubPhase === "text-gen" \|\| generationSubPhase === "shot-gen") && !isError` —— 包含了 text-gen 分支（character_design / screenplay / storyboard 都触发） |
| **修复（1 行）** | `{state.generationSubPhase === "shot-gen" && !isError && (` —— 删除 text-gen 分支 |
| **附加文案修正** | StageC.tsx L106-110 的 stage subtitle map：character_design / screenplay / storyboard / character_ready 四行的"AI 正在创作故事，可以选择后台生成" 改成"AI 正在创作故事，请稍候"（不再误导用户可以离开）|
| **派发** | Frontend Sonnet xhigh ~10 min（test15 e2e 跑通后立即派，dev hot reload 不影响 backend）|
| **PM 备注** | Wave 7 RISK-T14-12 当时设计意图被理解偏（text-gen + shot-gen 都显示），test15 中被 Founder 当场纠正 → text-gen 不该显示。这是**设计意图修正**，不是新 bug |

---

## ✅ Wave 7 全闭环（2026-05-13 17:30）— 13 RISK-T14-* 全修

> **完成时间**: 5/13 16:30 spawn → 17:30 PM 全员地毯审查通过
> **战果**: 4 P0 + 7 P1 + 1 P2 + 1 P3 全闭环（Wave 8 RISK-T14-10 参考图并行化待）
> **5 组 Mureka 真测**: 5/5 PASS + Founder 听感"都非常贴切 我很满意"
> **agent 工作量**: Backend 5 + 1 R2 = 6 任务 / Frontend 6 任务 / AI-ML 6 子任务 + 11 组真测
> **PM 自修**: SettingsContent null-safe 1 处 + 3 处 BGM wiring 死代码
> **DECISIONS 新增**: DEC-026 BGM 通用性框架 / DEC-027 后台通知 / DEC-028 不截断 / DEC-029 参考图并行
> **0 越权 / 0 共享文档并发冲突** ✅
>
> 详: TEAM_CHAT [2026-05-13 17:30] Wave 7 收尾段 + `.team-brain/analysis/BGM_UNIVERSAL_FRAMEWORK_2026-05-13.md`

---

## 🔍 Test14 重点观察项（2026-05-13 PM 亲读 B1 代码后发现的 3 个 risk）

> **来源**: PM 5/13 亲自 Read B1 改动 4 文件（AuthContext / CreateContent / StageC / createUrl）发现，Explore agent 漏报。
>
> **不阻塞 test14**，但需 Founder e2e 时重点观察。如观察到问题即派对应 agent 修。

### ✅ Wave 7 已修 RISK-T14-1 — 🔴 P0 StageC React anti-pattern 真根因不 100% 确定

| 字段 | 内容 |
|------|------|
| **现象** | Founder 5/12 现场截图 stack trace `CharacterPreview StageC.tsx:1181:11 → RedirectBoundary` 报 `Warning: Cannot update a component while rendering a different component` |
| **B1 修了什么** | useCallback 稳定 inline props (L735/L749) + console.log 移到 useEffect (L957-973) + useMemo portraitMap (L984-1003) |
| **PM 自审疑虑** | 当前 L1180-1182 实际是 `const charPortraitUrl = portraitMap.get(char.id) ?? null;` — **普通赋值不是 setState**。真 stack trace 指向 RedirectBoundary 暗示真根因可能是 **render 时调 router.push/replace**。B1 改动可能是 mitigation（减少 render churn），不是 root cause fix |
| **唯一确认方式** | Founder e2e test14 时打开 DevTools console，跑到 character_ready 触发 CharacterPreview → 看**是否仍出现** `Cannot update a component while rendering` warning |
| **修复方向（如 e2e 仍出现 warning）** | grep `router.push\|router.replace\|window.location` in StageC.tsx CharacterPreview/ScenePreview 组件 render path，移到 useEffect / event handler |
| **派发（如需）** | Frontend Opus xhigh，重点查 CharacterPreview render 内的路由跳转调用 |

---

### ✅ Wave 7 已修 RISK-T14-2 — 🟡 P1 AuthContext 5xx 期间 user=null + isLoggedIn=true，protected 组件可能 null reference crash

| 字段 | 内容 |
|------|------|
| **B1 改了什么** | AuthContext.tsx 新增 tokenInvalid state + isLoggedIn 改为 `!!user \|\| (!!token && !tokenInvalid)`。5xx 时保留 token + isLoggedIn=true，但 user=null |
| **PM 自审疑虑** | B1 **没改** dashboard / settings / UserMenu / Header 等 protected 组件。如这些组件用 `user.name` / `user.email`（非 optional chain）→ 5xx 期间 JS crash null reference 或显示空白。TS 类型 `User \| null` 强制 narrow 但**运行时 narrow 失败仍 crash** |
| **唯一确认方式** | Founder e2e test14 时**临时 stop backend mysql** 让 /auth/me 返 5xx → 刷新 dashboard / settings → 看是否 ✅ loading state 或 fallback 显示 / ❌ 白屏 / crash / "null" 字面字符串 |
| **修复方向（如 e2e 看到 crash/空白）** | grep frontend/src `user\.name\|user\.email\|user\.avatarUrl\|user\.plan\|user\.credits` 没 optional chain 的全改 `user?.X` + 加 fallback display "用户"/loading |
| **派发（如需）** | Frontend Sonnet xhigh，简单 null-safe 加固 |

---

### ✅ Wave 7 已修 RISK-T14-12 — 🟡 P1 缺失"后台生成"选项（Founder 5/13 16:06 反馈）

| 字段 | 内容 |
|------|------|
| **Founder 反馈** | "之前有的，在确认角色和场景后，进入后续生成的进度 process 里，是有'后台生成'选项的，用户可以点击后就在后台跑，然后在完成的时候在合适的位置通知用户" |
| **现状** | test14 实测 frontend 进度条页面（/generating）**没有"后台生成"按钮**，用户必须停留在该页面看进度。如果切走或关 tab，错过 R4-1/R4-2 checkpoint = Pipeline 30 min 超时 fail |
| **真根因** | StageC.tsx 进度条 UI 缺"后台生成"按钮 + 缺通知机制（浏览器 Notification API 或 dashboard 显示新故事 ready 角标 + 邮件 push）|
| **影响** | 🟡 P1 UX：用户不能切走做别的事，必须盯进度条 13+ min。多任务用户体验差 |
| **修复方向** | (a) /generating 加"后台生成"按钮 → 点击 router.push('/dashboard') + 后端继续跑（已经是这样设计）<br>(b) 完成时通知：浏览器 Notification API + dashboard 列表角标 "✨ 新故事完成" + 可选邮件 push（DEC-027 待 Founder 决策）|
| **派发** | Frontend Sonnet xhigh ~30 min（按钮 + Notification API + dashboard 角标）|
| **关联** | 历史曾经实现过（B-X 修复前），可能某次 refactor 误删 — grep `[Bb]ackground|后台生成` 看历史代码追踪 |

---

### ✅ Wave 7 已修 RISK-T14-11 — 🔴 P0 **BGM 通用性框架缺失** — style_preset 没传 Haiku，6 桶 mood 映射不考虑视觉风格（Founder 5/13 16:09 通用性需求 + PM 深挖代码层证实）

> Founder 5/13 16:09 升级关注："关于这点 要看看BGM的生成prompt到底是什么 我们要的是**通用性** 我感觉**风格也是要传入的** 比如情绪是悬疑但画面风格是中国古风水墨之类 能不能总体的BGM把这综合包括但不仅限于这两者的维度结合起来 在**听感 节奏 韵律等等全维度** 做到更贴切一点？"

#### 实测铁证（test14 5/13）

**BGM Haiku 生成 prompt（来自 `output/5cbd8ca0.../bgm_prompt_chapter0.txt`）**:
```
Minor key. Sparse percussion that won't quite become rhythm—single stone pieces
falling on wooden board at irregular intervals, like a pulse heard through fog.
Ambient drone underneath, low and persistent...
A dissonant cluster on strings, dampened. No resolution.
```

**真实生成 BGM** = 西式电影氛围（minor key + drone + dissonant strings），跟 ink 水墨武侠故事画面风格**完全割裂**。

#### 真根因（PM 深挖 `music_generation_service.py` + `story_music_extractor.py` + `meta_mixed_v3_quote_picking.md` 47KB template）

**1. extract_story_for_music() 15 字段维度不全**:
- ✅ 有: emotional_arc_*, narrative_pace, narration_paces, scene_moods, full_narration, user_selected_mood, visual_style_hint (字符串)
- ❌ **缺**: `style_preset` (ink/wuxia/cyberpunk/ghibli/realistic 等 80+ 显式名称) + style_description + character_types + setting_period

**2. Haiku Template (`meta_mixed_v3_quote_picking.md`) 6 桶映射只按 mood 走，不考虑 style_preset**:

| mood | 当前模板"必备调性词" |
|---|---|
| Mysterious 悬疑 | `minor key / sparse percussion / ambient drone / tension build / sudden silence / dissonant cluster / muffled pulse` |

**注意**：Mysterious 桶的"必备调性词"**没区分中国古风 vs 西方悬疑** — Haiku 拿到 mood=悬疑 直接落桶 → 输出西式 BGM。**这就是 test14 生成的 prompt 的来源**。

**3. 元原则 D"文化映射优先"是软提醒不是强约束**:
> Template 写: "中国故事承载中国声音记忆。年夜饭骨子里有二胡——不是大提琴。"

但**没有按 style_preset → 强制乐器列表**的硬规则，所以 Haiku 自由发挥时容易回归训练数据中最强烈的悬疑范例（西式电影）。

**4. visual_style_hint 是字符串塞 prompt 末尾，权重低于 6 桶映射**:
- Stage 1 outline.music_hint: "East Asian minimalist, guqin or dizi or xiao color, negative space breathes betw..."
- Template 把这个塞进 `{visual_style_hint}` 占位符，但 Haiku 看 6 桶 Mysterious 调性词比这个权重高，优先服从桶映射

#### 修复方向（产品设计 — 通用性 BGM 框架）

> **核心**: BGM 生成应是 **`mood × style × setting × pace × emotion_arc`** 多维度综合，不是单一 mood 桶映射。任何 mood + style 组合都能生成贴切 BGM = "通用性"

##### A. 扩展 story_music_extractor 维度（Backend 改动）
新增字段:
- `style_preset` (ink/wuxia/cyberpunk/realistic 等 80+ 显式名称)
- `style_category` (chinese_traditional / japanese_anime / western_realistic / sci-fi / fantasy / etc — 一级分类)
- `setting_period` (古代中国 / 现代中国 / 西方古代 / 未来 / 异世界，从 outline 推断)
- `character_dominant_type` (人类/动物/奇幻/机器人，从 characters 推断)

##### B. Template 加 `style × mood` 二维矩阵（AI-ML 设计）
替换或扩展当前 6 桶为：

| mood \ style_category | chinese_traditional (ink/wuxia/ink_painting) | western_realistic | sci-fi (cyberpunk) | japanese_anime (ghibli/anime) | fantasy/children (children_book/cartoon) |
|---|---|---|---|---|---|
| Mysterious 悬疑 | **guqin sparse / dizi tremolo / 古钟低鸣 / pentatonic / 散板 60-80 BPM / 留白 / 不解决** | piano + cello pizz + minor key + 4/4 80 BPM | dark synth + glitch + chromatic + 90 BPM | sparse harp + woodwind + modal | bell + sparse piano + minor + 70 BPM |
| Melancholic 沉重 | 古琴低音 + 箫 + 极慢 50-70 BPM | piano + strings cello + 60 BPM | dark synth + sub bass + 70 BPM | mournful flute + harp + 60 BPM | minor piano + violin + 70 BPM |
| Heroic 热血 | **战鼓 + 唢呐 + pentatonic + 鼓点行板 100-120** | brass + percussion + 4/4 120 BPM | synth lead + 808 + 130 BPM | full orchestra + chorus + 110 | march drum + horn + 110 |
| Warm 温馨 | **古琴 + 笛 + 慢 70 BPM + 留白** | piano + acoustic + 80 BPM | warm synth pad + 80 | piano + glockenspiel + 90 | ukulele + glockenspiel + 100 |
| Romantic 浪漫 | **二胡 + 古筝 + 散板 + 缠绵** | strings + piano + 70 BPM | dreamy synth + reverb + 80 | strings + harp + 80 | gentle piano + flute + 80 |
| Energetic 活泼 | **笛 + 锣鼓 + pentatonic + 跳跃 120 BPM** | piano + percussion + 120 BPM | electronic pop + 130 BPM | playful flute + bass + 120 | xylophone + tambourine + 120 |

每 cell 五维度: **instruments + scale + tempo + rhythm pattern + timbre**

##### C. 元原则 D 升级为硬约束（不只软提醒）
```
if story_data.style_category == "chinese_traditional":
    MUST_INSTRUMENTS = ["guqin", "dizi", "xiao", "pipa", "guzheng", "erhu", "战鼓"]
    MUST_SCALE = "pentatonic (宫商角徵羽)"
    FORBIDDEN_INSTRUMENTS = ["cello as primary", "distorted strings", "drum kit", "synth"]
    
if story_data.style_category == "sci-fi":
    MUST_INSTRUMENTS = ["synth", "electronic pad", "glitch percussion"]
    FORBIDDEN_INSTRUMENTS = ["guqin", "harpsichord", "traditional folk"]
```

##### D. Mureka API 调用前 prompt linter（防护层）
检查 prompt 是否含 style_category 必备词，缺失则**自动注入** + log warning。

#### 实施工时与验证

| 阶段 | 工时 | 验证 |
|---|---|---|
| (A) story_music_extractor 加 4 字段 | Backend 30 min | 单测 |
| (B) Template style × mood 矩阵 + 文化硬约束 | AI-ML Opus xhigh **2-3h**（核心，需调研 80+ style_preset 真实视觉特征 + 对应音乐风格）| 跑 6 mood × 5 style category = **30 组样本对比**测试 |
| (C) 元原则 D 硬约束 | AI-ML 1h | 单测 |
| (D) Mureka prompt linter | Backend 30 min | 单测 |
| **总** | **4-5h** | 30 组样本 |

#### 影响

🔴 **P0**：视觉听觉割裂 = 产品质量灾难。任何 style × mood 组合都必须能生成贴切 BGM。

#### 派发

- **AI-ML Opus xhigh**: 主导 — Template style × mood 矩阵设计 + 80 style_preset 音乐特征调研 + 30 组样本测试
- **Backend Sonnet xhigh**: 配合 — story_music_extractor 维度扩展 + Mureka prompt linter

#### 关联

- DEC-026 待加 — BGM 通用性框架决策（style × mood 矩阵 + 文化硬约束）
- 关联 80+ `style_preset` 现有定义（`app/services/style_enforcer.py` + `app/prompts/style_presets.py`）
- 历史 RISK-T14-11 之前判断"只加古琴"被 Founder 5/13 16:09 升级为通用性框架

---

### ⏳ Wave 8 待 — RISK-T14-10 — 🟡 P1 角色参考图 + 场景参考图阶段并行化（Founder 5/13 15:53 决策 DEC-029）

| 字段 | 内容 |
|------|------|
| **Founder 决策** | "确保质量的前提下 角色参考图和场景参考图也要并行（比如 3 连发）" |
| **现状** | test14 实测 angle 参考图阶段**完全串行** — 3 角色 portrait 串 ~135s + 3 fullbody 串 ~135s + 多 location anchor interior 串 + exterior 串 = 总 ~7 min 串行 |
| **设计可并行边界（确保质量）** | (a) 跨角色 portrait 之间**无依赖**可 3 路并行（节省 ~90s）<br>(b) 跨角色 fullbody 之间**无依赖**可 3 路并行（每角色用自己 portrait 作 ref 不影响跨角色）（节省 ~90s）<br>(c) 多 location scene anchor interior 之间**无依赖**可并行（节省 ~60-90s）<br>(d) 多 location scene anchor exterior 之间**无依赖**可并行（每 location 用自己 interior 作 ref，DEC-010）（节省 ~60-90s）|
| **不可并行边界（必须串）** | (e) 同一角色 portrait → fullbody 必须串（fullbody 用 portrait 作 ref 保持人脸一致性）<br>(f) 同一 location interior → exterior 必须串（exterior 用 interior 作 ref 保持环境一致性 DEC-010）|
| **预期节省** | ~6 min（参考图阶段从 ~7 min → ~1.5-2 min）。test14 总耗时从 ~25 min → ~19 min |
| **关键质量验证（必跑）** | 实施后**必须**跑 `pytest tests/test_character_consistency_regression.py`（CLAUDE.md 强制要求 + 角色一致性是产品生命线）|
| **修复方向** | `app/services/reference_image_manager.py` 把 portrait 循环改 asyncio.gather + Semaphore(3)；fullbody 同样改 asyncio.gather；`app/services/scene_reference_manager.py` 多 location 改 gather；保留同一 character/location 内 portrait→fullbody / interior→exterior 串行 |
| **派发** | Backend Sonnet xhigh，~45 min（含跨角色/location 并行实现 + 角色一致性回归测试 + 单测）|
| **关联** | 5/12 BUG-PARALLEL-M1-NOT-EFFECTIVE 降级 P2 → Founder 5/13 升级 P1 + 提供明确实现指引 |

---

### ✅ Wave 7 已修 RISK-T14-9 — 🟡 P1 StoryboardDirector 自动截断 26 shots → 18 = UX 灾难，Founder 5/13 明确"不要截断"

| 字段 | 内容 |
|------|------|
| **现象** | test14 5/13 15:41:53 backend log: `[StoryboardDirector] O-2: LLM 生成 26 shots，超出上限 18（chapter_duration=3min），自动截断` |
| **Founder 决策（5/13 15:44）** | **不要自动截断，把多出来的 8 shots 当送给用户**。用户看完整故事体验，不应被强制砍掉 |
| **真根因** | `app/services/storyboard_director.py` 的 O-2 截断逻辑：当 LLM 生成 shots 数 > chapter_duration / shot_duration（3min/4s = 18）时自动 slice[:18] |
| **影响** | 🟡 P1 UX：用户看到的故事不完整，LLM 生成的 8 个分镜（可能是关键过渡 / 情感细节）被丢弃 |
| **修复方向** | 移除 O-2 截断逻辑，让所有 LLM 生成的 shots 都 pipeline 生成（多花 8 × $0.030 = $0.24/故事，可接受）。或加用户选项"完整版"vs"3min 短篇" |
| **派发** | AI-ML / Backend Sonnet xhigh，~15 min（grep O-2 截断逻辑 + 移除 + 单测）|
| **关联** | 用户旅程 DEC-011 短篇 ~18 shots — 这个目标应改为"短篇 ~18-30 shots"灵活范围 |

---

### ✅ Wave 7 已修 RISK-T14-8 — 🔴 P0 B1 顶层 watcher 漏监听 storyboard/image_preparation/image_generation/bgm stages，PM 救场 confirm-scenes 后 frontend 永远卡 /scenes（test14 5/13 15:38 实测）

| 字段 | 内容 |
|------|------|
| **现象** | PM curl `POST /confirm-scenes` 救场后 backend stage=`storyboard` + scenes_confirmed=true + Pipeline 进 Stage 4，但 frontend 卡 `/scenes` 显示"场景还在生成中"永远不跳走。直到 Pipeline 完成 stage=`completed` watcher 才 force-route 到 /preview |
| **真根因** | `CreateContent.tsx` L1167-1262 顶层 watcher 只 force-route 3 个 stages：character_ready / scenes_ready / completed。**漏监听 storyboard / image_preparation / image_generation / bgm 这 4 个 mid-pipeline stages**，frontend 一旦在 /scenes 就出不来直到 completed |
| **铁证** | backend stage='storyboard' progress=39 持续，frontend URL 仍 /scenes 显示 ScenePreview 占位符 ~2+ min 不动 |
| **影响** | 🔴 P0：常规用户 confirm-scenes 后应自动跳 /generating 看进度条 13+ min，但当前卡 /scenes 看转圈 = UX 灾难 |
| **修复方向** | watcher 加分支：scenes_confirmed=true && stage in {storyboard, image_preparation, image_generation, bgm} → push /generating |
| **派发** | Frontend Sonnet xhigh，~15 min。但 RISK-T14-7 修了（GET /story 返 scenes_json）→ hydrate reconcile 应该也会自动 push /generating，可能不用单独修这个 |
| **关联** | RISK-T14-7（GET /story endpoint 条件错）+ B1 watcher 设计漏洞 |
| **workaround** | 用户手动改 URL 从 /scenes 到 /generating |

---

### ✅ Wave 7 已修 RISK-T14-7 — 🔴 P0 Stage 3 完成但 `/chapters/1/story` endpoint 仍 404，frontend 无法显示场景列表（test14 5/13 15:33-15:34 实测）

| 字段 | 内容 |
|------|------|
| **现象** | Stage 3 ScreenplayWriter 15:33:44 完成（7 场戏 + 2085 字旁白），但 curl `GET /api/projects/{uuid}/chapters/1/story` 持续返回 404 `{detail: ...}`。frontend `/scenes` 页面卡在 "场景还在生成中..."转圈，无法显示场景列表 + 确认按钮 |
| **铁证** | (1) backend log `15:33:44 ScreenplayWriter ✅ 剧本生成完成 场景数:7 动作节拍:26` (2) backend access log `GET /chapters/1/story HTTP/1.1 404` × N 持续返回 (3) curl 直查 keys=['detail'] 无 scenes 字段 |
| **真根因（5/13 PM curl 验证后确定）** | **scenes_json 真的写入 DB** ✅ (POST `/confirm-scenes` 返回 200 + 完整 7 场戏含 narration/dialogue)。但 **GET `/chapters/1/story` endpoint 条件错** — 只在 `chapter.full_script` 写入时返 200，但 full_script 仅在 Stage 5 完成才写入。**两个 endpoint 不对称** — POST 看 scenes_json，GET 看 full_script |
| **影响** | 🔴 P0：Founder 卡在 /scenes 看不到场景列表 → 无法点确认 → R4-2 超时 1800s 后 Pipeline fail。生产无法上线 |
| **修复方向** | grep `app/api/projects.py` 或 `app/api/chapters.py` 的 `/chapters/1/story` endpoint 实现 — 应该在 `chapter.scenes_json` 非空时返回 scenes（即使 chapter.status 不是 completed）|
| **派发** | Backend Sonnet xhigh，~30 min 完成（grep endpoint + 修条件 + 单测 + 重启）|
| **关联** | B42（scenes from chapter.scenes_json）+ B58（scenes_confirmed DB field）|
| **短期救场（test13 时 PM 做过）** | PM 直接 curl `POST /projects/{uuid}/confirm-scenes` 解锁 R4-2 → Pipeline 进 Stage 4 |

---

### ✅ Wave 7 已修 RISK-T14-6 — 🟡 P1 confirm-characters 后路由绕路: `/characters → /generating → /scenes`（test14 5/13 15:30-15:33 实测）

| 字段 | 内容 |
|------|------|
| **现象** | Founder 在 `/characters` 点"确认角色继续" → URL 跳 `/generating`（卡进度条 3+ min）→ Stage 3 完成才跳 `/scenes`。Founder 期望 **直接** `/characters → /scenes`（中间不应走 /generating）|
| **铁证** | client.log 15:30:35 url=/characters + 15:30:41 url=/generating + 15:33+ url=/scenes |
| **真根因** | `StageC.tsx handleConfirmCharacters` 后 frontend push 到 `/generating`（或没 push 让 watcher 自动 push）— 应该 push 到 `/scenes`（提前进 scenes-preview 等 scenes_ready 完成）|
| **影响** | 🟡 P1 UX：用户 confirm 后看 3+ min 进度条不知道下一步是啥（loadingstate 应是"场景生成中"而非通用进度条）|
| **修复方向** | StageC handleConfirmCharacters: confirm 成功后 `dispatch SET_GENERATION_SUB_PHASE: scene-preview` + `router.replace('/scenes')`（让 hydrate 看到 scenesConfirmed=false → 显示"场景生成中"loading state）|
| **派发** | 🟡 P1 不阻塞，Wave 7 一起修。Frontend Sonnet xhigh ~15 min |

---

### ✅ Wave 7 已修 RISK-T14-4 — 🔴 P1 ETA 显示全面问题（Founder 5/13 强调深挖 — test14 实测 7 个子问题）

> Founder 5/13 16:09 明确："对对 ETA 的显示有的相关问题也要深挖出来"。PM 地毯式拆解 7 个 sub-issues:

#### Sub-Issue 4a: ETA 大跳变（信任感差）

| 时刻 | Backend 报 ETA | Founder 看到 frontend | 真实剩余（test13 实测对照）|
|---|---|---|---|
| 15:25 Stage 2 中 | **1005s (17 min)** | 17 min ⚠️ | ~26 min（偏短）|
| 15:30 Stage 3 启动 | 显示老数据卡 10% | ETA 12 min ⚠️ | ~22 min（偏短）|
| 15:34 Stage 3 中 | 855s (14 min) | 14 min ⚠️ | ~18 min（OK）|
| 15:42 Stage 4 中 | 690s (11.5 min) | - | ~10 min（OK）|
| 15:48 Stage 5 anchor | **510s 卡 6 min 不动** | 510s 卡死 ❌ | ~6 min（OK，但显示卡）|
| 15:50 18 shots 启动 | 300s (5 min) | 5 min ✅ | ~3 min（OK）|

**真现象**: ETA 反复跳变 17→12→14→11.5→8.5→5 min，user 看不到平滑递减 → 信任感差。

#### Sub-Issue 4b: ETA 在 stage 内不实时更新（卡死现象）

Founder 5/13 15:48 明确反馈："65% 卡死不动 6 min"。Backend `estimated_remaining_seconds=510s` 不变 6 min（pipeline_orchestrator 不 mid-stage update jobs 表，跟 RISK-T14-5-v2 同根因）。

#### Sub-Issue 4c: ETA "没了" 现象（frontend 显示问题）

Founder 5/13 15:33 反馈："ETA 已经没有了 进度条 10%"。可能 backend 报 0 或 null 时 frontend fallback 隐藏 ETA。**真根因待查 frontend ETA 渲染逻辑** (StageC.tsx 或 CreateContent.tsx)。

#### Sub-Issue 4d: ETA 算法没考虑各 stage 真实耗时差异

当前 STAGE_DURATIONS 配置（推测）：
- Stage 1 Outline: ~3 min（Sonnet 4.6 实测 137-180s）
- Stage 2 CharacterDesigner: 98s LLM + 4 min portrait 串行 = ~6 min
- Stage 3 ScreenplayWriter: ~213s 实测
- Stage 4 StoryboardDirector: ~236s 实测（并行 4 scenes）
- Stage 5 image_preparation: ~7 min（参考图串行 ❌ Wave 7 修后 ~2 min）
- Stage 5 image_generation: 360s (D2 修过，max_concurrent=3 折算)
- Stage 6 BGM: ~95s + FFmpeg 2s = ~97s

修复后**RISK-T14-10 参考图并行化**会让 Stage 5 image_preparation 从 7 min → 2 min，ETA 算法**必须同步更新** STAGE_DURATIONS。

#### Sub-Issue 4e: 是否包含 R4 等待时间？

R4-1 / R4-2 backend timeout 1800s（30 min），但**用户确认时间不算 Pipeline 工作时间**。当前 ETA 算法**可能把等待 timeout 也算进去** → 用户看 ETA "30 min" 但实际只需点确认。**待 grep estimate_remaining 算法 verify**。

#### Sub-Issue 4f: 不截断后 ETA 失效（RISK-T14-9 协同）

Founder 5/13 决策 "不截断 26→18 shots" 实施后，Stage 5 实际 shot count 可变（18-30）。**当前 ETA 算 18×60/3=360s 写死**，shot count > 18 时 ETA 偏短不准。修复后 ETA 算法**必须从 `actual_shot_count` 动态算**。

#### Sub-Issue 4g: Stage 切换瞬间跳变

Stage 3 完成（213s）→ Stage 4 启动（236s 估算）切换瞬间，backend update jobs.estimated_seconds 从老值跳到新值，用户看 **ETA 从 855s 突变到 690s**（差 165s）= 跳变。应平滑递减不应突变。

---

| 字段 | 内容 |
|------|------|
| **影响** | 🔴 P1 UX：ETA 是用户判断"要等多久"的关键信号。当前 7 个子问题加起来 = 用户对系统的时间预期完全不可信任 |
| **真根因汇总** | (1) 算法没考虑 max_concurrent 折算（部分修过 D2）<br>(2) backend stage 内不 mid-update（RISK-T14-5-v2 协同）<br>(3) frontend ETA 渲染逻辑（待查）<br>(4) STAGE_DURATIONS 写死不动态<br>(5) 含 R4 等待 timeout（待 verify）<br>(6) 切换瞬间跳变 |
| **修复方向** | (a) backend pipeline_orchestrator 每 5-10s update estimate_remaining + progress<br>(b) STAGE_DURATIONS 改成 dynamic（从 actual_shot_count / unique_locations / max_concurrent 算）<br>(c) frontend StageC.tsx / CreateContent.tsx ETA 渲染逻辑：null/0 时显示"约 N min"用 backend 最新估算<br>(d) ETA **不含 R4 等待 timeout**（只算工作时间）<br>(e) 切换 stage 时 ETA 平滑过渡（不突变）|
| **派发** | Backend Sonnet xhigh ~45 min（5 stage 算法重写 + mid-stage update + R4 等待排除）+ Frontend Sonnet xhigh ~15 min（渲染 fallback）。**Wave 7 P1 必修** |
| **关联** | RISK-T14-5-v2（mid-stage update）+ RISK-T14-9（不截断 shots）+ RISK-T14-10（参考图并行化让 STAGE_DURATIONS 必改）|

---

### ~~RISK-T14-5~~ 已订正 → RISK-T14-5-v2 — 🟡 P1 Backend stage 只在完成时 update，不在 mid-stage 频繁 update（UX 体验问题非数据 bug）

| 字段 | 内容 |
|------|------|
| **PM 5/13 15:34 自我订正** | 之前 P0 判断错误 — Stage 3 完成时 backend **真的会** `DB UPDATE ('scenes_ready', 35, '场景已生成，等待用户确认...')`（15:33:47 铁证）。RISK-T14-5 真 P0 撤回 |
| **真现象（降级 P1）** | Stage 3 ScreenplayWriter 跑 213s 期间，backend chapter_generation_jobs 表 `current_stage='character_ready' progress=10` 一直不变 → frontend 进度条卡 10% 3+ min + ETA 显示老数据 → Founder 体验"进度卡死"误判 |
| **真根因** | `app/services/pipeline_orchestrator.py` 在 Stage 启动 / 进行中**不更新** jobs 表，只在 stage 完成切换下一个时一次性 UPDATE |
| **影响** | 🟡 P1 UX：用户长时间（200-300s/stage）看进度卡死。Stage 4 StoryboardDirector ~4 min + Stage 5 ShotImageGenerator ~9 min 都会复现此 UX 问题 |
| **修复方向** | `pipeline_orchestrator.py` 在每个 Stage 启动时加 `await update_jobs(stage='X', progress=Y_start, message='正在执行...')`。或更细粒度：Stage 跑期间分阶段 progress 上涨（如 ScreenplayWriter 每场戏完成时 +1%）|
| **派发** | 🟡 P1 不阻塞 test14，可 Wave 7（test14 后再修），Backend Sonnet xhigh ~30 min |
| **关联** | 跟 RISK-T14-4 ETA 算法问题协同 — ETA 算法假设 mid-stage update 存在，但 backend 没在 update |

---

### ✅ Wave 7 已修 RISK-T14-13 — 🟡 P1 UX-2 一致性检查发现 warnings 但不展示给用户（test14 5/13 15:19:49 实测）

| 字段 | 内容 |
|------|------|
| **现象** | test14 15:19:49 backend log: `[ConfirmOutline] UX-2: 一致性检查完成, has_inconsistency=True, warnings=3` — Haiku LLM 检查 Stage 1 outline 发现 **3 条不一致 warnings**，但 backend **直接 ✅ 大纲已确认**继续走 Pipeline，**没把 warnings 内容输出 / 展示给用户** |
| **真根因（推测）** | `app/api/projects.py` confirm_outline 端点 UX-2 检查后**结果只记日志不返回 frontend** — 类似 B44 SafetyAdvisor UI 之前没修前的状态 |
| **影响** | 🟡 P1 UX：LLM 自检发现的"故事/角色/情节不一致"问题被静默忽略，用户在 Stage B 看不到提示。如这些 warnings 是真问题（如"老槐守夜人 6 旬但情节描述 25 岁"），用户应能在 Stage B 修正后再 confirm |
| **修复方向** | (a) confirm_outline endpoint response 加 `inconsistency_warnings` 字段（array of warning objects 含 type/message/affected_field）<br>(b) frontend Stage B "确认故事大纲" 页面在 warnings 非空时显示警告 banner + 高亮影响字段<br>(c) 不阻塞用户 confirm（"知悉并继续"），但需让用户看到 |
| **派发** | Backend Sonnet xhigh + Frontend Sonnet xhigh，~30 min（含 response schema 加 warnings + frontend warning banner UI）|
| **关联** | B44 SafetyAdvisor UI（已修类似模式），可借鉴实现 |

---

### ✅ Wave 7 已修 RISK-T14-3 — 🟢 P3 createUrl.ts 代码味道：重复定义 2 个相同 set

| 字段 | 内容 |
|------|------|
| **现状** | `frontend/src/lib/createUrl.ts` L200-207 `POST_CHAR_STAGES_FOR_CHARS` + L231-238 `POST_CHAR_STAGES` 内容**完全相同** = `[screenplay, storyboard, image_preparation, image_generation, bgm, completed]` |
| **影响** | 功能 OK，仅代码味道。两组维护时容易漂移 |
| **修复方向** | 提到函数外做一个 const，两个分支共用。10 行改动 |
| **派发** | 🟢 P3 — 不阻塞，下次 frontend 改 createUrl 时顺手 dedup |

---

## 🗂️ test13 实测完整 Bug 清单（2026-05-12 13:56-15:53，共 11 新条 + 3 关联升级）

> **来源**: project_uuid=`70eed512-f747-457d-922f-2b6fa68b9fd5`, chapter=1, idea="夜班护士发现每晚 9 点 12 分都有同一个穿深红色毛衣的中年女人..."
>
> **测试范围**: 从 13:56:36 创建 project 到 15:53:03 后端最后一次 cascade，含完整 Pipeline + /preview 浏览
>
> **总耗时**: 3475.9s (核心 30 min + 等待 28 min)
>
> **总成本**: ~$1.16 (Seedream $0.030/张 × 28 + Mureka 10 credits + Sonnet/Haiku 文本)
>
> **暴露 bug**: 8 P0 + 1 P1 + 3 P2 = 12 条（含已存在 BUG-URL-PINGPONG-CHARACTER-READY 升级 P0）
>
> **派活建议**: P0 frontend 路由家族（4 条同源）合并成 TASK-T13-FRONTEND-ROUTING；P0 DB 连接池（2 条同源）合派 Backend 1 行配置即修；其余按严重度散派

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP — 🔴 P0 character_ready 时前端不自动跳 /characters

**修复**: `CreateContent.tsx` L1136-1262 顶层 status watcher useEffect (5s 轮询 `/chapters/1/status`)，检测 `status.stage === "character_ready" && !confirmed` → `dispatch SET_GENERATION_SUB_PHASE: char-preview` + `router.replace('/characters')`。用 4 个 ref 避免 closure stale。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段 + DEC-018 (后续若需)。

| 字段 | 内容 |
|------|------|
| **现象** | 14:06:24 backend `current_stage='character_ready'`, `stage_message='角色设计完成，请确认角色和场景'`, `R4-1 开始等待用户确认 (超时 1800s)`，但 frontend 仍卡 `/generating` 页转圈，**用户根本看不到 /characters 页面**，也就无法点确认按钮 |
| **铁证** | backend log 14:06:24 设置 character_ready，14:06:26-14:13:02 R4-1 等待 148s，期间 frontend 持续 polling `/chapters/1/status` 200 OK 但**没触发 router.push('/characters')** |
| **真根因** | frontend `CreateContent.tsx` 没监听 `current_stage='character_ready'` 事件触发自动路由跳转。设计文档（`createUrl.ts` 注释）写的是"status === generating with stage === character_ready → /characters (if not yet confirmed)"但实际没实现 |
| **影响** | 🔴 P0：30 min 超时后 R4-1 抛 TimeoutError，整个 Pipeline 失败回滚 → **生产无法上线**。test13 靠 React infinite loop 副作用意外触发了 confirm-characters，否则会真超时 |
| **修复方向** | frontend useEffect 监听 status.stage 变化，character_ready 自动 router.push('/characters')。同样适用 scenes_ready / completed 两个 checkpoint |
| **关联** | 跟 BUG-T13-COMPLETED-NO-AUTO-JUMP / BUG-URL-PINGPONG-CHARACTER-READY (已存在) 同源 |

---

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 — 🔴 P0 ⚠️ 5/12 实测复现 5/11 BUG-URL-PINGPONG-CHARACTER-READY

**修复**: `createUrl.ts` L191-220 reconcileBackendVsUrl `urlStage="characters"` 分支加 `backendPastCharStage` guard — 仅当 `charactersConfirmed && backend真过 character_ready 进 screenplay+ 阶段` 才 bounce 到 /generating（POST_CHAR_STAGES_FOR_CHARS = {screenplay, storyboard, image_preparation, image_generation, bgm, completed}）。+ `StageC.tsx` L148-153 `charactersConfirmedRef` 同步 state 防 closure stale。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | 用户**手动改 URL 到 `/characters`** 后，frontend hydrate 几秒后**又被踢回 `/generating`**，构成 ping-pong |
| **铁证** | Founder 实测: 手动到 `/characters` → "正在加载你的故事" → 自动跳回 `/generating` |
| **真根因（深挖）** | frontend reconcile 逻辑某分支在 character_ready 状态下错误地把 URL 判定为"应该回 /generating"。具体在 `CreateContent.tsx` 的 hydrate reconcile 分支（看 createUrl.ts 注释 vs 实际实现 mismatch） |
| **5/11 PM 已挂账状态** | 标 🟡 P1，5/12 Coordinator 实测**严重程度升级到 🔴 P0**（用户根本无法停留 /characters 操作 = 比 5/11 描述更严重）|
| **影响** | 跟 BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP 共同导致 R4-1 checkpoint 体验灾难 |
| **修复方向** | 看 `CreateContent.tsx` reconcile 分支 + `createUrl.ts` 路由策略对照实现 |

---

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-REACT-ANTIPATTERN-STAGEC — 🔴 P0 React anti-pattern: setState in render

**修复**: `StageC.tsx` 4 处升级：(a) L728-740 useCallback 稳定 inline arrow `onUpdateCharacter`/`onUpdateScene` props（消除每渲染 new function ref 级联）+ (b) L957-973 CharacterPreview render-time `console.log("[B36]...")` 移到 useEffect deps `[characters.length, projectId, isLocked, paused, countdown]` + (c) L984-1003 useMemo `portraitMap` 消除 `resolvePortraitUrl()` 重复计算（render 时 2x → 1x）+ (d) L148-153 `charactersConfirmedRef` 同步 state 防 closure stale。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | DevTools console 红色 error: `Warning: Cannot update a component (CreateProvider) while rendering a different component (CharacterPreview). To locate the bad setState() call inside CharacterPreview, follow the stack trace as described in https://reactjs.org/link/setstate-in-render`，stack trace 指向 `at CharacterPreview (StageC.tsx:1181:11)` |
| **铁证** | Founder 截图给 Coordinator 看，明确 stack：CharacterPreview → StageC → div → CreateContent → CreateProvider → CreateStagePage (Server) → InnerLayoutRouter → RedirectErrorBoundary → RedirectBoundary → NotFoundBoundary → LoadingBoundary |
| **真根因** | `CharacterPreview` 组件在 render 阶段调 setState（更新 `CreateProvider` 的 context）→ 触发 React 强制重渲染 → 又 setState → infinite loop → 进 RedirectBoundary → 看起来"页面卡死且自动跳转"|
| **真位置** | `frontend/src/components/create/StageC.tsx:1181:11` — 必须看这一行的 setState 调用，移到 useEffect 或 event handler |
| **影响** | 🔴 P0：导致 BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP + BUG-T13-URL-PINGPONG-CHARACTER-READY-V2 的 ping-pong 现象 — **修这条可能同时修好那两条** |
| **修复方向** | 1. **先做 TASK-CLIENT-LOG-PIPE**（不然 Frontend 看不到其他 13 errors）<br>2. 看 StageC.tsx:1181 的 setState 调用 → 移到 useEffect / event handler / useMemo |
| **派发** | Frontend Sonnet 4.6 xhigh，必须先有 client log pipe 数据 |

---

### ✅ 已闭环 (Backend 17:30 + Frontend 17:48) BUG-T13-SCENES-CONFIRM-PATH-MISMATCH — 🔴 P0 ⚠️ 升级 5/11 BUG-SCENES-CONFIRM-MISSING（真根因深挖）

**Backend 17:30 修**: `app/api/projects.py` 新增 project-level alias `POST /{project_id}/confirm-scenes` 转发 chapter_number=1，原 chapter-level 兼容。
**Frontend 17:48 修 (C1-frontend)**: `StageC.tsx` `handleConfirmScenes` 改调 `POST /projects/{uuid}/confirm-scenes`（项目级，与 confirm-outline / confirm-characters 对称）替换原 chapter-level 调用。失败仍 non-fatal 静默继续。

| 字段 | 内容 |
|------|------|
| **现象** | scenes_ready checkpoint 时 frontend 不调 confirm-scenes endpoint，backend R4-2 等待 400s 直到 Coordinator 直接 curl 救场 |
| **真根因（5/12 Coordinator 实测深挖）** | endpoint **挂在 chapter 级**：`POST /api/projects/{uuid}/chapters/{n}/confirm-scenes`（`app/api/projects.py:685`），但 `confirm-outline` 和 `confirm-characters` 挂 **project 级**：`POST /api/projects/{uuid}/confirm-{outline,characters}`。**设计不对称** → frontend 没构造 chapter-level 路径调用 |
| **铁证** | Coordinator 试 `/api/projects/{uuid}/confirm-scenes` → 404，改成 `/api/projects/{uuid}/chapters/1/confirm-scenes` → 200 success<br>backend log: `14:35:01 [ConfirmScenes] ✅ 场景已确认 chapter=1`（手动 curl 后才解开 R4-2）|
| **影响** | 跟 BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP 同样可能导致 30 min 超时 → Pipeline 失败 |
| **修复方向（二选一）** | **A** Backend 加 alias `POST /api/projects/{uuid}/confirm-scenes`（保持向后兼容）<br>**B** Frontend 改成调 chapter-level 路径（推荐）<br>**C** 两个都做：endpoint 对称 + frontend 调正确路径 |
| **派发** | Backend + Frontend 协同 |

---

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-COMPLETED-NO-AUTO-JUMP — 🔴 P0 status='completed' 时前端不自动跳 /preview

**修复**: `CreateContent.tsx` L1186-1196（与 CHARACTER-PAGE-NO-AUTO-JUMP 同一顶层 watcher useEffect）— 检测 `status.status === "completed" || status.stage === "completed" || status.progress >= 100` → `router.replace('/preview')`。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | 14:58:20 backend Pipeline 完成，14:58:32 chapter status='completed', summary 写入，但 frontend 仍卡 `/generating` 转圈，用户**根本看不到成片** |
| **铁证** | backend log: `14:58:20 ========== Pipeline 完成 ==========` + `14:58:32 status='completed'`；Founder 实测：前端"故事显示生成完成，就是 /generating 还在转" |
| **真根因** | frontend 没监听 `chapter_generation_jobs.status='completed'` 事件触发 `router.push('/preview')`。`createUrl.ts` 设计文档明确写"status === completed → force /preview (URL stale)"，但**实际没实现** |
| **影响** | 🔴 P0：用户花了 30+ min 等 Pipeline 完成，**完全看不到成果** = 体验灾难。必须手动改 URL 到 /preview，或从 dashboard 点击进入 |
| **修复方向** | 跟 BUG-T13-CHARACTER-PAGE-NO-AUTO-JUMP 同源，frontend useEffect 监听 status 变化自动跳转 |

---

### ✅ 已修 (2026-05-12 17:30 Backend) BUG-T13-MYSQL-STALE-CONNECTION — 🔴 P0 阿里云 MySQL idle 长连接被 server close

| 字段 | 内容 |
|------|------|
| **现象** | 多次 backend 错误：`(pymysql.err.OperationalError) (2013, 'Lost connection to MySQL server during query')` |
| **铁证** | 14:59:58 第 1 次 + 15:53:03 第 2 次 + 15:56:32 第 3 次（Pipeline 完成后 idle 期间反复）|
| **真根因** | SQLAlchemy engine 没设 `pool_pre_ping=True` + `pool_recycle=N`。阿里云 MySQL 默认 `wait_timeout=28800`（8h）但内网中间设备可能 30-60 min 就 RST，连接池里的 stale connection 下次 query 必失败 |
| **影响** | 🔴 P0：单次失败用户感知"页面 500"。**更严重**：触发 BUG-T13-DB-POOL-EXHAUSTION cascade |
| **修复方向（1 行配置根治）** | `app/database.py` SQLAlchemy engine 加：<br>`pool_pre_ping=True,    # 每次 checkout 前 ping，stale 自动重建`<br>`pool_recycle=1800,     # 30min 主动回收（< MySQL wait_timeout）`<br>`pool_size=10, max_overflow=20`（顺手扩大池，防 cascade）|
| **派发** | Backend Sonnet 4.6 xhigh，10 min 完成（含 alembic 测试）|

---

### ✅ 已修 (2026-05-12 17:30 Backend) BUG-T13-DB-POOL-EXHAUSTION-CASCADE — 🔴 P0 connection pool 耗尽 cascade（衍生于 #6）

| 字段 | 内容 |
|------|------|
| **现象** | 15:02:20-21 集中爆发 16 个 `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00`，**包括 /api/auth/me 都 500** = 整个 backend 不可用 |
| **铁证** | backend log: 15:02:20.876/.891/.894/.896/.899/.901/.904/.906/.908/.910/.912/.915/.917/.919/.921 + 15:02:21.189 共 16 个 ERROR cascade |
| **真根因链** | 1. 14:59:58 第一次 stale connection（Bug #6 根因）<br>2. SQLAlchemy 试图重连，但 frontend 在不停 polling `/chapters/1/status`（每 2-3 秒一次）<br>3. 每次 retry 占一个新 connection，旧 stale connection 没释放<br>4. 15 个连接（pool_size=5 + overflow=10）**全卡住等 30s timeout**<br>5. 之后所有请求 500 cascade |
| **影响** | 🔴 P0：用户感知整个网站挂掉。当时 Founder 的 /preview 加载请求恰好撞上 → /api/auth/me 500 → 触发 BUG-T13-AUTH-FALSE-LOGOUT-ON-500 |
| **修复方向** | 跟 #6 同根因，1 行配置根治：`pool_pre_ping=True` + `pool_recycle=1800` |
| **关联** | #6 (root cause) + #11 (downstream effect) |

---

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-AUTH-FALSE-LOGOUT-ON-500 — 🔴 P0 frontend 撞上 5xx 误判 session 失效

**修复**: `AuthContext.tsx` 新增 `tokenInvalid` state（仅 401 真发生时 set true）+ `isLoggedIn` 改为 `!!user || (!!token && !tokenInvalid)`（5xx 时 user=null 但 token 还在 → 仍判 logged in）+ `attemptHydrate(isRetry)` 指数退避重试 (2/4/8/16/30s 上限) + login/register/logout 同步重置 tokenInvalid 状态。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | Founder 进 `/preview` → 显示 "正在加载你的故事" → **跳到 /login** → token 还在 → **跳到 /dashboard**。session 实际没失效，只是 backend 一秒钟挂了 |
| **铁证** | Founder 实测：14:58 完成后第一次进 /preview 时撞上 15:02:20 cascade，frontend `/api/auth/me` 拿到 500 → AuthContext 误判 |
| **真根因** | frontend `AuthContext.tsx` 区分 401/non-401 时**对 5xx 处理不当**。代码注释写"其他错误（500/超时/网络）保留 token，下次刷新重试"，但 `/preview` 页另一处 auth guard **没遵守**，看到 5xx 直接当作未登录 → router.push('/login') |
| **影响** | 🔴 P0：用户被误强制重新进入 dashboard，丢失 /preview 浏览状态 + 误以为 session 过期需重登 |
| **修复方向** | 1. AuthContext 统一规则：**只有 401 才 force logout**，5xx/超时/网络保留 token retry<br>2. /preview 和其他敏感页面用统一的 auth guard（不再各自实现）|
| **派发** | Frontend Sonnet 4.6 xhigh |

---

### ✅ 已修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-T13-PREVIEW-DIRECT-LOAD-SLOW — 🔴 P0 直接 URL 进 /preview 卡死，dashboard 点击 OK

**修复**: `CreateContent.tsx` L617-674 + L887-892 — BGM fetch 加入 hydrate Promise.all 4 路并行（status + storyboard + story + bgm），原本 BGM 在 chapter 之后串行；删除原串行 BGM fetch 块；+ 协同 #1 React anti-pattern 修复消除 render 卡死 + #5 Auth 修复消除 5xx 误踢级联 = 3 根因协同减小直链加载时间。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | 直接打开 `http://localhost:3000/create/{uuid}/preview` URL → 卡 "正在加载你的故事" 几分钟到打不开<br>从 dashboard 点击进入 → 正常加载 18 张 + BGM |
| **铁证** | Founder 实测对比：直接 URL 多次"打不开"；dashboard 点击 → 正常浏览（backend log 加载 18 张 shot + BGM 全部 200 OK）|
| **真根因** | frontend hydrate 路径 N+1 fetch + React anti-pattern + 重复请求；dashboard 点击有 stories[] 缓存跳过 hydrate |
| **影响** | 🔴 P0：用户无法直接分享/收藏 /preview URL；任何"通过链接进入"场景全部失效 |
| **关联** | 跟 BUG-DASHBOARD-PERF-N1 (P1) 同源问题升级 |
| **修复方向** | 跟 BUG-DASHBOARD-PERF-N1 一起修：合并 hydrate endpoint + dedup + 修 React anti-pattern (Bug #5) |

---

### ✅ 已修 (2026-05-12 17:30 Backend) BUG-T13-UX-2-LLM-JSON-TRUNCATED — 🟡 P2 confirm-outline 一致性检查 JSON 截断

| 字段 | 内容 |
|------|------|
| **现象** | 14:00:06 `WARNING [ConfirmOutline] UX-2: 一致性检查失败（非阻塞）: Unterminated string starting at: line 1 column 491 (char 490)` |
| **真根因** | UX-2 一致性检查的 LLM 调用走了**自己的 JSON 解析路径**，**没接入 `app/services/_llm_helpers.py`**（5/12 BUG-LLM-JSON-PARSE-MARKDOWN-UNCLOSED 修复时建的通用 helper）。Sonnet 长输出 max_tokens 截断 → 字符串没闭合 → JSON.parse 失败 |
| **影响** | 🟡 P2：非阻塞（UX-2 本身是 advisory check，失败 fallback OK），但**功能失效**（用户改动 outline vs 原始 outline 一致性检查没真跑）|
| **修复方向** | UX-2 改用 `_llm_helpers.parse_llm_json` 统一 helper |
| **派发** | Backend Sonnet 4.6 xhigh，5 min |

---

### ✅ 已修 (2026-05-12 17:30 Backend) BUG-T13-ETA-OVERESTIMATE — 🟡 P2 估算时间用串行老基线，没反映 max_concurrent=3 加速

| 字段 | 内容 |
|------|------|
| **现象** | 14:06:24 backend `estimated_seconds=1065` (=17.75 min) 推到前端，前端显示 "ETA 18 分钟"。但 Stage 5 18 shots 阶段实际 max_concurrent=3 真生效，吞吐 ~30s/张 = ~9 min 完成 |
| **铁证** | ETA 1065s vs Stage 5 18 shots 阶段实测 9 min（含参考图共 ~16 min），前端 ETA 高估 ~30% |
| **真根因** | `chapter_generation_jobs.estimated_seconds` 计算公式按串行 60s/shot 算，**没考虑 max_concurrent=3 (round 4 修复后实际生效)**|
| **影响** | 🟡 P2：用户体验差（"18 分钟"心理预期吓人）；BP 上 "实测 4.5 min" 不影响（因为是 18 shots 阶段独立测的，去除参考图）|
| **修复方向** | `pipeline_orchestrator.py` 估算逻辑：18 shots 阶段除以 max_concurrent；参考图阶段保持串行 |

---

### ✅ 已修 (2026-05-12 22:30 AI-ML 方案 D — Opus 4.7 xhigh) BUG-T13-T17-VALIDATOR-FALLBACK — 🟡 P2 Shot 6 关键道具缺失重试到上限后 fallback 保存

**修复**: AI-ML 自创方案 D 4 层防御（净化 D-1 + lenient prompt D-2 + 阈值放宽 D-3 + 文档防御 D-4）。Founder 5/12 22:00 plan mode 批准方案 D（淘汰 PM 给的 A/B/C 三选一，越权说明 + 选型理由详 DEC-025）。代码已实施 5/12 16:42 + 备份 `.bak-20260512-d3-pre`。**验收**: py_compile 双文件 PASS + pytest tests/test_architecture.py 7/7 PASS + 单元 29/29 PASS（test13 真数据回放）。⚠️ 端到端 LLM 真测待 @tester 跑 test14 验证 11% → 目标 < 2%。

详: `.team-brain/analysis/T17_VALIDATOR_FIX_ANALYSIS.md` (545 行 / 9 段) + DEC-025 + KEY_LEARNINGS 经验段"数据契约错配比 prompt 写得差更隐蔽"。

| 字段 | 内容 |
|------|------|
| **现象** | 14:55:09 `[T17] ⚠️ Shot 6 验证失败: 关键道具缺失过多: 2/2 (blurred edge of a monitor screen corner..., a second nurse..., the dark corridor window behind them...)` → `Shot 6 已达最大重试次数，使用当前结果` → 保存 |
| **真根因（5/12 AI-ML 5 层调用栈追踪锁定）** | **数据契约错配** — Stage 4 LLM 在 composition.foreground/background 字段写完整构图描述句（90-366 chars），pipeline_orchestrator.py:1068 把这两字段当 key_props 列表项喂给 Haiku 做严格匹配 → 长描述大概率返 false → 18 shots 11% 误判率（不是 prompt 写得差，不是模型限制，是数据契约错位）|
| **影响** | 🟡 P2：Shot 6 视觉质量打折但能用，不阻塞 Pipeline |
| **修复方向（已实施方案 D）** | D-1 ShotValidator 入口净化长描述（80c 截断保留前置核心名词）+ D-2 Lenient prompt（"AT LEAST ONE 可见即算 found"）+ D-3 阈值放宽（≥2 probes 且 100% 全失才 fail，部分缺失只 log）+ D-4 storyboard_prompts.py 加 COMPOSITION_FIELD_SEMANTICS_NOTE 文档常量（仅注释不注入 LLM prompt） |
| **派发** | AI-ML Opus 4.7 xhigh ✅ 完成 (代码 + 文档 + analysis 报告 + DEC-025) |

---

### BUG-DATA-CONTRACT-COMPOSITION-AS-PROPS — 🟢 P3 数据契约重构（D3 后续根治建议，2026-05-12 AI-ML 提）

| 字段 | 内容 |
|------|------|
| **来源** | AI-ML 5/12 D3 修复 BUG-T13-T17-VALIDATOR-FALLBACK 后提议（详 DEC-025 + analysis §8.1） |
| **现状** | `pipeline_orchestrator.py:1068-1080` 把 `composition.foreground/background/key_object` 当 key_props 喂 ShotValidator (T28)，但这三个字段是 Stage 4 LLM 写的构图描述句不是离散道具名 |
| **D3 已修** | ShotValidator 内部加 4 层防御（净化 D-1 + lenient prompt D-2 + 阈值放宽 D-3 + 文档防御 D-4）；当前不阻塞 Pipeline，test14 验证 11% → 目标 < 2% |
| **根治方案** | (a) Stage 4 LLM schema 加新字段 `narrative_props: ["phone", "monitor", "passport"]` 离散短名词列表；(b) `pipeline_orchestrator.py:1068` 改读 narrative_props 字段而非 composition；(c) ShotValidator D-1 净化层保留作 backward compat 兼容老 storyboard.json |
| **影响** | 改 4 处: `app/services/storyboard_director.py` Stage 4 prompt + JSON schema / `_validate_storyboard` 加 narrative_props 校验 / `app/services/pipeline_orchestrator.py:1068` 改读字段 / 老 storyboard.json 兼容（fallback to composition） |
| **优先级** | 🟢 P3 — D3 已兜底，不阻塞；本季度内做完即可 |
| **派发** | Backend (sonnet high)，工时 1-2 hr |
| **关联** | DEC-025 / `.team-brain/analysis/T17_VALIDATOR_FIX_ANALYSIS.md` §8.1 |

---

## 🗂️ test13 实测重要确认（pass，无需新派活）

✅ **max_concurrent=3 真生效**（同毫秒三连发铁证 14:46:15.507/.507/.508）→ DEC-020 / BP_SUPPLEMENT 第 6 节"M1 实测 4.5min"**不需要校准**
✅ **ARCH-1 修复生效**（chapter_scene_images 18/18 写入 14:55:55）
✅ **ARCH-4 修复生效**（api_cost_logs 写入 18 行 + DB tracker query 14:46:08）
✅ **BUG-MUREKA-BLOCK-EVENT-LOOP 没复现**（轮询 8s 间隔均匀，可降级或归档）
✅ **D.15/B39 aspect_ratio 透传**（'3:4' 真实 INSERT + 真实传 LLM）
✅ **B33 user_selected_mood 强制注入 LLM 约束**（'悬疑' 在 GenerateOutline 日志看到）
✅ **角色一致性**（3 角色 100% Schema 通过 + Seedream 18 shots 跨场景一致 — 待 Founder 主观确认）

---

### ~~BUG-PARALLEL-M1-NOT-EFFECTIVE — 🔴 P0~~ → 降级 🟡 P2 参考图阶段串行（by design，可优化）（2026-05-12 14:47 Coordinator 反转）

> **重大反转 14:47**：18 shots 阶段实测 max_concurrent=3 **真生效**！铁证：14:47:07/12/19 三张 shots（Shot 3/1/2，单张 52-64s）在 12 秒窗口内连续完成 = parallel=3 标志。之前 14:43 看到的"串行 60s/张"只是参考图阶段（character refs portrait+fullbody + scene anchors interior+exterior，by design 串行因为 portrait→fullbody 需 ref）。**根因确认为 #1**：参考图阶段 by design 串行，18 shots 阶段并行已生效。
>
> **结论**：DEC-020 / BP_SUPPLEMENT 第 6 节"M1 实测 4.5min" **不需要紧急校准**（仅适用 18 shots 阶段）。降级为 P2：可考虑参考图阶段也并行化（portrait/fullbody 跨角色之间无依赖，scene anchor 内→外有依赖但跨 location 也无依赖）。

---

### ~~BUG-PARALLEL-M1-NOT-EFFECTIVE — 🔴 P0~~ 原始描述（保留供历史参考）

#### Stage 5 图像生成完全串行，max_concurrent=3 没生效（2026-05-12 14:43 Coordinator 实测铁证）

| 字段 | 内容 |
|------|------|
| **现象** | TASK-PARALLEL-M1 round 4（PM 5/11 标记"实测 max_concurrent=3 生效，21 shots ~5 min"）在 5/12 test13 实测**完全失效**。Stage 5 图像生成回退到完全串行，**每张 ~60s 间隔串发 Seedream dispatch**，没有任何并行调用证据 |
| **铁证时序** | project_uuid=`70eed512-f747-457d-922f-2b6fa68b9fd5`<br>backend.log Seedream dispatch 时间戳：<br>`14:39:05` dispatch #1<br>`14:40:05` dispatch #2 (+60s)<br>`14:41:09` dispatch #3 (+64s)<br>`14:42:14` dispatch #4 (+65s)<br>`14:43:36` dispatch #5 (+82s 含 1 次 IncompleteRead 重试)<br>**5 次 dispatch / 271s = 平均 54s/张串行**。如果 max_concurrent=3 真生效应看到三连发 dispatch（同一秒或相邻秒），实际全部一次一张 |
| **跟 round 4 实测的反差** | round 4（5/11，21 shots ~5 min）= **14.3s/shot**（含并行加速）<br>本次 test13（5/12，24+shot 估算）= **54s/shot**（纯串行）<br>**慢 3.8x，跟 round 4 修复完全相反** |
| **可能根因（按概率排序）** | **#1（最可能）**：当前在跑参考图阶段（character refs portrait+fullbody + scene anchors interior+exterior），按设计**就是串行**（portrait→fullbody 需要前者作 ref，scene anchor 内→外需要前者作 ref）。round 4 并行只应用于 **18 shots 真生图阶段**，参考图阶段依然串行 by design<br>**#2**：round 4 修复**只在某条代码路径生效**（如 NB2 path），Seedream path 没接入并行<br>**#3**：max_concurrent=3 只是配置，实际 ImageGenerator/SeedreamGenerator 没真用 asyncio.gather/Semaphore<br>**#4**：5/12 之后某个 commit 把并行改坏了 |
| **诊断步骤（待 Backend 跑）** | 1. 跑完整 Stage 5 看 18 shots 阶段是否变并行（dispatch 时序变三连发）<br>2. 如果 18 shots 阶段也串行 → 根因 #2/#3/#4 之一，需 grep `pipeline_orchestrator.py` Stage 5 主循环<br>3. 如果 18 shots 阶段并行了 → 根因 #1，参考图串行 by design，**但应在 PENDING 加一条 P2：参考图阶段也应该并行（portrait/fullbody 跨角色之间无依赖，可以 3 路并行；scene anchor 同理）** |
| **影响** | - 用户感知延迟：参考图阶段串行 6 张 = 6 min（vs 并行 2 min），**前端 ETA 18 min 跟实测 24 min 接近**<br>- 跟 BP 4 层成本路线图 L1 工程并行化（DEC-020）冲突 — 如果 round 4 真没生效，BP 上写的"M1 已实测 4.5 min"是错的<br>- BUG-DASHBOARD-PERF-N1 + 这个 = 整体 UX 慢的累积 |
| **优先级** | 🔴 P0：BP 文档"已实测"的承诺被 5/12 实测推翻，必须立刻确认根因 + 重测，否则给 VC 看 BP 时数据会被打脸 |
| **派发计划** | 1. @Backend 跑 grep 确认 round 4 修复在哪条 path + 为什么参考图阶段串行（设计意图 vs 漏修）<br>2. @Tester 等本次 test13 跑完，统计 18 shots 阶段真实 dispatch 时序<br>3. 如根因是 #2/#3/#4 → @Backend 重新接入 max_concurrent=3 到 Seedream path<br>4. 文档更新：DEC-020 + BP_SUPPLEMENT 加风险注释 + COST_UX_ROADMAP_2026Q2.md L1 实测数据校准 |
| **关联** | - DEC-020 M1 工程并行化优先<br>- COST_UX_ROADMAP_2026Q2.md L1 章节<br>- BP_SUPPLEMENT_2026-04-23.md 第 6 节"M1 实测 4.5 min" 承诺<br>- 5/11 PENDING TASK-PARALLEL-M1 round 4 "实测 max_concurrent=3 生效"声明 |
| **派发状态** | ⏳ 待 test13 完整跑完后 PM 派发 |

---

### ✅ 已闭环 (2026-05-12 17:00) Backend ✅ + Frontend ✅ (含 PM 收尾 URL `/api` 约定修) — TASK-CLIENT-LOG-PIPE — 🔴 P0 基建（test13 实测 ROI 铁证升级 2026-05-12 16:00）让 Coordinator/Agent 能看到浏览器 client-side console（2026-05-12 14:18 Founder 提）

**完成状态**:
- ✅ Backend (5/12 17:30): `app/api/client_log.py` 新建 + `__init__.py` 注册，POST `/api/_client_log` 无 auth，写 `logs/client.log`
- ✅ Frontend A2-frontend (5/12 16:37): `frontend/src/app/layout.tsx` 注入 console proxy，全 7 类捕获（error/warn/onerror/unhandledrejection/React strict/Next hydration/network failure）
- ✅ Frontend A2 URL fix (5/12 17:01): hardcoded localhost → `NEXT_PUBLIC_API_URL` env var
- ✅ PM 收尾 (5/12 17:15): 修复 frontend agent 打破 `NEXT_PUBLIC_API_URL` 含 `/api` 后缀约定的双 /api 风险，layout.tsx 改 `${API_BASE} + '/_client_log'` + .env.{local,production} 加 `/api` 后缀
- ✅ Build verify: `var ENDPOINT = "http://localhost:8000/api" + '/_client_log';`（dev）/ Docker ENV 优先 `https://prefaceai.mov/api`（生产）

**待验证**: PM 重启 backend + frontend 后跑 console.error('test') → tail logs/client.log 看到记录。test14 时 client log monitor 拉起。

详 KEY_LEARNINGS 新经验"项目命名约定必须 grep 全代码再改 env var"（5/12 PM 学到）。

---

### 历史描述（保留参考）— TASK-CLIENT-LOG-PIPE — 🔴 P0 基建（test13 实测 ROI 铁证升级 2026-05-12 16:00）让 Coordinator/Agent 能看到浏览器 client-side console（2026-05-12 14:18 Founder 提）

> **2026-05-12 16:00 升级理由**：test13 实测时 Founder DevTools 显示 **14 errors + 18 warnings**，但 Coordinator 只能通过 Founder 截图看到 1 errors（React anti-pattern StageC.tsx:1181）+ 4 warnings（hydrate 404 routine），**剩 13 errors + 17 warnings 完全是黑箱**。可能是 P0 bug 也可能是 routine，**没 client log pipe = 永远诊断不全**。从"💡 基建提议"升级到 **🔴 P0 基建**。
>
> **特别**：本次 PENDING 新增的 BUG-T13-* 系列里，BUG-T13-REACT-ANTIPATTERN-STAGEC P0 派 Frontend 修之前**必须先做 TASK-CLIENT-LOG-PIPE**，否则 Frontend 没 console 数据无法定位其他 13+ errors。
>
> **强制要求（Founder 2026-05-12 16:00 加）**：修复后必须**全量捕获、不丢任何一条、不采样、不限频**。覆盖范围必须包含：
> - `console.error` / `console.warn` / `console.log`（可选，只在需要时开）
> - `window.onerror` 全局未捕获错误
> - `window.unhandledrejection` Promise rejection
> - React strict mode warnings（如 setState in render）
> - Next.js hydration mismatch warnings
> - Network failures（非 200/3xx 都记）
> - Source map 解析后的真实 file:line（不是 webpack-internal）
> - 测试时实际 errors 数（从今天 14/18 看，真实环境高峰期可能更高）— **目标：每一条都能被 grep 到，永远不再依赖 Founder 手动截图**

| 字段 | 内容 |
|------|------|
| **现状** | Coordinator 只能看 server 端日志（`logs/backend.log` uvicorn + `logs/frontend.log` Next.js dev server 编译/SSR），**完全看不到浏览器内 client-side `console.error/warn/log` + Network 请求详情 + React runtime warning**（这些都跑在用户浏览器进程里）|
| **痛点（test13 实测暴露）** | Founder 实测发现 `CharacterPreview StageC.tsx:1181 setState in render` React anti-pattern 这种 P0 bug 时，Coordinator 必须等 Founder 手动截图/复制粘贴 console error，才能定位真根因。每个 bug 都要拍照沟通 = 浪费 5-15 分钟/bug |
| **目标** | Coordinator/Agent 能像看 backend.log 一样实时看 browser console，无需 Founder 手动截图 |

#### 6 个方案对比（按 setup 复杂度排序）

| # | 方案 | 改动量 | 持久度 | 用户操作 | 推荐度 |
|---|------|-------|--------|---------|--------|
| **1** | **Backend `/api/_client_log` endpoint + Frontend `app/layout.tsx` 自动注入 console proxy `<script>`** | Backend ~5 行 + Frontend ~10 行 | ✅ 永久（所有页面所有刷新自动生效）| ❌ 零 | 🟢 **首选** |
| 2 | Backend endpoint 同上 + Console 手动粘拦截脚本（每次刷新重粘）| Backend ~5 行 | ⚠️ session 内 | ⚠️ 每次刷新粘 1 次 | 🟡 临时 |
| 3 | Chrome 启动加 `--remote-debugging-port=9222` + Python CDP client 接管 | 0 代码改动（client 用 Python `pychrome` / `playwright sync` 库）| ✅ 永久 | ⚠️ 每次启动 Chrome 加 flag + 不能用普通 user data dir | 🟡 调试用 |
| 4 | Service Worker 拦截 console 写入 IndexedDB，定期 sync POST | Frontend ~30 行（SW 注册）| ✅ 永久 + 离线缓存 | ❌ 零（首次注册需用户 reload）| 🟢 进阶 |
| 5 | 集成 Sentry / LogRocket / Highlight 等第三方监控 SaaS | Frontend ~5 行 SDK init + 注册账号 | ✅ 永久 + UI 看板 | ❌ 零 | 🟡 生产期再上 |
| 6 | 自写 Chrome 扩展（manifest v3 + content script 自动注入）| 30-50 行 manifest + content.js | ✅ 永久 | ⚠️ 装一次扩展（开发者模式加载）| 🔴 维护成本高 |

#### 各方案细节

**方案 1（推荐）：Backend endpoint + Frontend 自动注入**

Backend：
```python
# app/api/client_log.py
from fastapi import APIRouter, Request
router = APIRouter()

@router.post("/_client_log")
async def client_log(request: Request, payload: dict):
    log_path = "logs/client.log"
    with open(log_path, "a") as f:
        f.write(f"{payload.get('ts')} {payload.get('level')} {payload.get('args')}\n")
    return {"ok": True}
```

Frontend `app/layout.tsx` 注入：
```tsx
<script dangerouslySetInnerHTML={{
  __html: `
    (function() {
      ['error', 'warn'].forEach(level => {
        const orig = console[level];
        console[level] = function(...args) {
          fetch('http://localhost:8000/api/_client_log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              level, ts: new Date().toISOString(),
              args: args.map(a => a instanceof Error ? a.stack : String(a)),
              url: location.href
            })
          }).catch(() => {});
          orig.apply(console, args);
        };
      });
      window.addEventListener('error', e => console.error('[uncaught]', e.message, e.filename, e.lineno));
      window.addEventListener('unhandledrejection', e => console.error('[promise-reject]', e.reason));
    })();
  `
}} />
```

Coordinator 监控：`tail -F logs/client.log` + `Monitor` 工具实时跟踪

**方案 2：手动粘脚本**

适合"今天测试期不想改代码"，每次刷新页面后在 Console 粘：
```javascript
['error', 'warn'].forEach(level => {
  const orig = console[level];
  console[level] = function(...args) {
    fetch('http://localhost:8000/api/_client_log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ level, ts: Date.now(), args: args.map(a => String(a)) })
    }).catch(() => {});
    orig.apply(console, args);
  };
});
console.log('[console-proxy] installed');
```

**方案 3：Chrome CDP**

```bash
# 1. quit Chrome
osascript -e 'quit app "Google Chrome"'
# 2. 重启 Chrome 加 debugging port + 独立 user dir（避免污染主 profile）
open -a "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-debug-xuhua
# 3. Coordinator 用 Python CDP client（pychrome 或 playwright.sync_api）连接
#    pip install pychrome
#    import pychrome; browser = pychrome.Browser(url="http://127.0.0.1:9222")
#    tab = browser.list_tab()[0]; tab.start()
#    tab.set_listener('Runtime.consoleAPICalled', lambda **kw: print(kw))
```
代价：**当前 localhost:3000 session 状态丢失（要重新登录）**，且必须用独立 user dir

**方案 4：Service Worker**

Frontend 注册一个 SW，SW 在 install 时拦截 console，写入 IndexedDB。每 5s POST 到 backend `/api/_client_log_batch`。**好处**：离线时也能缓存，下次上线 sync。**坏处**：开发期 SW 调试麻烦

**方案 5：第三方 SaaS（Sentry 推荐）**

```tsx
// frontend/src/app/layout.tsx
import * as Sentry from "@sentry/nextjs";
Sentry.init({ dsn: process.env.NEXT_PUBLIC_SENTRY_DSN, tracesSampleRate: 0.1 });
```
Coordinator 通过 Sentry API 拉 issues，但**不是实时**（有 delay）+ 需付费账号。生产期上线必备，开发期不必

**方案 6：Chrome 扩展**

写一个简单 extension，content_scripts 注入 console proxy。装一次永久生效。但维护 manifest + 升级 v3 麻烦，**不推荐**

#### 实施建议

**短期（今天测试期）**：方案 2（手动粘）+ Backend 加 endpoint —— 不打扰前端代码，5 min 搞定

**中期（本周）**：方案 1 升级（Frontend 自动注入），永久基建，Founder 零操作

**长期（产品上线）**：方案 5（Sentry）+ 方案 1 双管齐下（Sentry 生产，方案 1 开发）

#### 派发建议

| 阶段 | 派发对象 | 工时 |
|------|---------|------|
| 方案 2 | Backend Sonnet xhigh | 15 min（加 endpoint）|
| 方案 1 升级 | Backend + Frontend Sonnet xhigh | 1h（前后端协同 + 测试）|
| 方案 5 | DevOps + Frontend | 半天（Sentry 账号 + SDK + 验证）|

#### 关联

- 跟今天 test13 实测发现的 React anti-pattern bug 直接相关（如果有方案 1，能立刻 grep `at CharacterPreview` 定位根因）
- 跟 BUG-DASHBOARD-PERF-N1 关联（也涉及前端 client-side 问题，monitor 起来后能验证 N+1 fetch 是不是真的来自前端）

---

### ✅ 已验 + 部分修 (2026-05-12 17:48 Frontend Opus 4.7 xhigh) BUG-DASHBOARD-PERF-N1 — 🟡 P1 Dashboard 加载 3-5 分钟（N+1 + 重复 fetch + dev mode 累加）（2026-05-12 13:48 Founder 实测）

**修复**: B1 验证 `AuthContext.refreshStories` 调 `GET /projects/`（单次返回所有 project，**已无 N+1**） + StoryCard 组件无独立 fetch + CreateContent hydrate 已有 `hydratedFor` + `isOurOwnPush` dedup + BGM 并行化（同 PREVIEW-DIRECT-LOAD-SLOW 修复）= 主要慢源已消除。Founder test14 复测 dashboard 加载时间，若仍 >30s 再深挖（可能 dev mode 编译累加，prod build 不复现）。详 TEAM_CHAT [2026-05-12 17:48] @frontend 段。

| 字段 | 内容 |
|------|------|
| **现象** | Founder 登录进入 dashboard，**等待 3-5 分钟才显示内容**。HTML 已 200 返回（7593B），Next.js `Compiled /dashboard in 171ms`，backend `GET /api/projects/ 200 OK`，但页面长时间空白（DashboardContent 是 `'use client'`，SSR 只输出 toast 容器空壳，必须 client hydration）|
| **真根因（3 条）** | **#1 N+1 query**：14 个项目（user_id=8: 29,28,27,26,25,24,23,22,21,20,15,14,2,1）每个再请求 4-5 个子 endpoint（projects/{uuid}, /chapters/1/story, /status, /storyboard, /bgm）= **~70 个串行 API 调用**<br>**#2 重复 fetch**：`/api/projects/` 至少 4 次；`/api/projects/{uuid}/chapters/1/bgm` 重复 **3 次/项目** = +42 冗余调用（前端 useEffect 缺 dedup）<br>**#3 SQL 双 logger**：每条 SQL 在 backend.log 重复打印 2 次（SQLAlchemy echo + extra handler 残留），让 100+ DB query 噪音翻倍（不影响延迟，但污染日志）<br>**叠加因素**：阿里云远程 MySQL RTT 50-200ms × 100+ query + Next.js `next dev`（比 build 慢 3-5x）+ 14 张封面图走 backend `/static/outputs/...` 而非 nginx |
| **量化数据** | - 项目数：14（user_id=8）<br>- `/api/projects/` 调用次数：≥4<br>- bgm endpoint 重复：3 次/项目<br>- 子请求总量：~70 串行 + 42 冗余<br>- DB query：100+ 次（含双 logger 噪音翻倍）<br>- 封面图：14 张 shot_01.png 通过 FastAPI `/static/outputs/` 加载（非 CDN/nginx）<br>- 用户感知延迟：**3-5 分钟** |
| **影响范围** | - C 端用户体验：**P0 灾难量级**（Founder 偏好"产品级 UI/UX"，3-5 min 不可上线）<br>- 受影响页面：`/dashboard`（DashboardContent.tsx）+ 任何展示项目列表的地方<br>- 项目越多，恶化越严重（线性 N+1） |
| **修复方案（按性价比排序）** | **🔥 短期（今天可做）**<br>1. **Frontend dedup fetch**：DashboardContent + 子组件 useEffect 加 dedup，bgm 3 次→1 次（`Frontend 0.5h`，立刻 -50% 请求）<br>2. **Backend 合并 endpoint**：新增 `GET /api/projects/?include=summary`（一次返回 projects + chapter status + cover_url + bgm 状态摘要），消除 N+1（`Backend 1-2h`，14 N+1 → 1 query）<br><br>**🟡 中期（本 sprint）**<br>3. dev → build && start 试一下（开发不便但快 3-5x，`5 min`）<br>4. 静态图改走 nginx 直出（生产已是，本地 dev 也走 Python 是历史遗留，`DevOps 1h`）<br><br>**🟢 长期（顺手清理）**<br>5. SQL 双 logger 修掉（`5 min`，仅日志清理）<br>6. 项目列表分页（>20 个项目时分页加载，目前 14 个还撑得住） |
| **派发计划（建议）** | 🔥 短期 1+2 一起派：<br>- @Backend Sonnet 4.6 xhigh：实现 `/api/projects/?include=summary` endpoint，返回 list + per-project summary（chapter_status, cover_url, bgm_state），保持向后兼容（不传 include 仍返回旧格式）<br>- @Frontend Sonnet 4.6 xhigh：DashboardContent + StoryGrid useEffect 改为单 fetch + dedup，移除 per-project bgm 调用<br>- @Tester：Playwright 实测 dashboard 首屏到内容渲染时间 ≤ 5 秒（接受 dev mode 慢 buffer） |
| **验收标准** | - dashboard 首屏到 React mount 完成 + projects 渲染 ≤ **5 秒**（dev mode）/ ≤ **2 秒**（build mode）<br>- backend access log 中 `/api/projects/` 调用 = 1 次/dashboard 加载<br>- bgm endpoint 调用 = 0 次（合并到 summary）/ 必要时按需 lazy load<br>- 14 个项目场景下，DB query ≤ **5 个**（vs 当前 100+）<br>- monitor 静默健康（无 ERROR） |
| **优先级理由** | 🟡 P1 而非 P0：dashboard 已能加载（不阻塞 create flow 测试），但 3-5 min 完全不能上线给真实用户。MVP 上线前必修。Founder 决定具体派发时机 |
| **派发状态** | ⏳ 待 Founder 拍板派发时机（当前 Founder 在测 create pipeline，monitor 在跑，不阻塞）|
| **关联** | - PM 已派的 TASK-PARALLEL-M1（图像生成并行化）独立，不重叠<br>- 跟数据层债 ARCH-1（chapter_scene_images 0 行）独立<br>- 跟 dev mode 慢这个事一起考虑，可能是顺手批 |

---

### ✅ BUG-LLM-JSON-PARSE-MARKDOWN-UNCLOSED — P0 Stage 2 crash (2026-05-12 Backend 已修)

| 字段 | 内容 |
|------|------|
| **现象** | Pipeline 失败于 Stage 2，`[CharacterDesigner] JSON提取失败, 响应长度: 13443 chars, 前200字: \`\`\`json` |
| **真根因** | LLM 长输出被 max_tokens 截断，结尾 ``` 缺失 → 正则要求闭合匹配失败 → fallback json.loads 因含 \`\`\`json 前缀失败 → ValueError |
| **Backend 状态** | ✅ 已修 — 新建 `app/services/_llm_helpers.py` 通用 helper，4 个 LLM 服务全部委托 |
| **影响范围** | Stage 1-4 全部（character_designer / story_outline_generator / screenplay_writer / storyboard_director） |
| **Tester 待验** | 重跑 test15（PM 重启 backend 后），Stage 2 不应 crash；极端场景：mock 超长 LLM 响应 |

**修改文件**:
- `app/services/_llm_helpers.py` 新建
- `app/services/character_designer.py` L254-260
- `app/services/story_outline_generator.py` L632-648
- `app/services/screenplay_writer.py` L1118-1143
- `app/services/storyboard_director.py` L1452-1458

---

### ✅ BUG-CLOTHING-SCHEMA-HAIKU-STR — P0 Stage 3 crash (2026-05-12 Backend 已修)

| 字段 | 内容 |
|------|------|
| **现象** | 用户改角色 clothing 为"米黄色毛衣" → adjust_character Haiku 输出 `clothing="米黄色毛衣"` (str) → Stage 3 `clothing.get(...)` AttributeError → Pipeline 失败 |
| **真根因** | Wave 6 B52-fix v3 reload 让 Stage 3 读 DB 数据；Haiku prompt 缺 clothing schema 约束 |
| **Backend 状态** | ✅ 已修 — 修复 1（3 文件 isinstance guard）+ 修复 2（Haiku prompt MANDATORY schema + 解析后 fallback） |
| **Tester 待验** | 复现场景：adjust 角色 clothing 为中文字符串（如"米黄色毛衣"） → 确认 → 跑 Pipeline → Stage 3 不应 crash |
| **Frontend 待修** | ⚠️ UI bug — Pipeline fail 后跳 /preview（应显示错误页）；backend 已返 `status="failed"`，前端未处理 |

**修改文件**:
- `app/services/screenplay_writer.py` L403, L864
- `app/services/storyboard_service.py` L771, L1093, L1255
- `app/api/projects.py` L1072-1080 + L1107-1116

---

## 🗂️ test12 实测完整 Bug 清单（2026-05-11 17:42-18:35）

**测试上下文**：
- Project: `a7bf046d-2471-4a28-88a1-ff79053526b8` 第42天的豆沙包（晨跑浪漫故事）
- Founder 操作：Stage 2 暂停 → adjust 林晓薇头发为亚麻青 → 确认 → Pipeline 跑完
- 总耗时: 2426.4s ≈ 40 min 26s（含中途 Shot 9 网络重试 4 次）
- 产物: 17/18 shots + BGM ✅
- 视觉验收: 7 张黑发 + 8 张亚麻青 + 1 张王阿姨正确黑发 + 2 张无林晓薇

| Bug ID | 优先级 | 类型 | 一句话描述 |
|--------|--------|------|----------|
| BUG-B52-CASCADE-V2-INCOMPLETE | 🔴 P0 | 后端核心 | Pipeline in-memory characters 永不 reload → adjust 后 Stage 3/4/5 用老黑发数据 |
| BUG-SCENES-CONFIRM-MISSING | 🔴 P0 | 全栈断裂 | 前端 ScenePreview 完整设计，后端 4 处断裂（端点/字段/Pipeline/heuristic）|
| BUG-URL-PINGPONG-CHARACTER-READY | 🟡 P1 | 前端状态机 | StageC text-gen poller 在 character_ready stage 仍 dispatch char-preview，URL 反复跳 |
| BUG-ETA-DISAPPEAR-AT-STAGE-EDGE | 🟡 P1 | 后端字段 | 进度条 ETA 在 Stage 4→5 边界丢失（estimated_remaining_seconds=null）|
| BUG-MUREKA-BLOCK-EVENT-LOOP | 🟡 P1 | 异步阻塞 | Stage 6 Mureka 同步轮询阻塞 event loop，backend /health 5s 超时 |
| BUG-PROGRESS-LIST-SKIP-SHOT | 🟡 P2 | 前端展示 | UI 进度列表跳过 Shot 11（实际成功，UI 没展示该条 message）|
| BUG-SHOT-RETRY-NETWORK-FRAGILE | 🟢 P2 | 网络韧性 | Shot 9 IncompleteRead 4 次重试全失败（阿里云网络抖动期间退避策略不够强）|

**Wave 5 已实测验证 PASS（不在 bug 清单）**:
- ✅ Wave 5 B46 partial_failure 兜底（Shot 9 失败不阻塞其他 17 shots）
- ✅ Shot 9 用户重生功能（18:24:18→18:25:16 一次成功）
- ✅ B57 fullbody 同步重生（17:46 portrait + 17:48 fullbody 亚麻青）
- ✅ B49 hydrate 后期稳定（pipeline 进 Stage 5 后 URL 不再回弹）
- ✅ B56 description 字段同步（UI 卡片显示"亚麻青色头发"）
- ✅ B47 mood 保"浪漫"（user_selected_mood + mood legacy 都是"浪漫"未滑温馨）
- ✅ B51 v2 fallback Scene 全覆盖（11 scenes → 18 shots，无 _is_fallback 标记）
- ✅ B49 characters_confirmed 真返（DB 字段 + serialize + hydrate 全链路通）
- ✅ BGM 生成完整链路（LUFS -14.2 dB / 静音检测 ✅ / meta_version=mixed）
- ✅ StageD UI 错误处理（红色 warning + 查看并重生按钮 + 失败 shot 占位卡片 + B46 自动定位）

---

### BUG-MUREKA-BLOCK-EVENT-LOOP — 🟡 P1 Stage 6 Mureka 轮询阻塞 event loop（2026-05-11 18:17 Monitor 抓到）

| 字段 | 内容 |
|------|------|
| **负责人** | Backend（主修） |
| **优先级** | 🟡 P1 — backend 不响应 health check 期间监控误报，但 Pipeline 业务实际正常推进 |
| **预计工期** | 1-2 hr |

#### 现象

Stage 6 BGM 生成期间（test12 18:16:32-18:18:43，约 2 分钟），backend `/health` 端点连续 5s 超时，Monitor v17 自动告警 `alive_no_health`。

#### 证据

backend log 18:16:48-18:18:11 Mureka 轮询：
```
18:16:48 Mureka task_id=138026592436227，开始轮询...
18:16:59 Mureka elapsed=8s  status=running
18:17:10 Mureka elapsed=16s status=running
18:17:20 Mureka elapsed=24s status=running
18:17:32 Mureka elapsed=32s status=running
18:17:43 Mureka elapsed=40s status=running
18:17:53 Mureka elapsed=48s status=running
18:18:11 Mureka elapsed=56s status=reviewing
18:18:22 Mureka elapsed=64s status=succeeded
```

curl /health 同期 `Operation timed out after 5004 milliseconds`。

#### 真根因

`app/services/music_generation_service.py` Mureka 轮询使用同步 `requests.get()` 或 `time.sleep()` 而非 `aiohttp` / `asyncio.sleep`，阻塞 FastAPI uvicorn 的 event loop（单 worker）。

#### Backend 实施清单

1. grep `music_generation_service.py` 中所有 `requests.\|time.sleep\|httpx.Client` 同步调用
2. 改为 `aiohttp` / `httpx.AsyncClient` / `asyncio.sleep`
3. 或者把整个 BGM 生成放到 `asyncio.to_thread()` / `run_in_executor()` 让 event loop 不阻塞

#### Tester 验收

1. ✅ Stage 6 期间 curl /health 持续返 200，不超时
2. ✅ Monitor 不再触发 alive_no_health 告警
3. ✅ Mureka 业务功能不退化（BGM 生成成功 + LUFS 检测 + meta_version 都正常）

---

### BUG-URL-PINGPONG-CHARACTER-READY — 🟡 P1 URL 反复跳 /characters → /scenes → /generating（2026-05-11 17:50 Founder 实测）

| 字段 | 内容 |
|------|------|
| **负责人** | Frontend（主修） |
| **优先级** | 🟡 P1 — test12 中症状自愈（pipeline 进 Stage 5 后 stage='character_ready' 不再返），但根因没修，下次 adjust 流程会再触发 |
| **预计工期** | Frontend 1 hr + Tester 0.5 hr |
| **Frontend 状态** | ✅ **Frontend Wave 6 完成** (2026-05-11) — StageC.tsx character_ready 分支加 state.charactersConfirmed guard |

#### 现象

test12 17:50 用户确认角色后，URL 在 4 个状态间反复跳：
```
/create/{uuid}/characters → /scenes (加载中) → /characters (回弹) 
→ /generating (10% 进度) → /characters (又回弹)
```

直到 pipeline 进入 Stage 5（stage 不再返 'character_ready'）才稳定到 /generating。

#### 根因（Frontend agent 18:10 已诊断）

`frontend/src/components/create/StageC.tsx:L456` text-gen poller 在 `status.stage === "character_ready"` 时**无条件** dispatch `SET_GENERATION_SUB_PHASE: "char-preview"`，但此时 `characters_confirmed=true`（用户已确认），不应该再跳回 char-preview。

#### 复现链

1. 用户点确认 → `confirm-characters` API → subPhase 改为 scene-preview → URL /scenes
2. hydration 重新触发（urlStage 变 scenes）
3. reconciledStage = "generating"（characters_confirmed=true + scenes_confirmed=false）→ router.replace("/generating")
4. URL 变 /generating → subPhase 设为 text-gen
5. text-gen poller 启动，status API 返回 stage="character_ready" → **L456 触发 → dispatch char-preview** → URL 变 /characters
6. /characters → hydration → reconciledStage="generating" → /generating → 回到步骤 4 循环

#### Frontend 实施清单

`StageC.tsx:L456` 改：

```typescript
if (status.stage === "character_ready") {
  // B49-followup: if characters already confirmed, do NOT revert to char-preview.
  if (state.charactersConfirmed) {
    console.log("[StageC] character_ready but charactersConfirmed=true, skipping char-preview re-entry");
    return; // continue polling
  }
  dispatch({ type: "SET_GENERATION_SUB_PHASE", payload: "char-preview" });
}
```

#### Tester 验收

1. ✅ 新 test → 确认角色后 URL 不反复跳，稳定在 /scenes 或 /generating
2. ✅ 第一次进 /characters → 确认后 → URL 不回弹
3. ✅ 浏览器刷新 /generating 不被弹回 /characters

---

### BUG-ETA-DISAPPEAR-AT-STAGE-EDGE — 🟡 P1 进度条 ETA 在 stage 边界丢失（2026-05-11 17:55 Founder 发现）

| 字段 | 内容 |
|------|------|
| **负责人** | Backend（主修 ETA 兜底）+ Frontend（unify 显示）|
| **优先级** | 🟡 P1 — UX 不严重但用户失去进度预期，体感差 |
| **预计工期** | Backend 1-2 hr |

#### 现象

test12 17:55 Founder 看到 /generating 进度条："剧本编写中"显示"预计还有一分钟"。**进度跳到 35% 后 ETA 文字消失**，只剩"AI 正在全力创作"。

#### 真根因

`app/services/job_manager.py:L45/L100/L206` `estimated_seconds: int | None = None` 字段允许 null。某些 stage 内部 callback 没传 estimated_remaining_seconds 参数 → job 表写入 null → 前端读到 null 就不显示。

历史: TASK-T6-FIXBATCH Wave 1.1（2026-04-28）曾改过 ETA 死代码（estimate_remaining 函数定义存在但 0 次调用）。当时 PM 没地毯式审查全 stage 覆盖。

#### Backend 实施清单

1. grep 所有调用 `progress_callback("stage_name", ..., estimated_remaining_seconds=...)` 的位置
2. 找出哪些 stage **没传**或传 None
3. 给所有 stage 加 ETA 默认计算（即使是粗略值，如 stage-based default）：

```python
STAGE_DEFAULT_ETA = {
    "story_generation": 60,
    "character_design": 80,
    "screenplay_writing": 120,
    "storyboard_drafting": 90,
    "character_reference": 180,
    "scene_reference": 90,
    "image_generation": 420,  # 18 shots × 23.5s
    "bgm_generation": 120,
}

def get_eta(current_stage, progress):
    base = STAGE_DEFAULT_ETA.get(current_stage, 60)
    remaining_in_stage = base * (1 - progress / 100)
    # 加上后续 stage 默认时间
    remaining_total = remaining_in_stage + sum(后续stage的default)
    return int(remaining_total)
```

4. 单调递减守护：`new_eta = min(last_eta - 1, new_eta)` 防止 ETA 跳涨

#### Tester 验收

1. ✅ 全 6 stage（story_generation → bgm_generation）期间 ETA 都显示不为空
2. ✅ ETA 单调递减，不跳涨
3. ✅ Stage 边界过渡时 ETA 不消失

---

### BUG-SHOT-RETRY-NETWORK-FRAGILE — 🟢 P2 Shot 9 IncompleteRead 4 次重试全失败（2026-05-11 18:10 监控发现）

| 字段 | 内容 |
|------|------|
| **负责人** | Backend（重试策略增强）|
| **优先级** | 🟢 P2 — 单张失败不阻塞 pipeline，partial_failure 兜底已 work，重生功能也 work，但**单批失败率偏高**值得优化 |
| **预计工期** | 1 hr |

#### 现象

test12 Shot 9 18:07:04-18:10:46 期间 4 次 IncompleteRead 全失败：
```
attempt 1: 557192 bytes read, 112338 more expected
attempt 2: 361712 bytes read, 309058 more expected
attempt 3: 794464 bytes read, 3146 more expected   ← 差点成功
attempt 4: 354472 bytes read, 295738 more expected
```

退避: 2s → 4s → 8s（共 14s），仍未度过网络抖动期。

最终：Shot 9 标记永久失败，pipeline 不阻塞继续跑（partial_failure=true 兜底 ✅）。后续用户手动点重生 → 18:24:18 一次成功。

#### 根因

阿里云 Seedream API 在 18:07-18:10 期间网络中断（下载图片中途断流），重试策略 2s/4s/8s 不足以等过抖动窗口。

#### Backend 实施清单（可选优化）

1. IncompleteRead 类网络错误退避加长：2s → 8s → 30s → 60s（4 次尝试）
2. 或者：固定时间退避不够，改用 **抖动+指数退避**：`base * 2^attempt + random(0, base)`
3. 失败时 log 加更详细的网络诊断（DNS 时间 / TLS 握手时间 / 下载速率）

#### Tester 验收

1. ✅ 模拟 IncompleteRead 注入 → 重试退避大于 30s 仍能恢复
2. ✅ Pipeline 跑完整轮 18 shots 失败率 < 2%

---

### BUG-B52-CASCADE-V2-INCOMPLETE — 🔴 P0 B52 Wave 5 修复不完整，2/5 层漏修（2026-05-11 18:20 PM 自查发现）

| 字段 | 内容 |
|------|------|
| **负责人** | Backend（主修 2 层）+ Tester（视觉回归）|
| **优先级** | 🔴 P0 — 用户改了角色外观，但生成的 18 shots 全用旧外观（亚麻青 → 实际全黑发） |
| **触发** | test12 实测，PM 自查 storyboard prompt 抽样发现 Shot 1/10 prompt 写 "black hair" |
| **预计工期** | Backend 2-3 hr + Tester 0.5 hr |
| **执行时机** | test12 视觉验收后立即启动（这个 bug 让 test12 视觉验收会失败）|

#### 完整证据链（铁证，2026-05-11 18:30 PM 视觉验收后修正）

**视觉真实分布**（Founder 18:28 看完 18 shots）：
| 发色 | Shot 编号 | 张数 |
|------|----------|------|
| ⚫ 黑发 | 1, 2, 3, 4, 5, 6, 15 | 7 张 |
| 🔵 亚麻青 | 9（重生）, 10, 11, 12, 13, 14, 16, 18 | 8 张 |
| ⚫ 黑发（char_003 王阿姨本就是黑发，正确）| 7 | 1 张 |
| ❓ 其他（无 char_001 林晓薇）| 8, 17 | 2 张 |

**Shot prompt 抽样分析**（核心发现）：

| Shot | prompt hair 描述 | 视觉 | 推断根因 |
|------|----------------|------|---------|
| 1 | `"Her black hair is pulled into a ponytail..."` 写死黑发 | 黑发 | Stage 4 LLM 用旧 `2_characters.json` 的 `hair_color=deep black` 写 prompt |
| 4 | `"dark hair pulled into a ponytail..."` | 黑发 | 同上，写"dark"（仍偏黑）|
| 2, 5, 6, 15 | 无 hair color 关键词，但 prompt 长（含 character description 注入）| 黑发 | character description 注入时 `physical.hair_color=deep black` 影响模型 prior，prompt 越复杂越漂移到 prior |
| 10, 11, 12 | 含 `"hair"` 但无颜色 | 亚麻青 | 参考图发色生效 |
| 13, 14, 16, 18 | 完全无 hair 关键词 | 亚麻青 | 参考图发色生效 |
| 7 | `"jet-black hair pinned neatly into a bun"` | 黑发 | **正确** — char_003 王阿姨本就是黑发 |

**关键修正之前判断**（PM 18:20 错误诊断）：

❌ 之前说："Stage 5 reference manager 18:00:07 覆盖亚麻青 portrait + fullbody 为黑发版本，所以 17 shots 全黑发"

✅ 真相：18:00:07 reference regen **没把亚麻青覆盖为黑发**（参考图层真实生效，多张 shot 是亚麻青 证实）。真问题在 **Stage 4 storyboard 写 prompt 时用旧 `2_characters.json`**（hair_color=deep black）：
1. **直接 hardcode**: Shot 1/4 prompt 文本直接写"black/dark hair"
2. **间接 prior 注入**: Shot 2/5/6/15 prompt 没写发色但 character description 块的 `physical.hair_color=deep black` 作为模型 prior 影响生成

**时间轴**（修正）：

| 时间 | 事件 | 数据源 | 真效果 |
|------|------|--------|--------|
| 17:42:23 | Stage 2 完成 → 写 `2_characters.json` | 文件 hair=deep black | - |
| 17:45:18 | Adjust API 改林晓薇为亚麻青 | **只改 DB chapter.characters_json，未改 `2_characters.json` 文件** | DB 真改 |
| 17:46:36 | R7-3 portrait 重生 → `char_001_portrait.png` | DB 数据 | 亚麻青 |
| 17:48:17 | B57 fullbody 重生 → `char_001_fullbody.png` | 新 portrait 作参考 | 亚麻青 |
| 17:57:13 | Stage 4 storyboard 生成 | **读 `2_characters.json`（黑发）** | 7 shots prompt 含 black/dark hair 描述 |
| 18:00:07 | Stage 5 reference regen | **真亚麻青（视觉证实）** | 参考图正确 |
| 18:03+ | Stage 5 shot 生成 | 亚麻青 reference + Stage 4 prompt（部分黑发）| **7 张黑发 + 8 张亚麻青 + 1 张正确**（王阿姨）|
| 18:24:18 | Shot 9 用户重生 | 同 Stage 4 prompt（无 hair color 写死）+ 亚麻青参考图 | 亚麻青 ✅ |

**抽样 Stage 4 prompt（铁证）**：
- Shot 1 image_prompt: `"Her **black hair** is pulled into a ponytail..."`
- Shot 10 image_prompt: `"...ponytail secured with a cream-white hair tie..."` + `"black hair"`
- 全 18 shots prompt 搜 `black hair` → **多处命中**，搜 `ash blue / linen blue / 亚麻青` → **0 命中**

**文件 mtime 对照（铁证）**：
- `2_characters.json` mtime = `2026-05-11 17:42:23`（adjust 17:45 后**从未更新**）
- `char_001_portrait.png` mtime = `2026-05-11 18:00:07`（被 Stage 5 reference manager **覆盖**为黑发版本）
- `char_001_fullbody.png` mtime = `2026-05-11 18:00:07`（同样被覆盖）

#### 修复矩阵（2026-05-11 18:35 第三次修正 — Explore agent very-thorough 完整审计后）

**🔥 终极真根因**: `pipeline_orchestrator.py:L380` `characters = await character_designer.design(outline)` 这个 **in-memory python 变量永不 reload**。R4-1 wait loop（L466-485）只轮询 `Project.characters_confirmed` 字段，**不从 DB reload `chapter.characters_json`**。adjust API 改完 DB 后，Pipeline 进程的 in-memory dict 仍是 Stage 2 老黑发数据。

| 层 | 状态 | 关键事实 |
|---|---|---|
| L1: adjust 改 DB chapter.characters_json | ✅ Wave 5 完成 | projects.py:L1027-1030 写入 |
| L2: ~~adjust 改 2_characters.json 文件~~ | ⚪ **无需修复** | grep 整个 services/*.py **无任何代码读 2_characters.json**，文件只为调试，不影响生图 |
| L3: portrait/fullbody 重生（用 DB 数据） | ✅ Wave 5 完成 | 17:46/17:48 亚麻青 |
| L4: Stage 5 reference manager 18:00:07 重生 | ✅ **真实生效** | 视觉证明仍是亚麻青；通过 `reference_images` 通道传到 Seedream |
| L5: **🔥 Pipeline 进程 in-memory `characters` reload** | ❌ **未修 — 真核心 bug** | pipeline_orchestrator R4-1 退出后**不从 DB reload**，继续用 Stage 2 老黑发数据跑 Stage 3/4/5 |
| L6: Stage 4 LLM 写黑发字眼 | ⚠️ **副效应** | 因为 L5 没修，Stage 4 LLM 拿老黑发 description 写 prompt，Shot 1/4/18 主动写"black/dark/jet-black hair" |
| L7: Seedream 模型先验漂移 | ⚠️ **次级问题** | 当 prompt 不写发色（Shot 2/5/6/15），模型回归"亚洲女生黑发"统计先验，参考图 attention 被稀释 |

→ **修 L5 就够了**（L6/L7 是副效应，L5 修好之后 LLM 拿到亚麻青 description，自然就不再写黑发字眼）。

#### Explore agent 关键证据（2026-05-11 18:35 输出，1500 字以内）

**1. 2_characters.json 不影响生图**（Explore very-thorough 已 grep 整个 services/*.py）：
- 文件存在仅为调试 / 测试 / 历史断点检查
- Stage 4 / Stage 5 / image_generator / seedream_generator **没有任何代码读它**
- → 我之前提出"adjust 同步写文件"是**错误修复方向**

**2. Pipeline in-memory `characters` 永不 reload**（铁证）：
- pipeline_orchestrator.py:L380 `characters = await character_designer.design(outline)` 拿 Stage 2 输出
- 这个 python dict **从此永不重新从 DB 拉取**
- R4-1 wait loop（L466-485）只 `select(Project.characters_confirmed)`，**不重读 chapter.characters_json**
- adjust API 改 DB 完成后，Pipeline 进程的 in-memory dict 仍是老黑发
- Stage 4 调用 `storyboard_director.direct(characters=characters)` (L538) 传入这个老 dict
- Stage 4 内部 L1189-1204 遍历 `characters.get("characters", [])` 拼 prompt — 看到的就是黑发

**3. Seedream 路径 不读 characters dict**：
- seedream_generator.py:L613-619 最终 prompt 只是 `shot.get("image_prompt", "") + text_overlay_instruction`
- 不做任何 character description 二次前置/后置注入
- → 只要 Stage 4 image_prompt 是亚麻青，Seedream 收到的就是亚麻青

**4. Stage 4 LLM 看到的 character data**（L1196-1199 B52 v1 fix）：
```python
physical_summary = char.get("description","").strip() or f"{hair_color} {hair_style}, ..."
```
- description 来自 in-memory characters → "深黑马尾辫 deep black hair in a neat ponytail"
- LLM 写出来的 image_prompt:
  - Shot 1: "Her black hair is pulled into a ponytail..."
  - Shot 4: "dark hair pulled into a ponytail..."
  - Shot 18: "jet-black ponytail..."
  - Shot 2/5/6/15: 简短没写发色，但 character data block 含黑发 description

**5. 参考图通道完好但被模型先验稀释**（Shot 2/5/6/15 黑发原因）：
- 18:00:07 reference regen 真亚麻青（视觉证实 Shot 10-14/16/18 是亚麻青）
- 但 prompt 越长越复杂（character description + 服装 + 场景 + 动作），模型对参考图的 attention 越弱
- 当 prompt 不写发色，模型回归"亚洲女生 + heather-gray top + 晨跑"的统计 cluster → 默认黑发
- 这是模型行为，**不能 100% 靠代码消除，但 L5 修复后 Stage 4 LLM 拿到亚麻青 description 会主动写"ash blue hair"，模型就跟着走**

#### 🎯 100% 确定真因（Shot 5 vs Shot 10 完整对比 — Explore agent 18:40 输出）

**Shot 5（黑发）vs Shot 10（亚麻青）完整 Seedream 输入对比**：

| 比对项 | Shot 5 | Shot 10 |
|--------|--------|---------|
| reference_images_log | char_001+char_002 fullbody + crossroads anchor | **100% 相同** |
| Seedream payload model | doubao-seedream-5-0-260128 | 同 |
| Seedream payload size/aspect | 3:4 → 1664×2218 | 同 |
| Seedream payload seed/temperature | **无（无随机性参数）** | 无 |
| sanitize_attempts | 0（一次过） | 0（一次过） |
| **image_prompt 含 black/dark/jet** | **"her black ponytail lifted behind her mid-stride"** | **完全没有任何颜色词** |
| 视觉结果 | 黑发 | 亚麻青 |

→ **唯一差异**是 Stage 4 image_prompt 文本：Shot 5 写了 `"black ponytail"`，Shot 10 没写。

**全 18 shots 黑发字眼扫描**（铁证）：

| Shot | image_prompt 关键词 | 视觉 | 应改否 |
|------|-------------------|------|--------|
| 1 | `"Her black hair is pulled into a ponytail"` | 黑发 | 改林晓薇 |
| 2 | `"cream-white-tied black ponytail"` | 黑发 | 改 |
| 3 | `"her dark ponytail"` | 黑发 | 改 |
| 4 | `"dark hair pulled into a ponytail"` | 黑发 | 改 |
| 5 | `"her black ponytail"` | 黑发 | 改 |
| 6 | `"Her jet-black ponytail"` | 黑发 | 改 |
| 7 | `"Her jet-black hair pinned neatly into a bun"` | 黑发 | **❌不改 — char_003 王阿姨本就黑发** |
| 9-14, 16, 18 | 无颜色词或仅 "hair" | 亚麻青 ✅ | 仍 OK |
| 15 | 无颜色词 | 黑发 | 模型先验漂移 — L6 加强 |

**Seedream 模型行为铁律（Explore 验证）**：在 prompt 文字 + 参考图冲突时，**text > reference attention weight**。Shot 5 文字明确说"black"，Seedream 涂黑（参考图亚麻青被忽略）；Shot 10 文字没颜色，Seedream 从参考图继承亚麻青。

→ **L5 修复 100% 能解决 Shot 1/2/3/4/5/6 类问题**，但有**2 个前提必须满足**：

1. **L5 必须同时做两件事**：
   - ① Pipeline in-memory `characters` reload（pipeline_orchestrator R4-1 退出后）
   - ② **Stage 4 storyboard 重跑**生成新 image_prompt（仅 reload 不重跑无效，因为 `4_storyboard.json` 已 hardcode "black"）

2. **Stage 4 prompt 模板必须真从 `physical.hair_color` 读** 而非 LLM 凭印象写"black"
   - 加 strict instruction: `"在 image_prompt 中提及发色时，必须严格使用 character.physical.hair_color 字段的值"`

3. **Shot 7 风险点**：char_003 王阿姨的"jet-black hair pinned into a bun"是**正确**的，不应被改。修复时按 character_id 精确替换，**仅改林晓薇（被 adjust 的角色）**

#### 必修代码改动（最小集 — 修 L5 一处即可主修）

**修复 L5 - 主修（必做，1-2 hr）**:

`app/services/pipeline_orchestrator.py` R4-1 wait loop 退出后（约 L485-490 附近）插入 reload 逻辑 + Stage 4 重跑触发：

```python
# R4-1 等到 characters_confirmed=True 后
# B52-fix v3 (2026-05-11): in-memory characters 必须从 DB reload，否则用户的 adjust 不会被 Stage 3/4/5 看到
if characters_confirmed:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Chapter).where(
                Chapter.project_id == project.id,
                Chapter.chapter_number == 1
            )
        )
        chapter = result.scalar_one()
        if chapter.characters_json:
            characters = json.loads(chapter.characters_json) if isinstance(chapter.characters_json, str) else chapter.characters_json
            logger.info(f"[Pipeline] B52-fix v3: characters reloaded from DB after R4-1 confirm")

            # 关键: 如果 chapter.characters_json 的 updated_at > 原 characters in-memory updated_at
            # → 必须**清空已有 Stage 4 storyboard 数据**让其重跑（否则旧 storyboard.json 含 hardcoded "black"）
            # 注意: 当前流程 R4-1 退出时 Stage 3/4 还没跑，所以不需要清空，只需要保证后续 Stage 3/4 用新 characters
            # 但如果未来允许"已跑完 Stage 4 后回退到 adjust"，必须加清空逻辑

# 之后所有 stage 都拿这个 fresh characters
```

**关键说明**: 当前 Pipeline 时序是 R4-1 退出 → Stage 3 → Stage 4 → Stage 5 → Stage 6 一次性顺序跑。L5 reload 在 R4-1 退出时执行，**Stage 4 storyboard 尚未生成**，所以 L5 修了之后 Stage 4 LLM 拿亚麻青 description 写新 image_prompt，问题自然解决。**无需额外触发 Stage 4 重跑**。

**修复 L6 - 防御性（✅ AI-ML 完成 2026-05-11）**:

`app/services/storyboard_director.py` Stage 4 LLM 系统 prompt 加 rule（强制每个 shot 提及发色）：

```python
# 在 Stage 4 system prompt 加:
"""
HAIR COLOR REQUIREMENT (MANDATORY):
For every image_prompt where a character appears with visible hair, you MUST explicitly mention their hair color exactly as specified in the character description (e.g., "ash blue ponytail", "jet-black bun"). 
This is REQUIRED even in close-up / wide shot / back view shots where hair might be off-frame — mention it as scene context.
Failure to mention hair color allows the image model to default to its statistical prior, breaking character consistency.
"""
```

**修复 L7 - 锦上添花（可选，纳入未来 Wave）**:

如果想 100% 消除模型先验漂移，可在 `seedream_generator.py:L613-619` 调用前加 character description 前置注入（参考 NB2 路径的 `build_identity_line_phase2`）。但 D.17 单一模型铁律 + Seedream 当前架构主张 prompt 干净，**建议先不做，看 L5+L6 是否够用**。

#### Tester 验收清单（修正版）

1. ✅ 新 test14：Stage 2 → adjust 改某角色发色（如金色/粉色）→ 确认 → Pipeline 跑完
2. ✅ Stage 4 storyboard.json 抽样 18 shots image_prompt grep 新颜色关键词 → **必须命中 ≥80%**（防御性 L6 修复后）
3. ✅ Stage 4 storyboard.json 抽样 grep "deep black" / "deep_black" → **0 命中**
4. ✅ Stage 5 输出所有有该角色的 shot 图片肉眼检查 → **必须 100% 新颜色**
5. ✅ backend log 含 `[Pipeline] B52-fix v3: characters reloaded from DB after R4-1 confirm`
6. ✅ DB chapter.characters_json 与 Stage 4 LLM 看到的 character description 完全一致

#### 之前 PM 诊断失误回溯（教训）

| 诊断 # | 时间 | 错误结论 | 真相 |
|--------|------|---------|------|
| 1 | 17:48 | "B57 fullbody 完整 PASS，Wave 5 完美闭环" | 参考图层确实修了，但 Pipeline in-memory data 没 reload 是漏修 |
| 2 | 18:20 | "Stage 5 reference 18:00:07 覆盖亚麻青为黑发，全 17 shots 黑发" | 反 — reference 是亚麻青，部分 shot 是亚麻青；只有 7 张黑发 |
| 3 | 18:25 | "Stage 4 读文件 2_characters.json，必修双层" | 错 — 没人读文件，Stage 4 读 in-memory dict |
| 4 ✅ | 18:35 | "Pipeline in-memory characters 永不 reload" | ✅ Explore agent 全审计确认 |

**PM 教训**: 不能拿"看到 prompt 含 black hair"就推断"Stage 4 读旧文件"。必须**追完整调用栈**：prompt 来自 LLM → LLM 输入 prompt 来自代码哪里拼 → 代码读哪个数据源 → 数据源何时被设置何时被更新。这次直接派 Explore agent very-thorough 才追到 in-memory dict 不 reload 的真因。

#### Backend 实施清单

**修复 1：adjust 端点同步写文件**（`app/api/projects.py` adjust_character 函数）

```python
# 现有：只更新 DB chapter.characters_json
# 新增：同步写文件 2_characters.json

output_dir = f"./output/{project_uuid}"
chars_file = f"{output_dir}/2_characters.json"
if os.path.exists(chars_file):
    with open(chars_file) as f:
        chars_data = json.load(f)
    # 更新对应角色
    for c in chars_data.get('characters', []):
        if c.get('id') == character_id:
            c['description'] = new_description  # Haiku 输出
            c['physical'].update(new_physical)  # 含 hair_color/style 等
            break
    with open(chars_file, 'w') as f:
        json.dump(chars_data, f, ensure_ascii=False, indent=2)
    logger.info(f"[AdjustCharacter] B52-fix: 已同步写 {chars_file}")
```

**修复 2：Stage 5 reference manager 不重生已存在的 adjust portrait**（`pipeline_orchestrator.py` Stage 5 启动前）

判断逻辑：
- 如果 `char_001_portrait.png` 存在且 mtime > `2_characters.json` mtime → 说明是 adjust 后重生，**不要再覆盖**
- 或者：用 DB 字段 `character_refs_generated_at` 记录 adjust 重生时间，pipeline 跳过 reference regen

```python
# pipeline_orchestrator.py 启动 Stage 5 前
for char in characters:
    portrait_path = f"{output_dir}/character_refs/{char['id']}_portrait.png"
    chars_json_path = f"{output_dir}/2_characters.json"
    if os.path.exists(portrait_path) and os.path.exists(chars_json_path):
        portrait_mtime = os.path.getmtime(portrait_path)
        chars_mtime = os.path.getmtime(chars_json_path)
        if portrait_mtime > chars_mtime:
            logger.info(f"[Pipeline] B52-fix: {char['id']} portrait 比 characters.json 新（adjust 重生过），跳过 Stage 5 reference regen")
            continue
    # 否则才重生
    await reference_image_manager.generate_character_portrait(char, ...)
```

**修复 3：Stage 4 storyboard 读 DB chapter.characters_json，不读文件**（`app/services/storyboard_director.py`）

- 现状：grep 看 storyboard_director 是否读 `2_characters.json` 文件 vs DB chapter.characters_json
- 改为：从 DB chapter.characters_json 读最新（adjust 后的）角色数据
- 关联 Wave 5 B52 修复（L1194-1199 physical_summary 优先读 description fallback physical）— 但 description 来源仍是文件不是 DB

```python
# 旧：from output/2_characters.json
# 新：from DB chapter.characters_json
async with SessionLocal() as session:
    chapter = await session.execute(
        select(Chapter).where(Chapter.project_id == project_id, Chapter.chapter_number == 1)
    )
    chars_data = json.loads(chapter.scalar_one().characters_json)
```

#### Tester 验收清单

1. ✅ 新 test14（idea 任选）→ Stage 2 完成后**改某角色头发为非默认色（如金色/粉色）** → 确认 → Pipeline 跑完
2. ✅ Stage 4 storyboard.json 抽样 5 shots image_prompt grep 新颜色 → **必须命中**
3. ✅ Stage 5 输出 shot 图片肉眼看角色发色 → **必须是新颜色**
4. ✅ `char_001_portrait.png` + `fullbody.png` mtime 在 adjust 之后**不被 Stage 5 覆盖**
5. ✅ `2_characters.json` 文件在 adjust 后 mtime 更新（physical 字段含新颜色）
6. ✅ DB chapter.characters_json 与文件 2_characters.json **完全一致**

#### 文档更新清单

- [ ] Wave 5 完成总结需更正：B52 标"**部分**完成（1/5 层）"
- [ ] TEAM_CHAT 18:20 自查记录已加（更正之前"PASS"判断）
- [ ] PM memory 教训：B52 之前以为"修了 description 同步就够"是错的，必须地毯式查所有读取路径

#### 风险

1. **历史 test 数据无法重测**：test12 a7bf046d 已跑完，不能重测验证修复。需新 test 项目
2. **B52 v1 (Wave 4) 修复是只读 description 不读 physical** — 但 description 来源也是文件没改，所以 B52 v1 也没真生效
3. **Stage 5 reference image manager 的"无条件覆盖"行为可能影响其他场景** — 修复时要保留"正常 pipeline 首次生成时正确写入"的行为，只在"adjust 后"跳过

#### 引用

- 完整证据 backend log: `/tmp/xhstory_backend.log` 17:45-18:00 段
- Stage 4 prompt 抽样: PM 自查 18:20
- test12 project: `a7bf046d-2471-4a28-88a1-ff79053526b8`

---

### BUG-PROGRESS-LIST-SKIP-SHOT — 🟡 P2 UI 进度列表跳过 shot 编号（2026-05-11 18:15 Founder 发现）

| 字段 | 内容 |
|------|------|
| **负责人** | Frontend（主修） + Backend（核 stage_message 写入频率） |
| **优先级** | 🟡 P2 — 仅影响 UX 展示，不影响产物，但用户会误以为 shot 失败 |
| **触发** | test12 实测 Founder UI 截图发现 |
| **预计工期** | Frontend 1-2 hr + Backend 0.5 hr 排查 |
| **执行时机** | test12 全 Pipeline 跑完后启动，跟 BUG-SCENES-CONFIRM-MISSING 一起批量修 |
| **Frontend 状态** | ✅ **Frontend Wave 6 完成** (2026-05-11) — generationLogRef + gap-fill 逻辑合成跳号条目 |

#### 现象（test12 实测，2026-05-11 18:13 截图）

UI 在 `/generating` 页面"已生成 N/18 个片段..."列表展示：

```
✅ 已生成 7/18 个片段...
✅ 已生成 8/18 个片段...
✅ 已生成 9/18 个片段（含失败）...   ← Shot 9 永久失败正确标注
✅ 已生成 10/18 个片段...
✅ 已生成 12/18 个片段...            ← 跳过了 11
✅ 已生成 13/18 个片段...
✅ 已生成 14/18 个片段...
```

→ Shot 11 在 UI 进度列表中**消失**，用户会误以为 Shot 11 失败/跳过。

#### 真实情况（backend log + 文件系统确认）

Shot 11 **生成成功，无任何问题**：
- `[SeedreamGenerator] ✅ Shot 11 生成成功 (1664x2218, 52.76s, sanitize_attempts=0)` @ 18:13:16
- `[ShotValidator] Shot 11: valid=True, reason=pass` @ 18:13:24
- `✅ Shot 11 保存: ./output/.../images/shot_11.png` @ 18:13:24
- 文件系统 `shot_11.png` 真实存在

→ **真实 shot 11 没问题，只是 UI 进度列表 stage_message 丢了一条**。

#### 根因假设（待 Frontend + Backend 联查）

**假设 1（最可能）**: Frontend polling `/status` 端点的 stage_message 列表是**事件流追加**的，但前端用某种 key dedup 后只取最新一条，导致 polling 间隙跨越 Shot 11 的 stage_message 被 Shot 12 覆盖。

- 复现窗口：Shot 9 失败延迟（18:10:46）→ Shot 10 完成 → Shot 11 完成（18:13:24）→ Shot 12 完成在 18:13:30 附近
- Shot 11 完成时刻与 Shot 12 完成时刻接近，polling 间隔（推测 1-3s）覆盖
- 前端可能用 `stage_message` 字符串去重，相同前缀"已生成 N/18"只保留最新 N

**假设 2**: Backend `stage_message` 写入策略：每次 shot 完成时更新 chapter_generation_jobs.stage_message 为"已生成 N/18 个片段..."，但**写入太快被下一次覆盖**，前端 polling 抓不到中间值。

- 检查 `app/services/job_manager.py` 或 `pipeline_orchestrator.py` 中 stage_message 写入频率
- 是否每个 shot 完成都 `await session.commit()` 写一次？还是 batch 写？

**假设 3**: 前端 `GenerationProgressList`/`ShotProgressLog` 组件渲染逻辑用 React key 不当，相邻同前缀 message 被 React 复用导致丢失。

#### Frontend 实施清单

1. **定位渲染组件**: grep `已生成.*个片段` 在 `frontend/src/components/create/` 找展示组件
2. **检查 message 累积逻辑**: 是 polling 每次拉最新 stage_message + push 到 React state 数组？还是有去重？
3. **React key 检查**: 列表 key 是否用 message 字符串而非 unique id（同前缀会冲突）
4. **测试用例**: 模拟连续 18 次 stage_message 更新（每 50ms 一次），看 UI 是否每条都展示

#### Backend 实施清单

1. **stage_message 写入策略**: `pipeline_orchestrator.py` Stage 5 主循环每个 shot 完成后调用 `progress_callback` 是否每次都写 DB？
2. **写入频率优化**: 如果两个 shot 完成时间接近（<polling 间隔），第一次写入会被第二次覆盖。可能需要把 stage_message 改成**事件追加表**（chapter_generation_events）而非单字段覆盖
3. **临时方案**: 给 stage_message 加序号或时间戳，让前端能识别去重

#### Tester 验收清单

1. ✅ 新 test13 跑完 18 shots，UI 列表显示 1, 2, 3, ..., 18 **全部 18 条**，不跳号
2. ✅ 即使 shot 完成时间接近（如并发返回），UI 也能展示全部
3. ✅ 失败 shot 标注"（含失败）"行为不变（B58 不退化）

#### 引用

- test12 截图来自 conversation 2026-05-11 18:13
- Shot 11 完成 log: `/tmp/xhstory_backend.log` 18:13:16-24
- Shot 9 永久失败: BUG-SCENES-CONFIRM-MISSING 同次测试

---

### BUG-SCENES-CONFIRM-MISSING — 🔴 P0 场景确认环节后端断裂（2026-05-11 18:10 Founder 确认）

| 字段 | 内容 |
|------|------|
| **负责人** | Backend（主修） + Frontend（hydrate 改字段） + Tester（回归） |
| **优先级** | 🔴 P0 — 用户失去场景调整权（设计上应停留，实际跳过） |
| **触发** | test12（project a7bf046d-2471-4a28-88a1-ff79053526b8）Founder 实测发现 scenes 页面被跳过；Founder 明确反驳 PM 之前"by-design"判断 |
| **历史** | B42 P1（2026-05-09）+ B50 P1（2026-05-11）已两次质疑，PM 之前未补完后端 |
| **预计工期** | Backend 0.5-1 天 + Frontend 0.5 天 + Tester 0.5 天 |
| **执行时机** | test12 全 Pipeline 跑完 + Wave 5 其他验收完成后启动 |
| **Frontend 状态** | ✅ **Frontend Wave 6 完成** (2026-05-11) — hydrate 改读真字段 + ScenePreview 60s 倒计时 + handleConfirmScenes 调真 API |

#### 背景（地毯式回溯证据，Explore agent 2026-05-11 18:08 完整审查）

**前端层（设计完整且代码存在）**：

| 证据 | 文件:行号 |
|------|----------|
| `scene-preview` sub-phase 定义 | `frontend/src/types/create.ts:221` GenerationSubPhase 类型 |
| `ScenePreview` 组件完整存在 | `frontend/src/components/create/StageC.tsx:1140`（约 80 行） |
| UI 文案"场景确认 / 确认场景描述，或修改后开始绘制" | `StageC.tsx:1221-1223` |
| URL `/scenes` 是 6 个 URL stage 之一 | `frontend/src/lib/createUrl.ts:42-57` URL_STAGES |
| `CONFIRM_SCENES` reducer | `frontend/src/contexts/CreateContext.tsx:255-256` |
| `handleConfirmScenes` callback | `StageC.tsx:645-646` |
| 20 秒自动倒计时确认（R6-4 改动，原 10 秒） | `StageC.tsx` ScenePreview useState(20) |
| createUrl 判断分支 `if (!scenesConfirmed && urlStage === "scenes")` | `createUrl.ts:180` |

**后端层（完全断裂 — 4 处缺失）**：

| 缺失项 | grep 证据 |
|--------|----------|
| `POST /confirm-scenes` API 端点 | grep `confirm.scene\|confirm-scenes` 在 `app/api/projects.py` 全文 → **0 结果** |
| DB `scenes_confirmed` 字段 | grep 在 `app/models/project.py` `app/models/chapter.py` → **0 结果** |
| `app/schemas/project.py` scenes_confirmed 字段 | grep → **0 结果** |
| Pipeline Stage 3 完成后 pause/wait 用户确认 | `pipeline_orchestrator.py:517-518` Stage 3 写完 scenes_json 后**直接进 Stage 4**，无 callback("scenes_ready") + 无轮询等 scenes_confirmed |
| 类比 R4-1（characters_confirmed 轮询） | `pipeline_orchestrator.py:450-492` characters 有 1800s 等待，**scenes 完全没有对应逻辑** |

**前端 hydrate 用 heuristic 兜底（注释自承认）**：

`frontend/src/app/create/CreateContent.tsx:682-683`:
```typescript
// scenesConfirmed: backend has no scenes_confirmed field yet, infer from stage
const scenesConfirmed = backendStage === "screenplay" || backendStage === "storyboard" || ...
```
→ 用户根本没机会点确认，pipeline 进 screenplay 后前端就把 scenesConfirmed 推断为 true。

**TEAM_CHAT 历史质疑（PM 之前两次没补完）**：

- **B42 P1（2026-05-09 18:01 Founder）**: "scenes 确认是否真有停留？（Founder 怀疑 PM 验证不全）" — TEAM_CHAT.md:2588
- **B50 P1（2026-05-11 15:42 Founder test11）**: "Scenes 确认页面用户没看到内容就被跳过" — TEAM_CHAT.md:3054-3077
- **B50 根因分析**: B49 + B42 双 bug → 用户看不到 ScenePreview → 20s 倒计时自动 dispatch CONFIRM_SCENES → 跳 shot-gen
- **PENDING B49 follow-up**: "scenesConfirmed 推断（同类问题，但目前 backend 无 `scenes_confirmed` 字段）" — PENDING.md:3045
- **D.14 背景**: "backend confirmed_outline / characters_confirmed / scenes_confirmed 已写入" — PENDING.md:1782（此处是文档"期望状态"，非实际 DB 字段）

**Wave 5 修复盲点（PM 自查）**：

Wave 5（2026-05-11）修了 B49（URL 不回弹 /characters）+ B50（ScenePreview 不空白）+ B47/B51v2/B52/B56/B57，**但完全没补**：
- ❌ Backend `POST /confirm-scenes` 端点
- ❌ `scenes_confirmed` DB 字段 + Alembic 迁移
- ❌ Pipeline Stage 3 后 pause/wait 逻辑
- ❌ Frontend 改读真字段而非 heuristic

→ 即使 B49/B50 修了，pipeline 不等用户 + 前端 heuristic 推断 scenesConfirmed=true，结果 test12 用户**根本看不到 scenes 页面**直接跳到 /generating。

#### Backend 实施清单

**DB 迁移（Ben 或 Backend 主修）**：

```sql
ALTER TABLE projects ADD COLUMN scenes_confirmed BOOLEAN NOT NULL DEFAULT FALSE;
```
- 走 Alembic：`alembic revision -m "add_scenes_confirmed"` + 写 upgrade/downgrade
- 部署时按 `feedback_shared_db_only.md` 走阿里云共享 MySQL，**不自建本地 DB**

**Model 字段**（`app/models/project.py`）：

```python
scenes_confirmed = Column(Boolean, default=False, nullable=False)  # R4-2: 用户确认 scenes 后设为 True
```

**Schema 字段**（`app/schemas/project.py`）：

```python
class ProjectDetail(BaseModel):
    ...
    characters_confirmed: bool = False
    scenes_confirmed: bool = False  # B58: 场景确认状态
```

**Serialize 暴露**（`app/api/projects.py:204` 附近）：

```python
scenes_confirmed=bool(project.scenes_confirmed),
```

**新 API 端点**（`app/api/projects.py`，参照 confirm-characters L648）：

```python
@router.post("/{project_id}/chapters/{chapter_number}/confirm-scenes")
async def confirm_scenes(
    project_id: str,
    chapter_number: int,
    payload: ConfirmScenesRequest,  # 可携带用户修改后的 scenes 数组
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. 验证 project 归属 + chapter 存在 + scenes_json 非空
    # 2. 如 payload 含 modified_scenes → 更新 chapter.scenes_json（合并用户修改）
    # 3. project.scenes_confirmed = True
    # 4. 触发 pipeline_orchestrator 继续 Stage 4（解开 R4-2 轮询锁）
    # 5. 返回 200 + 新 scenes
```

**Pipeline 等待逻辑**（`app/services/pipeline_orchestrator.py:517-518` 附近，参照 R4-1 L450-492）：

```python
# Stage 3 完成后
await checkpoint_callback("scenes_json", scenes_json)
await progress_callback("scenes_ready", "场景已生成，等待用户确认")

# R4-2: 轮询 DB Project.scenes_confirmed，最多等 1800 秒
max_wait_seconds = 1800
poll_interval = 2
elapsed = 0
while elapsed < max_wait_seconds:
    async with SessionLocal() as session:
        result = await session.execute(
            select(Project.scenes_confirmed).where(Project.uuid == project_uuid)
        )
        if result.scalar():
            break
    await asyncio.sleep(poll_interval)
    elapsed += poll_interval
else:
    # 超时降级：30 min 仍未确认 → 自动继续（保持 R4-1 同款兜底）
    logger.warning(f"[Pipeline] R4-2: scenes_confirmed 等待超时 {max_wait_seconds}s, 自动继续")

# 进 Stage 4
```

**ConfirmScenesRequest schema**：

```python
class ConfirmScenesRequest(BaseModel):
    modified_scenes: Optional[List[SceneModel]] = None  # 用户修改后的 scenes（可选）
```

**重置逻辑**（参照 R4-1 重置 characters_confirmed L684-685）：

```python
# 每次启动 pipeline 时重置 scenes_confirmed（避免上次残留）
project.scenes_confirmed = False
```

#### Frontend 实施清单

**1. 改 hydrate scenesConfirmed 读真字段（`CreateContent.tsx:682-683`）**：

```typescript
// 旧（heuristic）:
// const scenesConfirmed = backendStage === "screenplay" || ...

// 新（B58 follow-up）:
const scenesConfirmed = project.scenes_confirmed === true;
```

**2. `ProjectDetailResp` 类型加字段（CreateContent.tsx:482 附近）**：

```typescript
characters_confirmed?: boolean;
scenes_confirmed?: boolean;  // B58
```

**3. `handleConfirmScenes` 调真 API（`StageC.tsx:645-646`）**：

```typescript
const handleConfirmScenes = useCallback(async (modifiedScenes?: Scene[]) => {
  await fetch(`/api/projects/${projectId}/chapters/1/confirm-scenes`, {
    method: 'POST',
    body: JSON.stringify({ modified_scenes: modifiedScenes }),
    headers: { 'Content-Type': 'application/json' },
  });
  dispatch({ type: "CONFIRM_SCENES" });
}, [projectId]);
```

**4. ScenePreview 编辑能力（StageC.tsx:1140 ScenePreview 组件）**：

- 当前 ScenePreview 只展示 scenes 列表（read-only）
- B58 要求支持用户**修改 description / description_zh 字段**（参照 outline 编辑模式）
- 修改后传 `modifiedScenes` 给 onConfirm
- 编辑模式 UX：点 "调整" 按钮 → textarea 可编辑 → "保存修改" → 调 confirm-scenes 传 modified_scenes

**5. 20 秒倒计时策略评估**：

- 当前 R6-4 设计是 20s 自动 confirm → 在新设计下可能太短（用户来不及读完所有 scenes）
- 建议改为：默认**不倒计时**，用户主动点 "确认场景，继续" 才推进
- 或保留倒计时但延长到 60-90s（参照 outline 确认页用户停留时长）
- 待 Founder 决策最终 UX

#### Tester 验收清单

**正向 case**：
1. ✅ 跑新 test13（idea 任选）→ Stage 2 后看到 /characters 角色页 → 确认 → Stage 3 完成后**真停留 /scenes 页面**
2. ✅ /scenes 页面显示所有 scenes 的中文 description
3. ✅ 用户点 "调整" 修改某 scene description → 保存 → backend chapter.scenes_json 真有用户修改的内容
4. ✅ 用户点 "确认场景，继续" → backend project.scenes_confirmed=true → pipeline 解锁 Stage 4 启动

**边界 case**：
5. ✅ 用户在 /scenes 页面刷新浏览器 → hydrate 真读 `project.scenes_confirmed=false` → 仍停留 /scenes（不被 heuristic 错误推断为 true）
6. ✅ 用户关闭浏览器去吃饭 30 min 内不点确认 → pipeline 1800s 超时后自动继续（不卡死）
7. ✅ characters_confirmed=false 时 scenes_confirmed 也必须是 false（不能跳过角色确认直接确认场景）
8. ✅ 重新启动 pipeline（用户在 StageD 点重生）→ scenes_confirmed 被重置为 false

**回归 case**：
9. ✅ Wave 5 B49/B50 修复不退化（URL 不回弹 /characters / ScenePreview 不空白）
10. ✅ characters_confirmed = R4-1 流程仍正常（B49 不被新代码破坏）

#### 文档更新清单

- [ ] `.team-brain/decisions/DECISIONS.md` — 加 DEC-021 "场景确认作为用户旅程第三停留点"（修订 DEC-011 用户旅程）
- [ ] `xuhua_story/CLAUDE.md` 用户旅程章节（Stage B 改为：outline 确认 + characters 确认 + scenes 确认 三停留点）
- [ ] `.team-brain/handoffs/PENDING.md` 删除本 BUG 条目
- [ ] `.team-brain/TEAM_CHAT.md` 追加修复完成通知

#### 风险

1. **现有运行中项目兼容**：Alembic 迁移给老 project 加 scenes_confirmed=false 后，老 project 如果 pipeline 已跑过 Stage 3，会被新代码当成"未确认"卡住吗？
   - **缓解**: 迁移时把已跑完 Stage 4 的项目 `scenes_confirmed` 直接设为 true（迁移 SQL 加 UPDATE 语句）
2. **UX 决策**：20s 倒计时还是用户主动点？需 Founder 决策
3. **R4-1 R4-2 风格统一**：两个等待逻辑代码风格必须一致（参数名 / 超时值 / 日志格式），便于未来加 R4-3（storyboard 确认？）扩展

#### 引用

- 历史 B42: PENDING.md:2588 附近
- 历史 B50: PENDING.md:3054-3077
- Wave 5 修复说明: TEAM_CHAT.md 末尾
- 用户旅程设计原意: DEC-011 + CLAUDE.md "用户旅程设计" 章节（Stage B 表格 scenes 调整应是"可调整项"）

---

### TASK-PARALLEL-M1 — 🔥 P0 图像生成并行化改造（2026-04-25 派发）

| 字段 | 内容 |
|------|------|
| **负责人** | PM 派发 → Backend 主实施 → Tester 验收 → DevOps 部署 |
| **优先级** | 🔥 P0（BP 单位经济路线图 M1 节点，最高杠杆事件） |
| **决策依据** | DEC-020（M1 工程并行化优先）|
| **完整路线图** | `.team-brain/analysis/COST_UX_ROADMAP_2026Q2.md` |
| **预计工期** | Backend 1-2 天 + Tester 0.5 天 + DevOps 部署 0.5 天 |
| **预期效果** | 20 张耗时 **13.5 min → ~4.5 min**（达 Midjourney Fast Mode 体验），成本不变 |

#### 背景

Code Forensics Agent（2026-04-25）地毯式审查发现：
- `pipeline_orchestrator.py:524-677` Stage 5 主循环**完全串行**（for + asyncio.sleep(0.5)）
- `max_concurrent_images=2`（run() 签名）和 `IMAGE_MAX_CONCURRENT=3`（config.py:32）**全是死参数**
- `image_generator.py:1475 generate_batch()` 已实现 `asyncio.Semaphore + asyncio.gather()`，**被孤立**
- 实测 20 张 = **807s ≈ 13.5 min**（PROJECT_STATUS R6 数据）

#### Backend 实施清单

**主路径修改**：
1. `pipeline_orchestrator.py:524-677` Stage 5 主循环：替换为调用现有 `image_generator.generate_batch(shots, max_concurrent=3)`
2. Haiku validator（`shot_validator.validate_shot()`）也并行化（每张图后的串行验证 → 并发 gather）
3. 保留 `asyncio.sleep(0.5)` 冷却（在 Semaphore 内部，避免突发）
4. 接入现有 `IMAGE_MAX_CONCURRENT=3` 环境变量（config.py:32），让其真正生效

**风险兜底（用户强调，必须各种情况都覆盖）**：

> NB2 高峰期 429 失败率 ~30%（Agent B 调研，2026-04 数据）。Backend 必须在并行场景下确保 Semaphore 限流 + 退避兜底覆盖**所有失败路径**：

| 失败分支 | 必须的兜底行为 | 验收测试 |
|---------|--------------|---------|
| 单张 429（限流）| `MAX_RETRIES=3` 重试，`RETRY_DELAY=2s × (attempt+1) × 2` 翻倍退避 | 模拟 1 张 429 → 重试成功 |
| 单张 CONTENT_SAFETY | 立即 break + 调 `PromptRewriter` 改写后重试（`MAX_REWRITE_ATTEMPTS=2`）| 模拟 1 张 CS → 改写后成功 |
| 单张永久失败（重试耗尽）| Shot 层 `MAX_SHOT_RETRIES=1`，最终标记失败但不阻塞其他 shot | 模拟 1 张永久失败 → 其余 19 张成功 |
| 多张并发 429 | Semaphore 控制并发 ≤ 3，自动节流 | 模拟 5 张同时 429 → 排队完成 |
| 全部失败 | Pipeline 优雅降级，job 状态正确写入 `failed`，`PipelineCostTracker` 不超 $10 熔断 | 模拟 20 张全失败 → job.status=failed |
| 部分失败（如 3 张失败 17 张成功）| 成功的 17 张正常返回，失败的 3 张占位（image_path=null + error_message），用户可在 Stage D 手动重试 | 模拟混合失败 → 前端 StageD 正确展示 |
| 网络中断 | aiohttp / google-genai SDK 内部 timeout + 重试（确认现有配置）| 模拟网络抖动 → 自愈 |
| Cancel 中途取消 | `cancelRef` 信号能正确传播到所有并发 gather，不留僵尸 task | 用户中途取消 → 所有 task 优雅停止 |

**禁止删除/修改的内容**：
- 现有 `MAX_RETRIES=3` / `RETRY_DELAY=2s` / `MAX_REWRITE_ATTEMPTS=2` / `MAX_SHOT_RETRIES=1` 重试逻辑
- 0.5s 冷却（移到 Semaphore 内部，不删）
- StyleEnforcer / 角色参考图传递链（CLAUDE.md 已强调"参考图传递链必须完整"）

#### Tester 验收清单

**性能验收**：
- [ ] 20 张实测耗时 ≤ 5 min（目标 4.5 min，留 10% buffer）
- [ ] 单张 NB2 调用峰值并发 = 3（不超 IMAGE_MAX_CONCURRENT）

**质量回归（CLAUDE.md 强制要求）**：
- [ ] 3 角色场景一致性 = **100%**（不能掉，teststory6.4 / 6.5 重跑）
- [ ] 6 角色场景一致性 ≥ **90%**（teststory6.6 重跑）
- [ ] 跨题材稳定（现代都市 / 武侠古装 / 写实 / 水墨 各跑 1 个）

**风险路径回归**：
- [ ] 上面 8 个失败分支每个都跑一次模拟测试（注入失败 → 验证兜底行为）

**集成回归**：
- [ ] 全链路 A→E 在 VPS 上跑通（不只是 Backend 单元测试）
- [ ] BgmPlayer / Stage D / 文字叠加都正常

#### DevOps 部署

- [ ] 通过后 push 到 GitHub（必须先 push，再部署 — CLAUDE.md 铁律）
- [ ] rsync 部署 VPS（注意 trailing slash 陷阱，feedback memory 已记录）
- [ ] /api/health 验证容器 healthy
- [ ] 生产环境再跑 1 次完整故事生成验证

#### PM 派发要点（避免歧义，feedback memory "任务派发必须具体化"）

- 派 Backend 时**必须**让其先读：本任务全文 + DEC-020 + COST_UX_ROADMAP_2026Q2.md L1 章节 + CLAUDE.md "角色一致性"和"代码规范"章节
- 任务**Sonnet 4.6** 即可（执行类，不需要 Opus）
- 完成后 Backend 必须更新 backend-progress 三件套（current / context-for-others / completed）
- 验收前先检查 progress 文件 modified time（PM 审查三步顺序）

---

### MVP 后 Pipeline/Frontend 细节修复批 — 💡 P2/P3（2026-04-23 TASK-BUG-FIX-BATCH-1 延出）

| # | 类别 | 描述 | 文件:行 | 优先级 |
|---|------|------|---------|------|
| 1 | Backend | 完成时 job.stage 被写成 "story_generation"，覆盖真实最后 stage（image_generation / bgm 等）| `job_manager.py:302` | P2 |
| 2 | Backend | Stage 6 BGM 生成期间没有 `progress_callback`，前端进度卡 90% 数分钟 | `pipeline_orchestrator.py:687-730` | P2 |
| 3 | Frontend | `imageUrl=null` 预览页 fallback 显示"画面生成中..."，真实失败场景会误导用户 | `StageD.tsx:186-197` | P2 |
| 4 | Frontend | BgmPlayer 显示"暂无配乐"时缺 url strip 引号 fallback（已由 BE-4 根因修复解决，但前端仍该加兜底防御）| `BgmPlayer.tsx` | P3 |
| 5 | Frontend | Shot `<img>` onError 没有占位图（SKIP 模式修复后不再触发，但真实失败场景需要）| `StageD.tsx` | P3 |
| 6 | Frontend | 进度条数字变化无过渡动画，35→65→100 跳变观感生硬 | `StageC.tsx` progress bar | P3 |

**触发条件**: MVP 正式上线前做第二轮打磨

---

### 数据层架构债 — 💡 技术债（2026-04-23 / 04-24 陆续发现）

| # | 描述 | 严重度 |
|---|------|------|
| ~~ARCH-1~~ ✅ | ~~`chapter_scene_images` 表被 18+ 处代码依赖（`chapters.py` L362/458/579/...），但 **Pipeline 完成后从不批量写入**，只有 `regenerate_single_image_task` 失败路径才写一条错误记录。导致 GET /images 永远返回空，单张重生成/局部编辑功能形同虚设~~ **已修 (2026-04-28 Wave 2 Agent F)**：pipeline_orchestrator Stage 5 完成后批量 DELETE+INSERT，job_manager 传 chapter_id | ~~P1（功能缺失）~~ ✅ |
| ARCH-2 | `project_character_references` 表完整定义（12 列），但**整个代码库 0 引用**，是死表 | P2（技术债）|
| ARCH-3 | R8 只有 10 张 shot 图，19 shots 场景需要 mod 循环（已在 2026-04-23 SKIP 分支做 mod 循环）。正式生图时无此问题 | ✅ 已临时修 |
| **ARCH-4** | **`api_cost_logs` 表全时 0 行（2026-04-24 PM 地毯式审查发现）**。代码 grep `api_cost_logs\|ApiCostLog\|INSERT.*api_cost` 在 app/ **0 命中**。schema 已定义（9 列），但没有 SQLAlchemy model 或写入路径。影响: `/api/monitoring/costs/summary` 端点永远返回 0，无法做成本熔断/追踪 | P1（观测性缺失）|

**触发条件**: ARCH-1 在"单张 shot 重新生成"或"批量编辑"功能投产前必修；ARCH-2 可等下一轮数据库清理时删表

---

### DevOps / 配置债 — 💡 P3

| # | 描述 | 文件:配置 |
|---|------|---------|
| OPS-3 | uvicorn nohup stdout 不 flush（缺 `PYTHONUNBUFFERED=1`）导致实时诊断困难，日志需 sleep 等待 buffer | docker/Dockerfile.api or env |

---

### ✅ TASK-BUG-FIX-BATCH-1 — 完成（2026-04-23）

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 完成 — PM 独立审查通过，待 @devops 部署 VPS |
| **Route B @backend** | job_manager.py checkpoint isinstance 判断 + pipeline_orchestrator SKIP 分支复制 R8 写 image_url + Stage 6 credits_used checkpoint + main.py /static/outputs mount + DB chapter id=2 清理 |
| **Route C @frontend** | FE-5 根因（StrictMode completedRef 污染）+ 修复；FE-1 STAGE_LABEL 细化；FE-2 CreateContext full-dedup；FE-3 progress 直信 backend；FE-4 stage 透传 |
| **验证** | pytest 7 passed / /health healthy / /static HTTP 200 / DB clean / npm build 0 error |

---

### 生图模型选型调研 — 💡 技术预研（2026-04-24 完成基线调研）

**调研**: R1 + R2 双 agent 完成 Top 6 深度对比，详见 TEAM_CHAT.md 2026-04-24 TASK-IMAGE-MODEL-RESEARCH

**Top 6 排名（Arena ELO 2026-04-22）**:
1. GPT Image 2 — 1,512 ★ 质量天花板
2. Nano Banana 2 — 1,264 ★ 当前默认
3. Nano Banana Pro — 1,217 ★ 摄影级
4. FLUX 2 Pro — 1,157 ★ LoRA 生态
5. Imagen 4 Ultra — 1,148 ★ 文字渲染
6. Ideogram 3.0 — N/A ★ 文字气泡专项

**最大颠覆点**: GPT Image 2 Medium $0.053/图 + Batch 折扣 $0.027/图 比 NB2 ($0.067) 便宜 **且** Arena ELO 高 248 分 + 文字渲染 99% → 2026-05 GA 后可能直接替代 NB2 作为 Pipeline 默认。

**待决策**（等 GPT Image 2 API 正式 GA）:
- A/B 测试 GPT Image 2 vs NB2 on 条漫场景（特别是文字气泡）
- 若 GPT Image 2 99% 文字准确率验证通过 → 可能**废弃 TextOverlayServiceV2**（后处理叠字）架构

**触发条件**: 2026-05 初 GPT Image 2 API 正式 GA 后 1-2 周内安排测试

---

### ✅ max_tokens=8631 魔法数字统一 — 完成（2026-04-22）

| 字段 | 内容 |
|------|------|
| **状态** | ✅ 完成 — grep 0 代码命中 + pytest passed + /health healthy |
| **改动** | 13 处 `8631 → 16384`（5 个文件：character_designer / alignment_service / story_outline_generator L196 补齐 / storyboard_director / screenplay_writer）|
| **教训** | 首次调查汇报"14 处 + story_outline_generator 已改"不准确。PM 独立地毯式 grep 核对为 13 处 + 半改状态。Backend 本次任务已做自我纠错记录 |

---

### ✅ TASK-MUREKA-PIPELINE-INTEGRATION — 完成（2026-04-21）

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @Backend + @AI-ML + @Frontend + @DevOps + @Tester |
| **前置闸门** | ✅ TASK-HAIKU-QUOTE-EXTRACTION 通过（方案 A mixed v3.2 作为最终版）|
| **完整 TASK 文档** | `.team-brain/handoffs/TASK-MUREKA-PIPELINE-INTEGRATION.md` |
| **Wave 1 状态** | ✅ 完成 — music_hint + extract_story + ffmpeg_post_processor |
| **Wave 2 状态** | ✅ 完成 — 服务层三剑客 + Mureka E2E 跑通 |
| **Wave 3 状态** | ✅ 完成 — @backend REST API (4 端点) + @frontend BgmPlayer + StageD 集成 (build 20 路由 0 错) |
| **Wave 4 状态** | ✅ 完成 — @tester 6P/2W/1S，PM 修 style_preset→get_music_hint bug 两处，Founder 听 3 mp3 确认风格层有辨识度 |
| **VPS 部署** | ✅ 完成（PM 代执行）— commit `b998cbf` push + rsync + MUREKA_API_KEY + docker rebuild + /health healthy |
| **MVP 后 (P3)** | music_hint 在 Haiku 层效用有限、秋梨膏温暖故事金句重试、自定义 BGM 上传 |

---

### music_hint meta-prompt 层效用有限 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 可接受 — Founder 2026-04-21 实际听 3 首 BGM 确认音乐层面有风格差异）|
| **发现** | Wave 4 集成测试 @tester 跑同一年夜饭故事 × 3 风格（韩漫/水墨/赛博朋克）。Haiku 输出的 BGM prompt **几乎完全一样**，music_hint 的关键词（guqin/synth/K-drama）在 Haiku 输出里**0 命中**。但 Mureka 生成的最终 mp3 仍有可听的风格差异 |
| **根因** | 故事 narration+mood（~1500 字）完全压倒 music_hint（~25 字）。V4 哲学推 Haiku 走"身体感觉+故事 mood"，music_hint 被当作次级信息 |
| **缓解方向（未来）** | (A) 把 `{{visual_style_hint}}` 从 user prompt 搬到 system prompt 显眼位置；(B) 加规则"Music genre MUST emerge from visual_style_hint, not default to piano"；(C) 调整 prompt cache 策略（动态部分含 style_hint 放 system 前缀）|
| **触发条件** | MVP 上线后用户反馈"水墨故事配 acoustic guitar 违和"等具体问题再启动 |
| **状态** | 📝 记录 |

---

### 秋梨膏类"温暖动作性故事"金句质量重试机制 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 后，LLM 随机性决定先看实际 BGM 质量）|
| **来源** | Founder 2026-04-21（TASK-HAIKU-QUOTE-EXTRACTION 评审发现）|
| **背景** | Haiku 4.5 在"温暖家庭叙事"（如秋梨膏）故事里连续 3 次测试都偏爱挑"温情动作序列"金句（握手/带回/提着），违反 Quote Selection Protocol 反向清单第 5 条。v3 一次挑对是 outlier |
| **提议机制** | Backend 代码检测金句是否是连续动作叙述（启发式：3+ 个动词连缀 + 无独立画面意象），触发 Haiku 重试一次 |
| **触发条件** | MVP 集成完成后，实际测 BGM 音乐质量，若秋梨膏类故事 BGM 听觉质量被影响再启动 |
| **状态** | 📝 已记录，MVP 后根据实测决定 |

---

### 用户自定义 BGM 上传 — 💡 MVP 后迭代（P3）

| 字段 | 内容 |
|------|------|
| **优先级** | P3（MVP 后）|
| **来源** | Founder 2026-04-18（见 TEAM_CHAT 对 PM "还需要补的 10+ 维度" 第 10 点的决策）|
| **说明** | 用户可上传自己的 mp3 作为 BGM，跳过 Mureka 自动生成。DEC-011 之外的未来功能 |
| **触发条件** | MVP 上线后，根据用户反馈决定优先级 |
| **关联风险** | 上传版权合规性检查、mp3 格式/时长/音质约束、与 Mureka 生成流的切换 UX |
| **状态** | 📝 已记录，MVP 后讨论 |

---

### TASK-API-COST-TABLE — 🔄 @Backend api_cost_logs 建表 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @Backend |
| **来源** | Coordinator 指令 (2026-04-13) |
| **说明** | 在 Aliyun 共享 MySQL 中创建 `api_cost_logs` 表，用于追踪 API 调用成本。表结构需记录：project_id、stage（1-5）、model、input_tokens、output_tokens、cost_usd、created_at |
| **状态** | 🔄 进行中（Background Agent 运行中） |

---

### Resonance 新时间线 — 📝 待 Founder 重新定义

| 字段 | 内容 |
|------|------|
| **优先级** | P2 |
| **指派** | @Resonance（等 Founder 指示后启动） |
| **来源** | 原时间线（500+ 申请）已作废 (2026-03-23)，正式内测启动时间待 Founder 通知 |
| **说明** | Resonance 主战场：抖音"一话故事" → 小红书 → B站。预算：常规 2-3k/月，高 ROI 可提至 20k/月。等 Founder 确认内测启动时间后重新制定具体执行方案 |
| **状态** | 📝 暂缓，待 Founder 重新定义时间线 |

---

### 续写模式 Phase 3 #11 — 📝 待 Founder 决定是否开始设计

| 字段 | 内容 |
|------|------|
| **优先级** | P2（暂缓） |
| **指派** | 待 Founder 决策后再派发 |
| **来源** | 产品路线图 Phase 3 第 11 个功能点 |
| **说明** | 用户在 Stage D 预览完成后可选择"续写"，系统基于当前故事状态继续生成下一集/后续情节。涉及：历史上下文传递、角色记忆、Story Continuation API 设计 |
| **状态** | 📝 等待 Founder 决定是否进入设计阶段 |

---

### 监控告警系统 R4 — 📝 @DevOps 待启动 (P1)

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @DevOps |
| **来源** | Harness V2 Engineering 计划（DEC-015）中的 R4 监控组件 |
| **说明** | VPS + Pipeline 监控告警系统：① 修复外部 `/api/health` 端点 404 问题（Nginx 路由前缀）② 配置 Uptime Robot 或 Grafana 告警 ③ 6 个 EP Sensor 端点整合进监控看板 |
| **前置** | Harness V2 Phase 1-3 已全部完成 (2026-04-15) |
| **状态** | 📝 已计划，待 DevOps 启动 |

---

### TTS Key 填入 — 🔄 @DevOps 执行中

| 字段 | 内容 |
|------|------|
| **优先级** | P1 |
| **指派** | @DevOps |
| **来源** | Coordinator 指令 (2026-04-13) |
| **说明** | 火山引擎 TTS（Doubao）配置：将剩余 TTS Key 填入 VPS 环境变量。当前状态：4/6 Key 已配置，需补全 VOLCENGINE_TTS_APPID 等剩余项 |
| **状态** | 🔄 Background Agent 执行中（adda04757d96a67bd） |

---

### TASK-STYLE-EXPANSION — 📝 暂缓 (P1，备忘)

| 字段 | 内容 |
|------|------|
| **优先级** | P1（暂缓） |
| **说明** | 从剩余 80 种风格中筛选适合普通用户的上架风格（预计 25-35 种），补写 StyleEnforcer 规则 + 生成缩略图 |
| **前置** | TASK-STYLE-THUMBNAILS 15 张通过后再启动 |
| **背景** | style_config.py 有 95 种风格，当前仅 15 种有 enforcer 规则并上架 |
| **状态** | 📝 已记录，暂缓 |

---

## ✅ 已归档交接（全部完成）

### 2026-04 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-HARNESS-V2** | **Harness V2 Engineering：GitHub Actions CI + Schema 验证 + $10 成本熔断 + 6 EP Sensor + 监控端点，3 Phase 全完成，VPS PASS** | **2026-04-15** ✅ |
| **TASK-PROMPT-B-DEFAULT** | **Prompt B' 格式设为默认（-46% tokens，盲测 5:4 Founder 偏好），全 VPS 部署** | **2026-04-15** ✅ |
| **TASK-STAGE-D-PRODUCT** | **Stage D 产品逻辑：调整画面（Haiku 重写 image_prompt）+ 编辑文字（编辑 chinese_text）+ 重新生成（re-roll）** | **2026-04-14** ✅ |
| **TASK-PIPELINE-UX-CONNECT** | **Pipeline 前端接通真实 API 轮询（每 2s）+ character_ready 检查点 + 真实用户确认等待** | **2026-04-07** ✅ |
| **TASK-PIPELINE-OPT-R6** | **Pipeline 优化 R1→R6：批处理 + 并行 + 进度显示 + 角色确认检查点，R6 Founder 实测 807s/20shots/零错误** | **2026-04-06** ✅ |
| **TASK-HARNESS-V1** | **Harness V1：PostToolUse pyright/tsc hooks + PreCommit 架构测试 + PrePush 全量测试** | **2026-04-05** ✅ |
| **TASK-DB-LONGTEXT** | **DB 迁移：所有 TEXT→LONGTEXT + characters_confirmed 新列 + pool_recycle 修复** | **2026-04-04** ✅ |
| **TASK-PLOTPOINT-REORDER-FIX** | **情节拖拽元数据跟随修复，Frontend+Backend+Tester 并行，39/39 PASS** | **2026-04-03** ✅ |
| **TASK-CONFIRM-OUTLINE-WIRE** | **StageB confirm-outline 接通 Pipeline（前端调 confirm-outline + start-generation，后端用 confirmed outline 跳过 Stage 1），39/39 PASS** | **2026-04-03** ✅ |
| **TASK-JSON-REPAIR-V3** | **JSON 修复状态机 V3（`_fix_unescaped_quotes()` 正则→状态机，24/24 PASS），4a/4b/4c 修复，VPS 部署** | **2026-04-01** ✅ |
| **TASK-UPLOADER-ENV-FIX** | **5 个 Uploader 环境变量统一修复（NEXT_PUBLIC_API_BASE_URL → NEXT_PUBLIC_API_URL），VPS 部署** | **2026-04-01** ✅ |

### 2026-03 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **T29-T37 全周期** | **R6/R7/R8/T-A~T-K/T11~T28 全系列修复（对话系统+shot质量+角色一致性+气泡+回归测试）** | **2026-03-17** ✅ |
| **TASK-DEPLOY-CLEANUP** | **DevOps 部署 R8B + CLEANUP（rsync + Docker rebuild）** | **2026-03-17** ✅ |
| **TASK-BRAND-MANIFESTO** | **品牌宣言 V2 整合 Pipeline 模块 + About 页重写，Founder 终审通过** | **2026-03-17** ✅ |
| **TASK-STYLE-THUMBNAILS** | **15 张风格缩略图生成 + 压缩集成（1024×1024→400×400 JPEG, 27MB→1MB）** | **2026-03-10** ✅ |
| **TASK-LOGO-REPLACE** | **Header/SubPageHeader/CreateHeader/Footer Sparkles→新 logo，VPS 部署** | **2026-03-16** ✅ |
| **TASK-GIT-PUSH-DUAL-TEAM** | **Git push 59 文件（commit 33eaac6），双团队工作流建立** | **2026-03-19** ✅ |

### 2026-02 完成

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-PROMPT-BUBBLE 全周期** | **TASK-PROMPT-BUBBLE + FOLLOWUP + FOLLOWUP-R2 + BUBBLE-SPEAKER-FORMAT-DEPLOY（气泡对话嵌入 + speaker_format=english）** | **2026-03-06** ✅ |
| **TASK-DEPLOY-PREP** | **VPS + Docker + SSL + Nginx 全部完成，VPS 已上线 prefaceai.mov** | **2026-03-06** ✅ |
| **TASK-F1-F5-FIX 全周期** | **T1-T28 全系列修复 + R4/R5/R6 E2E 验证 + PM 独立复核** | **2026-03-09~14** ✅ |
| **TASK-SHOT-QUALITY-UPGRADE** | **SQ-1~SQ-8 全部完成 + 回归验证 4.36/5 + Bug #5 修复，TASK-GIT-COMMIT-3** | **2026-03-05** ✅ |
| **TASK-STYLE-DESC-REWRITE** | **14 个风格场域式改写，Step 1-4 闭环，Founder 批准为默认策略** | **2026-03-04** ✅ |
| **TASK-E2E-REGRESSION 全周期** | **R2/R3/R4/R5/R6 E2E + F1-F5 深挖 + 平台级改进 T17-T22 + T23-T28** | **2026-03-09~14** ✅ |
| **TASK-NB2-SWITCH** | **NB2 模型切换（gemini-3.1-flash-image-preview），5/5 shots PASS** | **2026-02-27** ✅ |
| **TASK-DIALOGUE-SYSTEM** | **对话系统三层重构（dialogue≥60% 规则），Backend L1 + AI-ML L2+L3** | **2026-02-27** ✅ |
| **TASK-NB2-NATIVE-TEXT** | **NB2 原生文字渲染切换（speaker_format=english），PM Review PASS** | **2026-02-28** ✅ |
| **TASK-CREATE-UPGRADE** | **Frontend P0+P1+P2 全部完成（注册页+工作台+故事详情+StoryCard 等），PM 复验 4.8/5** | **2026-03-03** ✅ |
| **TASK-GIT-COMMIT-2** | **Git 提交 12 天积压变更（3批：926f284+825aece+e05bbd2，67 文件）** | **2026-02-24** ✅ |
| **TASK-SCENE-REF-ASPECT** | **场景参考图宽高比修复 16:9→2:3（DEC-010）** | **2026-02-24** ✅ |
| **TASK-MODEL-UPGRADE** | **7 个服务文件模型全面升级（主力 Sonnet 4.6，备用 Gemini 3 Pro）** | **2026-02-26** ✅ |
| **TASK-STYLE-SLAMDUNK** | **StyleEnforcer 新建 slam_dunk 风格预设（DEC-012）** | **2026-02-26** ✅ |
| **TASK-E2E-TEST-2** | **Slam Dunk + Sonnet 4.6 完整 E2E 测试，PM 复核通过** | **2026-02-27** ✅ |
| **TASK-UI-STAGE-A** | **Stage A 输入界面（故事文本框+篇幅卡片+风格卡片），PM 复验 4.5/5** | **2026-02-26** ✅ |

### 2026-01 及更早

| 编号 | 内容 | 完成时间 |
|------|------|----------|
| **TASK-LP-PAGES-FIX** | **LP 子页面 4 项修复（PM 复验 4.8/5）** | **2026-02-14** ✅ |
| **TASK-ASPECT-2x3** | **宽高比统一改为 2:3（9 文件 26 处，PM 核验通过）** | **2026-02-14** ✅ |
| **TASK-LP-POLISH** | **Landing Page 2 项代码质量修复（5.0/5）** | **2026-02-12** ✅ |
| **TASK-LP-FIX** | **Landing Page 8 项修复（4.5/5）** | **2026-02-12** ✅ |
| **TASK-GIT-COMMIT** | **Git 提交 LP 修改（a6a0359+08a0e9f，PM 核验通过）** | **2026-02-12** ✅ |
| **HANDOFF-2026-02-12-001** | **TASK-GIT-INIT Git 仓库初始化** | **2026-02-12** ✅ |
| HANDOFF-2026-02-03-001 | Backend 架构重构+核心修复 | 2026-02-03 |
| HANDOFF-2026-02-02-015 | P1 修复（碰撞检测+气泡） | 2026-02-02 |
| HANDOFF-2026-02-02-013 | P0 修复（Speaker 前缀+气泡位置） | 2026-02-02 |
| HANDOFF-2026-01-31-012 | 配置调整 | 2026-01-31 |
| HANDOFF-2026-01-30-011 | 42 张测试脚本 | 2026-01-30 |
| HANDOFF-2026-01-29-010 | Landing Page 交接 | 2026-01-29 |
| HANDOFF-2026-01-22-009 | 条漫完整故事测试 | 2026-01-22 |

---

### TASK-PARALLEL-M1 进度更新 (2026-04-25 16:10)

- ✅ Phase 0 (TASK-RATELIMIT-RESEARCH): max_concurrent=3 安全性确认。报告 `.team-brain/analysis/RATELIMIT_RESEARCH_2026-04-25.md`
- 🟡 Phase 1 (实施): 代码 24/24 测试通过附 3 隐忧（conftest stub / project_id graceful skip / 文档未更新）
- 🔄 Phase 1 round 2: Backend 修隐忧
- ⏸ Phase 2 (Tester): 等 round 2 完成
- ⏸ Phase 3 (DevOps): 等 Phase 2 通过


---

### TASK-PARALLEL-M1 进度更新 (2026-04-27)

- ✅ Phase 0 (RATELIMIT-RESEARCH): max_concurrent=3 安全
- ✅ Phase 1 (实施): 24/24 unit test，pytest 真实 venv
- ✅ Phase 1 round 2 (3 隐忧修): conftest 删 / project_id 映射 / 文档 OK
- ✅ Phase 2 D1 round 1 (旧代码): 暴露 4 production bug (project_id=None / Validator 鉴权 / IncompleteRead / Event loop)
- ✅ Phase 1 round 3 (4 bug 修): pytest 24/24，Bug 2 完全修，Bug 1+4 partial
- ✅ Phase 2 D1 redo: 14/14 全过 8 故事，¥34.3 实花
- 🔄 **Phase 1 round 4 派发 (2026-04-27)**: 修 Bug 1 (1 行 dispatcher) + Bug 5 (图压缩 < 5MB)
- ⏸ Founder 本地+域名测试: round 4 完成后启动
- ⏸ Phase 3 (DevOps 部署): 暂缓，等 Founder 测试通过

### 🆕 Bug 5 (2026-04-25 D1 redo 发现)

ShotValidator 调 Anthropic Claude API 时部分 Seedream PNG 输出超 5MB 上限触发 fail-open。需要图压缩（resize / quality 降低）到 < 5MB 后传 Claude。Round 4 范围内修。


### TASK-PARALLEL-M1 round 4 ✅ 完成 (2026-04-27 11:20 PM 审查通过)

- ✅ Bug 1 dispatcher 1 行修 (image_generator.py L1399 `**_kwargs_copy`)，DB 实证 id 167-181 全 None vs id 182-197 全 12 (integer)
- ✅ Bug 5 ShotValidator 5MB 图压缩路径就位 (shot_validator.py `_compress_for_claude` 渐进 quality+resize)
- pytest 24/24 真实 venv 通过，¥3.5 实证成本

**5 Bug 最终全部解决** (除了 4b aiomysql GC cleanup cosmetic noise，已记入 ERROR_PATTERNS.md EP-017，**留着不修**)

⏸ Founder 本地 + 域名测试 → 决定 Phase 3 部署 VPS


---

### 🆕 MVP 前必修 P1 — UX 改进 2 项 (2026-04-27 Founder 测试 T5 发现)

#### UX-1: Stage C 角色预览盲调（无图调外观）— 修复方案确认

**Founder 04-27 提问**: Stage 2 提前生 portrait 数据/描述/prompt 够不够？

**PM 答**: ✅ 数据充足。Stage 2 LLM 输出的 characters_json 含完整 visual description (name/age/gender/role/详细面部+服装描述)，等同于 Stage 5 现在生 portrait 时的输入。技术上 Stage 2 后立即调 reference_image_manager 生 portrait 完全可行。fullbody 涉及完整服装/姿态/场景上下文，仍可放 Stage 5（依赖 storyboard 信息）。

**修复方案 (确认 A)**: Stage 2 LLM 完成后立即调 Seedream/NB2 生 portrait（每角色 1 张，3 角色 ~¥0.66），让 Stage C 用真 portrait 做卡片。fullbody 仍 Stage 5 生

**现象**: Stage C 角色预览页只展示 LLM 文字描述 + 占位"播放按钮"图标，没有真实 portrait 图。用户面对"换发色 / 换服装 / 更年轻 / 更成熟 / 换风格"按钮无法目测判断，只能盲调文字。

**根因**: Pipeline 设计将 character_refs（portrait + fullbody）放到 Stage 5 一起生（与 scene_refs + shot images 并列）。Stage C 只是 LLM 角色描述确认 checkpoint。

**影响**:
- 用户体验差：盲调外观，反复 try-and-error
- "换发色"等按钮的点击预期与实际行为不一致（用户期望看到图变化，实际只是改文字描述）
- MVP 上线后用户大概率投诉

**修复方案**:
- **方案 A（推荐）**: Stage 2 LLM 角色设计完成后**同时生 portrait**（每角色 1 张 portrait，约 ¥0.66/3 角色），让 Stage C 真有图可看可调。fullbody 仍延后到 Stage 5（因为 fullbody 跟场景/服装强耦合，前置生意义不大）。
- **方案 B**: 砍掉 Stage C 的"换发色 / 换服装"等按钮，UI 改成纯文字调整入口（更诚实，但功能阉割）。

**触发条件**: MVP 前必修 P1（用户体验关键路径）。建议方案 A。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 2 后段、`app/services/character_designer.py`、`frontend/src/components/StageC.tsx`、`reference_image_manager.py`

---

#### UX-2: 故事内部数字一致性问题（**升级 P1，多处 LLM 漂移**）

**现象**: Stage B 大纲编辑页用户改 Plot 1 的关键数字（"二十八对" → "三十二对"），但 Plot 7 末句仍是"烧掉了那本统计**二十八对**新人的小本子"。系统不提示，confirm-outline 后 Stage 3-4 LLM 直接继承这个内部矛盾。

**根因**: confirm-outline 端点只校验 schema（角色数 / 情节点数 / 场景数），不做"语义一致性"检查。LLM 也不会主动跨 plot 比对数字 / 名字 / 时间。

**影响**:
- 用户编辑后下游 LLM 沿用矛盾数据
- Stage D 单镜头编辑可修，但用户得自己挑出错的 shot
- 故事内部的关键数字 / 角色名 / 时间线如果不一致，质量打折

**修复方案**:
- **方案 A（推荐）**: 前端 Stage B 加"前一致性提示"：用户改 Plot N 时若该 plot 有数字 / 角色名出现，前端 highlight 其他 plot 里同样的数字 / 名字让用户检查。**纯前端实现，零后端成本**。
- **方案 B**: 后端 confirm-outline 时跑一次"内部一致性 LLM 检查"（Sonnet 4.6 一次调用，~¥0.05），返警告给前端展示。
- **方案 C**: Stage 3 剧本生成 prompt 里加一段"主动检测 outline 内部矛盾并修正"（最小代码改动，但效果不可控）。

**触发条件**: MVP 前必修 P1。推荐方案 A 优先实施（成本最低 + 用户主导决定要不要改）+ B 兜底（如果用户不仔细看也能挽救）。

**关联文件**: `frontend/src/components/StageB.tsx` (前端校验)、`app/api/projects.py` confirm-outline 端点 (后端校验)、`app/services/screenplay_writer.py` Stage 3 prompt 微调

---


#### UX-3: Stage 切换时前端进度条卡帧不同步

**现象** (2026-04-27 Founder T5 测试发现): backend Stage 3 已完成 + Stage 4 进行中（DB stage_message 已是 `screenplay 35%`），但前端仍显示"正在设计角色 10%"约 2 分钟没变化。视觉上像卡死。

**根因**: 前端 progress polling 频率/缓存策略问题。怀疑：
- polling interval 偏大（如 5s+ 才能看到下一次更新）
- 或 React state 没正确响应 backend stage 切换
- 或 stage_message vs current_stage 不同步显示

**影响**: 用户以为卡死，可能误操作（点取消 / 刷新）

**修复方案**: 排查 `frontend/src/hooks/useGenerationStatus.ts`（或类似）poll 逻辑，确保 stage_message 变化即刻反映到 UI。Polling 间隔建议 ≤ 2s（已是 backend 卡帧节奏）。

**触发条件**: MVP 前 P1。

**关联文件**: 前端 progress polling hook / StageC.tsx / StageD.tsx wait 页


#### ~~UX-4: 等待页 milestone 列表只显示一条不追加~~ — ❌ PM 误判已纠正 (2026-04-27 15:18)

**现象** (2026-04-27 Founder T5 测试发现): Stage 等待页底部绿色 ✓ "已完成里程碑"框只显示 character_ready 那一条 "角色设计完成，请确认角色和场景"。Stage 推进到 screenplay / storyboard 后**没有追加新里程碑**（如 "剧本生成完成"、"分镜生成完成"）。

**理想设计**:
```
✓ 大纲生成完成
✓ 角色设计完成，请确认角色和场景
✓ 剧本生成完成
✓ 分镜生成完成
🔄 正在生成画面 N/18
```

**实际**: 只看到 character_ready 那条 ✓，其他 milestone 没出现。

**根因**: 前端 milestone 列表组件可能只订阅了 character_ready 信号或只在初次 stage_message 变更时插入一条，后续 progress_callback 没被正确累计。

**影响**: 用户看不到后端实际有在推进，体感像卡住

**修复方案**: 排查前端 milestone list 累加逻辑（每次 stage_message 变化都 push 一条新记录到列表，去重 by stage_message 字符串）

**触发条件**: ❌ PM 误判，撤销。实际 milestone 列表按 stage 完成事件正常追加。10% 那时只完成 character_ready 1 个事件，所以只显示 1 条；后续 stage 完成后正常追加 ✓ 剧本编写完成等。**不是 bug**

**关联文件**: 前端 wait page milestone list 组件 / `useGenerationStatus.ts`


#### ~~UX-5: StoryboardDirector batch 完成无 progress_callback~~ — ❌ PM 误判已修正 (2026-04-27 15:21): 实际 backend 在每个 scene 完成时**有** progress_callback。Founder 截图证实 milestone 追加正常 (Scene 1/7→2/7→3/7)。真正问题是 UX-6（ETA 算法低估 Stage 4 实际耗时）

**现象** (2026-04-27 Founder T5 测试发现): Stage 4 StoryboardDirector 按 7 个 scene 分批跑（每批 Sonnet 调用 ~40-50s），但**每个 batch 完成时没 progress_callback** 推进 chapter_generation_jobs.progress 字段。仅在 Stage 4 启动时打了一次 progress=39 / message="分镜生成中 (Scene 1/7)..."。结果：跑 5/7 batch 时前端看到的 progress 仍是 39%，message 仍是 "Scene 1/7"，体感卡死。

**修复方案**: `app/services/storyboard_director.py` 在每个 scene batch 完成时调 `progress_callback("storyboard", 39 + (batch_idx / total_batches) × 11, f"分镜生成中 (Scene {batch_idx+1}/{total_batches})...")` 让进度从 39% 平滑推进到 50%。

**关联文件**: `app/services/storyboard_director.py`、`app/services/pipeline_orchestrator.py` Stage 4 调用上下文

**触发条件**: MVP 前 P1（与 UX-3 一起一轮改透前端 wait page + backend stage 进度细化）

#### UX-6: 前端 ETA 在 progress 卡死时无 fallback

**现象**: 当 backend progress 字段长时间不变化（如 1+ min），前端 ETA 公式 `(elapsed / progress) × (1 - progress)` 算出来越来越长（9 → 10 → 11 min），让用户以为越跑越慢。

**修复方案**:
- 方案 A：检测 progress 卡死 30s 不动时，ETA 锁定为最后一次正常计算值（不再增长）。
- 方案 B：ETA 算法换成"按 stage avg time × 剩余 stage 数"，不依赖 progress 字段。
- 方案 C：进度卡死时显示"~"代替具体数字。

**关联文件**: 前端 wait page ETA 计算代码

**触发条件**: MVP 前 P1（独立解决 backend 不修也能改善 UX）


#### UX-7: 整体 ETA 算法需要彻底重做（汇总 UX-3 / UX-6）

**Founder 04-27 T5 测试观察记录**:
```
开始 (Stage 2)         13 min
character_ready 后     20 min  ← 增加（用户阅读时间补进去）
Stage 3 中段           8 min   ← 减少
Stage 3 完成 / Stage 4 启动  9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 min  ← 持续上涨 (Stage 4 实际比估算久)
Stage 4 完成 / Stage 5 启动  6 min   ← 跳到 6 min（Stage 5 启动估算重置）
Stage 5 跑了一会儿        7 min   ← 又开始上涨
```

**核心问题**:
- ETA 没有"全局一致性"，每次 stage 切换重新估算导致跳跃
- ETA 在同 stage 内只单向增长（progress 不动 + elapsed 涨 → ETA 涨），不会因临近完成而稳定下降
- 给用户的体感是"越等越久"而不是"接近完成"，违反用户对加载条的直觉

**应有的体感（重做目标）**:
- ETA 单调下降为主（小幅修正可以，大幅跳变不行）
- 接近 100% 时 ETA 趋近 0
- stage 切换不应让 ETA 跳变（应该是 ETA 持续平滑过渡）

**修复方案选项**:

**方案 A（推荐）**: 后端不再返 estimated_seconds，前端按"基线时间表 + 进度倒推"算
- 维护一份 baseline 时间表（按故事 shot 数 × 每 shot ~1.5 min × stage 权重）
- 前端 ETA = baseline_total × (1 - progress) — 永远跟随 progress 单调下降
- 异常超时时显示"实际比预期久，可能因网络/API 拥堵"提示而不是数字

**方案 B**: 后端按 stage avg 时间累计（不依赖 progress）
- baseline: Stage 1 ~30s, Stage 2 ~2-3 min, Stage 3 ~3-4 min, Stage 4 ~5-6 min, Stage 5 ~6-10 min, Stage 6 ~1-2 min
- ETA = sum(剩余 stage 的 baseline)
- progress 只用于动画，不参与 ETA 计算

**方案 C（最严谨）**: 历史数据驱动
- 收集 100+ 真实生成数据，按 (shots, character count, scene count, style) 维度建估算模型
- 后端启动时按模型预测，运行中按实际耗时校准
- 工程量大，MVP 后做

**临时缓解（MVP 前必做）**:
- 前端 ETA 算法加 monotonicity guard：新 ETA 不允许大于 (旧 ETA - 1.5 × poll interval)
- 也就是说 ETA 至少要按 polling 频率单调下降，杜绝"涨数字"现象
- 即使后端 estimated_seconds 跳变，前端只取下降值

**触发条件**: MVP 前 P1（用户体验关键路径，影响留存）

**关联文件**: 前端 progress polling hook (ETA 计算) / `app/services/pipeline_orchestrator.py` estimated_seconds 字段写入逻辑

**取代/合并**: UX-3 / UX-6 都归入此条统一处理


#### UX-8: 等待页文案 "图像" → "片段"

**现象** (2026-04-27 Founder T5 测试反馈): Stage 5 等待页文案是"已生成 N/18 张图像..."，应改成"已生成 N/18 个片段..."。"图像"对内（开发视角）正确但对用户体感不友好；"片段"更贴合用户心智模型（每张 shot 是叙事片段，不是单纯的图像）。

**修复**: 前端 wait page 文案微调。

**关联文件**: 前端 progress message 显示组件 / `useGenerationStatus.ts` / 后端 `pipeline_orchestrator.py` 中的 `progress_callback("image_generation", X, "已生成 N/M 张图像...")` — 看是后端写死还是前端 i18n 决定改哪边。

**触发条件**: MVP 前 P2（用户体验微调）


#### UX-9: 等待页大标题永远是"正在编写剧本"，不随 stage 变化

**现象** (2026-04-27 Founder T5 测试发现): 不管 backend 进入哪个 stage（screenplay / storyboard / image_generation / completed），等待页大标题都显示"正在编写剧本"。即使 progress=100% / 故事生成完成! / 已生成 18/18 — 标题仍是"正在编写剧本"。

**截图证据**: 100% + "故事生成完成!" + 已生成 18/18 张图像，但顶部大字依然 "正在编写剧本"

**根因**: 前端标题映射可能只在 stage_message 第一次为 "screenplay" 时设置，后续不再更新。或标题逻辑只读 stage 第一次值后缓存了。

**应有行为** (按 stage 切换):
- story_generation: "正在生成故事大纲"
- character_design: "正在设计角色"
- screenplay: "正在编写剧本"
- storyboard: "正在创建分镜"
- image_generation: "正在绘制画面"
- bgm: "正在生成配乐"
- completed: "故事生成完成"

**修复**: 前端 wait page 标题做成纯函数 `getStageTitle(current_stage)`，每次 polling 拉到的 current_stage 都重新映射，不缓存。

**关联文件**: 前端 wait page 组件（StageC/StageD wait 页 / `useGenerationStatus.ts`）

**触发条件**: MVP 前 P1（直接误导用户感知，明显 bug）


#### BE-3 🔴 **CRITICAL P0**: Stage 5 真生图后未写 image_url 到 storyboard JSON

**现象** (2026-04-27 Founder T5 测试发现): Pipeline 完成后 Stage D 预览页**所有 shot 图加载失败**，img alt 显示 "Shot 12" 占位。

**实证**:
```
disk:  output/{uuid}/images/shot_01-18.png ✅ 全部存在
4_storyboard.json: shots[*].image_url = MISSING (全部缺字段) ❌
```

**根因**: Stage 5 真生图分支**没把 image_url 写回 storyboard.shots[*]**。Round 1 修过 SKIP_IMAGE_GENERATION=true 分支的 image_url 写回（pipeline_orchestrator.py SKIP 分支复制 R8 写 image_url），但**真生图分支（IMAGE_GEN_PROVIDER=seedream + SKIP=false）的对应写回逻辑缺失**。

**影响**: **MVP 阻断 bug**。所有用户跑完 pipeline 看不到任何图。

**修复**: `app/services/pipeline_orchestrator.py` Stage 5 主循环（已并行化）中每张 shot 完成后写 `shot["image_url"] = f"/static/outputs/{project_uuid}/images/shot_{NN}.png"` 回 storyboard 字典，最终保存到 4_storyboard.json + chapter.storyboard_json DB 字段。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 5 image generation 完成后的 storyboard update + checkpoint_callback 写 chapter.storyboard_json

**触发条件**: 立即修（P0）— MVP 必修阻断点


#### UX-10: Stage 6 BGM 生成期间无任何 UI 提示

**现象** (2026-04-27 Founder T5 测试发现): Stage 5 18/18 张图完成后，Stage 6 Mureka BGM 生成阶段（~1-2 min）UI 完全没提示"正在生成配乐"。前端进度卡 100% / 文案"故事生成完成!" / 标题仍是"正在编写剧本"，用户以为已结束但实际还在跑 BGM。

**根因**: 已知问题（PENDING 早期记录），Stage 6 BGM 缺 progress_callback。Pipeline 主循环 Stage 5 后直接进 Stage 6 没发 progress 信号给前端。

**修复**: `pipeline_orchestrator.py` Stage 6 启动时调 `progress_callback("bgm", 92, "正在生成配乐...")` + 完成时 `progress_callback("completed", 100, "故事生成完成!")`。

**触发条件**: MVP 前 P1（与 UX-9 一起改透 wait page stage transition）

**关联**: PENDING 早期已记 P2 Backend Stage 6 BGM 生成期间没有 progress_callback

#### UX-11: Pipeline 100% 后未自动跳转 Stage D（卡 ~2 min）

**现象** (2026-04-27 Founder T5 测试发现): Backend 15:35:31 已发 [JobManager] ✅ 生成任务完成，但前端等待页 100% 卡了 ~2 min 才自动跳到 Stage D 预览页。

**根因**: 前端 polling 拉到 `current_stage="completed"` 后没立即 redirect 到 Stage D，可能轮询频率慢或要等下一次 polling tick。

**修复**: 前端 polling 检测到 status=completed 立即 redirect，无需等下一 tick。

**触发条件**: MVP 前 P2（小延迟，但用户等了 30+ min 后这 2 min 显得格外漫长）

#### BE-4: chapter storyboard 端点 404

**现象** (Monitor 抓到): 前端调 `GET /api/projects/{uuid}/chapters/1/storyboard` 返 404 Not Found。

**根因**: 端点不存在或路径错了（可能正确路径是 `/chapters/{n}` 而不是 `/storyboard` 子资源）。

**修复**: 看 frontend 代码确认期望的 URL，对照 backend `app/api/chapters.py` 确认实际注册路径。可能加个端点 alias 或前端改 URL。

**关联文件**: `app/api/chapters.py`、`frontend/src/components/StageD.tsx` (或 fetch 逻辑处)

**触发条件**: 与 BE-3 一并修（MVP 必修）


#### UX-12: 等待页副标题"AI 正在逐张绘制画面"在 Stage 1-4 阶段误导

**现象** (2026-04-27 Founder T5 测试观察): 等待页副标题写"AI 正在逐张绘制画面，可以选择后台生成"，但 Stage 1-4 时根本没在绘制画面（在写大纲/剧本/分镜）。文案与实际不符，进 Stage 5 前都是误导。

**修复**: 副标题做成 stage 感知 — Stage 1-4 显示"AI 正在创作故事"或类似；Stage 5 显示"AI 正在逐张绘制画面"。

**触发条件**: MVP 前 P2

#### ~~UX-13: 等待页静态励志文案~~ — ❌ Founder 04-27 撤销: 这是产品文案告诉用户"中篇支持更长"，不是 bug

**现象** (2026-04-27 Founder T5 测试发现): 等待页中段轮播文案有"中篇模式支持 36 张画面" / "你知道吗？序话支持 28 种视觉风格" 等静态励志短语。但实际故事只有 18 shots（不是 36）。文案是固定励志库，没和当前故事参数绑定。

**修复**: 励志文案库要么去掉具体数字（改泛指"序话支持中长不同长度故事"），要么数字按当前故事参数动态填（"你的故事将由 18 张画面组成"）。

**触发条件**: MVP 前 P2

#### UX-14: 角色预览占位图标用"播放按钮"反直觉 — 合入 UX-1 修复

**现象** (2026-04-27 Founder T5 测试发现): Stage C 角色卡片在确认前没图，占位图标是橙色"播放按钮 ▷"。这是产品全局的图标但在角色场景里**反直觉**（用户期望看到人形 silhouette 头像占位，而不是视频播放图标）。

**修复**: 角色占位图换成人形 silhouette / 半透明头像剪影 / 灰底 + "等待生成"图标。

**触发条件**: MVP 前 P2（与 UX-1 一起改 Stage C 角色页）

#### OBS-1: Seedream 对中文叙事故事 sanitize 触发率偏高

**现象** (2026-04-27 Founder T5 测试观察): 18 shots 中至少 4 张 (shot_06/11/15/16) 触发 InputTextSensitiveContentDetected → sanitize 3 次重试。触发关键词大概率是"红色绸带" "婚礼热闹" "唢呐悲怆"等中国民俗叙事词。

**影响**: 每张被 sanitize 的 shot 增加 78s × N 重试 = +2-4 min 总耗时；额外 ¥0.22 × N 重试成本。中文古风/民俗类故事尤其多发。

**待评估**: 是否值得做"风格预审 + 提前换词"或"sanitize 字典加豫北农村婚礼相关词"先发制人。

**触发条件**: MVP 后观察实际数据再决定（本地 1 次测试样本不够）

#### OBS-2: T5 故事性能 baseline 数据

**记录** (2026-04-27 Founder T5 测试): 18-shot 中篇故事 + 铅笔素描 + Seedream + 3 并发 + 真生图模式实测：
- Stage 1 大纲: ~30s
- Stage 2 角色 LLM: ~1 min
- Stage 3 剧本: ~3 min (7 scenes × 40-50s Sonnet)
- Stage 4 分镜: ~6 min (7 scenes × 40-50s Sonnet)
- Stage 5 真生图: ~10 min (18 shots × 27s 平均 / 3 并发 + sanitize retry)
- Stage 6 BGM: ~1.5 min
- **Total: 36.9 min** (含 ~4 min 用户在 Stage C 确认时间)

**用作**: ETA 算法 baseline 参考（UX-7 修复时用） + Seedream 18-shot 实际成本 baseline (~¥6-8)。

#### OBS-3: 故事内部数字一致性问题（ idea→大纲 LLM 漂移）

**现象** (2026-04-27 Founder T5 观察): 用户输入故事 "统计了二十八对" → LLM 大纲输出 Plot 1 也是"二十八对" → 用户编辑改成"三十二对" → Plot 7 仍是"二十八对"。LLM 在 Plot 7 烧本子时**没看 Plot 1 的数字**，独立用了"二十八对"。

**根因**: Stage 1 outline LLM prompt 没强调"故事内部所有数字/名字/时间必须前后一致"。

**修复**: outline prompt 加一条规则"故事中提及的所有数字/角色名/时间点必须前后保持一致"，或后处理时跑一次自检。

**触发条件**: MVP 前 P2（与 UX-2 一致性校验配合）


#### BE-5 🔴 **CRITICAL P0**: Stage 6 BGM 生成后 bgm_url 没写回 DB（同 BE-3 一类）

**现象** (2026-04-27 Founder T5 测试发现): Stage D 预览页 BgmPlayer 显示 "已消耗 10 credits"（Mureka 真调过 API），但播放按钮按了无声、时长显示 "--:--"、当前位置 "0:00"。BgmPlayer src 为 null。

**实证**:
```
disk:  output/{uuid}/bgm_chapter0.mp3 (3.5 MB) ✅ 存在
/static URL: http://127.0.0.1:8000/static/outputs/{uuid}/bgm_chapter0.mp3 → 200 OK ✅ 可访问
chapter.bgm_url DB 字段: 未写入（推测，导致前端 src=null）
```

**根因**: Stage 6 Mureka BGM 生成完成后**没把 bgm_url 写回 chapter.bgm_url DB 字段**。Round 1 修过 SKIP 模式 + credits_used 写入，但**真生成 BGM 模式下 bgm_url 写回逻辑也缺**（与 BE-3 image_url 同模式）。

**影响**: **MVP 阻断 bug**。所有用户跑完 pipeline 听不到 BGM。

**修复**: `app/services/pipeline_orchestrator.py` Stage 6 BGM 完成后调 `checkpoint_callback("bgm_url", f"/static/outputs/{project_uuid}/bgm_chapter{N}.mp3")` 把 URL 写到 DB chapter.bgm_url。

**关联文件**: `app/services/pipeline_orchestrator.py` Stage 6 BGM 完成后 + `app/services/checkpoint_callback`

**触发条件**: 立即修（P0）— MVP 必修阻断点

**关联**: BE-3 image_url 同根因，**两个一起修**（pipeline_orchestrator Stage 5 写 image_url + Stage 6 写 bgm_url）


#### BGM-1 🔴 outline schema 缺 music_hint 字段（Wave 1 设计字段未实施或被回滚）

**现象** (2026-04-27 Founder T5 测试发现): T5 豫北农村悲伤民俗故事的 BGM 不贴切——听起来像温情怀旧 acoustic 而不是悲怆民俗（应有唢呐+二胡）。

**根因**:
- outline JSON 实际 keys: `mood, emotional_arc, narrative_pace, visual_tone, ...`
- **缺**: `music_hint` 字段（Wave 1 原设计 95 风格各对应一个 hint）
- Haiku 仅靠 `visual_style_hint=pencil_sketch` 推 BGM 风格
- "铅笔素描"传达"轻柔/怀旧/纸感" → Haiku 推成 acoustic guitar / piano，而非悲怆民俗 (应是二胡/唢呐)
- 这正是 PENDING 早期记的 P3 "music_hint 在 Haiku 层效用有限" 的实例

**实证**:
- `app/services/music_generation_service.py` Wave 4 流程完整跑通（meta_version=mixed v3.2，Haiku 747 chars，Mureka 64s succeeded）
- 但 Haiku 输入缺 music_hint 字段，导致输出 BGM prompt 偏离故事真实情绪基调

**修复方案**:
- **方案 A（推荐）**: 在 outline schema 加 `music_hint` 字段 + outline LLM prompt 强调"按风格 + mood + emotional_arc 综合给出 BGM 关键词（如『悲怆唢呐 + 二胡 + 民乐』）"。Stage 1 LLM 直接输出，story_music_extractor 透传给 Haiku。
- **方案 B**: 把 visual_style_hint 改成 `music_style_hint`（独立字段），让用户在 Stage A 选风格时**单独选 BGM 风格**（轻柔/悲怆/史诗等 6-8 种）。
- **方案 C**: 维护一份 95 风格 → music_hint 的字典（AI-ML 早期设计过），后端 Stage 1 后用 visual_style_preset 查表填 outline.music_hint。**最低成本**。

**触发条件**: MVP 前 P1（直接影响 BGM 质量，T5 实测验证 Wave 1 设计字段缺失）

**关联**: 取代 PENDING 早期 P3 "music_hint 在 Haiku 层效用有限" — 实际是字段缺失，不是效用有限

**关联文件**: `app/services/story_outline_generator.py` (outline schema + prompt) / `app/services/story_music_extractor.py` (字段读取) / 95 风格 music_hint 字典


#### ~~UX-15: Stage C 角色 adjust latency~~ — ❌ Founder 04-27 撤销: 估计是沟通间 latency，不是 bug

**现象** (2026-04-27 Founder T5 测试发现): Stage C 焦小顺卡片点"重新生成"后立即截图，描述仍显示"瘦高"（旧），但 backend 已成功改成"匀称"。Founder 等几秒后/刷新后看到正确"匀称"。前端没有立即 re-fetch + re-render。

**根因**: 前端 adjust 成功 callback 后没立即 refresh character data，依赖下一次 polling 才同步。

**修复**: adjust 成功后 immediately re-fetch character data（或 backend 返回 updated character → 前端直接用 response 数据更新 React state）。

**触发条件**: MVP 前 P2

#### OBS-4: Stage B "情绪"字段持久化路径未明

**待 Founder 确认** (2026-04-27): Founder 在 Stage B 编辑大纲时选择了情绪"至于"（疑似笔误 → 应是"释然"或某个枚举值）。但 outline JSON 里没看到 `emotional_tone` 字段（只有 `mood`, `emotional_arc`）。需要排查：
- "情绪"选择是否真传到 backend
- 持久化到 outline 的哪个字段
- Stage 6 Haiku 是否读取了这个值
- 如果是 typo，Stage B 是否应该用枚举下拉而非自由输入

**触发条件**: 与 BGM-1 一起排查（同属 outline schema 完整性问题）

#### OBS-5: 部分功能本次 T5 测试未覆盖

**未测路径** (2026-04-27 Founder T5 测试范围之外):
- Stage C "换发色 / 换服装 / 更年轻 / 更成熟 / 换风格" 5 个微调按钮的实际效果（仅测了自由输入"重新生成"）
- "后台生成，去做别的" 按钮 — 是否真能离开页面后回来继续看进度
- BgmPlayer "换一首"（5 credits）/ "重新生成"（10 credits）按钮
- Stage D 单 shot 编辑 / 重新生成 / 删除（之前 TASK-STAGED-WIRE 接通）
- "确认交付" → 下载漫画包 / 导出视频 流程

**触发条件**: MVP 前必须每条都端到端测一次（建议组合到下次 T6/T7 测试）


#### UX-2 升级补充 (2026-04-27 PM 深挖证据)

**T5 故事内部数字 3 重漂移实证**:
| 位置 | 数字 | 说明 |
|---|---|---|
| 用户原 idea | 28 对 | 输入 |
| Stage B 用户编辑 Plot 1 | **32 对** ✅ | 用户改的，Plot 1 真正生效 |
| Plot 7 LLM 没同步 | **28 对** ❌ | LLM 跨 plot 漂移（**真不一致**）|
| shot_03 chinese_text | **第 33 个叉** ✅ | Founder 04-27 纠正：32 + 即将再吹的 1 次 = 33，**叙事逻辑合理，不是漂移** |

**真实问题（PM 误判已纠正）**: 只是 Plot 1 (32) ↔ Plot 7 (28) 不一致一处。shot_03 的 33 是正确戏剧推演（"已统计 32 个，下一次吹百鸟朝凤就是第 33 个"），LLM 把握剧情数字递进逻辑没错。

**修复方案**:
- **方案 A1（前端校验）**: Stage B 用户改 Plot N 数字时高亮其他 plot 中相同数字
- **方案 A2（后端 outline 内部一致性 LLM check）**: confirm-outline 时跑 Sonnet 4.6 检测内部矛盾，Plot 1 改了 Plot 7 也跟改

**触发条件**: MVP 前 P2（降级，问题局限于 outline 内部 plot 间一致性，不涉及 Stage 3/4 LLM 数字漂移）

#### UX-11 重定义 (2026-04-27 Founder 反馈)

**Founder 答**: 100% 后卡 ~2 min 的本质是 BGM stage 完成信号没传给前端，做好 Stage 6 BGM 完成后立即 progress_callback("completed", 100, "故事生成完成") + 前端检测到立即 redirect Stage D，问题就解决。

**修复方案确认**:
- backend `pipeline_orchestrator.py` Stage 6 BGM 写完 chapter.bgm_url 后立即 `progress_callback("completed", 100, "故事生成完成")`
- 前端 polling 检测到 `current_stage="completed"` → 立即 redirect Stage D，不等下一 tick

**关联**: 与 UX-10 (BGM 期间无提示) + BE-5 (bgm_url 写回) 同一处改

#### UX-14 合入 UX-1 (2026-04-27 Founder 反馈)

**Founder 反馈**: silhouette = 人形剪影/灰底人形占位图。Founder 倾向方案 A — Stage 2 提前生真 portrait，直接用真图当 Stage C 卡片，不需要 silhouette。

**结论**: UX-14 不再需要单独修，**完全合入 UX-1**：Stage 2 提前生 portrait 后 Stage C 卡片用真 portrait（不再有占位图标问题）

#### OBS-4 升级 P1 bug (2026-04-27 PM 深挖实锤)

**Founder 04-27 反馈**: Stage B 选择的"情绪"想写的是 **"治愈"**（healing）。

**实证**: outline JSON 全文 grep "治愈" → **0 命中**。
- outline.mood = "感人"（generic 默认值）
- outline.emotional_arc = anxious_superstitious_dread → bittersweet_self_confrontation（LLM 自己定的，跟"治愈"完全不一致）
- 故事最终基调（外婆面馆 + 妻子离开 + 漫长悲怆）也跟"治愈"不沾边

**根因（推测）**:
- Stage B "情绪选择"前端控件值未传给 backend
- 或传给 backend 但被丢弃
- 或传给 outline LLM 但 LLM 用 mood/emotional_arc 自定义未读用户偏好
- 与 BGM-1 同属 "outline schema 字段缺失或不传到 LLM" 一类

**修复方案**:
- 排查 Stage B 前端"情绪"控件 → confirm-outline API 链路
- backend confirm-outline 端点是否接收并存"情绪"字段（如 emotional_tone）
- outline LLM prompt 是否注入用户选定的情绪基调
- 修通后 outline.mood / emotional_tone 字段就反映用户选择

**升级**: P1 bug（影响故事核心情绪基调，同 BGM-1 严重）

#### OBS-5 处理结论 (2026-04-27 Founder 反馈)

**Founder**: "可以修复优化更新后下一次测" — 不阻塞当前修复批次，下一次 T6/T7 测试覆盖。


---

### 🆕 TASK-T5-FIXBATCH 14 条修复全部完成 (2026-04-27 16:36)

**状态**: 🔄 修复完成 → 待 @tester Phase 2 端到端验证 + Founder 主观验收

**Phase 1 完成内容**:
| 类别 | 条目 | 修复者 |
|---|---|---|
| P0 (3) | BE-3 / BE-4 / BE-5 | @backend ✅ |
| P1 后端 | BGM-1 / OBS-4 / UX-10/11 / UX-1+14 | @backend ✅ |
| P1 前端 | UX-7 / UX-9 / UX-11(FE) / UX-1(FE) | @frontend ✅ |
| P1 AI-ML | BGM-1 字典 (95 风格) | @ai-ml ✅ |
| P2 后端 | UX-2 A2 outline 一致性 LLM check | @backend ✅ |
| P2 前端 | UX-2 A1 / UX-8 / UX-12 | @frontend ✅ |

**测试验收**:
- ✅ Backend: 211/211 unit tests (7 architecture + 17 parallel + 187 music_hint)
- ✅ Frontend: npm run build 20 routes 0 errors

**Phase 2 待启动**: @tester
- T6 全新故事端到端跑通验证 14 条修复
- OBS-5 未测路径覆盖 (5 个微调按钮 / 后台生成 / BGM 换一首/重新生成 / Stage D 单 shot 编辑 / 确认交付)


#### UX-16 ✅ Create 页 URL dynamic route — 已修复 (2026-04-28 15:06 Wave 1.2 Agent C)

**完成实现**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage 6 枚举值 (outline / characters / scenes / generating / preview / delivery)

**新建/改动文件**:
- 新建 `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` — Dynamic route 入口 + isUrlStage 校验 404
- 新建 `frontend/src/lib/createUrl.ts` — URL ↔ state 映射 + reconcileBackendVsUrl 决策树
- 改 `frontend/src/app/create/CreateContent.tsx` — hydrate hook + state↔URL 双向同步（push/replace 区分 + echo guard + completion guard）
- 改 `frontend/src/contexts/CreateContext.tsx` + `frontend/src/types/create.ts` — HYDRATE_FROM_BACKEND action

**验收**:
- ✅ npm build 21 routes 0 errors
- ✅ HTTP smoke: 6 valid stages 200, invalid 404, dashboard 不破坏
- ✅ 4 核心场景 trace: F5 刷新 / 浏览器后退 / 复制链接 / 跨 stage 切换全过

**详细完成报告**: TEAM_CHAT 2026-04-28 15:06 条目 + frontend-progress/completed.md

**已知遗留**: hydrate 后 StageC START_GENERATION reset progress 短闪 ~1.6s（轻微，下批优化）


#### UX-17 P1 Stage E 预览页右侧故事文本显示 original_idea 而非用户编辑后大纲

**现象** (2026-04-27 Founder T5 测试发现): Stage E 项目预览页右侧故事描述区域显示用户原始 idea 文本（"统计了二十八对"），即使用户在 Stage B 编辑大纲改成"三十二对"，预览页仍显示原 idea。

**实证**:
- `project.original_idea` = "...统计了二十八对..." (用户原文)
- `chapter.summary` = "《百鸟朝凤》不能给活人吹" (短标题)
- `outline.plot_points[0].content` = "...三十二对..." (用户 Stage B 改的)
- 截图右侧显示 = `project.original_idea` (含"二十八")

**根因**: Stage E 前端组件读 `project.original_idea` 字段做故事描述展示，没读用户编辑后的 `outline.summary` / `outline.confirmed_outline_json` 等综合内容.

**预期行为**: 预览页应展示**用户最终确认后的故事内容**（如 outline.summary 或 chapter.summary 详细版），不是用户灵感笔记原文.

**修复方案**:
- **方案 A**: 前端 Stage E 改读 `outline.summary` 或 `chapter.summary` (详细版) 字段
- **方案 B**: 后端在 chapter 表加 `final_synopsis` 字段（综合 plot_points + summary 的最终故事介绍），Stage 4 完成后写入. 前端读这字段
- **方案 C**: 前端用 outline.plot_points 拼接生成"故事简介"显示

**触发条件**: MVP 前 P1（用户编辑没在最终产物体现，违反"所见即所得"原则，跟 BGM-1 / OBS-4 / UX-2 同一类）

**关联文件**: `frontend/src/components/StageE.tsx` (或预览页组件) / `app/api/chapters.py` (如方案 B)



---

## TASK-T5-FIXBATCH-R5 ChapterStory Schema Hotfix ✅ 完成 (16:50)

**根因**: ChapterStory Pydantic schema 跟 chapter.scenes_json 实际字段分叉 → 41 validation errors → /chapters/{n}/story 端点 500
**修复**: app/schemas/chapter.py 删 SceneInfo / CharacterInfo, scenes/characters 改 list[dict[str, Any]]
**验证**: 211/211 pytest + /story 401 (auth) 不再 500

---

## TASK-T5-FIXBATCH-R6 Stage E dashboard 详情页 7 Bug (17:20 派发)

| Bug | 严重度 | Owner | 状态 |
|-----|:-:|:-:|:-:|
| A 故事不存在闪 10s | P0 | frontend | 派发中 |
| B shots 7 vs 18 (fetch 错 endpoint) | P0 | frontend | 派发中 |
| C 缩略图全黑 (imageUrl null hardcoded) | P0 | frontend | 派发中 |
| D summary 显示标题非大纲 | P1 | frontend + backend | 派发中 |
| E 情绪基调硬编"待生成" | P1 | frontend + backend | 派发中 |
| F 角色无 portrait | P1 | frontend | 派发中 |
| G 无 BGM player | P2 | frontend | 派发中 |

**串行派发**: backend (5-8 min) → frontend (20-25 min)

**关联文件**:
- backend: `app/schemas/project.py` + `app/api/projects.py`
- frontend: `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` + `frontend/src/types/create.ts`



---

## TASK-T5-FIXBATCH-R7 候选 (2026-04-27 21:00 PM 深度诊断)

> Founder R6 修复后验收 dashboard，发现 dashboard **列表卡片** + **详情页 5 按钮** 仍有问题。R6 仅修了 `dashboard/[storyId]/StoryDetailContent.tsx` 详情页，**没碰列表页**和**modal 实现**。

### ✅ R7-1 P1 Dashboard 列表卡片 4 个 bug — 全部完成 ✅ (Backend Agent D 2026-04-28 16:00 + Frontend Agent E 2026-04-28 16:30)

**文件**: `frontend/src/contexts/AuthContext.tsx` `mapProject()` 函数 (L67-80)
**也涉及**: `frontend/src/components/dashboard/StoryCard.tsx` (展示组件)

**根因清单**:

| # | 现象 | 根因 (位置) | 验证证据 |
|---|------|-----------|---------|
| 1 | 缩略图永远是橙色 logo 占位 | AuthContext.tsx L71 `coverImageUrl: "/brand/logo-48.png"` hardcoded | 没读 storyboard.shots[0].image_url |
| 2 | 故事列表"0 shots" 永远显示 | AuthContext.tsx L74 `shotCount: 0` hardcoded | mapProject 仅 fetch `/api/projects/`，没 fetch chapter / storyboard 数据 |
| 3 | 时间显示 "4/27 07:10"（北京下午测试时） | backend `created_at = datetime.utcnow()` 字符串没带时区标记 → 前端 `toLocaleDateString("zh-CN")` 按 UTC 渲染 | UTC 07:10 + 8h = 北京 15:10（接近测试时段） |
| 4 | "共 0 张画面" 数据卡片永远 0 | DashboardContent.tsx L27 `totalShots = stories.reduce((sum, s) => sum + s.shotCount, 0)` | 因 #2 hardcoded 0 → 累加永远 0 |

**修复方案**:
- **方案 A 推荐 (后端扩列表端点)**:
  - backend `GET /api/projects/` 响应每条加 `cover_image_url` (storyboard.shots[0].image_url) + `shot_count` (storyboard 长度) + `mood` (confirmed_outline.mood)
  - frontend mapProject 直接读这些字段
  - backend datetime 序列化用 `.isoformat() + "Z"` 或 ISO with timezone
- **方案 B (前端额外 fetch)**:
  - 不改后端，前端在 mapProject 后并行 fetch 每个 project 的 storyboard endpoint — N+1 query 风险大，不推荐

**预估**: backend ~10 min + frontend ~10 min = ~20 min 串行

**Frontend Agent E 完成内容 (2026-04-28 16:30)**:
- `AuthContext.tsx` `ApiProject` 接口加 `cover_image_url / shot_count / mood`；`mapProject()` 用 `toAbsoluteUrl()` 转封面 + fallback logo + 读 shot_count + mood + ISO Z 时间直接赋值
- `types/create.ts` `StoryCard` 加 `mood: string | null`
- `StoryCard.tsx` metadata 行 mood badge 条件渲染
- `mock-data.ts` 6 条 mock 补 mood 字段
- npm build 21 routes 0 errors ✅

### 🟡 R7-2 P2 详情页右上角 5 按钮 4 个 Mock 占位

**文件**: `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` + 各 modal 组件

**实情清单**:

| 按钮 | 真实功能 | 文件 | 状态 |
|-----|---------|------|:-:|
| ❤️ 点赞 | `setIsFavorite` 仅 local state，无 API persist | StoryDetailContent.tsx L324 | ❌ Mock |
| 🔗 分享 | ShareModal 用 `Date.now()` 生 fake link `/s/{时间戳}` | components/ui/ShareModal.tsx L15 mockLink | ❌ Mock |
| 📋 做同款 | `router.push /create?style=...&length=...` 真路由 | StoryDetailContent.tsx L297-299 | ✅ 真 |
| ⬇️ 导出 | ExportModal `onExport` callback 空函数 `() => {}` | StoryDetailContent.tsx L485 | ❌ Mock |
| 🎬 合成视频 | VideoSynthesisModal 仅 setInterval 模拟 progress 动画，无真合成 | components/ui/VideoSynthesisModal.tsx L17-25 | ❌ Mock |

**修复方案**:
- 点赞: backend `/api/projects/{id}/favorite` toggle endpoint + projects 表加 `is_favorite` 列
- 分享: backend 生 share token + 公开页面（`/s/{token}` 真路由）— 中等工作量
- 导出: backend `/api/projects/{id}/export?format=...` 打包 zip 返回（图片 / 图+音频 / 全部素材）— 大工作量
- 合成视频: 调 ffmpeg 拼接 shots + BGM + 旁白（需 TTS pipeline 接通） — 大工作量，可能整体留给 MVP 后

**触发条件**: MVP 后讨论（不阻塞 MVP，因为详情页核心展示已 OK）

### 📊 T5 老数据局限说明（已知）

T5 项目 (uuid `283bd407-0e64-43bb-b2eb-8f6b4063c4af`) 是 R6 修复**之前**创建的：
- `characters_json[*].portrait_url=None` → silhouette fallback 生效（**预期**，T6 新故事会有真 portrait，因为 UX-1 修了 Stage 2 portrait 提前生成）
- `confirmed_outline.user_selected_mood=None` → fallback 到 `confirmed_outline.mood="感人"`（OBS-4 是新逻辑，T5 没经过新流程）

### ✅ T5 详情页旁白验证（PM 直查 DB 实证不是 bug）

Founder 怀疑旁白可能"瞎编"或"按 scene 复用"，PM 直查 DB 证伪：

```
shot[0] scene_id=2 narration_segment[:50]='管家是个惯于用沉默施压的人，那叠钞票拍下去...'
shot[1] scene_id=2 narration_segment[:50]='门缝里，焦小顺的一只眼睛圆睁着，左手腕上那条褪色的红腕带...'
shot[2] scene_id=2 narration_segment[:50]='那一夜漫长得像是被人刻意拉长，焦立河坐在那叠钱和那把唢呐之间...'
```

- 同 scene_id=2 但 3 个 shot narration_segment **完全不同**
- Stage 4 storyboard director 给每个 shot 单独写旁白
- 前端 L116 `narrationSegment: shot["narration_segment"]` 直读 storyboard 真字段
- **结论**: 旁白功能完全正确，无需修复

### 🟢 T6 新 pipeline 测试 — 完全可以立即跑

**理由**:
- R6 仅改 `app/schemas/project.py` + `app/api/projects.py` + `dashboard/[storyId]/StoryDetailContent.tsx` + `frontend/src/types/create.ts`
- R6 **未碰** pipeline 任何代码（image_generator / storyboard_service / pipeline_orchestrator 等 mtime 全是 R4-R5）
- 创建流程 StageA→E 跟 dashboard 详情页是**两套独立组件**，零交互
- 跑 T6 的预期效果（前面 T5-FIXBATCH 14 + R5 + R6 全部生效）:
  - 真 portrait (UX-1 修了 Stage 2 portrait 提前生成)
  - user_selected_mood 持久化 (OBS-4)
  - 真 image_url 写回 (BE-3)
  - 真 bgm_url 写回 (BE-5)
  - 正确风格的 BGM (BGM-1 + 95 风格字典)
  - ETA 单调下降 / 大标题随 stage / 文案"片段" / 100% 自动跳 Stage D (UX-7/9/8/11)

**已知 T6 caveat**:
- 跑完进 dashboard **列表**仍显示 "0 shots" + 时区错（R7-1 未修）
- 但点进**详情页**完全正确（18 shots + 真 portrait + 200 字大纲 + 真 mood + BGM）



---

## 🟡 P2 Frontend `sharp` missing in production mode (2026-04-27 21:10 monitor 触发)

**现象**: frontend npm start (production standalone) 模式下 next/image 渲染时报错：
```
⨯ Error: 'sharp' is required to be installed in standalone mode for the image optimization to function correctly.
Read more at: https://nextjs.org/docs/messages/sharp-missing-in-production
```

**触发频率**: 每次 next/image 组件渲染都会触发（dashboard logo / StoryCard 缩略图等），9+ 次/页面加载

**影响**:
- ⚠️ 控制台日志噪音
- ✅ 实际图片仍能 fallback 显示（next/image 优化失败后回退原始 URL）
- 🔍 next/image 优化未生效（图片不会被自动 resize / format 转换 / lazy load 优化）

**根因**: Next.js 14 standalone production mode 要求 `sharp` 库做图片优化。`package.json` dependencies 没装 sharp。本地 dev 模式（`npm run dev`）不需要，但 `npm start` (production) 需要。

**修复 (1 行)**:
```bash
cd frontend && npm i sharp
# 重启 frontend
```

**触发来源 (非本次 R6)**: 旧代码已有 next/image 调用：
- `frontend/src/app/dashboard/DashboardContent.tsx` (L41 logo)
- `frontend/src/components/dashboard/StoryCard.tsx` (cover image)
- 其他 layout 组件

R6 改动 StoryDetailContent.tsx 用的是 `<img>` 标签（非 next/image），未新增 next/image 调用。

**触发条件**: P2 — 不阻塞功能（图片仍能显示），仅控制台噪音 + 优化失效。本次干净重启时一并修复（npm i sharp）。



---

## 🟠 R7-3 + R7-4 配套修复 (2026-04-28 11:18 T6 实测发现)

### 背景
T6 测试时 Founder 在 StageC 用 `/characters/{id}/adjust` 调整林晓苗"马尾辫→黑长直发"，但发现：
1. Backend `adjust_character()` (app/api/projects.py L684-822) 只更新 description / physical / clothing 字段，**不重新生成 portrait** → 老 portrait_v1（马尾辫）跟新描述（黑长直发）不一致
2. Stage 5 prep `generate_character_multi_refs()` 无条件重生 portrait + fullbody，**Stage 2 提前生的 portrait 被浪费**

### R7-3 P1 — adjust API 触发 portrait 重生
**文件**: `app/api/projects.py` `adjust_character()` L684-822
**修复**: L810 后补：
```python
# 7. 重新生成 portrait（用新描述）
from app.services.reference_image_manager import ReferenceImageManager
_ref_manager = ReferenceImageManager()
_portrait_result = await _ref_manager.generate_character_reference(
    character=updated_char_with_id,
    project_style=ProjectStyleConfig(style_preset=project.style_preset),
    image_generator=image_generator,  # 需要从 dependency injection 拿
    ref_type="portrait",
)
if _portrait_result.get("success") and _portrait_result.get("pil_image"):
    _portrait_path = os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
    _portrait_result["pil_image"].save(_portrait_path)  # 覆盖老 portrait
    chars_list[char_index]["portrait_url"] = f"/static/outputs/{project_id}/character_refs/{char_id}_portrait.png"
    chars_list[char_index]["updated_at"] = datetime.utcnow().isoformat()  # 给 R7-4 用
    chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
```
**工时**: ~10 min

### R7-4 P2 — Stage 5 prep 复用最新 portrait（freshness check）
**文件**: `app/services/pipeline_orchestrator.py` L585-615 (Stage 5 prep loop) + `app/services/reference_image_manager.py` `generate_character_multi_refs()` L164-236
**修复**:
1. pipeline_orchestrator Stage 5 prep loop：传入已有 portrait 作 seed_image 跳过 portrait 重生
   ```python
   for char in char_list:
       char_id = char.get("id")
       existing_portrait = char.get("portrait_url")
       portrait_seed = None
       if existing_portrait:
           local_path = existing_portrait.replace("/static/", "static/")
           if os.path.exists(local_path):
               portrait_mtime = os.path.getmtime(local_path)
               char_updated_at = char.get("updated_at_ts", 0)
               if portrait_mtime > char_updated_at:
                   portrait_seed = Image.open(local_path)  # 复用
       
       await ref_manager.generate_character_multi_refs(
           character=char, ..., 
           seed_image=portrait_seed,  # 传入则跳过 portrait 生成
           skip_portrait=portrait_seed is not None,  # 新增参数
       )
   ```
2. `generate_character_multi_refs()` 加 `skip_portrait` 参数：
   ```python
   if not skip_portrait:
       portrait_result = await self.generate_character_reference(..., ref_type='portrait')
   else:
       portrait_image = seed_image  # 用传入的复用 portrait
   # fullbody 部分不变
   ```
**工时**: ~15 min

### 成本节省 (NB2 $0.067/张)

| 场景 | 现状 | R7-3 only | R7-3 + R7-4 |
|------|:-:|:-:|:-:|
| 用户不 adjust | 3 张/角色 (浪费 1) | 3 张 (浪费 1) | 2 张 ✅ |
| 用户 adjust 1 次 | 3 张 (portrait 不一致) | 4 张 (浪费 1) | 3 张 ✅ |
| 用户 adjust N 次 | 3 张 (不一致) | 3+N 张 (浪费 1) | 2+N 张 ✅ |

每 T6 类项目（3 角色）省 ~$0.20 NB2 成本。

### 验证 T6 现状
- T6 (project_id=15) char_003 林晓苗:
  - 11:03:55 portrait_v1 (马尾辫) 已生 ✅
  - 11:12:15 adjust 写描述"黑长直发" ✅，**portrait 仍是 v1 马尾辫** (R7-3 未修)
  - Stage 5 prep 时 portrait_v2 会用新描述覆盖 v1（current behavior, R7-4 未修就会发生这次浪费）
- 最终 18 shots 林晓苗 = 黑长直发 (因 fullbody 用 portrait_v2 作 ref)

### 必须配套修
**警告**: 单修 R7-3 不修 R7-4 反而**增加浪费**（adjust 重生 + Stage 5 又重生 = 两次重画）。这两条必须一起修。



---

## 🔴 R7-5 P1 Stage label system-wide 错位 (2026-04-28 11:21 T6 实测发现)

**现象**: Founder T6 测试时 Stage 3 ScreenplayWriter 已在跑（11:20:10 启动），但前端大标题显示"正在设计角色"。

**根因 (pipeline_orchestrator.py)**: 3 处 progress_callback 都用"上一个 stage 名"而不是"即将进入的 stage 名"：

| Line | 当前 | 应改为 |
|------|------|--------|
| L338 | `progress_callback("story_generation", 5, "大纲生成完成，正在设计角色...")` | `progress_callback("character_design", 5, ...)` |
| L488 | `progress_callback("screenplay", 35, "剧本编写完成，正在创建分镜...")` | `progress_callback("storyboard", 35, ...)` |
| L528 | `progress_callback("storyboard", 65, "分镜创建完成，正在生成图像...")` | `progress_callback("image_generation", 65, ...)` |

**实际影响**: 整个 pipeline 大标题滞后一个 stage：

| 实际 backend 跑 | 当前显示 | 正确显示 |
|------|------|------|
| Stage 2 角色 | "正在生成故事大纲" | "正在设计角色" |
| Stage 3 剧本 | "正在设计角色" | "正在编写剧本" |
| Stage 4 分镜 | "正在编写剧本" | "正在创建分镜" |
| Stage 5 真生图 | "正在创建分镜" | "正在绘制画面" |
| Stage 6 BGM | "正在绘制画面" | "正在生成配乐" |

**触发条件**: 体验 P1（用户始终看到比实际滞后一阶段的标题），MVP 前必修

**工时**: ~5 min backend 改 3 行

**关联**:
- 已知 Phase 1 修 UX-9 时漏改这 3 处
- 实际这是 progress_callback 的"语义模式"问题 — 应该在 stage 启动时设新 label，不是完成时回头设



---

## 🟡 R7-6 P2 StageC checkpointPreview 文案错位 (2026-04-28 11:28 T6 实测)

**现象**: Founder T6 测试时 progress 从 39% 一次性跳到 65%（Stage 4 完成 → Stage 5 启动），中间 55-63% 区间一闪而过，触发显示"即将到达角色预览检查点"，但用户**早已经过角色预览**（Stage 2 → character_ready 时已过，那时 progress=10%）。

**文件**: `frontend/src/components/create/StageC.tsx` L209-214

```ts
const checkpointPreview = (() => {
  const progress = state.generationProgress;
  if (progress >= 55 && progress <= 63) return "即将到达角色预览检查点";
  return null;
})();
```

**根因**: 老代码 stale — 假设 progress 55-63% 区间是角色预览检查点。实际 pipeline 架构已变：
- 角色预览检查点 = Stage 2 完成 = `character_ready` stage = progress 10%
- progress 55-63% 实际是 Stage 4 分镜尾声 → Stage 5 真生图启动
- 二者完全错位，misleading 用户以为还要回去看角色

**修复方案**:
- **方案 A 推荐**: 直接删除 `checkpointPreview` 这段（L209-214 + L调用处），整段语义已死
- **方案 B**: 改成 `if (stage === "character_design" && progress < 10)` 仅在角色设计前才显示

**触发条件**: P2 体验，仅在 progress 跨 55-63% 区间瞬间出现，多数用户可能注意不到，但增加困惑

**工时**: ~3 min frontend

**关联**: 这种"老代码假设跟新架构错位"在 pipeline 多次重构后是常见 patten — R7-5 也是同类（progress_callback stage 名跟实际 stage 错位）



---

## 🟠 R7-7 P1 ETA 算法 stage 速率差异 (2026-04-28 11:32 T6 实测)

**现象**: Founder T6 进度 65%（Stage 5 真生图刚启动）时 ETA 显示"1 分钟"，但实际真生图 18 张 max_concurrent=3 至少需要 ~5 min。**严重低估**。

**根因**: `frontend/src/components/create/StageC.tsx` L177-186 fallback 线性外推：
```ts
const totalEstimated = elapsed / (progress / 100);
const remaining = totalEstimated - elapsed;
```
假设速率均匀，但实际不同 stage 速率差异巨大：
- Stage 3 剧本（10-35%）：1 min → 速率快（25%/min）
- Stage 5 真生图（65-90%）：5 min → 速率慢（5%/min）
- 算法用 Stage 1-4 平均速率算到 Stage 5，错估为 1 min

**关键发现**: Frontend L173-176 已预留 backend 主导路径：
```ts
const backendSec = backendEstimatedSecondsRef.current;
if (backendSec !== null && backendSec > 0) {
  rawSec = backendSec;
}
```
但 backend 没给 `estimated_remaining_seconds` 字段。

**修复方案 (推荐 A — backend 主导)**:
- `app/services/pipeline_orchestrator.py` 在每次 `progress_callback` 时计算 stage-specific ETA：
```python
STAGE_DURATIONS = {
    "story_generation": 60,
    "character_design": 120,
    "screenplay": 60,
    "storyboard": 300,
    "image_generation": 300,
    "bgm": 120,
}
def estimate_remaining(current_stage: str, stage_progress: float) -> int:
    seq = ["story_generation","character_design","screenplay","storyboard","image_generation","bgm"]
    idx = seq.index(current_stage)
    remaining = STAGE_DURATIONS[current_stage] * (1 - stage_progress)
    for s in seq[idx+1:]:
        remaining += STAGE_DURATIONS[s]
    return int(remaining)

# progress_callback 改 signature 加 estimated_remaining_seconds
await progress_callback(stage, progress, message, estimated_remaining_seconds=...)
```
- `app/services/job_manager.py` 写入 `job.estimated_remaining_seconds` (新列) 或 status response 直接返
- `app/api/chapters.py` `/status` 返回 `estimated_remaining_seconds` 字段
- frontend 自动 pickup（已就绪）

**工时**: ~15 min backend + 0 frontend

**触发条件**: P1 体验 — ETA 严重低估让用户以为快好了，等 5 倍时间会失耐心

**关联**:
- UX-7（已修，monotonicity guard）只保证 ETA 不增长，不解决速率不均
- 跟 UX-3（卡帧不同步）部分关联



---

## 🔴 R7-5 补充 — Stage 5 prep 阶段实测滞后量 (2026-04-28 11:34 T6)

### Founder 实测：滞后 ~4 分钟

| 时间 | Backend 实际工作 | Frontend 大标题 | 状态 |
|------|----------------|--------|:-:|
| 11:30:00 | Stage 4 分镜完成 → Stage 5 prep 启动（生场景参考图）| "正在创建分镜" | ❌ |
| 11:30-11:34 | Stage 5 prep 4 分钟（场景参考图 / fullbody / 角色 refs setup）| "正在创建分镜" | ❌ |
| 11:34:20 | Shot 1/21 真生图启动 → backend 设 stage="image_generation" | "正在绘制画面" | ✅ |

**滞后量**: ~4 分钟。整个 Stage 5 prep 期间用户看到的都是"正在创建分镜"，跟实际 backend 工作不符。

### R7-5 更深本质（不止 3 行修复）

之前 PENDING 列了 3 处 progress_callback (L338/L488/L528) stage 名错位。**实际更深问题**: 整个 progress_callback 设计模式 — **都在 stage 完成时设 stage 名（命名为已完成的 stage）**，不是 stage 启动时设新 stage 名。

这导致：
- Stage 5 prep 工作（场景参考图 / fullbody）持续 ~4 分钟，期间 stage 还是上一个 "storyboard"
- 用户体感：每个阶段切换都滞后 stage 真正切换时间 1-4 分钟

### 推荐架构修复（升级版）

**方案 B**（升级 R7-5）：拆分 stage 粒度 + stage 启动时立刻设
- 加 `image_preparation` stage（场景参考图 + fullbody，progress 65-75%）
- 加 `image_generation` stage（真 shots 生成，progress 75-90%）
- 每个 stage 入口立刻调 progress_callback 设新 stage 名
- 不在 stage 完成时设上一个 stage 名

**最简方案 A**（已记 R7-5 的 3 行修）只解决"label 错位"，不解决"滞后量"。

工时：方案 B ~30 min backend（增 stage + 改 4-5 处 callback）



---

## 🆕 TASK-T6-FIXBATCH (2026-04-28 T6 测试发现 + 规划)

> **范围**: T6 端到端测试 (10:57-11:50) 暴露 + PENDING 旧账整合 = 39 项修复
> **Founder 决策 (2026-04-28 ~12:00)**: 全部要修，Wave 1 风险最低分两阶段，ARCH-1 抽到 Wave 2，Tester T7 真生图（控制成本），UX-16 用方案 A dynamic route

### T6 新发现 5 条（R7-8 ~ R7-12）

#### 🟡 R7-8 P2 — Stage 5→6 切换 progress 倒退 95% → 92%
- **现象**: T6 11:44 Stage 5 真生图 21/21 完成（前端 95%）→ Stage 6 BGM 启动后倒退到 92%
- **根因**: `app/services/pipeline_orchestrator.py` L968 `progress_callback("bgm", 92, ...)` 写死 progress=92，覆盖 Stage 5 最后到的 95%。UX-7 monotonicity guard **只管 ETA 不管 progress**
- **修复**: BGM 入口 progress 改成 `max(current_progress, 92)`，并升级 UX-7 加 progress 单调 guard（架构层 A-4）
- **工时**: 5 min（与 P1-2 合并）

#### 🔴 R7-9 P0 — 完成时大标题倒退到"正在生成故事大纲"
- **现象**: T6 11:45 status='completed' 时前端大标题显示"正在生成故事大纲" + tip "把你最喜欢的电影情节用一句话描述..."
- **根因实锤**: `job.current_stage = 'story_generation'`（应 `'completed'`） — backend mark_completed 把 stage 重置回 Stage 1
- **关联**: 与 PENDING 早期 "MVP 后 P2 #1" (`job_manager.py:302`) 是**同一根因**，本次升级到 P0
- **修复**: `app/services/job_manager.py` mark_completed 设 `stage='completed'`，前端 STAGE_LABEL["completed"] 已就绪
- **工时**: 5 min

#### 🟡 R7-10 P2 — 完成态副标题文案冲突
- **现象**: 100% 时同时显示"即将完成" + "故事生成完成！"（两个 UI 区域读不同源）
- **根因**: 一个区域读 progress 阈值（>95%→"即将完成"），一个读 message（"故事生成完成"）。状态机不统一
- **修复**: `frontend/src/components/create/StageC.tsx` 统一读 message，stage='completed' 直接走完成态
- **工时**: 5 min

#### ⚪ R7-11 P3 — 100% 完成后 carousel tip 还在 rotation
- **现象**: 完成态弹"把你最喜欢的电影情节用一句话描述..." 与场景脱节
- **根因**: `frontend/src/components/create/StageC.tsx` CAROUSEL_TIPS setInterval 没在 stage='completed' 时停止
- **修复**: useEffect 依赖加 stage，completed 时 clearInterval
- **工时**: 3 min

#### 🔴 R7-12 P0 — StageD 预览图 + 配乐全部 404（**Founder 当前阻塞**）
- **现象**: T6 跳转后 21 张 shots 全显示破图标，配乐 0:00 / --:-- 不响
- **根因实锤**: `frontend/src/components/create/StageD.tsx` L186-188 `<img src={currentShot.imageUrl}>` + bgm src 缺 `toAbsoluteUrl()` 转换。浏览器把 `/static/...` 解析为 `http://localhost:3000/static/...` → frontend port 没代理 static → 404
- **实证**: backend HTTP `localhost:8000/static/outputs/.../shot_01.png` 返 200 / 3MB / bgm 3.6MB ✅。Dashboard 详情页 `StoryDetailContent.tsx` L121 已有 `toAbsoluteUrl(rawImageUrl)` 工作正常 — StageD 漏了
- **关联**: 与 PENDING 早期 "MVP 后 P2 #3" (StageD imageUrl=null fallback) 同文件不同问题，本次升级到 P0
- **修复**: StageD 引入 `toAbsoluteUrl()` 包裹所有 `/static/...` 路径
- **工时**: 10 min

### F-1 P0 — StageC 角色预览看不到 portrait（T6 早期发现）
- **现象**: T6 11:08 StageC 全 silhouette 占位，DB 实际 3 个 portrait 全已写入
- **根因**: `frontend/src/components/create/StageC.tsx` L295-309 `character_ready` handler 读 `state.outline.characters` 取 `c.portrait_url`，但该字段写在 `chapter.characters_json` 不在 outline → 永远 null
- **修复方案 A**: character_ready 触发后 fetch `/api/chapters/{n}/story` 拿 chapter.characters，从那里读 portrait_url
- **工时**: 15 min

### F-2 P1 — StageC 角色卡刷新按钮 mock
- **文件**: StageC.tsx L732-735 `handleRegenerate()` 是纯 mock setTimeout 2s
- **修复**: 接 backend `/api/projects/{id}/characters/{char_id}/regenerate-portrait` 端点（与 R7-3 backend 一并实现）
- **工时**: 15 min（与 R7-3 backend 联调）

---

## 📋 修复总规划（4 Wave）

### Wave 0 — PM 文档收尾 ✅ (2026-04-28 12:05 进行中)
- PENDING.md 写本任务（本条目）
- TEAM_CHAT.md / pm-progress / TODAY_FOCUS 更新

### Wave 1 第一阶段 — Backend A ✅ + Frontend B ✅ 并行完成 (2026-04-28)

#### 🟦 Agent A (Backend Sonnet 4.6) ✅ 完成 + 修复 round 1 完成 ✅
集中修 pipeline_orchestrator + job_manager + projects.py + reference_image_manager（避免 merge 冲突）：

| 项 | 描述 | 文件 | 状态 |
|----|------|------|------|
| P0-2 | mark_completed 设 stage='completed' 不是 story_generation (R7-9 / 旧 P2 #1) | `job_manager.py:302` | ✅ |
| P1-1 | Stage label 重构方案 B：拆 image_preparation/image_generation 粒度 + stage 入口立即 callback (R7-5 + B-3 + B-4 + 架构 A-1) | `pipeline_orchestrator.py` 多处 | ✅ |
| P1-2 | ETA backend 主导：STAGE_DURATIONS 字典 + estimate_remaining() + /status 返 estimated_remaining_seconds + UX-7 升级管 progress 单调 (R7-7 + R7-8 + B-7 + 架构 A-4) | `pipeline_orchestrator.py` + `job_manager.py` | ✅ |
| P1-2 修复 | **ETA 链路接通**：chapters.py /status 实际调用 estimate_remaining()，旧 elapsed 逻辑替换 | `app/api/chapters.py` L21 + L143-156 | ✅ 修复 round 1 |
| P1-3 | adjust 重生 portrait + Stage 5 prep freshness check (R7-3 + R7-4 必须配套) | `app/api/projects.py adjust_character()` + `pipeline_orchestrator.py Stage 5 prep` + `reference_image_manager.py generate_character_multi_refs()` | ✅ |
| P1-3 修复 | **freshness check 30s buffer**：`_portrait_mtime > (_char_ts + 30)` | `pipeline_orchestrator.py` L645 | ✅ 修复 round 1 |
| P1-5 | character_ready 等 portrait 全成 + characters_json 写完才设（架构 A-3） | `pipeline_orchestrator.py` Stage 2 末 | ✅ |

**合计 ~1.5-2 hr + 修复 round 1 (~20min)**

#### 🟩 ✅ Agent B (Frontend Sonnet 4.6) — 完成 2026-04-28 14:30
集中修 StageC + StageD + Stage E + BgmPlayer：

| 项 | 描述 | 文件 | 状态 |
|----|------|------|------|
| P0-1 | StageD image/bgm 全部走 toAbsoluteUrl (R7-12 + 旧 P2 #3) | `StageD.tsx` | ✅ |
| P0-3 | StageC character_ready 后 fetch chapter.characters_json 拿 portrait_url (F-1) | `StageC.tsx` | ✅ |
| P1-6 | Stage E 读 outline.summary 不是 original_idea (UX-17) | `StageE.tsx` | ✅ |
| P2-2 | 删除 StageC checkpointPreview L209-214 stale 区间 (R7-6) | `StageC.tsx` | ✅ |
| P2-4 | 完成态副标题统一 + carousel tip 停止 rotation (R7-10 + R7-11) | `StageC.tsx` | ✅ |
| F-2 | 角色卡刷新按钮接真 API（与 Agent A P1-3 联调） | `StageC.tsx` | ✅ 前端就绪，等 Agent A P1-3 |
| 旧 P3 4-6 | BgmPlayer url 引号 strip + Shot onError 占位图 + 进度条 spring 动画 | `BgmPlayer.tsx` + `StageD.tsx` + `StageC.tsx` | ✅ |
| STAGE_LABEL | character_design + image_preparation 两个新 stage 标签 | `StageC.tsx` | ✅ |

**新建**: `frontend/src/lib/url.ts` — toAbsoluteUrl() 共享工具（StageD/BgmPlayer/StageC/StoryDetailContent 全引用）
**npm build**: ✅ 20 routes 0 errors

**合计 ~1.5 hr**

#### 🟦 Agent A 与 Agent B 协作约束
- Agent A 增加新 stage 名 `image_preparation` → 必须告诉 Agent B 让它在 STAGE_LABEL map 加 `image_preparation: "正在准备画面"`
- Agent A 增加 `estimated_remaining_seconds` 字段 → Frontend 已就绪 pickup（StageC L173-176），不需要改
- Agent A `/api/projects/{id}/characters/{char_id}/regenerate-portrait` 端点契约 → Agent B 在 F-2 用

### Wave 1 第二阶段 — UX-16 URL 路由 ✅ 完成 (2026-04-28 15:06 Agent C Opus 4.7)

#### 🟪 Agent C (Frontend Opus 4.7) — UX-16 dynamic route
- ✅ **P0-4 UX-16**: dynamic route `/create/[projectUuid]/[stage]` 实施完成
- ✅ **方案选择**: 单 dynamic route + 6 stage 枚举（不是 6 嵌套路由），详尽 trade-off 见 TEAM_CHAT
- ✅ **新建**: `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` + `frontend/src/lib/createUrl.ts`
- ✅ **改造**: CreateContent.tsx + CreateContext.tsx + types/create.ts
- ✅ **验收**: npm build 21 routes 0 errors，4 核心场景 trace 通过
- ✅ **风险防护**: lastPushedUrlRef echo guard + derivedFromState 短路 + completion guard 三层防护避免反馈环
- **实际工时**: ~1.5 hr

### Wave 2 — Backend D + Frontend E 串行 + ARCH-1 单独修

#### ✅ Agent D (Backend Sonnet) — Dashboard 列表后端字段 (2026-04-28 16:00)
- **P1-4 R7-1 backend**: ✅ 完成 — `/api/projects/` 每条新增 cover_image_url + shot_count + mood + ISO 时区时间
- **修改文件**: `app/schemas/project.py` + `app/api/projects.py`
- **pytest**: 24/24 ✅（architecture 7 + parallel_stage5 17）

#### 🟩 Agent E (Frontend Sonnet) — Dashboard 列表前端读字段（等 D 完成）
- AuthContext.tsx mapProject 改读后端新字段
- **工时**: 10 min

#### ✅ Agent F (Backend Sonnet) — ARCH-1 chapter_scene_images 写入 (2026-04-28 15:50)
- **P1-7 ARCH-1**: ✅ 完成 — pipeline 完成后批量写入 chapter_scene_images 表
- **修改文件**: `app/services/pipeline_orchestrator.py` + `app/services/job_manager.py`
- **pytest**: 211/211 ✅

### Wave 3 — Tester 验收 ✅ 完成 (2026-04-28 21:00 Agent G)

#### ✅ Agent G (Tester Sonnet) — T7 真生图端到端验证完成

**T7 UUID**: `631eef3c-4a26-413a-bcb1-1f038d176e85` | 故事: "深夜灯火" | 2 角色，16 shots，插画风，1:1 | 花费: ~¥3.50

**12 项验收汇总**: 11 PASS / 1 FAIL / 0 未触发

- [x] StageC character_ready 后 portrait 显示（P0-3）— PASS
- [FAIL] adjust 角色后 portrait 自动重生（R7-3 P1-3）— FAIL，非阻塞异常 `'str' object has no attribute 'get'` at projects.py L987，portrait mtime 不变
- [x] Stage label 实时跟随（P1-1）— PASS，6 阶段全观察到
- [x] ETA 单调下降（P1-2）— PASS，855s→270s→0s
- [x] progress 不倒退（R7-8）— PASS
- [x] 完成时 current_stage='completed'（R7-9）— PASS
- [x] 完成态副标题不冲突（R7-10）— PASS
- [x] 100% 后 carousel tip 停止（R7-11）— PASS
- [x] StageD shots + BGM 可访问（P0-1）— PASS
- [x] Stage E 读 outline.summary（P1-6）— PASS
- [x] URL /create/[uuid]/[stage] 路由（P0-4）— PASS
- [x] Dashboard 封面+shot 数+北京时区（P1-4）— PASS
- [x] D.15 P0 shot 尺寸 = 2048x2048（PIL 实测 16/16）— PASS

**新 Bug**: R7-3 portrait 重生 P1 bug — @backend 需修 `app/api/projects.py` adjust_character() 约 L945，`updated_char` 类型错误

**回归观察**: 角色一致性主观评估良好；风险路径未本次触发（Seedream 全程 16/16）

**详细验收报告**: TEAM_CHAT.md [2026-04-28 21:00]

### Wave 4 — DevOps 部署

#### ✅ Agent H (DevOps Sonnet) — 完成 2026-04-29
- [x] push GitHub — commit 84a2d35（Wave 1.1+1.2+2+2.5+3.5 全批，16 文件）
- [x] 通知 Ben — `.team-brain/team_ben/TEAM_CHAT.md` 后端改动清单已 append
- [x] rsync VPS — `rsync -avz app/ vps:/opt/xuhua-story/app/` + `rsync -avz frontend/ vps:/opt/xuhua-story/frontend/`（trailing slash 正确）
- [x] Docker rebuild + force-recreate api + frontend — `docker compose build --no-cache api frontend` → `docker compose up -d --force-recreate`
- [x] `/health` 验证 200 ✅
- [x] 生产 T8 完整故事验证 — UUID a3966a40-6d27-42c0-a7cf-109729e453e7，1:1 朋友圈，16 shots NB2 真生图，status=completed

**验证结果**:
- D.15: PIL 实测 1024x1024（1:1 正方形，不再 hardcoded 2:3）✅
- R7-1: cover_image_url + shot_count=16 返回正常 ✅
- R7-3: portrait mtime +45s（adjust 后真实重生）✅
- UX-16: GET /create/{uuid}/preview → HTTP 200 ✅

---

## 🚦 暂缓项（不进本批）

| 项 | 原因 |
|----|------|
| R7-2 5 按钮 mock 接真功能（点赞/分享/导出/合成视频）| 工作量大，MVP 上线后做 |
| ARCH-2 死表清理 | 下次 DBA cleanup 一并 |
| OPS-3 PYTHONUNBUFFERED | 下次 docker rebuild 一并 |
| 监控告警 R4 / TASK-STYLE-EXPANSION / 续写 Phase 3 / Resonance 时间线 | 已暂缓 |
| T-1 milestone "片段"漏改 / T-2 storyboard_director 内部 callback / O-1 OBS / O-2 短篇 21 shots cap | 文案/OBS 类小 bug，凑齐一批改 |
| OBS-1 Seedream sanitize 触发率统计 | MVP 后观察实际数据 |
| OBS-3 outline LLM 一致性规则 | 凑前端 UX-2 校验一起做 |


---

## ⚠️ TASK-T6-FIXBATCH 风险与注意点（全维度，毫无遗漏）

### A. 代码层面风险

#### A.1 🔴 角色一致性回归 — 高风险
- **风险**: Agent A 改 `pipeline_orchestrator.py` 多处（stage label / ETA / Stage 5 prep portrait 链 / character_ready 切换时机）涉及 CLAUDE.md 列为高风险的文件
- **影响**: 可能破坏现有的角色一致性传递链（portrait → fullbody → shots reference）
- **缓解**:
  1. Agent A spawn prompt 必须包含 CLAUDE.md "角色一致性"章节作为强制必读
  2. Agent A 严禁动 `image_generator.py` / `storyboard_prompts.py` / `seedream_generator.py` / `style_enforcer.py` / `reference_image_manager.generate_character_reference()`（只能动 `generate_character_multi_refs()` 加 freshness check）
  3. Wave 3 Tester 必须跑全回归测试：3 角色 100% / 6 角色 ≥90% / 4 题材稳定（CLAUDE.md 铁律）
  4. 派发任务时显式列出"禁止删除/修改的内容"

#### A.2 🟠 progress_callback signature 兼容性
- **风险**: Agent A P1-2 给 `progress_callback` 加 `estimated_remaining_seconds` 参数，但 pipeline_orchestrator 有数十处调用，全部要兼容
- **缓解**: 用 default value `estimated_remaining_seconds: int | None = None`，已有调用不需改

#### A.3 🟠 character_ready 切换时机改了 → 前端 polling 行为变化
- **风险**: Agent A P1-5 让 Stage 2 等 portrait 全成才设 `character_ready`。前端 StageC `useGenerationStatus` polling 检测到 `character_ready` 立刻 redirect 到角色预览页。改了之后前端可能会在 Stage 2 多等 30-60s 才进 StageC，**Founder 体感是 progress 卡 5-10% 更久**
- **缓解**:
  1. 加新 stage `character_design` 让 backend 在 LLM 输出完成（但 portrait 还在生）时设 `character_design` (progress 6%)，等 portrait 全成才升 `character_ready` (progress 10%)
  2. Frontend Agent B 在 STAGE_LABEL map 加 `character_design: "正在生成角色画像"`
  3. 让 Founder 知道这是预期行为（"在 portrait 全准备好之前不会进入 StageC"是好事，不是 bug）

#### A.4 🟠 Stage 5 prep freshness check 复用 portrait → 文件 mtime 时间戳依赖
- **风险**: Agent A P1-3 加 freshness check 用 `os.path.getmtime(local_path)` vs `char.get("updated_at_ts")` 比较。Linux/Docker 可能有时区差异 / 文件系统 mtime 精度差异
- **缓解**:
  1. char 用 ISO datetime 字符串记录 `updated_at`，转 unix timestamp 比较（统一 UTC）
  2. 加 30s buffer（mtime 比 updated_at 晚 30s 才认为 fresh，避免边界情况）
  3. fallback 逻辑：mtime 取不到则当作不 fresh，重生（保守）

#### A.5 🟡 R7-3 + R7-4 必须配套修
- **风险**: 单修 R7-3（adjust 重生 portrait）不修 R7-4（Stage 5 prep freshness check）会**反而增加浪费**：用户 adjust 1 次 → portrait 重生 1 次 + Stage 5 prep 又重生 1 次 = 浪费 1 次（~$0.067）
- **缓解**: Agent A 任务清单 P1-3 写明"两条必须一起修，不能只完成一条"

#### A.6 🟠 UX-16 dynamic route 改造可能引入新 bug
- **风险**: UX-16 改 `/create` 单页为 `/create/[projectUuid]/[stage]` 涉及：
  - Next.js dynamic route 配置
  - 各 Stage 组件 URL 同步（`router.replace()` 时机）
  - 刷新时根据 URL 还原 state（要拉 backend chapter API + project API + character_ready 状态）
  - useGenerationStatus hook 跟 URL 联动
  - 浏览器后退按钮行为
- **缓解**:
  1. Agent C 单独 spawn（不与其他改动同 PR），用 Opus 4.6 深度思考
  2. Wave 1 第二阶段（A+B 跑通后才 spawn C）
  3. 验收时强制测：F5 刷新 / 浏览器后退 / 复制链接打开 / 跨 stage 切换 4 个核心场景
  4. 与 dashboard 详情页 `/dashboard/[storyId]` 路由不冲突（不在同 path prefix）

#### A.7 🟠 ARCH-1 改动大 — 18+ 处既有引用
- **风险**: ARCH-1 让 chapter_scene_images 表 pipeline 完成后批量写入。但代码 18+ 处依赖该表（`chapters.py` L362/458/579/...），现有 GET 都返空。改了之后这些端点行为会变（开始返真数据），可能触发既有前端 bug
- **缓解**:
  1. 抽到 Wave 2 单独做（已采纳 Founder 决策），不混 Wave 1
  2. Agent F spawn prompt 列出 18+ 处引用文件，要求 grep 全部确认行为兼容
  3. 单 shot 重生成功能验收（Wave 3 Tester 项）

### B. Agent 协作风险

#### B.1 🟠 三个 agent 并行 spawn → context 错位
- **风险**: Agent A / B / C 同时跑可能不知道对方在改什么
- **缓解**:
  1. **Wave 1 不并行 spawn 三个，分两阶段**:
     - 阶段 1: A + B 并行（互不冲突，A 改 backend，B 改 frontend）
     - 阶段 2: C 单独（A+B 完成且通过审查后才 spawn）
  2. 每个 spawn prompt 包含完整必读清单 + 文件权限边界
  3. PM 在群聊提前公告本批次 spawn 的所有 agent + 各自范围

#### B.2 🟠 Backend ↔ Frontend API 契约
- **风险**: A 加 `image_preparation` stage / `estimated_remaining_seconds` 字段 / `regenerate-portrait` 端点。B 必须知道这些
- **缓解**: 在 spawn prompt 显式列出契约，A 完成后通过 SendMessage 直接告诉 B

#### B.3 🟡 越权风险
- **风险**: PM 反复落入"自己写代码"陷阱（feedback memory: pm_no_scripting）
- **缓解**: PM 严禁动代码，全部派 agent

### C. 测试与部署风险

#### C.1 🟠 T7 真生图测试成本控制
- **风险**: Founder 同意 Tester 跑 T7 真生图，但 NB2 ¥0.067/张 × 18 张 + Mureka 10 credits + LLM ≈ ¥1.2-1.5/次。如果 sanitize 触发率高，成本翻倍
- **缓解**:
  1. **T7 故事选简单生活短篇**（不要悲剧/民俗/婚礼/古装 — 高 sanitize 触发题材，参考 OBS-1）
  2. 选短篇模式（≤ 18 shots，不让 LLM 像 T6 那样跑到 21）
  3. 跑前确认 PipelineCostTracker $10 熔断生效
  4. 单次预算 ≤ ¥1.5
  5. 失败重试不超过 1 次

#### C.2 🟠 progress_callback signature 改 → 旧 chapter status 端点消费方
- **风险**: 加 `estimated_remaining_seconds` 字段后，老 frontend / 老移动端可能不识别（虽然现在只有 web）
- **缓解**: 用 Optional 字段，old client 可以忽略

#### C.3 🟠 部署节奏
- **风险**: Wave 4 部署若不规范会出事故
- **缓解**:
  1. 必须先 push 再部署（铁律 — feedback memory）
  2. rsync 注意 trailing slash 陷阱（feedback memory）
  3. 阿里云共享 MySQL 不能改 schema（job_manager 加字段需 Alembic 迁移）
  4. 部署前 PM 自己跑 /api/health 验证 + 通知 Ben（feedback memory: 后端改动事先提醒）

#### C.4 🟡 DB schema 迁移
- **风险**: P1-2 ETA 方案如果选择"在 chapter_generation_jobs 表加 estimated_remaining_seconds 列"会需要 Alembic 迁移
- **缓解**:
  1. 推荐方案: **不加 DB 列**，只在 status response 实时计算返回（无状态，零迁移成本）
  2. Agent A spawn prompt 写明优先用 in-memory / response-only 方案

### D. 文档与流程风险

#### D.1 🟠 Spawn 前文档未更新
- **缓解**: PM 严格按 xhteam 协议 Wave 0 先更 PENDING/TEAM_CHAT/progress，再 spawn（feedback memory: docs_before_spawn）

#### D.2 🟠 审查跳过群聊重读
- **缓解**: 审查时 PM 严格按 feedback memory: review_read_chat_first

#### D.3 🟠 越权检测
- **缓解**: 审查时 PM 检查 modified files 是否在 spawn prompt 允许范围

---

## 📦 TASK-T6-FIXBATCH 暂缓项（不进本批，详细记录在案）

> 本节细化每条暂缓项：项名 + 优先级 + 暂缓原因 + 触发条件 + 关联文件 + 后续路径

### D.1 R7-2 — 详情页 5 按钮 4 个 Mock 接真功能
- **优先级**: P2
- **暂缓原因**: 工作量大（涉及 backend favorite endpoint + share token 端点 + export zip + ffmpeg 视频合成），且不阻塞 MVP 核心展示路径。Founder 认可详情页核心展示已 OK
- **包含子项**:
  - ❤️ 点赞: backend `/api/projects/{id}/favorite` toggle + projects 表加 `is_favorite` 列（小工作量）
  - 🔗 分享: backend 生 share token + 公开页面 `/s/{token}`（中等工作量，要 server-side render）
  - ⬇️ 导出: backend `/api/projects/{id}/export?format=...` 打包 zip 返回（大工作量，需 zip stream + 选择哪些资源）
  - 🎬 合成视频: ffmpeg 拼接 shots + BGM + TTS narration（最大工作量，需 TTS pipeline 接通）
  - 📋 做同款: 已是真功能，无需修
- **触发条件**: MVP 上线后讨论用户实际诉求优先级，可能选择性实施（例如先做点赞 + 分享，导出/视频留更后）
- **关联文件**:
  - `frontend/src/app/dashboard/[storyId]/StoryDetailContent.tsx` L324 / L297-299 / L485
  - `frontend/src/components/ui/ShareModal.tsx` L15
  - `frontend/src/components/ui/VideoSynthesisModal.tsx` L17-25
  - 待新建 backend: `app/api/share.py` / `app/api/exports.py` / `app/services/video_synthesis.py`
- **后续路径**: MVP 后 Founder 决定优先级 → 拆 4 个独立 TASK 派发

### D.2 ARCH-2 — project_character_references 死表清理
- **优先级**: P2 技术债
- **暂缓原因**: 死表不影响功能（无 SQLAlchemy model 引用），仅占 DB schema 空间。清理需要 Alembic drop migration 操作 production DB，风险大于收益
- **触发条件**: 下次 DBA cleanup（与其他遗留表一并）
- **关联**: schema 定义文件（待 Backend agent 后续 grep 定位）
- **后续路径**: Ben 主导的 DBA 季度清理任务，列入 backlog

### D.3 OPS-3 — uvicorn nohup PYTHONUNBUFFERED=1
- **优先级**: P3 DevOps 配置债
- **暂缓原因**: 仅影响诊断便利性（实时 tail log 需 sleep 等 buffer），不影响生产功能
- **触发条件**: 下次 docker rebuild 一并加 ENV 变量
- **关联文件**: `docker/Dockerfile.api`（待确认）or `docker-compose.yml` env 配置 or VPS .env
- **后续路径**: 下次 DevOps 部署时补 1 行 `ENV PYTHONUNBUFFERED=1`

### D.4 监控告警系统 R4
- **优先级**: P1（已暂缓）
- **暂缓原因**: Harness V2 Phase 1-3 全部完成后 R4 单独留作监控阶段。当前 MVP 修复批优先级更高
- **触发条件**: MVP 上线后 1-2 周内，根据 VPS 实际运行情况启动
- **包含**: ① 修复外部 `/api/health` 404（Nginx 路由前缀） ② 配置 Uptime Robot 或 Grafana ③ 6 个 EP Sensor 端点整合
- **关联**: DEC-015 Harness V2
- **后续路径**: 派 DevOps 启动

### D.5 TASK-STYLE-EXPANSION
- **优先级**: P1（已暂缓）
- **暂缓原因**: 前置 TASK-STYLE-THUMBNAILS 15 张通过后才启动。当前 95 风格只有 15 种上架（有 enforcer 规则 + 缩略图）
- **触发条件**: 缩略图 15 张全通过 + Founder 确认从剩余 80 种中再选哪 25-35 种
- **关联**: `app/services/style_config.py` 95 风格 + `style_enforcer.py` 规则
- **后续路径**: Founder 选风格 → 派 AI-ML 写 enforcer 规则 + 派设计/AI 生缩略图

### D.6 续写模式 Phase 3 (#11)
- **优先级**: P2（已暂缓）
- **暂缓原因**: 产品路线图 Phase 3，需 Founder 决定是否进入设计阶段
- **触发条件**: Founder 决策后再派发设计/实施
- **关联**: 涉及 Story Continuation API / 历史上下文传递 / 角色记忆机制
- **后续路径**: Founder 启动 → 派 PM 主导设计 → 派 backend 实施

### D.7 Resonance 时间线
- **优先级**: P2（已暂缓）
- **暂缓原因**: 原"3-4 周拿 500 申请"时间线已作废（2026-03-23），等内测启动时间
- **触发条件**: Founder 通知正式内测启动后重新制定
- **关联**: Resonance Agent / 抖音"一话故事" / 小红书 / B站
- **后续路径**: Founder 通知 → Resonance Agent 重新制定执行方案

### D.8 文案 / OBS 类小 bug 批（待凑齐一批改）
- **优先级**: P3
- **包含**:
  - **T-1**: milestone "已生成 X/21 张图像..." 漏改"片段"（UX-8 修复漏掉 milestone 区域）— 文件 `StageC.tsx` milestone 渲染 + backend message
  - **T-2**: storyboard_director scene 内部 callback 频率太低（message 卡 "Scene 1/7" 实际跑到 4/7）— 文件 `app/services/storyboard_director.py` 内部 callback
  - **T-3**: "中篇模式支持 36 张画面" tip 在短篇生成时弹（产品决策有意为之，UX-13 已撤销，记录不修）
  - **O-1 OBS**: UX-2 LLM 偶发 JSON 解析（Unterminated string col 414，已兜底吞掉）— OBS 应统计频率，超阈值再修
  - **O-2 P3**: Stage 4 LLM 给短篇生 21 shots（预期 18）— storyboard_director cap 上限 ≤ stories.shot_count
- **暂缓原因**: 单条修都太小，凑齐一批一并 PR 提高效率
- **触发条件**: 累计 5+ 条小 bug 时凑批派 frontend / backend / ai-ml 一次性修
- **关联**: 各自文件如上

### D.9 OBS-1 — Seedream 中文叙事 sanitize 触发率
- **优先级**: P3 OBS（MVP 后观察）
- **暂缓原因**: 本地 1 次 T5 测试样本不够（4/18 触发），需要更多生产数据决定是否值得做"风格预审 + 提前换词"
- **触发条件**: MVP 后累计 100+ 真实生成数据，统计触发率 + 关键词分布，超阈值（如 >20%）再启动
- **关联文件**: `app/services/sanitize_helper.py`（待 backend 加） + `seedream_generator.py` retry path
- **后续路径**: OBS 数据驱动决策，可能做"中文民俗词字典"或"风格预审 LLM"

### ✅ D.10 OBS-3 — outline LLM prompt 加内部一致性规则（Wave 5.1 AI-ML 已完成 2026-04-29 17:33）
- **优先级**: P2 → **已修复**
- **修复实施**: `app/services/story_outline_generator.py` L415-427 加"故事内部一致性规则（MANDATORY — 输出前必须自检）"覆盖数字/角色名/时间地点物件三类一致性 + 自检指令（以 plot_point 1 为准）。L512-538 JSON 解析三 fallback 加 logger.warning + brace-extract 附 200 字符预览。
- **PM 地毯式审查**: 6 角度通过（mtime/规则文本/logger.warning 三处/_build_prompt 调用链路/三件套 mtime/索引标记）
- **pytest**: 7/7 PASS 不退化

### D.11 BGM-related P3 (PENDING 早期记录)
- **music_hint meta-prompt 层效用有限**: P3，等 MVP 用户反馈"水墨故事配 acoustic guitar 违和"再启动
- **秋梨膏温暖故事金句质量重试机制**: P3，等实际测 BGM 质量决定
- **用户自定义 BGM 上传**: P3，等用户反馈

### D.12 续写 / Phase 3 / Resonance 等产品功能（已记 D.6 D.7，提醒别忘）

### D.13 F-Hydrate-1 — Hydrate 后 progress 短闪烁（2026-04-28 Wave 1.2 Agent C 主动暴露）
- **优先级**: P3
- **现象**: 用户 F5 刷新或复制链接打开 `/create/[uuid]/generating` 时，hydrate 把 backend progress 还原到 React state，但 StageC text-gen useEffect 入口 `START_GENERATION` action 会 reset progress=0；~1.6s 后 polling 拉到真值恢复 — 短闪烁
- **暂缓原因**: 只是 1.6s 视觉闪烁，不影响功能正确性。Wave 1.2 大改造不能再扩范围
- **修复方向**: StageC text-gen useEffect 入口加 hydrate guard — 检测 state.generationProgress > 0 时跳过 START_GENERATION reset
- **触发条件**: MVP 后 Founder 体验时若觉得闪烁明显，启动修复
- **关联文件**: `frontend/src/components/create/StageC.tsx` text-gen useEffect 入口段（~L260-280）
- **后续路径**: 派 frontend agent 加 ~5 行 guard

### D.14 F-Lock-Family — confirmed 后中段后退到 outline/characters/scenes 没警告（2026-04-28 Founder 确认 P2 + 家族扩展）

- **优先级**: 🟠 **P2**（Founder 2026-04-28 15:35 确认升级，理由见下"决议背景"）
- **范围（家族 bug，3 处同源）**:
  - StageB `/outline` — 大纲已确认后未锁定
  - StageC char-preview `/characters` — 角色已确认后未锁定
  - StageC scene-preview `/scenes` — 场景已确认后未锁定

- **现象**: 用户 pipeline 中段（generationStatus === "generating"）按浏览器后退，URL 回到上述 3 个 stage 任一页面，看到熟悉的"编辑/确认"按钮。但 backend confirmed_outline / characters_confirmed / scenes_confirmed 已写入 + Stage 后续已基于此跑，用户再改无效

- **决议背景（2026-04-28 PM 深度论证 + Founder 确认）**:
  - **触发频率**: UX-16 Wave 1.2 实施后浏览器后退真能用了 → ~10-15% 用户路径会触发（trackpad 双指误触 / 鼠标侧键 / 好奇）
  - **用户损失**: 误以为可编辑 → 改了 → 没生效 → 困惑/愤怒（"产品在敷衍我"），比 P3 类小 bug 严重得多
  - **产品诚实性**: UX-16 承诺"能后退能复制能 F5"，如果后退看到 editable UI 但实际不可编辑 → 承诺打折
  - **修复成本极低**: 方案 A ~25 min（3 处 banner + 共享 lock hook + 隐藏编辑按钮）
  - **跟现有 P2 项同类严重度**: OBS-3 outline LLM 一致性 / R7-2 详情页 5 mock — F-Lock-Family 跟 OBS-3 同类（避免用户看到矛盾结果），明显比 R7-2 mock 严重（mock 用户能感知"按了没反应"，本 bug 用户以为生效实际没生效更隐蔽）

- **修复方案 A（推荐，3 处共享 hook）**:
  ```ts
  // 新建 frontend/src/hooks/useStageLock.ts
  function useStageLock(stage: 'outline' | 'characters' | 'scenes') {
    const { state } = useCreate();
    const isLocked =
      state.generationStatus === 'generating' || state.generationStatus === 'complete';
    return isLocked;
  }
  ```
  - StageB / StageC char-preview / StageC scene-preview 三处：
    - 顶部黄色 banner: "📌 大纲/角色/场景 已确认，AI 正在创作画面。如需修改请新建项目"
    - 内容只读显示（隐藏 input/textarea，改用纯文本展示）
    - 编辑/调整按钮隐藏或灰掉
    - "确认/开始绘制" 按钮替换为"返回创作进度"按钮（点击 router.replace `/create/[uuid]/generating` 或 `/preview` 取决于当前状态）

- **修复方案 B（备选，工作量大）**: 后端加 `/api/projects/{uuid}/reset` 端点重置 pipeline + 清理 storyboard / images / bgm + 允许重启 — 成本高（~2 hr backend + 浪费已生成 ¥1.5 数据）

- **暂缓原因**: 不是 P0/P1 阻塞 MVP，但是产品打磨批次的优先项。Wave 1-4 完成 + T7 测试通过后，启动下一批"产品打磨批次"时优先做

- **触发条件**: Wave 1-4 + T7 完成后启动下一批 — 优先级靠前

- **关联文件**:
  - 新建 `frontend/src/hooks/useStageLock.ts`
  - `frontend/src/components/create/StageB.tsx`（如果存在 — 否则在 confirm 阶段渲染处）
  - `frontend/src/components/create/StageC.tsx`（char-preview + scene-preview 双处）
  - `frontend/src/contexts/CreateContext.tsx`（确认 state.generationStatus 字段语义稳定）

- **后续路径**: 派 frontend agent (Sonnet 4.6 effort high) ~25 min 加共享 hook + 3 处 banner + 隐藏编辑入口

- **完整 UX 走查（修复后用户体验）**: 见 `.team-brain/TEAM_CHAT.md` 2026-04-28 15:30 PM 详细论证

---



---

## TASK-T6-FIXBATCH Wave 1.2 UX-16 ✅ 完成 (2026-04-28 15:25)

### 实施详情

- **URL 命名方案**: 单 dynamic route `/create/[projectUuid]/[stage]`，stage ∈ {outline, characters, scenes, generating, preview, delivery}（6 枚举）
- **新建 2 文件**: `frontend/src/app/create/[projectUuid]/[stage]/page.tsx` + `frontend/src/lib/createUrl.ts`
- **改 3 文件**: `frontend/src/app/create/CreateContent.tsx` + `frontend/src/contexts/CreateContext.tsx` + `frontend/src/types/create.ts`
- **3 层反馈环避免**: lastPushedUrlRef echo guard + derivedFromState 短路 + completion guard
- **npm build**: 21 routes 0 errors

### Agent C 主动暴露 2 遗留（P3 后续追踪）

1. **F-Hydrate-1**: Hydrate 后 StageC text-gen useEffect 入口 START_GENERATION 会 reset progress=0，~1.6s 后 polling 真值恢复 — 短闪烁。建议加 hydrate guard 优化（progress 已 hydrate 时跳 START_GENERATION）
2. **F-Outline-Lock-1**: 用户用浏览器后退到 `/outline` 想再编辑大纲，但 confirm-outline 已不可逆，StageB 未警告。建议加"已确认仅展示"提示 banner

### Wave 1.2 PASS 后下一步

进入 Wave 2 (Backend D + Frontend E + Backend F)。


### ~~D.15~~ ✅ aspect_ratio hardcoded → 修复完成（2026-04-28 Wave 2.5 Backend）
- **状态**: ✅ **已修复（Wave 2.5 Backend，2026-04-28）**
- **修复范围**:
  1. `seedream_generator.py` `_ASPECT_RATIO_TO_SIZE` 补 `3:4` / `4:3`（现 7 种比例，覆盖 frontend 全部 4 个选项）
  2. `pipeline_orchestrator.py` `run()` 加 `aspect_ratio: str = "2:3"` 参数（默认值向后兼容）
  3. `pipeline_orchestrator.py` L852: `generate_shot_image_phase2_safe(aspect_ratio=aspect_ratio)`（不再 hardcoded "2:3"）
  4. `pipeline_orchestrator.py` ARCH-1 写入块: `width/height/aspect_ratio` 从 `_ASPECT_RATIO_TO_SIZE` 动态查（不再 hardcoded）
  5. `job_manager.py` `run_story_generation_task()` 加 `aspect_ratio` 参数 + `pipeline.run()` 传值
  6. `projects.py` `_run_generation_in_background()` 加 `aspect_ratio` 参数
  7. `projects.py` `start_generation()` 传 `project.aspect_ratio or "2:3"`
- **验证**: pytest 292/292 passed（非 API 集成测试）✅
- **完整调用链路**: frontend POST /start-generation → projects.py（project.aspect_ratio）→ _run_generation_in_background → run_story_generation_task → pipeline.run() → generate_shot_image_phase2_safe → seedream/NB2 真生图 ✅

### D.16 types/create.ts StoryDetail.mood 跟 StoryCard 不一致（2026-04-28 Wave 2 E 审查发现）
- **优先级**: P3 文案/小 bug 杂项批
- **现象**: `frontend/src/types/create.ts` L170 `StoryCard.mood: string | null`（E 改）vs L201 `StoryDetail.mood: string`（E 漏）。StoryDetail extends StoryCard，子类型 override 更严格类型合法但逻辑不一致
- **不阻塞**: runtime 有 dashboard 详情页 StoryDetailContent.tsx R6 修的三层 fallback (user_selected_mood ?? mood ?? "—")，null 时不会 crash
- **修复方向**: L201 改成 `mood: string | null`
- **触发条件**: 凑齐文案/小 bug 一批改时一并修
- **关联文件**: `frontend/src/types/create.ts` L201
- **后续路径**: 凑下批 P3 文案修复批一并 1 行修复

---

## ✅ R7-3 P1 portrait 重生 bug — Wave 3.5 修复完成（2026-04-28 21:42）

**真因（Wave 3 Tester 发现 + Wave 3.5 Backend 深挖）**: 不在 adjust_character() Step 7 本身，是下游 `app/services/character_prompt_builder.py` `_build_human_description()` + `build_face_description()` 对 `physical/clothing/human` 字段直接调 `.get()`。T7 实测 LLM adjust 后这些字段保留为 **str 格式**（不是嵌套 dict），触发 `'str' object has no attribute 'get'`，被 try/except 吞掉，portrait 静默不重生。

**修复（仅改 1 文件，非高风险）**: `app/services/character_prompt_builder.py`
- `_build_human_description()` L102-116 _raw 变量 + isinstance(dict) 检查 + isinstance(str) fallback append
- `build_face_description()` L231/233 第 2 处同样 isinstance 防御

**实证（4 角度独立验证）**:
- ✅ pytest 24/24 不退化
- ✅ backend pid 27834 重启后真跑新代码（旧 pid 12059 已不监听 port）
- ✅ adjust API 实测：portrait mtime 20:37:34 → 21:42:03（+65min，文件真重写）
- ✅ DB chapter.characters_json[0].portrait_url + updated_at 真更新
- ✅ D.15 P0 aspect_ratio 链路完全保留无回归

**待办**: Tester 复测 adjust 路径独立验证（spawn 中），通过后进 Wave 4 DevOps 部署。

**Wave 3.6 Tester 独立复测 PASS（2026-04-29 15:12）**: 6 证据点全通过，str.get() 错误消除，portrait mtime 21:42:03→15:10:47，DB updated_at 2026-04-29T07:10:47Z，HTTP 200 1489KB，log 无异常。Wave 4 DevOps 部署可以启动。附带 P3: char_002 七岁小孩触发 CONTENT_SAFETY（独立问题，非 R7-3 bug）。

---

### D.17 CONTENT_SAFETY 脱敏策略族（2026-04-29 Founder 脑洞 + Wave 3.6 Tester 触发）

**起源**: BUG-2026-04-29-001 — Tester 复测 R7-3 时 char_002（七岁小孩"小宝"）adjust 触发 NB2 CONTENT_SAFETY 拦截（"7-year-old boy + red swollen eyes"）。Founder 提醒"还有其他方面需要类似脱敏策略吗"，PM 脑洞发散到 9 大维度。

**核心洞察**: 用户主观选择 → idea → Stage 1 outline LLM → Stage 4 storyboard prompt → NB2/Seedream 真生图，任何一环失守都拒。用户感知是"我故事就这样写了为什么生不出图"，跟 D.15 同类用户体验灾难（用户操作没生效）。

### 9 大脱敏维度（按风险 × 触发频率排序）

#### 🔴 P0 MVP 前必修

| # | 维度 | 触发示例 | 策略 |
|---|------|---------|------|
| **D.17.1** | 儿童角色（BUG-2026-04-29-001 实证）| `7-year-old + red swollen eyes`、儿童+受伤/哭闹/虐待 | 年龄 < 18 自动屏蔽负面身体词 → "若有所思/看着窗外" |
| **D.17.2** | 中文民俗（OBS-1 同源，T5 实证 4/18 触发）| 婚礼+红绸、唢呐悲怆、葬礼+白幡 | 民俗场景词改"传统装饰/民乐/告别仪式" |
| **D.17.3** | 暴力/受伤 | 流血、伤口、武器、打斗 | "血"→"汗"、"伤口"→"疲态"、"武器"→"工具" |

#### 🟠 P1 重要但部分有 fallback

| # | 维度 | 策略 |
|---|------|------|
| D.17.4 | 真实人物/名人脸（用户上传角色参考图）| 上传时脸部检测 + 名人识别 → 警告用户 |
| D.17.5 | 品牌/IP/版权角色（用户写"哈利波特那种小巫师"）| 词典屏蔽 + 引导改"魔法少年/卡通老鼠" |
| D.17.6 | 政治/历史/宗教敏感 | 硬词典直接拒接受 + 显式提示"不支持" |

#### 🟡 P2 长尾但用户痛点

| # | 维度 | 策略 |
|---|------|------|
| D.17.7 | 心理/医疗负面（抑郁/自杀/癌症）| 温情化："抑郁"→"心事重重"、"自杀"→"想离开" |
| D.17.8 | 性别/性向/年龄敏感词（紧身、丰满、性感）| "修身、健美、有魅力" |
| D.17.9 | 场景/职业敏感（监狱/夜店/性工作者）| "监狱"→"老房子"、"夜店"→"霓虹咖啡馆" |

### 修复方案（2026-04-29 15:50 Founder 决议简化 — 只 Layer 3 末端 fallback）

**Founder 反馈原文（重要保留）**:
> "我感觉有点过头，'7岁小孩眼眶红肿'我觉得不算是什么敏感内容，否则故事的生动性以及形象程度怎么保证？所以我觉得只要最后一层 'Layer 3 — 末端 fallback（生图被拒）'就好"

**核心原则**:
- 不主动脱敏（不破坏故事生动性 + 形象程度）
- 用户怎么写就怎么生
- 只在生图层真被拒时才兜底

### 唯一实施方案 — Layer 3 末端 fallback 链

```
Stage 5 真生图：
  NB2 调用
    ├─ ✅ 成功 → 写入 storyboard.shots[i].image_url，正常推进
    └─ ❌ CONTENT_SAFETY 拒 →
         PromptRewriter.rewrite(prompt) 自动改写
           ├─ ✅ 改写后 NB2 成功 → 正常推进
           └─ ❌ 改写后仍拒 →
                Seedream 试（不同审查阈值，可能比 NB2 宽松或严格）
                  ├─ ✅ 成功 → 正常推进
                  └─ ❌ 仍拒 →
                       占位图（灰底 + 警示图标）
                         + storyboard.shots[i].error_message="该画面因 AI 安全审查无法生成"
                         + 前端 StageD 提示用户"如不满意可微调画面文字"
```

### 实施细节

| 项 | 现状 | 待改 |
|----|------|------|
| `app/services/prompt_rewriter.py` PromptRewriter | 已存在（MAX_REWRITE_ATTEMPTS=2）| 升级改写质量（不只重写表层，按 9 维度分类替换更精准）|
| NB2 → Seedream 切换 | 现有架构 NB2 是 default，Seedream 是 fallback | 链路接通：NB2 拒 + 改写仍拒 → 自动切 Seedream，记录在 image_results.json 标记切换原因 |
| 占位图 + 提示 | StageD 现有 onError handler（Wave 1.1 P3-5）| 升级：error_message 字段从 backend 透传 + 前端显示具体原因 + 给用户重试按钮 |

### 关联文件

- `app/services/prompt_rewriter.py` 改写质量升级（参考 9 维度作为内部启发，不强制规则）
- `app/services/image_generator.py` NB2→Seedream 自动 fallback 链路
- `app/services/pipeline_orchestrator.py` 单 shot 失败 error_message 写回 storyboard
- `frontend/src/components/create/StageD.tsx` 失败 shot UI 显示具体原因 + 重试按钮

### 9 维度词典作为参考保留（不强制脱敏）

D.17.1-9 共 9 维度作为 PromptRewriter 升级时**内部参考启发**（让改写更精准），**不**作为前置过滤规则强制屏蔽用户输入。例如 PromptRewriter 收到拒了的 prompt 含"7岁小孩 + 红眼"，可启发"试试'7岁小孩 + 若有所思'"作为改写候选 — 但只在被拒后用，不主动改写用户原意。

### 触发条件

MVP 前 P1（不带病上线，Wave 4 部署前不做，作为下批产品打磨批次第 1 项）。

### 重要备注 — Seedream 首发可能性

**当前**: NB2 是 default 首发，Seedream 是 fallback
**未来可能**: Seedream 投入正式产品作为**首发生产**（待 Founder 确定）

**含义**:
- 如果 Seedream 转 default 首发，fallback 链改成 `Seedream 默认 → 拒 → NB2 fallback → 拒 → 占位`
- 测试用 Seedream 首发已经 T7 实证（D.15 P0 修复 PIL 16/16 通过 Seedream 生成）
- D.17 实施时需要考虑 default model 灵活配置（settings.IMAGE_GEN_PROVIDER 现已支持切换）

### 关联现有 PENDING

- **OBS-1** Seedream 中文叙事 sanitize 触发率 → 改用 Layer 3 fallback 后 OBS-1 现象不阻塞（自动 fallback）
- **R7-3** 修复 portrait 重生 + 但 adjust 调用 image_gen 仍可能撞 CONTENT_SAFETY → 同样走 Layer 3 fallback 处理
- **BUG-2026-04-29-001** 七岁小孩 CONTENT_SAFETY → Layer 3 fallback 完美兜底

---

### D.18 SceneImage width/height 元数据跟实际生成模型尺寸不一致（2026-04-29 Wave 4 T8 部署发现）

**优先级**: P3 元数据准确性

**现象**: T8 生产环境用 NB2 生 1:1 朋友圈，实际尺寸 1024×1024。但 SceneImage 元数据 width/height 从 `_ASPECT_RATIO_TO_SIZE["1:1"]="2048x2048"` 派生 → DB 写的是 2048×2048（错值）。

**根因**: D.15 修复时把 width/height 从 hardcoded 1664/2496 改成字典派生，但字典是 Seedream 标准（2048×2048），不是 NB2 标准（1024×1024）。

**影响**: 
- 视觉层面: 用户看到 1:1 ✅（D.15 P0 用户承诺保住）
- DB 元数据层面: width/height 不准（影响后续单 shot 重生成或局部编辑用 SceneImage 元数据作 prompt 参数时）

**修复方向**: model-aware width/height 派生
```python
SIZE_BY_MODEL = {
    "nb2": {"1:1": (1024,1024), "2:3": ...},
    "seedream": {"1:1": (2048,2048), "2:3": (1664,2496), ...},
}
width, height = SIZE_BY_MODEL[settings.IMAGE_GEN_PROVIDER][aspect_ratio]
```

**触发条件**: P3，与 D.15 同批未来"model 灵活配置"工作一起做（Seedream 转首发生产决议后）

**关联**:
- D.15 P0 ✅ 用户视觉承诺保住，本条仅元数据
- D.17 Layer 3 fallback 实施时也要 model-aware
- Seedream 首发可能性（PENDING D.17 备注）— 如果转 Seedream default，字典反而准了

---

### 🔴 D.17 二次修订（2026-04-29 17:25 Founder 决策最终版）

**之前两版方案均作废**（D.17 P3 三层架构 / Layer 3 fallback Seedream），最终方案：

**核心原则**: 全 pipeline 单一模型一致，**移除 NB2↔Seedream 自动切换**，失败用智能提示帮用户改 prompt。

**理由**: NB2 vs Seedream 视觉风格差太多。pipeline 内任一张图回退另一模型会破坏 18 张统一性，用户细看大概率发现异类。

**修复范围（必须删除现有混合 fallback）**:
1. `app/services/image_generator.py` L796-801 `generate_shot_image()` dispatcher fallback_callback 删除
2. `app/services/image_generator.py` L1389-1398 `generate_shot_image_phase2_safe()` dispatcher fallback_callback 删除
3. `app/services/seedream_generator.py` L720-740 `_run_fallback()` 改成返 sanitize_failure error，不调 NB2

**修复后流程**:
```
首选模型（NB2 or Seedream，看 settings.IMAGE_GEN_PROVIDER）
  ├─ ✅ 成功 → 返回
  └─ ❌ CONTENT_SAFETY 拒
        ↓
        PromptRewriter 改写 prompt（首选模型内）
        再调首选模型
          ├─ ✅ 成功 → 返回
          └─ ❌ 仍拒
                ↓
                [新增] prompt_safety_advisor.py Haiku 分析失败 prompt
                生成"建议改 X 为 Y"提示
                ↓
                占位图 + storyboard.shots[i].error_message + safety_advice
                ↓
                Frontend StageD 显示提示 + "改一下文字"按钮
```

**新建文件**: `app/services/prompt_safety_advisor.py`
- 接收: 失败 prompt + 失败 reason（CONTENT_SAFETY 类）
- 调用: Haiku 4.5 quick check
- 返回: { "suspected_terms": [...], "suggested_changes": [...], "user_message": "你的画面文字 'XXX' 触发了 AI 安全审查，可能因 'YYY'，建议改成 'ZZZ' 后重试" }

**全 pipeline 受影响环节**: portrait（Stage 2 UX-1）/ fullbody（Stage 5 prep）/ scene_anchor（Stage 5 prep）/ shots（Stage 5 真生图 18 张）— 全部走单一模型，无回退。

**Wave 5.1 实施中** — Backend agent 负责。

---

### ✅ O-1 + OBS-3 — Wave 5.1 AI-ML 完成（2026-04-29 17:33）

`app/services/story_outline_generator.py` L415-427 加内部一致性规则 + L512-538 JSON fallback OBS warning。详见 ai-ml-progress.

---

## ✅ Wave 5.1 完整 PASS（2026-04-29 19:30 PM 21+ 角度地毯式审查通过）

主索引完成标记:
- D.13 F-Hydrate-1 ✅
- D.14 F-Lock-Family ✅
- D.16 mood 类型 ✅
- T-1 milestone 文案 ✅
- D.17 二次修订 fallback 删除 + 智能提示 ✅
- D.18 SIZE_BY_MODEL ✅
- O-2 cap ✅
- T-2 scene callback ✅
- R7-2 点赞/分享/公开页（除导出/视频外）✅
- O-1 outline 一致性 ✅（Wave 5.1 早完成）

待: Wave 5.2 DevOps 部署（pytest + Alembic 002 upgrade head + push + rsync VPS + 通知 Ben）

---

### ✅ D.19 P0 hotfix — hydrate 误判 chapter 404 黑屏（2026-04-30 15:20 实测发现 + 立即修）

**现象**: Founder 测试 T7+ (project_id=20) 创建后访问 `/create/[uuid]/outline` 黑屏。

**根因**: `frontend/src/app/create/CreateContent.tsx` `hydrateProjectFromBackend()` L686 用宽 regex `/404|不存在/` 测错误消息后设 `notFound=true`。但 chapter 3 个 endpoint（status/storyboard/story）在 pre-confirm-outline 时都返 404 是 routine — 误判成"项目不存在"导致 setHydrateError + 黑屏。

**修复**: 重构 hydrateProjectFromBackend 分两步:
- Step 1 project endpoint 单独 try/catch — 只有这个 404 才 notFound=true
- Step 2 chapter 3 endpoint Promise.all 各自独立 .catch — 404 吞掉返默认值（status="pending" / null）
- 外层 catch — notFound=false（generic "加载失败重试"而不是误导"不存在"）

**部署**: 本地 frontend 重启 pid 36674 加载新代码（已生效）。Wave 5.4 部署时 push + VPS rebuild。

**实证**: 修复前 Founder 黑屏 → 修复后访问 `/create/2aa451e1-.../outline` 应正常显示 outline 编辑页。

---

### ✅ D.20 P0 hotfix v2 — StageB outline=null 黑屏修复（2026-04-30 17:09 完成）

**新现象**: D.19 修了 chapter 404 误判后访问大纲页**仍黑屏**

**Root cause**: Backend `GET /api/projects/{uuid}` 仅返 `confirmed_outline`（用户 confirm 才有），`raw_outline_json`（Stage 1 LLM 完成后写 DB）未暴露 ProjectDetail schema → hydrate 后 `state.outline = null` → StageB `if (!outline) return null` 渲染空 → 黑屏

**修复（双管齐下）**:

**Frontend Option D（即时止损）**:
- `CreateContent.tsx` L775-792: hydrate 后 outline=null && stage='outline' 自动调 `POST /generate-outline` 恢复 outline → 注入 dispatch HYDRATE_FROM_BACKEND
- `StageB.tsx` L130: `if (!outline) return null` → loading spinner "正在加载故事大纲..."

**Backend Option C（永久解法）**:
- `app/schemas/project.py` L83: `raw_outline: dict[str, Any] | None = None` 新字段
- `app/api/projects.py` L98-151: `_map_outline_to_response()` helper extract（DRY）
- `app/api/projects.py` L382-409: `generate_outline` 加 `force_regenerate` query param + 幂等检查（已有 raw_outline_json 不调 LLM 直接返缓存）
- 节省 ¥0.3-0.5 + 30-60s 每次 hydrate 触发

**实证**: Founder F12 console 真见 `[hydrate] outline null at /outline stage — recovering via generate-outline` + `[hydrate] outline recovered successfully`。pytest 292 passed。PM 11 角度地毯式 audit 全 PASS（含 DB 真测 project_id=22 raw_outline 真返 title="纸条里的父亲"）。

**部署**: 本地 backend pid 71921 + frontend pid 49226 真跑新代码。VPS Wave 5.x 部署时一并 push + rsync（DevOps 安排）。

---

### ✅ TASK-KEY-ROTATE-GEMINI — Gemini API Key 全量轮换（2026-05-01 00:09 完成）

**任务**: 旧 key `AIzaSyCX***[redacted-key-Apr29-old]` → 新 key `AIzaSyBm***[redacted-key-Apr29-new]`

**执行**: DevOps 10 步全 PASS（详见 TEAM_CHAT [00:09] 段）
- 本地 `.env:2` + VPS `/opt/xuhua-story/.env.production` 同步替换
- 本地 backend pid 71921 + VPS docker-api-1 Recreated
- 双端真 Gemini API 调用 (`gemini-2.5-flash`) 真返 'OK'

**待 Founder**: 立即 Google Cloud Console 撤销旧 key（已对话提醒）

**48 hr 后**: 清理双端 `*.backup-keyrotate-20260501` 备份（PM 责任提醒 DevOps）

---

### 🟡 TASK-SSH-HARDENING — ECS SSH 22 端口安全加固（2026-05-02 记录）

**触发**: 5-02 Founder 测试 Gemini key rotation 时审查 ECS 安全组发现 SSH(22) 对 0.0.0.0/0 开放（阿里云控制台标红警告）

**风险等级**: 🟡 中等
- ECS server `101.132.69.232` SSH 22 端口对全网开放
- 现有防御: 密码登录已禁用（4-29 D021）+ key 认证生效
- 攻击面: 全世界扫描器都能尝试连接（即使爆破不进，扫描日志/资源占用/0day 风险存在）

**两个安全组都开放 SSH 22 给 0.0.0.0/0**:
- `Sas_Malicious_Ip_Security_Group` 优先级 1 - 0.0.0.0/0 - SSH(22)
- `sg-uf67labj6qalw6cr6ukq` 优先级 100 - 0.0.0.0/0 - SSH(22)

**衍生风险（同安全组其他端口）**:
- ECS `Sas_Malicious_Ip_Security_Group`: HTTP(80) / HTTPS(443) 0.0.0.0/0 — 正常对外
- ECS `sg-uf67labj6qalw6cr6ukq`: 8000-9999 / 6379 / 3306 / RDP(3389) 0.0.0.0/0 — **过度开放**

**修复任务（独立批次，建议本周排）**:
1. SSH 端口改非默认（参考 VPS `107.148.1.199:58913` 的做法）
2. SSH source 收紧到 Founder + Ben 几个固定 IP（先确认实际使用方式）
3. 装 fail2ban
4. 禁 root 直登（`PermitRootLogin no`）
5. 同步收紧 RDP 3389 / Redis 6379 / 8000-9999 等不必要的全网开放
6. 注意：`Sas_Malicious_Ip_Security_Group` 是 SAS 自动管理，改了可能被覆盖 — 需先解除 SAS 自管或在 SAS 控制台设白名单

**派发对象**: DevOps 单独批次

**执行前置**:
- 确认 Founder + Ben 实际 SSH 上 ECS 的固定 IP（如有）
- 确认 ECS 上跑了哪些服务用到 22/3306/6379/3389/8000-9999 端口（避免误切关键端口）

**不阻塞**: 这是历史既存问题（一年前安全组建立时既如此），与今日 Gemini key rotation 无直接关联

---

### 🟡 TASK-DEV-SERVER-STABILITY — 本地 dev 服务稳定性方案（2026-05-02 记录）

**问题**: Founder MacBook 跑 backend (uvicorn) + frontend (next start) 跨日休眠后必丢:
- 5-01 → 5-02: backend pid 71921 + frontend pid 49226 都丢
- 5-02: backend pid 9684 因阿里云 MySQL idle TCP 切而 startup failed exit
- 每次重启需手工

**根因**: macOS 节能策略 `pmset -g` 显示 `standby = 1` — 系统进入 standby 时所有用户进程被冻结/终止。即使 nohup detached 也躲不过 standby。

**当前 5-02 已应用临时方案**:
- 启动 `caffeinate -i -d -s` 守护进程 (PID 15793) — 阻止 idle sleep / display sleep / system sleep
- backend uvicorn nohup 无 --reload (PID 15387) ppid=1 真 detached
- frontend `next start` (PID 15811) — caveat: warning "next start does not work with output: standalone, use node .next/standalone/server.js"

**caffeinate 局限**:
- ✅ 阻止 idle sleep（用户不动时自动休眠）
- ❌ 无法阻止合盖（lid close）触发的 sleep
- ❌ 无法阻止系统重启 / 用户手动关机 / OOM
- ❌ 无法阻止断电

**长期方案候选**（待评估）:
- Option A: launchd plist 配 LaunchAgent / LaunchDaemon — 系统重启后自动拉起，但开发期可能 noisy
- Option B: 把 dev 服务跑到 docker 本地 — 跟生产一致，但首次配置复杂
- Option C: 改用专用 dev 机（永远不休眠 server-grade 设备）
- Option D: 不改了，每次手动 caffeinate + 重启（接受现状）

**当前推荐**: 短期用 caffeinate（已应用），中期评估 Option A/B

---

### ✅ TASK-T7-FIRST-E2E — xuhuastorytest7 完整 E2E 测试（2026-05-02 17:02 跑完）

**故事**: xuhuastorytest7《我妈骂的AI客服是我训练的》(都市喜剧/网络段子/黑色幽默)
**参数**: pixar_3d × 3:4 × 短篇 18 shots × 3 角色（王翠芬/王小明/小敏）
**总耗时**: 54 分钟（16:08:31 confirm-outline → 17:02:54 Pipeline 完成）

**实证 ✅**:
- D.15 用户画幅真生效: 18 shot 真生 1664×2218 = 3:4 ratio（不是 hardcoded 2:3）
- D.16 数字一致性提示真显示（10086 多处提醒）
- D.18 SIZE_BY_MODEL Seedream 3:4 = 1664×2218 真传到模型
- D.20 outline 黑屏修复（hotfix v2 + Backend Option C 真生效）
- D.17 单一模型铁律（全程 Seedream）
- O-2 cap 真生效（LLM 39 shots → 截到 18）
- ARCH-4 uuid→db_id 映射
- TextOverlayServiceV2 中文气泡完美渲染（白底圆角+尾巴）
- Pixar 3D 风 + 角色还原 100%（红白格子衫+烫发自来卷+金耳环+叉腰）
- Stage 5 18/18 全成功 + sanitize_attempts=0（0 次 CONTENT_SAFETY 触发）
- Mureka BGM 56s 真生

**全程 15 个 bug 完整 retro 已记录在 daily-sync/2026-05-02.md 17:00 之后段**

---

### ✅ D.21 + stale-copy + D.23 — Frontend 三件套修复（2026-05-02 17:18-17:35 完成）

**D.21 hotfix（Frontend agent）**:
- chapter routine 400 catch（StageC.tsx）
- 4 层 portrait fallback（API → static URL → outline data → null）
- withTimeout 包装（超时不死等）
- timeout 后续调到 30/25/15s（10/8/4s 不够 backend 慢响应）
- 改文件: `frontend/src/components/create/StageC.tsx` + `frontend/src/app/create/CreateContent.tsx`

**stale-copy 修复（Frontend agent）**:
- 副文案"先喝杯可可"过期问题
- StageC.tsx L19-45: 删 `FIXED_TIP` 改 `getProgressTip(stage, subPhase)` 函数
- L653-664: 渲染条件扩展为 text-gen + shot-gen
- 5 档 stage → 文案 mapping（Stage 1-2/3-4/5/6/character_ready）

**D.23 自动跳 preview（Frontend agent）**:
- pipeline 完成时（chapter status='completed'）自动 router.push('/preview')
- StageC.tsx L251-304: `finalizeAndGoToPreview` 提升为组件级 useCallback
- L306-341: 新增 D.23 checkpoint watcher（char-preview/scene-preview 阶段每 5s 轮询完成态）
- L430-436: text-gen 轮询完成判断分离（status === completed → 直接跳 preview，不进角色预览）
- DashboardContent.tsx L31-33: handleContinue 改路由 `/create/{uuid}/outline` → hydration → reconcile redirect

**当前 frontend PID**: 22546（含全部修复 + D.21 timeout 30/25/15 + stale-copy + D.23）

---

### ✅ AI-ML BGM A+B+C 修复（2026-05-02 17:38 完成）

**Founder 验证根因**: BGM 调性偏离（年夜饭风而不是段子喜剧风）

**修复**:
- A. 加好例 3 都市喜剧范例（bouncy/kinetic/syncopated piano/snare clap on punchline/brass stab）
- B. 加调性优先匹配硬约束（overall_mood 喜剧词 → 禁参考好例 1 窒息范例）
- C. user prompt 把 overall_mood 提到顶部 + 权威注释（用户主动选 > LLM 元数据）

**改的文件**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/meta_mixed_v3_quote_picking.md`
- L51-81 (B 硬约束)
- L167-205 (A 好例 3 范例)
- L255-271 + L302-307 (C user prompt)
- 备份: `*.bak-20260508-bgm-fix`

**真重跑 BGM v2**: `test_output/manualtest/test7_bgm_after_fix/bgm_v2.mp3` (5MB / 157s)
**对比报告**: `test7_bgm_after_fix/COMPARISON_REPORT.md`

**调性词转向**:
- 旧: holding breath / hand trembling / weight that doesn't lie / Don't resolve it
- 新: Bouncy, kinetic / brass stab on the absurd moment / punchline lands sideways / Lift. Hold.

**待 Founder 试听**: `test_output/manualtest/test7_bgm_after_fix/bgm_v2.mp3` 验收

---

### 🔴 TASK-SCREENPLAY-SCENE-FAIL-FIX — Backend 修 Stage 3 Scene 失败（2026-05-02 17:35 RCA 完成 / 修复待派）

**RCA 结论（Backend agent）**: `_extract_json()` 缺内部引号自动修复逻辑

**故障**: Stage 3 ScreenplayWriter Scene 11/14/16 全部失败，根因：
- 逐 scene 模式调 `_extract_json()` (screenplay_writer.py L1076-1103) 仅 3 条 fallback，**无内部引号修复**
- 批量模式调 `_extract_batch_json()` (L528-661) **有 R4-4 内部引号修复 `_fix_inner_quotes`** (L574-615)
- 当 Claude 在 narration 字段引用角色对话用 `"..."` 时，未转义双引号导致三种解析策略全失败 → `_extract_json` 返回 None
- Scene 11/14/16 都是高潮/结尾段，narration 引号密度高 + chars 越来越长（2974 → 3207 → 4793）

**衍生发现**: Scene 16 `plot_16` 的根本问题是 PP16 outline 缺 `beat` 和 `estimated_duration_seconds` 字段（Stage 1 输出质量缺口）

**推荐方案 A+C 双保险（Backend agent 建议，约 45 min）**:
- A. 提取 `_fix_inner_quotes` 为共用 helper，`_extract_json` 也用上（首选）
- C. Prompt 强化（narration 引用角色台词必须用「」中文书名号）

**待 PM 派 Backend 实施 + Tester 用 test7 数据重跑 Scene 11/14/16 验证**

---

### 🟡 TASK-SCREENPLAY-MOOD-COHERENCE — Stage 3 sound_design_hint 沉重词治本（AI-ML 提议）

**问题**: Stage 3 LLM 写 sound_design_hint 时混入沉重词（如喜剧场景写"走廊隔音棉吸掉所有声音"），影响 BGM 调性

**推荐**: 改 `app/services/screenplay_writer.py` Stage 3 prompt，加 mood coherence 约束

**优先级**: P2（B11 BGM 修复后再做更彻底的治本）

---

### 🟡 TASK-OUTLINE-PLOT-COMPLETENESS — Stage 1 输出完整性（AI-ML 衍生发现）

**问题**: PP16 outline 缺 `beat` 和 `estimated_duration_seconds` 字段，让 Stage 3 fallback 到默认值 + 触发 Scene 失败

**推荐**: `StoryOutlineGenerator` 加 Pydantic 验证，必须含完整字段

**优先级**: P2（与 SCENE-FAIL-FIX 并行处理）

---

### 🟡 TASK-CHAPTER-STORY-400 — Backend chapters/{id}/story 端点 400 修复

**故障**: pipeline 跑中 frontend polling `GET /chapters/1/story` 持续返 400 Bad Request（不是 404 不是 5xx）

**影响**: D.21 timeout catch 缓解了但根因没修

**推荐**: Backend 看为什么 chapter story endpoint 在 pipeline 跑中返 400（应该返 404 = 还没生成 / 200 = 有数据）

**优先级**: P2

---

### 🟡 TASK-BROWSER-CACHE-BUST — 浏览器 cache 顽固持有旧 chunk 长期方案（Founder 5-02 记下）

**故障**: 强刷（Cmd+Shift+R）也无法清干净 disk cache，前端旧 chunk hash（旧 timeout 值）持续被加载

**临时方案**: 用隐身模式（无 cache）

**长期方案候选**:
- 加 cache-control header (max-age=0 for HTML / immutable for hash 资源)
- Service Worker 主动 cache busting
- next.js 配置强制 hash bust 静态文件

**优先级**: P2（隐身模式可用）

---

### 🟡 TASK-DEVOPS-PROGRESS-CATCHUP — DevOps progress 5-02 V1+V2 诊断补全

**问题**: DevOps 5-02 早些时候做了 V1（backend 卡死诊断）+ V2（MySQL 二轮诊断），但 progress completed.md / context-for-others.md 仍停在 May 1 00:11，没补 5-02 工作

**待**: 下次 spawn DevOps 时让其自补这两次诊断的 completed 段

**优先级**: P2

---

## ✅ 2026-05-08 20:45 — 11 task Master Plan 全闭环（PM 收尾标记）

| # | task | 状态 |
|---|------|------|
| B16 | REGENERATE-SHOT-IMPL P0 + P1 hotfix | ✅ 完成（Tester 重测 PASS）|
| B8 | SCREENPLAY-SCENE-FAIL-FIX A+C | ✅ 完成（_fix_inner_quotes_shared 共用 helper）|
| B6 | CHAPTER-STORY-400→404 | ✅ pending/generating → 404；failed 保 400 语义更准（Tester 接受）|
| B18 | OUTLINE-PLOT-COMPLETENESS | ✅ 完成（plot_point 必含 beat + estimated_duration_seconds + fallback 防御）|
| B19 | OUTLINE-MOOD-STANDARDIZE | ✅ 完成（8 enum + 中英文 mood_map fallback）|
| B20 | SCREENPLAY-MOOD-COHERENCE | ✅ 完成（_build_single_scene_prompt 加 MOOD COHERENCE 块）|
| B11 | BGM 6 桶完整通用化 | ✅ 完成（meta_mixed_v3 加好例 4/5/6 + 6 桶 + LLM 复合词归桶 + fallback Warm）|
| B17 | VALIDATOR-ANATOMY | ✅ 完成（severity 三档 + anatomy_issues 数组）|
| B21 | D.24 cache bust | ✅ 完成（bustCache helper + ?v= 自动加）|
| B24 | D.25 BGM 文案 | ✅ 完成（换种风格 + 再来一首 + tooltip）|
| B22 | DEVOPS-PROGRESS-CATCHUP | ✅ 完成（5-02 V1+V2 自补 + 教训固化）|
| B23 | Tester 集成验证 | ✅ 完成（pytest 295 + 6 维度 + B16 hotfix 重测 PASS）|

### 当前活跃 PENDING（未做）

- 🔴 TASK-PARALLEL-M1（4-25 派发，P0 工程并行化改造）— 仍未启动
- 🟡 TASK-API-COST-TABLE / 监控告警 R4 / TASK-STYLE-EXPANSION
- 🟡 SSH-HARDENING / DEV-SERVER-STABILITY / BROWSER-CACHE-BUST 长期方案
- 📝 TTS Key 填入 / Resonance 时间线 / 续写模式 Phase 3
- 📝 v3 BGM 持续优化（Founder 说 80 分，未来可再迭代）
- 📝 5 个未冒烟 mood 端到端 mock 测（温馨/紧张/感人/治愈/浪漫）

---

### 🔴 B26 P1 — D.21 character preview portrait fallback 修复**回归 bug**（2026-05-09 test8 实测发现）

**故障**:
- test8 (project_id=23) Stage 2 完成后 backend portrait 3 张真生成
  （`output/21ebb0d8-2eb0-483d-a4a5-fd8c93ec49ba/character_refs/char_00X_portrait.png` mtime 10:32-10:33）
- 但 frontend character preview 页面**完全空白**（仅"确认角色，继续"按钮 + 30s 倒计时）
- backend log grep 显示 frontend **0 次 GET portrait 请求** — character preview component 根本没尝试加载图

**对比**: D.21 修复（5-02 frontend agent）应该实现 4 层 portrait fallback（API → static URL → outline data → null），且新 build BUILD_ID May 8 20:13 应该含此修复 — 但 character preview 阶段**完全没渲染图**

**根因初判**:
- D.21 在 hydrate 路径有效（StageC.tsx L321-364 character_ready handler）
- 但 **subPhase = "char-preview" 时的图片渲染条件**可能没用 D.21 fallback chain
- 或者 component 收到 character data 但 portrait_url 字段为空（API 没返回）+ fallback 没触发 buildStaticPortraitUrl

**Founder 实测**: test8 不得不"被迫让 30s 倒计时跳过"（跟 5-02 一模一样的 bug）

**待派 Frontend 二轮诊断**: D.21 在 char-preview subPhase 渲染条件 + portrait_url 为空时是否真触发 buildStaticPortraitUrl

**优先级**: 🔴 P1（用户确认角色环节失效，被迫跳过 → 失去调整能力）

---

### 🔴 B27 P1 — `/scenes` URL frontend 渲染 spinner 而非进度条（2026-05-09 test8 实测发现）

**故障**:
- character 30s 倒计时跳过后 frontend 路由切到 `localhost:3000/create/{uuid}/scenes`
- 但 backend 还在 Stage 3 ScreenplayWriter（剧本编写中），scene_refs 真还没生
- 应该显示**进度条**（"剧本编写中"或类似 stage label）
- 实际显示**正在加载你的故事... spinner**

**初判**: D.23 frontend 修复后 router 引入了 `/scenes` 路径，但页面渲染条件不全覆盖 backend 早期 stage（Stage 3 剧本编写）— 应该跟 generation 主进度条页面合并/复用，或加 stage-aware 判断

**待派 Frontend 二轮诊断**: `/scenes` 路由组件 + 跨 stage state 转换条件

**优先级**: 🔴 P1（与 B26 character preview spinner 同类，影响用户感知 pipeline 进度）

---

### 🟡 B29 P2 — Prop Reference Image 系统（2026-05-09 test8 实测发现）

**故障**: test8 不同 shot 中老人拖的"黑色超大行李箱"形状/材质/轮子细节漂移
- shot_2 描述 "matte black hard-shell suitcase, one wheel uneven"
- shot_3 描述 "black hard-shell suitcase, wheeled case"
- shot_5 描述 "rolling suitcase"
- 用词漂移 + Seedream 每次自由想象 → 同一道具视觉不一致

**真根因**: pipeline 只有 character_refs（3 portrait + 3 fullbody）+ scene_refs（5 anchor），**没有 prop reference image 系统**

**修复方向**:
1. 第一次关键 prop 出现时（Stage 4 标识）生一张 prop reference image（与 scene_anchor 同等流程）
2. 后续所有出现该 prop 的 shot 传这张图作为 reference image（含 character_refs + scene_refs + prop_refs）
3. Stage 4 storyboard 加 prop_id 引用（shot.props=["suitcase_001"] 类似 character_id）

**优先级**: 🟡 P2（不阻塞，但用户细看会发现，影响视觉一致性）

---

### 🟡 B30 P2 — ShotValidator anatomy 检测 false negative（2026-05-09 test8 实测）

**故障**: test8 shot_3 Founder 报告"女生的手有点问题"，但 ShotValidator 通过（valid=True, sanitize_attempts=0）

**根因初判**:
- B17 修复后 anatomy_severity 三档（severe/mild/none）严格区分
- mild → 仅 log 不触发 sanitize（避免误伤艺术风格化）
- 但**复杂透视场景**（如趴栏杆）下 Haiku 4.5 可能漏判真正异常为 mild 或 none
- prompt 关键词不全（hands_count / extra_limbs_floating 强但缺 unnatural_arm_angle / missing_fingers / hand_position_impossible）

**修复方向**:
1. anatomy 检测 prompt 加更多关键词（不自然角度 / 手指缺失 / 关节方向反 / 透视错误）
2. mild 阈值下调（test 后再决定）
3. 或加二次审查（severe 直接拦截，mild + 用户报告反馈机制 → 加入未来训练 prompt）

**优先级**: 🟡 P2（不阻塞 — 用户可手动重生）

---

### 📝 B31 P3 — BGM 时长是否允许 ±10s 漂移（2026-05-09 Founder 提问）

**当前**: backend `music_generation_service.py` 严格裁切 BGM 到 target_duration（短篇=180s/中篇=360s）— Mureka 真生 188.80s → FFmpeg 裁到 180.00s

**Founder 提问**: "BGM 在前端显示 3:00 整，应该长短有差异吧，是不是写死？"

**真相**: 不是写死，是 backend FFmpeg 真裁切。当前严格 target 保证音画对齐。

**Founder 决策点**:
- 选 A. 保持当前严格 target（音画对齐 + 视频导出简单）
- 选 B. 允许 ±10s 漂移（更自然，188.80s 直接保留，但音画对齐复杂）
- 选 C. ±5s 漂移（折中）

**优先级**: 📝 P3 产品决策（不阻塞）

---

## ✅ 2026-05-09 14:40 — 全维度 Frontend 修复 + BGM 漂移 + Haiku Logging 全闭环（PM 收尾）

### 5-09 任务批次结果

| # | task | 状态 |
|---|------|------|
| **B26** | D.21 character preview portrait fallback 没生效 | ✅ Frontend 修（StageC.tsx 加 resolvePortraitUrl + dark theme silhouette）|
| **B27** | `/scenes` 路由 spinner 而非进度条 | ✅ Frontend 修（createUrl.ts 加 POST_CHAR_STAGES set）|
| **B28** | backend Stage 3 期间 30s timeout | ✅ Frontend 部分修（30s→120s, 25s→90s + slow warning）|
| **B31** | BGM 严格 target 改漂移 + 切尾 4s | ✅ Backend 修（ffmpeg_post_processor 不再 target 裁切，只切尾 4s）|
| **B32** | Haiku BGM prompt 持久化 | ✅ Backend 修（写 output/{uuid}/bgm_prompt_chapter{N}.txt）|
| 衍生 | URL 切换 spinner 1-2 min hydrate loop | ✅ Frontend 修（isOurOwnPush guard 避免 active session 重 hydrate）|
| 衍生 | ETA Stage 1/2 不显示 | ✅ Frontend 修（< 10% progress fallback 8min/7min）|

### 任务 3 BGM 真返 prompt 实证（test8 真返）

**B11 6 桶通用化在 user_selected_mood='悬疑' 评分: 4.2/5**

Mysterious 桶必备词命中:
- ✅ minor key
- ✅ ambient drone
- 🟡 sparse percussion (出现"sparse"语义部分)
- 🟡 sudden silence (出现"Let silence stretch")
- 🟡 muffled pulse (出现"muffled piano note"+"pulse"分散)
- ❌ tension build / dissonant cluster

禁用词 0/6 污染 ✅

**Backend 衍生发现 B33 (PEND P3)**: `app/services/story_music_extractor.py` 的 `primary_mood` 字段返回 None（未读 user_selected_mood），仅靠 overall_mood 驱动桶路由。建议 3 行小改读取 user_selected_mood 增强桶路由精度。

### B28 真根本修复待 Backend 后续做

Frontend B28 修复（120s timeout）只是缓解，**真根因**是 backend Stage 3 LLM 阻塞 254s 期间 DB 事务持有 row-level lock，导致 GET /projects 阻塞。

**真修复方向**: backend 把 LLM 调用移出 DB 事务，或用 background job + polling 替代同步等待。立 PEND B34。

---

### 🔴 B46 P1 — Stage 5 Shot 部分失败时 job 仍标 completed=100% 误导用户（test10 实测 2026-05-09 18:21）

**实测**: Shot 05 真失败（content_safety），但 job stage='completed' progress=100 status='completed'，前端 dashboard 看不到 1 张缺图警告。

**真根因**: pipeline 把 "Stage 5 完成: 10/11 图像生成成功" 仍视为 success（容错设计），但 frontend job table 没暴露 partial_failure 状态。

**修复方向**:
- backend chapter_generation_jobs 加 `failed_shot_count` / `partial_failure` 字段
- frontend StageD/dashboard 显示"10/11 生成成功，1 张待重生"
- 一键重生失败 shot（结合 B44 SafetyAdvisor）

**优先级**: 🔴 P1 — 用户体验断层（不知道有图缺失）

---

### 🔴 B45 P2 — Shot 手部 anatomy 失误（test10 Shot 08 manila folder + 林开宇手腕扭曲）

**实测 (Founder 像素查看 2026-05-11)**:
- Shot 08 LLM prompt 真写 "manila folder clamped with fierce pressure under his left arm" — 正确
- Seedream 生成图: 文件夹姿势怪、手腕扭曲、手指抓握不自然（像素级 review）
- 历史类似 fail: test8 shot_03 女生手 / test9 Shot 9 角色数量

**真根因**: Seedream 生成"手 + 道具"组合常见 anatomy 弱点（同类问题 NB2 也有）

**修复方向**:
- Stage 4 LLM prompt 加 "fingers clearly visible gripping {object} naturally" 强调指
- ShotValidator (Haiku 4.5) anatomy 判断更严，自动重生（B30 PEND 之前搁置）
- 或者降级方案：让用户在 StageD 一键重生 shot

**优先级**: 🟡 P2 — 视觉细节但不阻塞内容

---

### 🔴 B44 P1 — SafetyAdvisor 建议未触达 frontend 用户（test10 实测 2026-05-09 18:12）

**实测**: Shot 05 content_safety_failure，backend SafetyAdvisor 写了完整建议到 `5_image_results.json`:
- suspected_terms: ["barefoot impressions", "surveillance screen", "suppressing an instinctive reaction"]
- suggested_changes: 3 个替代词建议
- user_message: 中文友好提示

**问题**: Frontend StageD 没显示这些 safety_advice — 用户**不知道 shot 05 为啥失败 + 不知道怎么修**。

**修复方向**:
- backend GET /chapters/{n}/storyboard response 加 shot.safety_advice 字段
- frontend StageD shot 卡片显示 "图生成失败 ⚠️" + 展开看可疑词 + 建议替代
- "应用建议"按钮: 一键用 suggested_changes 替换原 prompt 重生

**优先级**: 🔴 P1 — content_safety 是高频场景，没建议用户无法自救

---

### 🟡 B43 P2 — Haiku BGM prompt 同步阻塞（B35 v2 — test10 实测 2026-05-09 18:19-18:20）

**实测**: Stage 6 BGM 调 Haiku 4.5 时，backend alive_no_health 70s（Monitor v14 报）。

**真根因**: B35 只修了 Sonnet 4.6 (character_designer/screenplay_writer/storyboard_director)，但 BGM Haiku prompt 调用是另一处 sync claude (`music_generation_service.py` 的 anthropic.Anthropic + messages.create)。

**修复**: 同 B35 模式 — `anthropic.Anthropic()` → `AsyncAnthropic()` + `await messages.create(...)`

**优先级**: 🟡 P2 — 单用户场景仅 70s 卡顿不破坏 Pipeline，但多用户并发会全部排队

---

### 🔴 B42 P1 — scenes 确认是否真有停留？（Founder 2026-05-09 18:01 怀疑 PM 验证不全）

**Founder 原话 (18:01)**: "scenes 确认应该也有停留吧 先记下来 等全跑完再全面深度复查"

**PM 当前验证（可能不全）**:
- grep `scenes_confirmed` backend pipeline 0 行
- grep 全 backend 0 行
- pipeline_orchestrator.py L518 有 `checkpoint_callback("scenes_json", ...)` 但是写 chapter 表，不是等待

**Founder 怀疑点**: 之前测试体验里似乎也有 scenes 确认停留（可能 16s 倒计时强制确认）— PM 没找到可能是 grep 关键词不全

**待深查（pipeline 跑完后做）**:
1. grep 其他可能字段名: `scene_confirmed` 单数 / `confirmed_scenes` / `scenesConfirmed` / `scene_ready` / `confirm-scenes` endpoint
2. frontend createUrl.ts L200+ 的 /scenes URL 路由逻辑（是否有等待用户点确认按钮）
3. StageC.tsx 是否有"确认场景"按钮 + scenesConfirmed state 真触发逻辑
4. test9 历史 backend log 看是否有"R4-2"或"等待用户确认场景"日志
5. confirm-scenes endpoint 是否存在 (类似 /confirm-characters)
6. 全 backend grep "scene.*confirm\|confirm.*scene" 看所有相关代码

**触发**: test10 全 Pipeline 跑完后地毯式深度复查，特别是 character_ready → screenplay 之间是否有 scene 确认 + R4-2 polling

**优先级**: 🔴 P1 — 用户体感影响大（如果真有 scenes 停留，frontend 必须显示明确"确认场景"UI 不能让用户卡）

---

### 🟡 B41 P2 — NB2 路径正式弃用清理（Founder 决策 2026-05-09 17:15 "以后用 seedream 不用 nb2 了"）

**当前状态**:
- `.env IMAGE_GEN_PROVIDER=seedream` ✅ production 真用 Seedream
- B38 mini verify PASS: model_used=seedream + 2048×2048 (1:1) + 23.5s/张
- 但 `app/config.py:63 IMAGE_GEN_PROVIDER: str = "nb2"` default 仍是 nb2 — **新部署忘配 .env 会回退 NB2**

**修复方向**:
1. `app/config.py` default 切 "seedream"
2. `app/services/image_generator.py` NB2 路径代码可保留（Premium 用户储备）但加注释 "DEPRECATED 默认不走"
3. CLAUDE.md 14 节"宽高比标准"+ "技术挑战" 角色一致性章节更新（NB2 → Seedream）
4. `.env.example` 默认 IMAGE_GEN_PROVIDER=seedream
5. `tests/test_character_consistency_regression.py` use_pro_model=True 注释（NB2 路径不再走默认）

**优先级**: 🟡 P2（不阻塞 Founder 当前测试，下次修复批清理）

**待派**: Backend agent

---

### ✅ B38 已闭环（2026-05-09 17:00 + 17:15 PM mini verify）

**修复**: image_generator.py L620-660 + L837 + L1430 加 IMAGE_GEN_PROVIDER=seedream dispatch
- 当 settings.IMAGE_GEN_PROVIDER == "seedream"，generate_image() / generate_shot_image / generate_shot_image_phase2_safe 都早 return Seedream
- NB2 路径完全保留（dispatch 之后的 T23 NB2 代码 0 改动）

**调用链路真接通**:
- reference_image_manager.py L126/L142 真调 image_generator.generate_image() → 触发 dispatch ✅
- scene_reference_manager.py L492/L504/L519 同样 ✅

**Mini verify (PM 17:15)**: 1 张 portrait Seedream / 2048×2048 (1:1) / 23.5s / model_used=seedream ✅

**待**: Founder test10 全 Pipeline 真跑（自然就是 18 张 shot 角色一致性回归）

---

### ✅ B39 已闭环（2026-05-09 17:00 + 17:15 PM mini verify）

**修复**: reference_image_manager + scene_reference_manager + pipeline_orchestrator 全链路接 aspect_ratio
- reference_image_manager.py L86/L172 加参数 + L129/L145/L224/L245 真透传给 image_generator.generate_image(aspect_ratio=)
- scene_reference_manager.py L300/L446 加参数 + L492/L504/L519 真透传
- pipeline_orchestrator.py L422/L674/L718/L857/L1105 5 个调用点真透传 project.aspect_ratio

**Mini verify (PM 17:15)**: 1:1 portrait 真生成 2048×2048 (ratio=1.0000) ✅，不再是 848×1264 (2:3) 硬编码

---

### ✅ B40 已闭环（2026-05-09 17:00 + PM verify）

**修复**: meta_mixed_v3_quote_picking.md (production 真路径) + L100-145 SYSTEM "Sub-Vibe 默认锁定" + L516-540 USER "Step 0.5 PREFER/AVOID 矩阵"
- 8 mood × 默认 sub-vibe / 误选 sub-vibe / 内敛诱因关键词 表
- 形状 > 内容铁律 + 4 反例（含 test9 "30 年磨砺 → explosive surge" 实测教训）
- Escape Hatch + 6 个 sub-vibe slip 黑名单
- 备份 .bak-20260509-b40-pre 38726 bytes
- docs/BGM_MOOD_BUCKET_REFINEMENT.md 22.6KB

**调用链路真接通**: music_generation_service.py:51 META_PROMPT_DIR + meta_mixed_v3_quote_picking.md → _load_meta_prompt() 按 "## 系统提示词" + "## 用户提示词模板" 边界解析 → return 含新增段 ✅

**待**: Founder test10 真跑 BGM 听感验证（应是激昂式而非 test9 的"坚守式"）

---

### 🟡 旧 B40 历史段（保留供审计）— Heroic 桶语义太宽，"热血"出来是"坚韧悲壮"不是"激昂"

**Founder 体感 (2026-05-09 16:30)**: "BGM 不是完全热血的感觉，开头有点平静悲凉，后面有点悲壮，有壮的成分，可能贴近一点热血的感觉，还需要对这块进行全面深挖"

**实测对得上 Haiku 文本**:
- "doesn't triumph but endures" → 坚守而非激昂
- "not relentless, but inevitable" → 平静推进
- "No dramatic crescendo" → 没有真正爆发
- "every step a small rebellion" → 有壮的成分但内敛
- 调性词命中: Driving / Brass / Cinematic / rising / crescendo（4.5/5 数据上对，但**听感**不对）

**真根因**:
- Heroic 桶语义太宽，包含 2 个截然不同 vibe:
  1. **激昂式热血** (Rocky 训练蒙太奇 / 体育片高潮 / 少年冲锋)
  2. **坚守式坚韧** (中年磨剑 / 30 年磨砺 / "doesn't triumph but endures")
- Haiku 看到 idea "55 岁 + 30 年差 0.5 分" 自动归第 2 类
- 用户选"热血"通常默认第 1 类（"我要打鸡血爽片不是文艺片"）
- 当前 Mureka 6 桶系统 Heroic 桶映射太粗

**修复方向 (派 AI-ML)**:
- 选项 A: 桶细分 — Heroic 拆成 `heroic_uplifting` (激昂) + `heroic_resolute` (坚韧)
- 选项 B: Haiku prompt 加约束 — "When user_selected_mood='热血', prefer uplifting/triumphant/explosive crescendo over enduring/resolute even if story plot suggests latter"
- 选项 C: 让用户在 Stage A 选 mood 时加副选项（"激昂"/"内敛"）— 复杂，先 A/B
- 选项 D: 不动桶，改 Mureka 提示策略 — 更难

**优先级**: 🟡 P1（不阻塞产品，但用户感受到"BGM 跟我选的不一样"）

**待 AI-ML 深挖**: prompt 工程层 + 8 中文 mood → 6 Mureka 桶映射回顾 + Haiku 输出实例验证

---

### 🔴 B38 P0 — NB2/Seedream 混合模型（违反 D.17 铁律 + memory feedback_pipeline_single_model_only）

**实测发现 (test9, 2026-05-09 15:54-16:13)**:
- Portrait (3 张, 15:54-15:55): `gemini-3.1-flash-image-preview` (NB2) — `image_generator.py`
- Anchor (5 张 scene refs, 16:08-16:12): `gemini-3.1-flash-image-preview` (NB2) — `image_generator.py`
- Shot (18 张, 16:12+): `doubao-seedream-5-0-260128` (Seedream) — `seedream_generator.py`

**违反铁律**: memory `feedback_pipeline_single_model_only.md`:
> 整个故事的所有图（portrait + fullbody + scene + 18 shots）必须出自同一模型。严禁 Seedream→NB2 或反向的运行时 fallback — 18 张图里出现 1 张异类风格用户细看大概率发现，破坏视觉统一性。

**真根因**:
- Wave 5.1 移除了 image_generator.py 的运行时 fallback (L796/L1389/L720)
- 但参考图层（`reference_image_manager.py` + `scene_reference_manager.py`）仍调 `image_generator` NB2 默认
- pipeline_orchestrator 切换 Shot 用 SeedreamGenerator 但**没把参考图层也切到 Seedream**

**修复方向**:
- 当 pipeline 选 Seedream 时，参考图层也用 SeedreamGenerator
- 当选 NB2 时，全栈都用 NB2
- 单一模型旗标统一从 config 读取，不分散在多个 service 里

**优先级**: 🔴 P0 — 用户视觉一致性体验

**Founder 注 (2026-05-09 16:14)**: "seedream没问题 目前测试就是seedream 之前也是的" — 但实际混合，需要修复让它真的全 Seedream

---

### 🔴 B39 P0 — Portrait/Fullbody 没按用户选的 aspect_ratio 生成（硬编码 2:3）

**实测发现 (test9, 用户选 1:1)**:
- projects.aspect_ratio = '1:1' ✅ (Stage A 选项真持久化)
- Portrait dimensions: **848×1264 (≈2:3)** ❌
- Fullbody dimensions: **848×1264 (≈2:3)** ❌
- Anchor dimensions: 待 verify
- Shot dimensions: 2048×2048 (1:1) ✅

**违反铁律**: memory `feedback_aspect_ratio_user_perception.md`:
> 任何"用户主动选择"参数（aspect_ratio / style / voice 等）必须从用户输入直接传到生成层。任何 hardcoded 中间环节让用户选了等于没选 = P0 用户体验灾难

**真根因**:
- D.15 P0 (2026-04-28) 修了 pipeline_orchestrator hardcoded aspect_ratio="2:3" → 真传 project.aspect_ratio
- 但只修了 Shot 层 (image_generator.py)
- 参考图层 (`reference_image_manager.py` + `scene_reference_manager.py`) 仍硬编码 2:3
- CLAUDE.md 14 节"宽高比标准（TASK-ASPECT-2x3，2026-02-14）"过时 — D.15 之后应该按用户选

**修复方向**:
- `reference_image_manager.py` portrait/fullbody 接收 aspect_ratio 参数（不硬编码 "2:3"）
- `scene_reference_manager.py` anchor 同样接收 aspect_ratio
- pipeline_orchestrator 把 project.aspect_ratio 透传到这两层
- CLAUDE.md 14 节描述更新（按用户选，不再"统一 2:3"）

**优先级**: 🔴 P0 — 用户主动选了画幅但 portrait/anchor 不跟，是用户体验灾难（B33 类型问题：用户选了等于没选）

---

### 🟡 B37 P2 — Frontend 4 文件 0 console.log + Backend 2 文件日志稀疏（debug 黑盒）

**Founder 强调 (2026-05-09 16:05)**: "全面毫无遗漏的深度复查下所有对应的 debug 日志是不是都齐全，不管前端还是后端还是架构还是数据库"

**Frontend 严重黑盒（修 B36/B27/B28 必须先补日志）**:

| 文件 | console.log/warn/error | 关键缺失 |
|------|------------------------|--------|
| `frontend/src/lib/createUrl.ts` | 0 | 路由决策（POST_CHAR_STAGES set 命中 / urlStage 推导）— B27 stale backendStage 修复必须能 trace |
| `frontend/src/lib/api.ts` | 0 | fetch wrapper（endpoint / duration / status / timeout）— B28 错误必须能定位 |
| `frontend/src/contexts/CreateContext.tsx` | 0 | reducer state transition（state.characters / userSelectedMood / projectId）— B36 角色卡片 0 渲染必须能 trace state 变化 |
| `frontend/src/components/create/StageB.tsx` | 0 | confirm-outline 提交 — UX-2 warnings 接收/解析 |
| `frontend/src/components/create/StageD.tsx` | 0 | 完成页交互 |
| StageC.tsx | 10（偏少） | hydrate / character_ready handler 关键路径 |

**Backend 局部稀疏**:

| 文件 | 密度 | 关键缺失 |
|------|------|--------|
| `app/services/storyboard_director.py` | 2.28% | Scene 失败时只打"❌ 失败"，没记 root cause（实测 Scene 5 失败 0 原因日志）|
| `app/services/job_manager.py` | 2.58% | background task 入口 stage transition 跟踪稀疏 |

**修复方向**:

Frontend:
- `createUrl.ts` 加 logger.debug 每个分支命中 + input/output
- `api.ts` 加 fetch wrapper 全程记录 (method, url, duration, status, error)
- `CreateContext.tsx` 加 reducer logger 记 action.type + state diff
- `StageC.tsx` hydrate effect / character_ready handler 加 console.log 记 state.characters.length / portraitUrl / 倒计时启动时机

Backend:
- `storyboard_director.py` Scene 失败时 log full exception + scene_id + retry attempt
- `job_manager.py` background task 入口/出口 + 每个 stage transition log

**优先级**: 🟡 P2（B36/B27/B28 修复前置条件，无日志只能瞎修）

**实测教训 (test9, 2026-05-09 15:54-16:05)**: B36 v2 / B28 timeout 跳错页 / B27 路由 stale，全程 5-6 分钟前端黑盒，PM 靠 backend log + Monitor v12 + DB 直查反推用户体感，缺前端日志反向 trace。

---

### ✅ B36 已闭环（2026-05-09 17:00 frontend agent 完成 + PM verify）

**修复**: StageC.tsx
- L916 `hasCharacters = characters.length > 0`
- L919-922 倒计时 GATED 当 hasCharacters=false（不强制确认空角色）
- L1039-1043 占位符 UI "角色还在生成中，请稍候…" + Loader2 spinner
- L1049 cards grid hidden 当 !hasCharacters
- L1125 确认按钮门控（hasCharacters && !isLocked）
- L922 加 `[B36][CharacterPreview] countdown GATED` console 调试日志

**Frontend agent verify**:
- npm run build 0 errors，新 BUILD_ID `zjKZpzY23BhjDBR5RLX7F` @ 16:58
- chunk 386 真含 "占位符 / 角色还在生成中" 字符串

**待**: PM 重启 frontend (kill 60089 + npm run start) 让新 build 真生效

---

### ✅ B27 已闭环（2026-05-09 17:00 frontend agent 审计 + PM verify）

**结论**: createUrl.ts 全路由表审计完成
- POST_CHAR_STAGES = `{screenplay, storyboard, image_preparation, image_generation, bgm, completed}`
- 当 stale backendStage 不在 set 内，reconcileBackendVsUrl 不会把 urlStage="scenes" 错误重定向 → 安全
- 加每分支 `[createUrl]` 日志，下次 stale 问题可定位

**待**: 同 B36，PM 重启 frontend 后真生效

---

### ✅ B28 已闭环（2026-05-09 17:00 frontend agent 完成 + PM verify）

**修复**: CreateContent.tsx L1116-1168
- `isTimeout = hydrateError.includes("服务器正忙")`
- timeout 场景: Loader2 spinner + "AI 正在努力创作中" + 双按钮（"刷新页面，继续等待" + "返回工作台"）+ 关闭页提示
- 404 场景: 保持原 AlertCircle + 单"返回工作台"
- 不再自动 fallback /outline URL

**待**: PM 重启 frontend

---

### ✅ B37 frontend 部分已闭环（2026-05-09 17:00）

**修复**:
- `lib/api.ts` 4 节点 `[API]` (start / network-error / http-error / success + ms)
- `lib/createUrl.ts` 每分支 `[createUrl]` (输入 snapshot + 决策理由)
- `contexts/CreateContext.tsx` switch-case 级 `[Reducer]`（HYDRATE_FROM_BACKEND 打印 chars/shots count）
- `contexts/AuthContext.tsx` 13 节点 `[Auth]`
- `components/create/StageB.tsx` 6 节点 `[StageB]` (handleConfirm 流程)
- `components/create/StageD.tsx` 8 节点 `[StageD]` (render + actions)
- `components/create/BgmPlayer.tsx` 13 节点 `[BgmPlayer]` (mount + fetch + bgm states)

**B37 backend 部分**: 等本波 Backend agent 完成（storyboard_director Scene 失败 / main.py exception_handler / auth.py / database.py）

---

### 🔴 旧 B36 历史段（保留供审计）— character preview 页面角色卡片 0 渲染（B26 v2 真回归）

**实测发现 (2026-05-09 15:57, test9 跑 Stage 2 完成后)**:
- Founder 截图: /create/{uuid}/characters URL，**只显示标题"角色预览" + 16s 倒计时 + "确认角色，继续"按钮**
- **3 个角色卡片完全没渲染**（不是图加载失败 — 是卡片组件根本没出现）
- Founder 反馈: "仍然看不见角色，被迫继续"

**数据层完全正常 (PM 直查 DB + 文件系统)**:
- chapter.characters_json 含 3 角色完整（陈志远/陈晓桐/林俊）
- char_001/002/003_portrait.png 全生成（1MB+ @ 15:55-15:56）
- portrait_url 字段填好: `/static/outputs/{uuid}/character_refs/char_NNN_portrait.png`
- job stage=`character_ready` progress=10 msg=`角色设计完成，请确认角色和场景`

**B26 v1 修复（2026-05-09 14:30）的 gap**:
- v1 修了 "图片加载失败 silhouette dark theme 不可见" → 加了 portraitErrors state + resolvePortraitUrl + bg-bg-secondary/60
- 但**根本问题更上游**: 当 characters_overview 数据真的没 hydrate 到 StageC `state.characters` 时，`{state.characters.map(...)}` 渲染 0 个，组件直接显示空白
- portraitErrors 只覆盖了"图片有 src 但加载失败"，没覆盖"characters 数组本身为空"

**真根因 (待 frontend agent 深入 debug)**:
- D.21 hydrate chain 在 character_ready 事件触发时，characters_overview 是否真触达 StageC state.characters
- character_ready handler 是否在 hydrate 完成前就触发了 16s 倒计时强制跳转
- 可能 race: GET /chapters/.../status 在 Stage 3 sync LLM 阻塞期间慢响应，hydrate 拿到部分数据就开始 render，characters 数组还没 populate

**修复方向**:
- StageC 加 characters.length === 0 的 placeholder UI（显示"角色还在加载..."而不是空白 + 倒计时）
- 倒计时只在 characters.length > 0 才启动
- D.21 hydrate chain 必须先把 characters_overview 同步到 state.characters，才允许 character_ready 切到 StageC

**优先级**: 🔴 P1 — 用户体验灾难（用户被迫确认空角色，根本不知道角色长啥样）

**Founder 体感 (2026-05-09 15:57)**: "仍然看不见角色，被迫继续"

---

### 🟡 B35 P2 — Pipeline Stage 2/3/4 sync Claude 调用阻塞 uvicorn event loop（B28 daily-sync 真根因订正 v2）

**实测发现 (2026-05-09 15:54-15:55, test9 跑 Stage 2)**:
- Founder 实测: confirm-outline 后进 generating 页面，前 1-2 分钟显示 "AI 正在创作中" slow warning，没出进度条；约 70s 后才显示 2% + "大纲已确认，正在设计角色..."
- Monitor v11 同步报 `[15:54:15] backend: ok -> alive_no_health` → `[15:55:23] alive_no_health -> ok`（70s 不响应外部 HTTP，含 /health）
- backend log 显示: 15:54:02 `[CharacterDesigner] [尝试 Claude Sonnet 4.6]` → 15:55:16 才有下一条 DB COMMIT 日志，期间 70s 静默
- ps aux: PID CPU 0.0%（idle，在 await 网络）

**真根因 (grep 验证)**:
- `app/services/character_designer.py:82` 用 **sync** `self.claude_client.messages.create()`（不是 AsyncAnthropic）
- 同样模式: `app/services/image_generator.py:700`、`:801`（grep 已确认）
- uvicorn 默认单 worker → sync LLM 调用阻塞整个 event loop → 期间所有 HTTP 请求（含 /health）暂停响应
- frontend GET `/chapters/.../status` 也阻塞 → 显示不出进度条 → 触发 B28 slow warning

**B28 daily-sync 写"Stage 3 LLM 阻塞 DB 事务"是错的（已订正 v2）**:
- v1 订正认为是 generate_outline endpoint 的 db session 占连接 — 修了一部分（B34 commit-before-LLM）
- v2 订正发现真根因是 **sync claude_client 阻塞 event loop**，不是 DB 事务也不是连接池
- B34 修复仍有意义（释放 row lock + 短事务写），但只覆盖了 generate_outline endpoint，没解决 background pipeline 同步阻塞

**修复方向 (Plan A)**:
- `character_designer.py` / `screenplay_writer.py` / `storyboard_director.py` / `image_generator.py` / `story_outline_generator.py` 全部 `claude_client = anthropic.Anthropic()` 换成 `claude_client = anthropic.AsyncAnthropic()`
- 调用处 `self.claude_client.messages.create(...)` 加 `await`
- 影响: backend 在 LLM 期间 `/health` 瞬响 + 支持多用户并发请求 + frontend 进度条立即显示

**优先级**: 🟡 P2 — 不阻塞 Founder 单用户测试（B28 slow warning 已 cover），但多用户并发场景必修。下个修复批一并改。

**Founder 体感 (2026-05-09 15:55)**: "前面的 generating 页面刚开始正在创作中有点慢，大概过了 1-2 分钟才出来进度条，目前来看问题不大，可以记下来之后审查"

---

### ✅ B33 — 已闭环（2026-05-09 15:35，产品决策升级版）

**Founder 决策升级**: 不只是修 3 行 — 产品调整把 mood 选择从 outline 编辑页移到 **Stage A**（大纲生成前），用户先选 mood → LLM 按 mood 写 outline → BGM 也按 mood 路由。理由："大纲都生成了 mood 也基本定了，后面再改有违和感"

**实施（Backend + Frontend 并行）**:
- DB: alembic 003 加 `projects.user_selected_mood VARCHAR(32)` ✅ upgrade head
- model/schema: `Project.user_selected_mood` Column + `ProjectCreate` 8 中文 Literal
- API: POST `/projects/` 真接收持久化 + `ProjectDetail` 真返
- Stage 1 LLM: `story_outline_generator` 注入 MANDATORY mood 约束 + 中文→英文 8 桶映射
- BGM: `music_generation_service` + `story_music_extractor` priority chain (project.user_selected_mood > confirmed_outline > visual_tone)
- 全链路透传: api → start_generation → job_manager → pipeline_orchestrator → music_service
- Frontend: StageA 加 8 chips + POST body + hydrate；StageB 完全移除 mood section
- 验证: 9 backend 文件 AST + frontend chunk 386-ac0fee450e03c78e.js 真含 user_selected_mood + BUILD_ID `SVbXl3_Z3Lr31obqPhC0T` (15:34) + alembic head=003 + backend PID 59918 (15:34) + frontend PID 60089 (15:35) 全 health 200

---

### ✅ B34 — 已闭环（2026-05-09 15:35，方案 A）

**🚨 根因订正**: B28 daily-sync 写"Stage 3 LLM 阻塞 DB"是描述错误。地毯式审查发现 pipeline_orchestrator Stage 3 ScreenplayWriter **本来就不在事务内**（`job_manager.py` checkpoint_callback 用 `async_session_maker()` 短 session，B-1 设计模式）。真根因是 **Stage 1 generate_outline endpoint** 的 254s LLM 占用 db session 期间持有连接。

**实施（方案 A）**:
- `app/api/projects.py:431-475` generate_outline endpoint:
  - L443 `await db.commit()` 提前提交 READ 事务释放 row lock
  - L449 LLM 调用（254s）**不在事务内**
  - L465 `async with async_session_maker()` 短事务写 raw_outline_json
- 验证: pytest test_architecture.py 7/7 PASS + AST 全过

---

### 🔴 B42 真相揭晓（5-11 10:40 PM 深查）— scenes 字段映射 mismatch + 20s 倒计时强制确认

**完整根因**:
1. **Backend confirmed_outline_json TOP-LEVEL keys 不含 'scenes'**（实测 verify TOP-LEVEL 15 keys，0 scenes）
2. Stage 3 ScreenplayWriter 把 scenes_json 写到 `project_chapters.scenes_json` 表列（不是 confirmed_outline）
3. Frontend hydrate L759-766 期望 `outline.scenes` → 但 outline 从 `co.confirmed_outline.scenes` 来 → **= []**
4. `previewScenes = []` → ScenePreview 显示 0 场景
5. ScenePreview L1153 `useState(20)` 20s 倒计时 → 0 时自动 dispatch CONFIRM_SCENES → 切 shot-gen
6. **用户体验灾难**: 用户看 20s 空场景列表 → "怎么没有场景？" → 倒计时归零自动跳过

**test10 没暴露**: 用户卡在 char-preview B36 v3 (PM SQL 解锁后), backend pipeline 自动跑过，frontend 没到 scene-preview 子阶段

**修复方向（与 B36 v3 同类）**:
1. Frontend hydrate 改成从 chapter.scenes_json (调 GET /chapters/{n}/storyboard 或 /chapters/{n}/story) 拿 scenes 数据
2. 或者 backend serialize_project_detail 把 chapter.scenes_json 解析后加到 confirmed_outline.scenes 字段
3. ScenePreview 加 hasScenes 门控（参考 B36 hasCharacters）— 0 场景时占位符 UI + 倒计时不启动

**优先级**: 🔴 P1 — 与 B36 v3 同类严重程度


---

### 🔴 B47 P1 — Stage 1 大纲 LLM 没强制按 user_selected_mood 输出（test11 实测 5-11 15:25）

**实测 (test11 project 1fbc017d-944c-457c-ba51-4020fe4a6f15)**:
- Stage A 用户选 **"幽默"** → DB `projects.user_selected_mood='幽默'` ✅
- backend log `[StoryOutlineGenerator] B33 user_selected_mood: 幽默 (强制注入 LLM 约束)` ✅
- 但 Stage 1 LLM 输出 `raw_outline.mood='治愈'` ❌ + `raw_outline.user_selected_mood=None` ❌
- confirmed_outline 跟着错（'治愈'）

**根因**: B40 反偏置 sub-vibe 锁定只修了 BGM Haiku prompt（`meta_mixed_v3_quote_picking.md`），**没修 Stage 1 大纲 LLM prompt**（`story_outline_generator.py` 注入的 B33 prompt 约束太弱）。

故事内容（孤独老人 + 凌晨3点 + 猫送外卖）让 LLM 自动归"治愈"sub-vibe，**忽视用户明确选的"幽默"**。

**修复方向**:
- `story_outline_generator.py` 的 B33 prompt 模板加 sub-vibe 反偏置约束（参考 B40 meta-prompt L100-145 SYSTEM "Sub-Vibe 默认锁定"）
- 明确指令 LLM: "user_selected_mood='幽默' 时**必须**输出 `mood=幽默`，**不允许**因故事内容含'孤独'/'独居'/'凌晨'等内敛诱因而滑向'治愈'/'感人'"
- LLM 输出还必须把 `user_selected_mood` 字段透传到 raw_outline（当前为 None）

**优先级**: 🔴 P1 — B33 端到端链路真断点（前端选对 + DB 持久化对 + LLM 自由发挥让 mood 偏离）

**这次 test11 BGM 应该按 confirmed_outline.user_selected_mood='治愈' 路由 Heartwarming 桶**（不是 Comedic 桶 — 已偏离用户原意）


---

### 🟡 B48 P2 — 角色预览卡片右上角"重新生成"按钮 UX 不直观（Founder 5-11 15:38 反馈）

**位置**: `frontend/src/components/create/StageC.tsx` L1089-1092 CharacterPreview 卡片右上角

**当前实现**:
- 图标 `RotateCcw` (反向旋转 ⟲，lucide-react)
- onClick `handleRegenerate(char.id)` — 用原 prompt 重生（同描述换 seed）
- title="重新生成" — hover 才显示
- 32×32px 黑色半透明圆形

**Founder 反馈**: "每个角色右上角的刷新按钮是什么意思，作为用户会有点困惑"

**问题**:
1. RotateCcw ⟲ 图标语义易误解（看着像"撤销 / 恢复原图"）
2. title 只 hover 显示，移动端不可见
3. 跟下方"✏️ 调整"按钮功能 overlap 但区别不直观（一个不改 prompt 重生，一个改 prompt 后重生）
4. 32×32 太小容易误点

**修复方向**:
1. 图标改 `RefreshCw` (↻ 顺时针刷新) 或 `Dices` (🎲) 或 `Sparkles` (✨)
2. 加显式 label "换一张" 或 hover tooltip 突出（不只 native title）
3. 视觉跟"调整"按钮区分（颜色 / 位置 / 大小）
4. 或者**直接移除右上角**，统一只用下方"调整"按钮（用户改 prompt + 留空表示"不改 prompt 只换 seed" — 简化 UX）

**优先级**: 🟡 P2 — UX 改进，不阻塞功能


---

### 🔴 B49 P1 — Frontend createUrl charactersConfirmed 推断错误，导致 /scenes 反弹 /characters（test11 实测 5-11 15:40-15:42）

**实测时间线**:
- 15:40:29 用户点"确认角色，继续" → ConfirmCharacters API ✅ `projects.characters_confirmed=1` 写入 DB
- 15:40:31 Pipeline R4-1 ✅ 检测到 → 跳出等待 → 进 Stage 3 ScreenplayWriter LLM
- 15:40:31-15:43+ Stage 3 LLM 跑中（~100-200s），job `current_stage='character_ready'` 不变（progress_callback 还没 emit 'screenplay'）
- frontend createUrl.ts L646-647 推断 `charactersConfirmed = ADVANCED_STAGES.has('character_ready') = FALSE`
- 用户 URL=/scenes → createUrl 推断 charactersConfirmed=false → **强制回弹 /characters**
- 反复重定向 → 用户卡在 /characters spinner（明明已确认）

**真根因**: `frontend/src/app/create/CreateContent.tsx` L646-647:
```typescript
const charactersConfirmed =
  ADVANCED_STAGES.has(status.stage || "") || status.status === "completed";
```
- 用 `job.current_stage` 推断，但 Stage 3 LLM 跑中时 stage 还是 `character_ready`（过渡态）
- **没用 `project.characters_confirmed` DB 字段真值**（ProjectDetail response 应已含此字段，需要 verify backend 暴露）

**修复方向**:
- backend ProjectDetail schema 暴露 `characters_confirmed: bool` 字段
- frontend hydrate 优先读 `project.characters_confirmed`，fallback `ADVANCED_STAGES.has(status.stage)`
- 同样适用 `scenesConfirmed` 推断（同类问题，但目前 backend 无 `scenes_confirmed` 字段）

**优先级**: 🔴 P1 — 用户体验断层（明明点了确认仍卡 /characters）

**临时绕过**: 用户在 Stage 3 LLM 完成（~3 min）后自动跳 /generating，但用户体验差


---

### 🔴 B50 P1 — Scenes 确认页面用户没看到内容就被跳过（test11 5-11 15:42 Founder 反馈）

**Founder 原话**: "对于 scenes 页面我只看到跳转地址 但没看到实际出来场景描述让我确认的页面"

**真根因**（综合 B42 + B49）:
- 用户点"确认角色" → URL 短暂跳 /scenes
- 但被 B49 (createUrl charactersConfirmed bug) **立刻回弹 /characters** → 用户看不到 ScenePreview
- 或者即使进了 /scenes（B49 修后）→ B42 scenes 字段 mismatch → previewScenes=[] → hasScenes=false → 占位符 "场景还在生成中..." → 20s 倒计时自动 dispatch CONFIRM_SCENES → 跳 shot-gen
- **整个 ScenePreview 真实场景列表用户永远看不到**

**修复依赖**:
1. B49 修后 frontend 不会回弹 /characters
2. B42 修后 ScenePreview 真显示场景（含 hasScenes 门控 + 占位符 — 已修但用户没等到 backend Stage 4 真生 scenes 就被 20s 倒计时跳过）

**新发现**:
- 即使 B42 hasScenes 门控生效（不强制确认），20s 后还是自动 dispatch CONFIRM_SCENES？让我看 StageC L1162-1171 ScenePreview useEffect 是否真的当 !hasScenes 时停止倒计时
- 实测应该停止，但 Founder 体感是"没看到场景就被跳过" — 可能是 B49 阻断了用户进入 /scenes URL，根本没启动 ScenePreview 组件

**修复方向（综合）**:
- 必须先修 B49（让 /scenes URL 真稳定不回弹）
- 然后 ScenePreview 必须等 backend Stage 3 完成 + chapter.scenes_json 真有数据 → frontend hydrate 真拿 → previewScenes.length > 0 → 用户看到场景才能确认
- 倒计时 20s **不够**（Stage 3 + Stage 4 需要 ~5 分钟），应该改成"有数据才启动" + 用户主动点确认才跳

**优先级**: 🔴 P1 — 跟 B42 + B49 同类，scenes 确认完全 broken


---

### 🟡 B51 P2 — Stage 4 StoryboardDirector Scene 偶发"shots 为空"无自动重试（test11 5-11 15:47:23）

**实测 (test11 project 1fbc017d-944c-457c-ba51-4020fe4a6f15, Stage 4 storyboard)**:
```
2026-05-11 15:47:23 ERROR xuhua [StoryboardDirector] Scene 4 生成失败: shots 为空，检查 LLM 返回或 JSON 解析
❌ 失败
```

**真根因**: Stage 4 Sonnet 4.6 LLM 跑 Scene 4 时输出空 shots 数组或 JSON 解析失败。当前 Pipeline 有容错继续跑其他 Scene（不 crash），但**Scene 4 的 shots 永久丢失**。

**当前行为**:
- ✅ Pipeline 不 crash，继续跑 Scene 5/6/7
- ✅ B37 logger.error 真生效（附 root cause "shots 为空，检查 LLM 返回或 JSON 解析"，test10 时只打"❌ 失败"无原因 — B37 改进了）
- ❌ 没自动 LLM 重试机制 — Scene 4 的 shots 永远缺失
- ❌ 最终 shot 数 < 总 Scene 拆出的 shot 数（test11 11 计划 - 1-3 缺失 = 8-10 实际）
- ❌ B46 `failed_shot_count` 字段不一定 trigger（这是 Stage 4 LLM 失败不是 Stage 5 image 失败）

**期望行为**:
- Scene 4 LLM 输出空 shots → 检测到 → 自动重试 1-2 次 (用稍微改的 prompt 或调高 temperature)
- 仍然失败 → 走 fallback minimal shot（如 1 张 "Scene 4: {scene_summary} 全景"）保证 Scene 不丢
- 或者 LLM prompt 加更严格 schema 约束（force JSON output + min 1 shot per scene）

**修复方向**:
1. `app/services/storyboard_director.py` `_generate_scene_shots` 加 retry decorator (最多 2 次 + temperature 渐增)
2. 二次失败时调 fallback minimal shot template
3. 同步暴露 chapter `failed_scenes_count` 字段（B46 衍生）

**优先级**: 🟡 P2 — 偶发（Sonnet 4.6 大部分场景正常），但用户体验不好（最终 shot 数<预期且无 UI 提示）

**B46 衍生**: B46 修了 Stage 5 image shot 失败的 `failed_shot_count`，但 Stage 4 LLM scene 失败没字段暴露 — 应该补 `failed_scenes_count`


---

### 🔴 B52 P0 — Character adjustment 3 层断点导致 shot 角色发色不一致（test11 5-11 实测）

**Founder 体感**: "shot02/03/07/08/18 女孩头发是黑色"（其他 shot 红发）

**真根因（PM 地毯式深挖 5-11 16:13）**:

**断点 1**: `POST /characters/{char_id}/adjust` (app/api/projects.py L870)
- Haiku 4.5 改了 `character.description`（含"一头鲜艳的红色长发"）
- 但**没改 `character.physical.hair_color` 字段**（仍 `deep_black_with_slight_brown_sheen`）

**断点 2**: `POST /characters/{char_id}/regenerate-portrait` (L1067)
- 只重生 portrait（用新 description → 红发 portrait）
- **没同步重生 fullbody**（fullbody 仍是 Founder 改之前的黑发版本）
- PM Read fullbody.png verify: char_001_fullbody.png 真显示**黑发马尾** ❌

**断点 3**: Stage 4 LLM (`storyboard_director.py:1139`)
```python
"physical_summary": f"{char.get('physical', {}).get('hair_color', '')} {char.get('physical', {}).get('hair_style', '')}"
```
- 直接读旧 `hair_color="deep_black"` → 注入 image_prompt
- shot 1/5/10 image_prompt 含 "black hair"，shot 7/8 含 "dark hair"

**断点 4 (cascade)**: Stage 5 Seedream
- shot 02/03/07/08/18 可能用 fullbody（黑发）作参考 → 生黑发
- shot 1/5/10 用 portrait（红发）作参考但 image_prompt 写 "black hair" — Seedream prompt 文字优先可能也黑发
- 实际 5 张黑发分布: shot 02/03/07/08/18 (Founder 实测)

**修复方向（必须同时修 4 层）**:
1. `/adjust` 端点 Haiku prompt 加约束 — 改 description 时必须同步改 physical 所有字段（hair_color/hair_style 等）
2. `/regenerate-portrait` 端点完成后**自动同步重生 fullbody**（用新 portrait 作参考）
3. Stage 4 storyboard_director 优先读 description 中的颜色描述（fallback hair_color）
4. CLAUDE.md 加铁律: character adjustment 必须四件套全更新 (portrait + fullbody + description + physical 字段)

**优先级**: 🔴 P0 — 用户感受到"明明改了红发 shot 还是黑发"，character adjustment 功能 broken

---

### 🟢 B51 v2 (扩展) — Scene 4/10 失败完整原因（已记 B51，新增 LLM 真返内容）

**实测 (test11 Stage 4)**:
- Scene 4 失败 (15:47:23): Claude 响应 6418 chars 耗时 39.8s → ERROR "shots 为空，检查 LLM 返回或 JSON 解析"
- Scene 10 失败 (15:49:36): Claude 响应 6216 chars 耗时 36.9s → ERROR "shots 为空"
- **LLM 真返 6000+ chars 内容但 JSON 解析失败 OR shots 数组为空**
- Scene 4: EXT. 蜿蜒夜巷 - 凌晨03:10（林小玲跟踪猫穿巷 — 故事关键动作）
- Scene 10: INT. 深夜便利店 - 凌晨03:00（数日后 — 故事节点）
- 缺这 2 个 scene 共 4 shot → 用户看视频感觉"剧情跳了"

**修复（B51 已记，再次强调）**: Stage 4 加自动重试（max 2 次 + 温度渐增）+ 永久失败时 fallback minimal shot（保证 Scene 不丢）

---

### ✅ B40 Comedic 桶反偏置实测验证（test11 BGM Haiku 真输出）

**bgm_prompt_chapter0.txt 完整分析**:
- meta header `user_selected_mood: 治愈` ❌（受 B47 上游 mood 错位影响）
- 但 Haiku 真输出**幽默欢快**调性（不被错误 mood 字段拖累）:
  - "Bouncy, kinetic, syncopated—like fingers tapping a keyboard right before a prank lands"
  - "Light piano with snare clap on each absurd reveal"
  - "trailing a cat through a fish market, chess pieces scattered by paw pads, four uncles laughing"
  - "Bassline that struts but doesn't swagger"
  - "Two beats of silence before the final brass stab"
  - "No melodrama here. The mischief snaps into place"
- B40 PREFER 命中: **Bouncy/snare clap/syncopated/brass stab** ✅
- B40 AVOID 0 污染: 无 bitter laughter / no self-mocking despair ✅

**结论**: 即使 mood 字段错（治愈），Haiku 看完整 story 内容仍按"幽默"sub-vibe 输出。Founder 体感"BGM 蛮欢快幽默"对得上 ✅。

但 mood 字段错（B47）仍需修 — 桶路由可能受影响（虽然这次 Haiku 救场）。

---

### 🟡 B53 P3 — Mucha 新艺术风格部分有部分没（test11 实测）

**Founder 反馈**: "18 张 Mucha 新艺术风格 shot 部分有这种感觉 部分没有 这个问题不大 之后调好了用更好的模型和 NB2 测测看 seedream 5.0 lite 就是测试用的 不会生产用"

**根因**: Seedream 5.0-lite 模型对装饰风格（Mucha/art_nouveau）的还原能力弱，部分 shot 装饰边框被简化或省略。

**修复方向**:
- 生产时切回 NB2 (`IMAGE_GEN_PROVIDER=nb2`) — 风格还原能力更强
- 或者 Stage 4 image_prompt 加强 "Mucha decorative border with floral and vine patterns" 等明确视觉锚点指令
- 或者升级到 Seedream 5.0 Pro / Seedream 4.0 完整版

**优先级**: 🟢 P3 — Founder 已知 Seedream 5.0-lite 测试模型限制，生产用 NB2


---

### 🟡 B54 P2 — BGM 长度 196.88s vs 故事预期 72s 严重不匹配（test11 实测 5-11 16:13）

**实测**:
- BGM mp3 真长度: **196.88s ≈ 3 分 17 秒**（用 ffprobe verify）
- 18 shot × 4s/shot = **72s** 期望（产品设计每 shot 停留 4 秒）
- BGM 比故事长 **125s（近 2 倍）** ← 严重 mismatch

**根因**:
- Mureka 模型默认输出 ~3 分钟（无视实际故事时长）
- B31 修了切尾 4s 但**只切水印**，没按 shot 数量重剪
- 当前 Pipeline 没"BGM 时长适配 shot 数量"逻辑

**用户体感**:
- 看完故事 BGM 还在播 124s
- 或者视频合成阶段强制裁短（test11 没到视频合成阶段 — B55）
- 用户调"换 BGM"会怪

**修复方向**:
1. Mureka 调用前传入 target_duration_sec = shot_count × 4s（Mureka API 支持 duration 参数）
2. ffmpeg_post_processor 重剪 BGM 到 shot 总时长（+ ~5s 缓冲）
3. 或者 shot 时长可变（按 narration_segment 长度）— 但产品当前固定 4s/shot

**优先级**: 🟡 P2（不阻塞但影响用户最终体验）

---

### 🟢 B55 P3/P4 — Phase 4.5 视频合成未上线（产品定位现状非 bug）

**summary.json stages_completed**: `[outline, characters, screenplay, storyboard, images, bgm]` 6 个 stage
- **没有**: TTS / timeline.json / video / final.mp4
- CLAUDE.md: "Phase 4.5: 🔄 WIP (5%) | 视频合成（FFmpeg集成方案选型中）"

**用户当前体感**:
- preview 页看到图集 + BGM 单独播放（不是合成视频）
- 期望"短视频/漫剧"但实际是"分镜图集 + 背景音乐"

**这是产品 roadmap 节点**，不是 bug。但 Founder 看 BGM 196s vs shot 72s 不匹配（B54）暴露这个产品定位边界。

**修复路径**（已在 CLAUDE.md Phase 4.5 计划）:
- FFmpeg 集成 shot 序列 → mp4
- TTS Doubao 朗读 narration_segment
- Whisper 对齐音画
- 最终 mp4 + BGM + TTS 合成

**优先级**: 🟢 P3/P4（不在 Wave 5 修复范围）

---

### 🟡 B56 P2 — characters.json description 字段为空（B52 cascade 根因之一）

**实测**: chapter.characters_json[char_001].description = **""** (空字符串)
- Stage 2 CharacterDesigner 输出: physical / clothing 完整但 description 空
- confirmed_outline.characters_overview[*].description 真有内容（Founder 在 outline 编辑页改的）
- **两个数据源完全分离** — chapter vs project.confirmed_outline

**B52 cascade 影响**:
- Stage 4 storyboard_director.py:1139 读 `char.physical.hair_color` 注入 image_prompt
- 不读 description（即使 description 有红发也没用）
- 结果 image_prompt 含 "black hair"

**修复方向**:
1. Stage 2 LLM prompt 加约束: characters 必须含 description 字段（综合 physical/clothing 写一句中英文描述）
2. Stage 4 storyboard_director 优先读 description（fallback physical 字段）
3. 或者 chapter.characters_json 在 confirm-outline 时**复制 confirmed_outline.characters_overview.description**到 chapter — 保证字段一致

**优先级**: 🟡 P2

---

### 🔴 B57 P1 — regenerate-portrait 不同步重生 fullbody（B52 子项，单独列）

**真根因（PM 看 app/api/projects.py:1068+）**:
```python
@router.post("/{project_id}/characters/{char_id}/regenerate-portrait")
async def regenerate_portrait(...):
    """P1-3 / R7-3: 手动重生成指定角色的 portrait。
    - 调用 ReferenceImageManager.generate_character_reference()（portrait 类型）
    - 保存到 character_refs/{char_id}_portrait.png
    - 更新 characters_json 中的 portrait_url 和 updated_at
    """
```

**明确不动 fullbody** → fullbody 永远是初始版本

**Cascade B52**:
- Founder 改红发 → portrait 红 ✅，fullbody **仍是初始 Stage 2 生成的黑发** ❌
- Stage 5 shot 用 fullbody 作参考（CLAUDE.md 角色一致性铁律: 场景图用 fullbody）→ 黑发 cascade

**修复方向**:
- regenerate_portrait endpoint 完成后**自动同步调** `ReferenceImageManager.generate_character_reference(type='fullbody')` 用新红发 portrait 作参考重生 fullbody
- 或者改为 `regenerate-character` endpoint 一次性重生 portrait + fullbody

**优先级**: 🔴 P1 (B52 真根因之一)

---

## 完整 13 PEND 总览（test11 累积，按优先级）

| ID | 描述 | 优先级 |
|----|------|--------|
| **B52** | character adjustment 4 层 cascade（综合 B56+B57+Stage4+Seedream）| **P0** |
| **B51 v2** | Stage 4 Scene 4/10 LLM 空 shots 无重试 → 故事跳剧情 | **P0** |
| **B47** | Stage 1 LLM 没强制 user_selected_mood（幽默→治愈） | P1 |
| **B49** | createUrl charactersConfirmed 推断错误 | P1 |
| **B50** | Scenes 确认 UI 用户没看到 | P1 |
| **B57** | regenerate-portrait 不同步重生 fullbody (B52 子项) | P1 |
| **B54** | BGM 长度 196s vs 故事 72s 严重不匹配 | P2 |
| **B56** | characters.json description 字段空 (B52 子项) | P2 |
| **B48** | 右上角"重新生成"按钮 UX 不直观 | P2 |
| **B43 v2** | Haiku/Mureka 仍 100s alive_no_health | P2 |
| **B53** | Mucha 风格还原弱（Seedream 5.0-lite 限制） | P3 |
| **B41** | NB2 dead code 清理（部分修） | P3 |
| **B55** | Phase 4.5 视频合成未上线 | P3/P4（roadmap）|


---

## [2026-05-18 15:30] TASK-T20-FIXBATCH (5 阻断 + 1 配套)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-3 招牌污染 (中文 location_name → scene_ref 染色) | 🔴🔴 P0 | Backend | ⏳ 派活中 |
| T20-7 B51 fallback 抛弃 screenplay (剧情完全退化) | 🔴🔴 P0 | AI-ML | ⏳ 派活中 |
| T20-2 ETA UX 复合 bug (跳变/消失/收尾误导) | 🔴 P1 | Frontend | ⏳ 派活中 |
| T20-1 B51 触发率 33% (LLM 返空 storyboard prompt 缺约束) | 🔴 P1 | AI-ML | ⏳ 派活中 (与 T20-7 串行) |
| T20-4 同 ref 多 fallback 几乎一样 (T20-7 子症状) | 🔴 P1 | AI-ML | ⏳ 派活中 (与 T20-7 合并) |
| T20-6 ShotValidator universal 缺陷 (fallback/wide skip + 重复气泡 false positive) | 🟡 P2 | AI-ML/Backend | ⏸ 后置 (待 T20-7 验证后) |

**Founder 决策**:
- T20-3 选方案 A (删 keyword fallback, 信任 Stage 1)
- 5 P0+P1 并行 spawn 修, 一起 PM 审查
- 不重跑 test18 (Founder 已接收当前结果)
- T20-6 后置, 等 T20-7 修完看效果

**完整审计**: `.team-brain/analysis/TEST18_FULL_AUDIT_2026-05-18.md` (12 章)


---

## [2026-05-18 17:50] TASK-T20-FIXBATCH-2 (7 RISK 全修)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-9 ETA 数字偏快 (backend + frontend) | 🔴🔴 P0 | Backend #1 + Frontend | ⏳ 派活中 |
| T20-8 outline UX-2 false positive + ending_id | 🟢 P3 | Backend #1 | ⏳ 派活中 |
| T17-1 markdown JSON 解析其他场景 | 🟡 P2 | Backend #2 | ⏳ 派活中 |
| T18-J Sync Anthropic event loop 阻塞 | 🟡 P2 | Backend #2 | ⏳ 派活中 |
| T19-9 emotional_arc dict/str defense | 🔵 P3 | Backend #2 | ⏳ 派活中 |
| POST_BETA-5 Seedream dispatch logging 增强 | 🟢 P3 | Backend #2 | ⏳ 派活中 |
| T18-I IncompleteRead 监控 dashboard | 🟢 P3 | DevOps | ⏳ 派活中 |


## [2026-05-18 20:50] TASK-T20-FIXBATCH-2 状态更新

| RISK | 状态 |
|------|------|
| T20-9 P0 ETA | ✅ COMPLETED |
| T20-8 P3 outline | ✅ COMPLETED |
| T17-1 P2 markdown JSON | ✅ COMPLETED |
| T18-J P2 Sync Anthropic | ✅ COMPLETED |
| T19-9 P3 emotional_arc | ✅ COMPLETED |
| POST_BETA-5 dispatch log | ✅ COMPLETED |
| T18-I 监控 dashboard | ✅ COMPLETED (DevOps 设计 + 本地脚本, VPS 部署待 Founder 决定) |

**累计**: 34/34 RISK completed, 0 pending


---

## [2026-05-19 10:50] TASK-T20-FIXBATCH-3 (1 P0 灾难)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-10 Wave 14 漏改 CharacterSchema + 5 处下游 consumer (anthropomorphic_animal Pipeline 100% 崩) | 🔴🔴 P0 | AI-ML (Opus 4.7 max) | ⏳ 派活中 |


## [2026-05-19 11:30] TASK-T20-FIXBATCH-3 状态更新

| RISK | 状态 |
|------|------|
| T20-10 Wave 14 漏改 schema + 5 下游 | ✅ COMPLETED |

**累计**: 35/35 RISK completed, 0 pending

### [2026-05-20 20:05] ✅ TASK-T20-53-SQLALCHEMY-POOL — Wave 3 COMPLETED (PM 5+ 维度审查通过)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| T20-53 SQLAlchemy + pymysql 并发 pool 偶发 `pymysql.err.InternalError: Packet sequence number wrong` (全 session 5 次, frontend 高频 poll status + Pipeline 内部 DB query 并发竞争 connection) | 🟢 P3 | Backend | ✅ **COMPLETED 5/20 20:05** (Wave 3, app/database.py 5 pool 参数全配: pool_pre_ping=True + pool_recycle=1800s + pool_size=10 + max_overflow=20 + pool_timeout=30, 13 单测 PASS) |

---

### [2026-05-22 13:32] 🟡🟡 TASK-T22-NEW-4-ADJUST-CHAR-FALLBACK — P1 用户操作 endpoint 缺 Haiku→Gemini fallback (Founder e2e test22 实测)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| AdjustCharacter / RegeneratePortrait / Shot regenerate 用 Haiku 改 schema, Haiku 529 overloaded 直接返 500, Founder 操作 blocked. Stage 1-5 真有 T20-14 fallback, 但用户操作 endpoint 漏了. Founder e2e test22 13:30 改阿海服装时遇到 | 🟡🟡 **P1** Wave 6 待派 | Backend Sonnet 4.6 xhigh | 🟡 **待派 (内测后)** |

**Founder 5/22 13:32 原话**: "这点要记下来 之后还是需要 fallback 的"

**根因详见**: KEY_LEARNINGS #55

**修复方向 (Founder 5/22 13:35 调整 fallback 顺序: 跨 provider 优于跨 size)**:
1. AdjustCharacter (`app/api/projects.py`) 加 **Haiku 4.5 → Gemini 3.1 Flash → Sonnet 4.6** 三层 fallback
   - 第 1 层 Haiku 默认 (快+便宜) / 第 2 层 Gemini Flash (跨 provider 主备) / 第 3 层 Sonnet 最强保底
   - 跨 provider 优于跨 size: Anthropic 整体 overload 时 Sonnet 同 provider 也挂, Gemini 跨 provider 更可能恢复
2. RegeneratePortrait (`app/api/projects.py`) 加同款 fallback
3. Shot regenerate (`app/api/chapters.py`) 加同款 fallback (待 audit)
4. **Stage 6 Music BGM (`music_generation_service.py`) 加同款 fallback** (5/22 13:56 e2e test22 实证: Haiku 3 次 retry 全 529, 故事无 BGM, 非阻塞但用户体验降级) — **新增第 2 个实证**
5. 前端 toast 友好提示 "服务繁忙, 自动切备用模型, 请稍候 ~10s"
6. 加 fallback rate metrics 监控 (Haiku/Gemini/Sonnet 各层触发率 + 业务影响)

**临时缓解 (e2e 已用)**: 用户等 30-60s 再重试 (Anthropic 通常 1 min 内恢复)

**关联**: KEY_LEARNINGS #55 + T20-14 Stage 1-5 fallback 真**已成熟 pattern**

---

### [2026-05-22 13:37] 🟡 TASK-T22-NEW-5-SKIP-R4-2-SCENES-TEXT — P2 砍场景文字确认页 (R4-2/B58), 用户旅程简化 (Founder e2e test22 实测)

| 提议 | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| 砍 /scenes 文字层场景确认页 (R4-2/B58), Pipeline 自动从 Stage 3 → Stage 4 → Stage 4.5, 用户只在 Stage 4.5 (R4-3) 通过场景**参考图**视觉层确认 | 🟡 **P2** Wave 6 待派 | Frontend + Backend Sonnet 4.6 xhigh | 🟡 **待派 (内测前/后讨论)** |

**Founder 5/22 13:37 原话**: "如图这样的页面可以跳过 不需要用户去修改确认了 直接自动 pipeline 延续 之后用户只需要通过预览确认场景参考图就行 可以先记下来"

**真根因 (UX 痛点)**:
- R4-2 /scenes 真**文字层** (EXT/INT + 描述 + 修改按钮): 6 行文字, 用户实际不会改 (文字抽象, 不直观)
- Founder e2e test22 实测: "象征性修改/完成 什么都没改"
- 真**多一步无价值的确认** = 用户旅程冗余 + 心理负担 + 等待焦虑

**真对比**:
- R4-2 (文字层): 用户面对 6 行 EXT/INT 文字, 不直观, 无修改动力
- R4-3 Stage 4.5 (视觉层): 用户看 interior + exterior 参考图, 真能感知是否符合, 真会改

**修复方向 (Wave 6 P2)**:
1. **Backend**: 移除 R4-2 闸门 (`pipeline_orchestrator.py` R4-2 wait loop), Stage 3 完成后直接进 Stage 4
2. **Backend**: STATUS_API_CONTRACT v1.4 → v1.5 (移除 `scene_review` ui_phase, 8 状态机)
3. **Frontend**: StageC.tsx `scene-preview` subPhase 移除, `createUrl.ts` UI_PHASE_TO_URL 移除映射, 用户旅程 9 → 8 stage
4. **DB**: `projects.scenes_confirmed` Boolean 列可保留 (兼容性) 或 Alembic 007 移除 (清理)
5. **跨题材验证**: 跑 test19/20/21 多题材确认 R4-2 砍后 Pipeline 真**正常推进** + 用户旅程真**变短**

**讨论点 (待 Founder 决定时机)**:
- 内测前砍: 风险 — 修动用户旅程核心, 内测窗口紧
- 内测后砍 (推荐): 用 Wave 6 一次性做, 跟 Layer 1 后续优化 + AdjustCharacter fallback 一起
- 真**反向决策**: B58 当时加 R4-2 是为 "用户确认场景文字", 现在 Founder 真**实测发现** 这步无价值 — 真**优化的优化** (B58 反向砍)

**关联**: B58 历史 (用户旅程 9 状态机) + DEC-024 用户旅程设计 + DEC-047 Stage 4.5 (R4-3 视觉层真**保留**) + R4-2 闸门移除涉及 backend + frontend + 契约升级

---

### [2026-05-22 13:48] 🟡 TASK-T22-NEW-6-LOCATION-ANCHOR-NOT-INJECTED — P2 Layer 1 inject location=N 真**未传 location dict** (e2e test22 实测发现)

| Bug | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| Backend `image_generator.py _apply_identity_anchors` 调 `inject_identity_anchors()` 真**未传 location** 参数 (real backend log: `Injected anchors: chars=2, style=Y, **location=N**, props=0, time=Y`). 真 5 维 anchor 真**缺 location 维**, 视觉一致性真**少一层** | 🟡 **P2** Wave 6 待派 | Backend Sonnet 4.6 xhigh | 🟡 **待派 (不阻塞内测)** |

**Founder e2e test22 实测发现 (5/22 13:47)**: 21 shots 全 `location=N`, 真**location anchor 永远不注入**

**真根因 (待 Backend grep verify)**:
- `inject_identity_anchors(location=None)` 默认 → 真**没注入** LOCATION ANCHORS block
- Backend 真**应**: shot.scene_id → screenplay.scenes[].location_id → outline.unique_locations[location_id] 真**查 dict** 真传给 inject
- 真**当前** image_generator 真**没有** 这条查询链路

**修复方向 (Wave 6 P2)**:
1. `image_generator.py _apply_identity_anchors` 真**新加** location lookup: 从 `shot["original_scene_id"]` → `screenplay.scenes[idx]["location_id"]` → `outline.unique_locations[]` 真查 location dict
2. 真传给 `inject_identity_anchors(location=location_dict)`
3. 真**单测**: 验证 location=Y 真**注入** (test_identity_anchor_injector.py 真**已 cover** 真 location case, 真**只**缺 wire)
4. 真**实测**: 跑 test22 重验真 backend log 真`location=Y`

**不阻塞内测** (character + style + time anchor 真**已注入**, Coral hair "soft pale coral pink" 真**强制 prepend**, 真**核心目标达成**. location 真**补强** 更佳但**非阻塞**)

**关联**: DEC-048 Layer 1 + AI-ML M1 spec C.1 location 真**参数已定义** + Backend 实施真**漏 wire**

---

### [2026-05-22 14:10] 🔴🔴 TASK-T22-NEW-7-FIRST-BATCH-CHARS-ZERO — P0 Layer 1 前 3 shot chars=0 真**character anchor 漏注入** (Founder e2e test22 视觉验证 Shot 2 实测发现)

| RISK | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| Backend `_apply_identity_anchors` 真**第一批 max_concurrent=3 shot** 真**全 chars=0** ❌ — Coral character anchor (hair "soft pale coral pink" + 鱼尾 + 珊瑚枝桠) 真**完全没注入** Shot 1/2/3 prompt. Shot 4-21 真**正常** chars=2. 真**第一批 race condition / first-batch bug** | 🔴🔴 **P0 内测前必修** | Backend Sonnet 4.6 xhigh | 🔴 **待派 Wave 6 P0** |

**Founder 实测视觉证据 (5/22 14:09 /preview Shot 2 真**完全错**)**:
- 珊瑚: schema `soft pale coral pink` hair → 图 **深蓝色** ❌
- 珊瑚: schema mermaid 真**鱼尾** → 图 **两条人腿** ❌ (根本不是美人鱼!)
- 珊瑚: schema 贝壳装 → 图 普通蓝白裙 ❌
- 阿海: schema `ash blonde` → 图 **深黑色** ❌
- 阿海: schema 绿白渔衣 → 图 绿色 + 黑色裤子 🟡

**真**实证日志 (backend.log 13:46:03)**:
```
[IdentityAnchorInjector] Injected anchors: chars=0, style=Y, location=N, props=0, time=Y (prompt 537 → 1192 chars)  # Shot 1
[IdentityAnchorInjector] Injected anchors: chars=0, style=Y, location=N, props=0, time=Y (prompt 467 → 1122 chars)  # Shot 2
[IdentityAnchorInjector] Injected anchors: chars=0, style=Y, location=N, props=0, time=Y (prompt 455 → 1110 chars)  # Shot 3
[IdentityAnchorInjector] Injected anchors: chars=2, style=Y, location=N, props=0, time=Y (prompt 753 → 2284 chars)  # Shot 4 ✅
```

**真**双重失败导致 Shot 2 错**:
1. **Bug A (P0 真**根因**)**: Backend 前 3 shot 真**没传** `characters_in_scene` to inject → chars=0 → Coral hair anchor 真**完全没在** prompt 真**前 prepend**
2. **Bug B (Seedream API 限制, 长期)**: 即使传了 2 张 portrait reference (Coral + Ah Hai), Seedream 真**没遵守** portrait 视觉 (淡粉色头发 + 珊瑚枝桠) — 真**生图模型本身真**weak ref following**. Layer 1 真**设计**就**靠 strong text anchor 补偿** Seedream weak ref. Bug A 真**让 anchor 真无 chars** → 真**双重失败**

**真**根因诊断方向 (Backend 待 grep)**:
- `app/services/image_generator.py _apply_identity_anchors` 真**第一批 max_concurrent=3** 真**characters_in_scene** 真**为空 list** 真**为什么**?
- 真**race condition**: characters 真**第一批 dispatch 时还没 loaded**? Pipeline async 真**order** 问题?
- 真**variable scope**: image_generator 真**self.characters** 真**第一批没初始化**? Shot 4 真才 init?
- 真**filter bug**: `chars_in_shot = [c for c in characters if c["id"] in shot["characters_in_scene"]]` 真**character["id"]** vs `shot["characters_in_scene"]` 真**ID 不匹配** (e.g., "char_001" vs "Coral")?
- 真**最可能**: Stage 5 真**第一批早于** Pipeline 真`B52-fix reload characters from DB`? 但**Stage 5 13:45:52 启动 vs reload 13:34:12 早 11 min** — 应该 reload OK. 真**奇怪**, 待 Backend 真**深查**

**修复方向 (Backend Wave 6 P0)**:
1. **诊断**: grep `image_generator.py` 真`_apply_identity_anchors` 真**characters_in_scene** 真**来源** 真**第一批 vs 后续** 真**有什么区别**
2. **修**: 确保第一批真**characters_in_scene 真**正确传入**
3. **单测**: 加 `test_apply_identity_anchors_first_batch.py` 真**模拟 max_concurrent=3** 真**第一批** 真 chars 真**不为 0**
4. **重跑 test22 验证**: 21/21 shot 真 inject log 真**全 chars=N (N>0)**
5. **视觉重验**: Founder 重看 21 shot 真**Coral 头发 21/21 淡珊瑚粉色一致**

**真**当前阻塞内测启动** 真**最关键 P0**

**关联**: DEC-048 Layer 1 + TASK-T22-NEW-6 (location=N 漏 wire 真**同款实施 bug**) + Seedream API 真**weak ref following** 真**长期** (Layer 1 真**核心解决方法 = strong text anchor**, 但 Bug A 真**让 anchor 真无 chars**)

---

### [2026-05-22 14:50] 🟡 TASK-T22-NEW-8-CONFIRM-OUTLINE-FRONTEND-WIRE — P2 升级**内测前必修** (Founder 5/22 14:50 决策)

| Bug | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| 用户在 /outline 页面点 "确认大纲" 真**前端没真调用** backend `POST /api/projects/{uuid}/chapters/1/confirm-outline` endpoint. Backend endpoint 已建 (5/21 Wave 5), 真**仅前端 wire 漏**. 当前 backend 兜底用 `raw_outline_json` (原版), Pipeline 跑通. 但用户**真改大纲**真改动**没保存** → 重启 Pipeline 用原版 (用户编辑丢) | 🟡 **P2 升级内测前必修** | Frontend Sonnet 4.6 | 🟡 Wave 8 待派 (~30 min) |

**Founder 5/22 14:50 原话**: "这两点都需要在内测之前做好，以长期根治的原则"

**修复方向 (Wave 8 ~30 min)**:
1. `frontend/src/components/create/StageB.tsx` 真**点 "确认大纲" 时**: 真调 `POST /api/projects/{uuid}/chapters/1/confirm-outline` body=`{outline: {modified_outline_json}}`
2. 真**用户改大纲文字** 真**前端真**已经 local state 保留** — 真**直接** body 发出去
3. 真用户没改 → 真**仍发 raw_outline_json** (backend 真**幂等** OK)
4. 真前端 toast "大纲已保存" 真**反馈**

**不冲突 Wave 7/8 其他 task**: StageB.tsx 真**独立 frontend** (T22-NEW-5 真改 StageC + createUrl + CreateContent, 真**不动** StageB)

**关联**: memory project_confirm_outline_not_wired + 用户编辑真**保存铁律**

---

### [2026-05-22 14:50] 🟡 TASK-T22-NEW-9-SCHEMA-GENERIC-FALLBACK-ARCH — P2 升级**内测前必修, 长期根治** (Founder 5/22 14:50 决策)

| 架构 | 优先级 | Owner | 状态 |
|------|--------|-------|------|
| 当前 hotfix 方案 (Wave 4 + 4.5): 19 character_types 中 17 type 真**逐个手动** 写 humanoid fallback 规则 (`_TYPE_REQUIRED_GROUPS` dict). 每加新 type 真**还得手动加 fallback**, 麻烦不优雅. 真**长期方案 B** (内测前根治): 真**通用 fallback** — 真**不分 type**, 真**任何 character 真都接受人类外貌字段** (用户**真想画拟人化任何东西** 真**不用先 hotfix schema**) | 🟡 **P2 升级内测前必修** (长期根治原则) | Backend Sonnet 4.6 xhigh | 🟡 Wave 8 待派 (~2-3h) |

**Founder 5/22 14:50 原话**: "这两点都需要在内测之前做好，以长期根治的原则"

**修复方向 (Wave 8 ~2-3h)**:
1. `app/services/pipeline_schemas.py` 真**重构** `_TYPE_REQUIRED_GROUPS`:
   - 真**全 19 type 真**通用**接受**人类外貌字段** (hair_color/skin_tone/face_shape/eye_color/eye_shape) 真**作可选 fallback**
   - 真**保留 type 特有字段** 真**主验**: 人 真**physical 主验** / 动物 真**species + fur_color 主验** / 机器人 真**robot_type + material 主验**
   - 真**通用 fallback rule**: 真**任何 character** 真**含 humanoid 外貌字段** 真**视为有效拟人形态**, 不验 type-specific 字段
2. 真**保留** 真**2 type 真严格** (Founder 决): pure animal + vehicle_character 真**不要求** humanoid fallback (它们真**就是** 真**非拟人**)
3. **跨题材 baseline regression** (Tester 真**Wave 8 后跑**): 真**19 type × 5 style = 95 case** 真**重跑**, 真**全 PASS**
4. 真**砍 16 个 hotfix 真**逐个 fallback rule** → 真**1 个通用 fallback function**
5. **不影响** 真**当前 19 type 真**已有故事**: 真**架构等价**, 用户层透明

**真**风险**: 真**碰** `pipeline_schemas.py` 真**核心 schema 文件**, 真**必须**:
- 真自跑 `tests/test_t21_digital_virtual_fallback.py` 25/25 不退化
- 真自跑 `tests/test_t21_new_2_humanoid_fallback_wave2.py` 16/16 不退化
- 真自跑 `tests/test_identity_anchor_cross_genre_baseline.py` 105/105 不退化 (Wave 7 真**已跑通**)

**关联**: memory project_schema_humanoid_fallback_remaining + Founder 真**长期根治原则** + KEY_LEARNINGS #51 (通用故事铁律)

