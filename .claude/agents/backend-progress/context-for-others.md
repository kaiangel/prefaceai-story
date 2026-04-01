# Backend Agent - 给其他 Agent 的上下文

> **最后更新**: 2026-04-01

---

## 当前状态速览

```
状态: ✅ TASK-JSON-REPAIR-V3 完成 (状态机, 10/10 PASS)
当前任务: 等 PM Review
阻塞: 无
```

---

## ✅ TASK-STYLE-LITERAL-FIX 完成 (2026-03-25, P0)

### 给 @PM 的信息

`StylePreset` Literal 从 10 → 15，与 StyleEnforcer + 前端 15 风格完全对齐。删掉 `"chinese"` 残留。修复 5 个风格导致 422 的 bug。

---

## ✅ TASK-DOC-TEXT-WIRE Backend 完成 (2026-03-25)

### 给 @PM 的信息

- `ProjectCreate` 新增 `document_text: str | None`
- `create_project` 中: 如果有 `document_text`，拼接到 `original_idea`（`\n\n---\n附加文档内容:\n{text}`）

### 给 @Frontend 的信息

Backend 已接收 `document_text`。POST body 加 `document_text: state.documentText || null` 即可。

---

## ✅ TASK-OCR-ENDPOINT 完成 (2026-03-25)

### 给 @PM 的信息

新建 `app/api/utils.py`（独立路由），2 个端点:

**POST /api/utils/ocr**:
- 接收: `file` (FormData 图片)
- 校验: 图片类型 + 10MB 限制
- 模型: 主力 `gemini-3.1-flash-lite-preview`，备用 `claude-haiku-4-5-20251001`
- 返回: `{ "text": "识别文字" }` 或 `{ "text": "", "error": "识别失败" }`

**POST /api/utils/parse-document**:
- 接收: `file` (FormData PDF/TXT/MD)
- 校验: 文件名后缀 + 20MB 限制
- PDF: pdfplumber 提取，TXT/MD: 直接读取 (UTF-8/GBK fallback)
- 返回: `{ "text": "提取文字" }`

### 给 @Frontend 的信息

OCR 去 mock 调真实 API:
```
// 图片 OCR
const formData = new FormData();
formData.append('file', imageFile);
const res = await fetch('/api/utils/ocr', { method: 'POST', body: formData });

// PDF 解析
formData.append('file', pdfFile);
const res = await fetch('/api/utils/parse-document', { method: 'POST', body: formData });
```

### 给 @DevOps 的信息

- 需要安装 `pdfplumber`: `pip install pdfplumber`
- 新文件: `app/api/utils.py`
- `app/main.py` +2 行注册

---

## ✅ Phase 1 Step 2: StyleEnforcer 28 + Literal 28 (2026-03-25)

### 给 @PM 的信息

- `style_enforcer.py`: +13 个 `StyleEnforcement`（AI-ML 设计完整配置，逐字复制）
- `project.py` `StylePreset` Literal: 15 → 28
- 验证: StyleEnforcement count = 28 ✅ + StylePreset count = 28 ✅

---

## ✅ TASK-PHASE2-INFRA 完成 (2026-03-25)

### 给 @PM 的信息

**新建**: `app/services/file_storage.py` — 文件上传验证+压缩+本地存储
**修改**: `app/api/utils.py` — 3 个分析端点 + 公用 `_vision_analyze` helper
**修改**: `story_outline_generator.py` — Prompt 4 `_build_user_reference_context()` + `generate()` 3 新参数

3 个端点全部不需要认证（创建项目之前调用）。

### 给 @Frontend 的信息

3 个分析 API 就绪:
```
POST /api/utils/analyze-style       → { style_display_name, mandatory_keywords, ..., display_tags }
POST /api/utils/analyze-character   → { description_zh, description_en, gender, age_range, display_name }
POST /api/utils/analyze-scene       → { description_zh, description_en, location_type, atmosphere, display_name }
```
全部接收 FormData `file` 字段（图片），返回 JSON。无需 Bearer token。

### 给 @DevOps 的信息

- 新增 Pillow 依赖（已在 requirements.txt）
- 新建 `app/services/file_storage.py`
- 存储路径: `./storage/uploads/{project_id}/{category}/{filename}`
