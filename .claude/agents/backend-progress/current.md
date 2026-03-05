# Backend Agent - 当前任务

> **最后更新**: 2026-03-04 18:07
> **状态**: ✅ TASK-SHOT-QUALITY-BUGFIX Backend 全部修复完成 (Bug#1+#2+#4+#5)

---

## 刚完成

### ✅ TASK-SHOT-QUALITY-BUGFIX Backend 部分 (2026-03-04 16:09)

PM Step 7 独立复核发现 4 个 Bug，Backend 负责 3 项（#1, #2, #4），全部修复完成。

#### Bug #1 (P1): 场景标签中文→□ 泄漏

**文件**: `scene_reference_manager.py`

| 修改点 | 修改前 | 修改后 |
|--------|--------|--------|
| `get_references_for_location()` L272 | `label = f"Scene: {loc_name} ..."` (中文名) | `label = f"Scene: {location_id} ..."` (英文 ID) |
| `_label_scene_image()` 字体列表 | Helvetica, DejaVuSans (不支持 CJK) | 新增 PingFang, STHeiti, NotoSansCJK 在前 (CJK 兜底) |

**根因**: `loc_name` 存储中文 display_name (如 "林家餐厅")，PIL 的 Helvetica/DejaVuSans 无法渲染 CJK → □。
**修复**: 标签改用英文 `location_id` (如 "loc_001")；同时在字体列表头部添加 CJK 字体作兜底。

#### Bug #2 (P2): Prompt 指令文字泄漏

**文件**: `image_generator.py`

| 修改点 | 修改前 | 修改后 |
|--------|--------|--------|
| `build_native_text_prompt()` 4 处 | 包含 "70-80% opacity" 技术英文 | 删除 opacity 描述行 |
| dialogue bubble 样式 L89 | "thin black outline (1-2px), rounded corners (radius ~15px)" | "thin black outline, rounded corners" |

**根因**: NB2 偶尔将英文技术指令 (opacity/px) 渲染为图上可见文字。
**修复**: 移除所有带具体数值的技术英文描述 (opacity, px)。

#### Bug #4 (P3): Validator 字段名 mismatch

**文件**: `storyboard_service.py`

| 修改点 | 修改前 | 修改后 |
|--------|--------|--------|
| `_get_camera_angle()` L1422 | `camera.camera_angle` | `camera.angle` |

**根因**: StoryboardDirector (SQ-5) 输出 `camera.angle`，Validator 读 `camera.camera_angle` → 永远 None → 默认 eye_level → 22/35 假阳性。
**修复**: 改读正确字段 `camera.angle`。

**3 个文件语法检查全部通过 ✅**

#### Bug #5 (P2): dialogue handler dict crash

**文件**: `image_generator.py`

| 修改点 | 修改前 | 修改后 |
|--------|--------|--------|
| `build_native_text_prompt()` L80 dialogue handler | 直接对 `txt` 调用 `_strip_speaker_for_native()` | 先检查 `isinstance(txt, dict)` → `txt = txt.get('text', '')` |

**根因**: Stage 4 LLM 对 `text_type="dialogue"` 的 `chinese_text` 可能输出 dict 列表 `[{"type":"dialogue","text":"..."}]`，dialogue handler 未处理此格式 → `.strip()` crash → Shot 10 高潮帧缺失。
**修复**: 与 compound handlers (L91+) 保持一致，遍历时添加 dict 类型检查。

**import 验证通过 ✅**

---

## 待处理队列

### 支线任务
- [ ] **Phase 4.5: 视频合成**（等待 Founder 决策后启动）
- [ ] API 文档整理（解锁Frontend）

---

## 更新记录

| 时间 | 更新内容 |
|------|----------|
| 2026-03-04 18:07 | ✅ Bug #5 修复 (dialogue handler dict check，1 文件) |
| 2026-03-04 16:09 | ✅ TASK-SHOT-QUALITY-BUGFIX Backend 3 项修复 (Bug#1+#2+#4，3 文件) |
| 2026-03-04 10:50 | ✅ Step 5c 全部完成 (SQ-8+SQ-2+SQ-1+SQ-6，6 文件修改) |
| 2026-02-28 11:31 | ✅ TASK-ROBUSTNESS-FIX 完成 |
| 2026-02-28 10:37 | ✅ TASK-NATIVE-TEXT-ROBUSTNESS 完成 |
| 2026-02-27 17:50 | ✅ TASK-NB2-NATIVE-TEXT 完成 |
| 2026-02-27 16:09 | ✅ Phase 3 四项任务完成 |
