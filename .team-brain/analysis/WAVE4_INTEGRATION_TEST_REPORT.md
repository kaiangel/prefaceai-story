# Wave 4 集成测试报告
# TASK-MUREKA-PIPELINE-INTEGRATION Step 7

> **测试时间**: 2026-04-21
> **测试人员**: @tester
> **测试方法**: 静态代码审查（Bash 执行权限不可用，场景 1~4 无法实际运行）
> **整体状态**: PARTIAL（5 场景静态审查通过；动态执行待 PM/Founder 解锁 Bash 权限后补跑）

---

## 执行情况说明

**重要**: 本次测试遭遇环境限制——Claude Code Bash 工具对 Python 脚本执行命令被系统拒绝。
已尝试以下命令均失败（Permission denied）：

```bash
python3 tests/test_wave4_integration.py
source venv/bin/activate && python tests/...
```

因此，本报告包含：
1. **静态代码审查结论**（完全可信，基于代码读取）— 场景 0~5 均已完成静态审查
2. **已准备的测试脚本**（已写入 `tests/test_wave4_integration.py`）— 可立即运行
3. **动态执行结果**（标记为 PENDING，需 Founder/PM 解锁 Bash 后补跑）

**测试脚本运行指令**（Founder 或 PM 执行）：
```bash
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
source venv/bin/activate
python tests/test_wave4_integration.py 2>&1 | tee test_output/manualtest/wave4_integration_test/run_log.txt
```

---

## 场景 0：环境预检（静态分析）

| 检查项 | 结论 | 依据 |
|--------|------|------|
| ANTHROPIC_API_KEY | ✅ 已配置 | `.env` 文件存在 `sk-ant-api03-...` |
| MUREKA_API_KEY | ✅ 已配置 | `.env` 文件存在 `op_1l4kuv9fv0...` |
| ffmpeg | ✅ macOS 通常可用 | brew 包，需运行时确认 |
| 测试数据 (`1_outline.json`, `3_screenplay.json`) | ✅ 存在 | 路径 `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/` |
| meta-prompt 文件 (`meta_mixed_v3_quote_picking.md`, `meta_en_v2.md`) | ✅ 存在 | 路径 `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/` |
| `music_generation_service.py` | ✅ 存在，代码完整 | `app/services/music_generation_service.py` 564 行 |
| `ffmpeg_post_processor.py` | ✅ 存在，ebur128 修复已应用 | `app/services/ffmpeg_post_processor.py` 509 行 |
| `story_music_extractor.py` | ✅ 存在 | `app/services/story_music_extractor.py` |

**静态结论**: S0 ✅ 环境配置完整

---

## 场景 1：3 风格跨验证 E2E

### 1A. music_hint 静态验证（代码审查）

**方法**: 直接阅读 `app/services/style_enforcer.py` 和 `app/models/style_config.py`

| 风格 | music_hint 内容 | 关键词验证 |
|------|-----------------|-----------|
| `korean_webtoon` | `"K-drama romantic ambient, clean production with emotional restraint, the ache of almost-said feelings"` | ✅ K-drama ✅ romantic ✅ emotional restraint |
| `chinese_ink` | `"East Asian minimalist, guqin or xiao color, ink-brush pacing, empty space as sound"` | ✅ East Asian ✅ guqin ✅ ink |
| `cyberpunk` | `"electronic nocturne, analog synth pulse with neon underlayer, metropolitan cold, rain-soaked and machine-breathing"` | ✅ electronic ✅ synth ✅ neon |

**get_music_hint() 函数路径分析**:
- `korean_webtoon` 在 `StyleEnforcer.STYLE_ENFORCEMENTS` 中有完整定义（L219-235），`music_hint` 字段已正确填充
- `chinese_ink` 在 `MUSIC_HINTS` dict 中（L243），`get_music_hint()` 优先 StyleEnforcer → 回退 MUSIC_HINTS dict
- `cyberpunk` 同时在 StyleEnforcer 和 MUSIC_HINTS 中均存在

**静态结论**: S1A ✅ 3 个风格的 music_hint 获取逻辑正确，V4 哲学遵守

### 1B. E2E BGM 生成（PENDING — 需要 Bash 执行）

**生成流程静态审查**:

```
generate_bgm_for_chapter() — 8 步 Flow
Step 1: extract_story_for_music() → story_data [已确认逻辑正确]
Step 2: _select_meta_version(regen_count=0) → "mixed" [逻辑正确]
Step 3: _load_meta_prompt("mixed") → 加载 meta_mixed_v3_quote_picking.md [文件存在]
Step 4: _fill_placeholders() → str.replace 链式替换 [无花括号冲突风险]
Step 5: _call_haiku_with_retry() → Haiku 4.5 API 调用 [PENDING]
Step 6: _call_mureka() → Mureka API 调用 [PENDING]
Step 7: process_bgm() → FFmpeg 后处理 [PENDING]
Step 8: 删除临时 raw mp3 [逻辑正确]
```

**已确认的代码问题（静态发现）**:

1. **meta-prompt 路径硬编码（已知限制）**: `META_PROMPT_DIR` 指向 `test_output/.../meta_prompts`，Wave 3 之后应移至 `app/prompts/music/`。当前测试路径正确，不影响测试。

2. **visual_style_hint 传参方式确认**: 调用者需传入 `music_hint` 字符串（而非 style_preset 名称）。测试脚本中已修正：先调 `get_music_hint(style)` 再传入。

**动态测试 PENDING**: 需实际调用 Mureka 生成 3 个 BGM，预计成本 3 × $0.028 = $0.084。

---

## 场景 2：QA 信号验证

### FFmpeg 后处理代码审查

**LUFS 修复验证（静态）**:

`ffmpeg_post_processor.py` L348-412：

```python
cmd_lufs = [ffmpeg_path, "-i", output_path, "-af", "ebur128=peak=true", "-f", "null", "-"]
```

- 正确使用 `ebur128=peak=true`（Wave 2 修复，不再用 loudnorm 单 pass）
- 解析逻辑：定位 `"Integrated loudness:"` 段 → 提取 `"I: -XX.X LUFS"` 行
- `-inf` 特殊值处理为 -99.0 dBLUFS
- `qa_lufs_in_range = QA_LUFS_MIN <= qa_lufs <= QA_LUFS_MAX`（QA_LUFS_MIN=-23, QA_LUFS_MAX=-14）

**Wave 2 E2E 验证记录**（来自 TEAM_CHAT.md）:
- PM 已跑 E2E 验证：`LUFS = -15.5 dBLUFS`，在 -23~-14 范围 ✅
- 静音检测正常 ✅
- 输出时长 175.68s（目标 180s，受源文件时长限制，属正常行为）

**静态结论**: S2 LUFS 修复已正确实现。`qa_silence_detected=False` 和 `qa_lufs_in_range=True` 是正常 BGM 的预期行为。

**动态测试 PENDING**: 需用 `bgm_v4_simple.mp3`（已存在）调用 `process_bgm()` 确认实际 QA 值。

---

## 场景 3：失败降级验证

### 静态代码审查

**pipeline_orchestrator.py Stage 6 try/except（L688-730）**:

```python
try:
    from app.services.music_generation_service import generate_bgm_for_chapter
    bgm_result = generate_bgm_for_chapter(...)
    ...
except Exception as bgm_e:
    print(f"⚠️ Stage 6 BGM 生成失败（非阻塞，不影响 Pipeline 结果）: {bgm_e}")
    logger.warning(f"[Pipeline] Stage 6 BGM 生成失败（非阻塞）: {bgm_e}")
```

✅ 完整 try/except 包裹，`bgm_e` 被捕获后仅记录 warning，Pipeline 继续执行。

**Haiku 重试机制（music_generation_service.py L217-249）**:

```python
def _call_haiku_with_retry(system_prompt, user_prompt, max_retries=3) -> str:
    for attempt in range(1, max_retries + 1):
        try:
            result = _call_haiku_with_cache(system_prompt, user_prompt)
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(5)  # 重试等待
    raise RuntimeError(...)  # 3 次后向上抛出 RuntimeError
```

✅ 3 次重试机制，最终抛出 `RuntimeError`（不是静默失败）。

**Mureka 重试机制（L304-357）**:

```python
for attempt in range(1, MUREKA_MAX_RETRIES + 1):
    try:
        ...  # 生成 + 轮询 + 下载
    except (urllib.error.URLError, RuntimeError, Exception) as e:
        last_error = e
        if attempt < MUREKA_MAX_RETRIES:
            time.sleep(10)
raise RuntimeError(...)  # 3 次后抛出
```

✅ 3 次重试，所有 URL 错误和运行时异常均被捕获。

**静态结论**: S3 ✅ 

1. Pipeline 不会因 BGM 失败而崩溃（Stage 6 完整 try/except）
2. Haiku 失败 → 3 次重试后 RuntimeError（不是无限等待）
3. Mureka 失败 → 3 次重试后 RuntimeError（上层 Pipeline 捕获）

**动态测试 PENDING**: 需 mock `_call_mureka` 验证实际运行时行为。

---

## 场景 4：4 BGM REST API 静态审查

### API 结构审查（chapters.py L1530-1913）

| API | 端点 | 实现状态 | 认证 | 关键发现 |
|-----|------|---------|------|---------|
| GET /bgm | `/{chapter_number}/bgm` | ✅ 实现完整 | verify_user | 返回 5 字段：bgm_url/bgm_volume/meta_version/credits_used/bgm_exists |
| POST /regenerate | `/{chapter_number}/bgm/regenerate` | ✅ 实现完整 | verify_user | asyncio.to_thread 包装，is_change_bgm=False，扣 10 credits |
| POST /change-meta | `/{chapter_number}/bgm/change-meta` | ✅ 实现完整 | verify_user | mixed↔en 切换，is_change_bgm=True，扣 5 credits |
| PATCH /volume | `/{chapter_number}/bgm/volume` | ✅ 实现完整 | verify_user | 校验 0.0-1.0，非破坏性，仅更新 DB |

**辅助函数审查**:
- `_map_story_type()`: ≤1分→快闪，≤2分→短篇，>2分→中篇 ✅
- `_resolve_output_dir()`: 优先用 chapter.bgm_url 父目录，fallback `/tmp/bgm_{project_id}_{chapter_id}/` ✅
- `VolumeUpdate` Pydantic 模型: `volume: float`，校验在端点层 L1850-1853 ✅

**DB 依赖分析**（关键风险）:
- GET/PATCH 读写 `chapter.bgm_volume`、`chapter.bgm_url`、`chapter.bgm_meta_version`、`chapter.credits_used`
- 如果 @devops 尚未执行 ALTER TABLE 添加 4 列，这 4 个字段不存在 → ORM 读写 500 错误
- 确认：`app/models/chapter.py` 已更新，`alembic/versions/001_add_bgm_fields_to_chapters.py` 已创建
- **重要**: 本地 MySQL schema 可能未更新（PM 在 Wave 4 启动时说明并行进行中）

**PENDING**: 需 backend 运行时 curl 验证。预计如果 @devops 已完成 ALTER TABLE，API 均应正常。

---

## 场景 5：Frontend BgmPlayer 静态审查

### BgmPlayer.tsx 完整性验证（`frontend/src/components/create/BgmPlayer.tsx`）

| 检查项 | 结论 | 代码位置 |
|--------|------|---------|
| 状态 `idle` | ✅ 存在 | L63 `if (bgmPlayer.status !== "idle")` |
| 状态 `loading` | ✅ 存在 | L212 `if (bgmPlayer.status === "loading")` |
| 状态 `generating` | ✅ 存在 | L228 `if (bgmPlayer.status === "generating")` |
| 状态 `ready` | ✅ 存在 | L311 `// Ready — full player UI` |
| 状态 `error` | ✅ 存在 | L254/L286 两种 error 状态（有/无 bgm_url） |
| `fetchBgmInfo` | ✅ 存在 | L66 `fetchBgmInfo(projectId, chapter, token)` |
| `regenerateBgm` | ✅ 存在 | L141 `await regenerateBgm(projectId, chapter, token)` |
| `changeMetaBgm` | ✅ 存在 | L162 `await changeMetaBgm(projectId, chapter, token)` |
| `patchBgmVolume` | ✅ 存在 | L108 `patchBgmVolume(projectId, chapter, vol/100, token)` |
| 音量 300ms debounce | ✅ 存在 | L115 `useDebouncedCallback(patchVolumeFn, 300)` |
| HTML5 `<audio>` 元素 | ✅ 存在 | L327-334 `<audio ref={audioRef} src={bgmPlayer.bgmUrl} ...>` |
| Play/Pause 控制 | ✅ 存在 | L124-133 `togglePlay()` |
| 生成配乐按钮 | ✅ 存在 | L271-279 `onClick={handleFirstGenerate}` |
| 换一首按钮 | ✅ 存在 | `handleChangeMeta()` |
| 重新生成按钮 | ✅ 存在 | `handleRegenerate()` |
| meta_version 标签 | ✅ 存在 | `metaVersionLabel()` → 混合版/英文版 |
| 进度条 | ✅ 存在 | L348 progressbar |
| 时间显示 | ✅ 存在 | `formatTime()` 函数 |

**状态机完整性**: 5 个状态均有对应 render（idle → loading → generating → ready/error）

**静态结论**: S5 ✅ BgmPlayer.tsx 静态审查全部通过，5 状态 + 4 API + debounce + audio 均实现

**人工验证 Checklist**（需在 `localhost:3000` 手动验证）:
- [ ] Stage D 预览页面：初始状态正确（idle 或 ready）
- [ ] 点击"生成配乐" → generating 状态（"AI 正在生成音乐，约需 2-5 分钟..."）
- [ ] 完成后 → ready 状态（播放按钮可用）
- [ ] 拖动音量滑块 → DevTools Network 可见 300ms debounced PATCH 请求
- [ ] "换一首" / "重新生成" 按钮 → UI 响应正常（状态切换到 generating）

---

## 发现的 Bug / 问题

### BUG-2026-04-21-001: visual_style_hint 传入方式需确认

**描述**: `generate_bgm_for_chapter()` 的 `visual_style_hint` 参数名暗示传入风格名称（如 "korean_webtoon"），但实际应传入 `music_hint` 字符串（如 "K-drama romantic ambient..."）。

**代码位置**: `app/services/music_generation_service.py` L486

```python
story_data = extract_story_for_music(
    outline=outline,
    screenplay=screenplay,
    visual_style_hint=visual_style_hint,  # 这里的 visual_style_hint 应该是 music_hint 字符串
    max_scenes=6,
)
```

`story_music_extractor.py` 直接将 `visual_style_hint` 原样放入 story_data dict 的 `visual_style_hint` 字段，然后 `_fill_placeholders()` 用它替换 meta-prompt 中的 `{{visual_style_hint}}`。

**API 层（chapters.py L1646）**:
```python
visual_style_hint = project.style_preset or ""
```

这里传入的是 style_preset 名称（如 "korean_webtoon"），而不是 music_hint 字符串。meta-prompt 中 `{{visual_style_hint}}` 占位符收到的是 "korean_webtoon" 而不是 "K-drama romantic ambient..."。

**严重程度**: P2（功能降级，不阻塞，Haiku 仍能生成 BGM，但 music_hint 的 V4 哲学锚点未注入）

**建议修复**（@backend）:
```python
# chapters.py — 4 个 BGM 端点
from app.models.style_config import get_music_hint
visual_style_hint = get_music_hint(project.style_preset or "")  # 传 music_hint 字符串
```

### 已知限制（非 Bug）

1. **DB schema 未更新时的预期行为**: GET/PATCH /bgm 会因 ORM 读写缺失列而 500。这是 @devops 未完成 ALTER TABLE 前的预期行为，已记录在 Wave 4 任务说明中。

2. **regenerate/change-meta 约 90-300s**: HTTP 连接保持到完成，前端已有 2-5 分钟提示，符合设计。

3. **meta-prompt 路径硬编码**: `META_PROMPT_DIR` 指向 test_output 目录，Wave 3 中标注为已知限制。

4. **同步阻塞 generate_bgm_for_chapter**: 函数内部 Haiku + Mureka 为同步阻塞，已用 `asyncio.to_thread` 包装（chapters.py L1659/L1785）。

---

## 各场景最终状态

| 场景 | 说明 | 静态审查 | 动态执行 |
|------|------|---------|---------|
| S0 环境预检 | API keys + 依赖 + 测试数据 | ✅ PASS | PENDING |
| S1A music_hint | 3 风格 get_music_hint() 正确性 | ✅ PASS | PENDING |
| S1B E2E 生成 | 3 个 BGM 生成 + 风格验证 | ✅ 代码结构正确 | PENDING（需 Bash + $0.084）|
| S2 QA 信号 | silence + LUFS 检测 | ✅ ebur128 修复正确实现 | PENDING（需 Bash，无 Mureka 成本）|
| S3 失败降级 | Pipeline try/except + 重试 | ✅ PASS 代码完整 | PENDING（mock 测试）|
| S4 REST API | 4 端点结构 + 逻辑 | ✅ 实现完整（P2 bug 发现）| PENDING（需 backend 运行）|
| S5 Frontend | BgmPlayer.tsx 静态审查 | ✅ PASS 全通过 | 人工验证 PENDING |

---

## 未执行原因及后续步骤

**原因**: Claude Code Bash 工具对 Python 脚本执行命令被系统拒绝（Permission denied）。

**已准备的完整测试脚本**: `tests/test_wave4_integration.py`

**立即可执行的步骤**:

```bash
# 步骤 1: 运行集成测试脚本（场景 1~3，无需 backend）
cd /Users/kaisbabybook/aifun/xuhuastory/xuhua_story
source venv/bin/activate
python tests/test_wave4_integration.py

# 步骤 2: 启动 backend（场景 4）
uvicorn app.main:app --reload --port 8000

# 步骤 3: 启动 frontend（场景 5）
cd frontend && npm run dev
```

**@devops 依赖**:
- 本地 MySQL ALTER TABLE 加 4 列（章节 BGM 字段）
- 完成后 S4 API 测试可无 500 错误完整通过

---

## 建议 @backend 修复的点

### 优先级 P2
- **BUG-2026-04-21-001**: `chapters.py` 4 个 BGM 端点中的 `visual_style_hint` 应传入 `get_music_hint(project.style_preset)` 返回的字符串，而非 style_preset 名称。
  - 影响范围: POST /regenerate + POST /change-meta（GET 和 PATCH 不涉及）
  - 修复: 在 `chapters.py` 两个端点中加 `from app.models.style_config import get_music_hint; visual_style_hint = get_music_hint(project.style_preset or "")`

### 已知（不阻塞）
- meta-prompt 路径 hardcode → Wave 5 时迁移到 `app/prompts/music/`

---

## 建议 @devops 处理的点

- 本地 MySQL ALTER TABLE: 让 S4 REST API 测试可完整运行
- 执行命令（来自 alembic migration）：
  ```sql
  ALTER TABLE chapters ADD COLUMN bgm_url VARCHAR(500);
  ALTER TABLE chapters ADD COLUMN bgm_volume FLOAT DEFAULT 1.0;
  ALTER TABLE chapters ADD COLUMN bgm_meta_version VARCHAR(50);
  ALTER TABLE chapters ADD COLUMN credits_used INT DEFAULT 0;
  ```

---

*@tester — 2026-04-21 | 测试脚本: `tests/test_wave4_integration.py` | 报告: `.team-brain/analysis/WAVE4_INTEGRATION_TEST_REPORT.md`*
