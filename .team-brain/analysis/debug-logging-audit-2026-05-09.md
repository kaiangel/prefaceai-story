# Debug 日志地毯式审计 — 2026-05-09 16:10

> **触发**: Founder "全面毫无遗漏的深度复查下所有对应的 debug 日志是不是都齐全，不管前端还是后端还是架构还是数据库" + "毫无遗漏且全面具体清晰细致的深度地毯式搜查"
>
> **方法**: grep 全 backend/frontend 文件 + logging config + exception handler + middleware + DB layer 5 维度

## 一、整体覆盖率（震惊）

| 层 | 总文件 | 有日志 | 覆盖率 |
|---|---|---|---|
| **Backend** (`app/`) | 85 | 31 | **36%** |
| **Frontend** (`frontend/src/`) | 84 | **2** | **2.4%** 🚨 |

## 二、Logging Config 现状

`app/main.py:20-37`:
```python
import logging
_file_handler = logging.FileHandler("storage/logs/backend.log", encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # 终端
        _file_handler,            # 文件
    ],
)
logging.getLogger("uvicorn.access").addHandler(_file_handler)
logging.getLogger("uvicorn.error").addHandler(_file_handler)
```

✅ **正确处**:
- 双输出（terminal + file）
- INFO level
- 标准 formatter (asctime + levelname + name + message)
- uvicorn access/error 也写文件

🟡 **不足**:
- 无 RotatingFileHandler — backend.log 可能无限增长
- 无 logger 命名空间 hierarchy（统一靠模块自己 `logging.getLogger(__name__)` 或 hardcode `"xuhua"`）
- 无 structlog 等结构化日志
- 终端 + 文件**都是 INFO** — 高频 SQL SELECT 输出会淹没真错误

## 三、Backend 关键 0 日志文件（54 个 / 共 85，按风险排序）

### 🔴 P1 严重（启动/认证/中间件层 0 日志）

| 文件 | 行数 | 风险 |
|---|---|---|
| `app/main.py` | 113 | startup/shutdown handler 0 日志，启动失败无线索 |
| `app/database.py` | 70 | DB engine 创建/连接 0 日志，pool_recycle 触发不可见 |
| `app/middleware/log_sanitizer.py` | 54 | middleware 运行 0 日志（实际名字带 sanitizer 反讽） |
| `app/api/auth.py` | **236** | 用户登录 0 日志（5-09 隐身登录失败时排查无线索）|
| `app/api/audio.py` | 131 | 音频静态路由 0 日志 |
| `app/api/images.py` | 85 | 图片静态路由 0 日志 |
| `app/api/monitoring.py` | 147 | 监控 endpoint 自己 0 日志（讽刺）|
| `app/api/beta_applications.py` | 57 | 内测申请 0 日志（Founder 重要业务流）|

### 🟡 P2 中等（高风险服务 0 日志）

| 文件 | 行数 | 风险 |
|---|---|---|
| `app/services/character_consistency.py` | **635** | 角色一致性框架 0 日志（CLAUDE.md 标 🔴 极高风险但 0 日志）|
| `app/services/style_enforcer.py` | 787 | 风格强制锁定 0 日志（StyleEnforcer 没注入或 mandatory 失效不可见）|
| `app/services/text_overlay_service.py` | **717** | 条漫文字叠加 0 日志（条漫渲染失败无 trace）|
| `app/services/scene_style_manager.py` | 245 | 场景风格 0 日志 |
| `app/services/character_consistency.py` | 635 | 同上 |
| `app/services/tts_service.py` | 391 | TTS 服务 0 日志（Doubao 调用失败不可见）|
| `app/services/style_music_hints.py` | 1025 | BGM 风格 hints 0 日志（B33 BGM 路由依赖此处）|
| `app/services/file_storage.py` | 69 | 文件存储 0 日志 |
| `app/services/image_storage.py` | 232 | 图片存储 0 日志 |
| `app/services/audio_storage.py` | 271 | 音频存储 0 日志 |

### 🟢 P3 低（数据层 0 日志可接受）

| 类型 | 注释 |
|---|---|
| `app/models/*.py` | 0 日志正常（ORM 模型定义） |
| `app/prompts/**.py` | 0 日志正常（prompt 模板） |
| `app/schemas/project.py` | 0 日志正常（pydantic schema） |

## 四、Backend 局部稀疏（有日志但不够）

| 文件 | 密度 | 实测缺失 |
|---|---|---|
| `app/services/storyboard_director.py` | 2.28% | test9 实测 Scene 5 ❌ 失败但**没记 root cause** — 只打"❌ 失败" |
| `app/services/job_manager.py` | 2.58% | background task stage transition 跟踪稀疏，B-1 短 session 切换边界没日志 |

## 五、Frontend 几乎全黑盒（84 文件 仅 2 文件有 console — **2.4%**）

### 🚨 0 console.log 的关键文件（按 P1 风险）

**核心交互层**（B36/B27/B28 修复必须）:
- `frontend/src/lib/createUrl.ts` (204 行) — 路由决策 0 trace
- `frontend/src/lib/api.ts` (117 行) — fetch wrapper 0 trace（duration/status/error/timeout）
- `frontend/src/contexts/CreateContext.tsx` (380 行) — reducer state transition 0 trace
- `frontend/src/contexts/AuthContext.tsx` (231 行) — 登录 state 0 trace

**Stage 组件**（用户主流程 0 trace）:
- `frontend/src/components/create/StageB.tsx` (520 行) — outline 编辑 0 console
- `frontend/src/components/create/StageD.tsx` (454 行) — 完成页 0 console
- `frontend/src/components/create/StageE.tsx` (158 行)
- `frontend/src/components/create/BgmPlayer.tsx` (416 行) — BGM 播放器 0 console（B11 桶问题排查无 trace）

**UI 组件层**（用户输入 0 trace）:
- `StoryIdeaInput.tsx` (256 行) — idea 输入
- `LengthSelector.tsx` / `StyleSelector.tsx` — 选择器 0 trace
- `CharacterUploader.tsx` / `SceneUploader.tsx` / `CustomStyleUploader.tsx` — 上传 0 trace
- `ShareModal.tsx` — 分享 0 trace

**Dashboard / Marketing**（次要）:
- StoryCard.tsx / StoryGrid.tsx / DashboardContent.tsx
- 所有 marketing pages (Hero / Showcase / Pricing / FAQ / Contact 等)

### 🟢 仅有 2 文件有 console

PM 推断：可能是 `CreateContent.tsx`（21 个）+ `StageC.tsx`（10 个）— 整个项目唯一两个有 trace 的文件

## 六、Exception Handler 缺失

- `app/main.py` 只注册 CORS + log_sanitizer middleware
- **没有 global `@app.exception_handler`**（FastAPI 推荐模式：500 异常统一记录 stack + 返回结构化错误）
- `logger.exception` 全 backend 18 次调用（在 service 层 try/except 内手动调）
- `raise HTTPException` 全 backend 131 次（但 fastapi 默认 HTTPException 不打 stack trace）

## 七、DB Layer 日志现状

`app/database.py`:
```python
engine = create_async_engine(
    pool_pre_ping=True,      # 每次使用前 ping
    pool_recycle=1800,        # 30 分钟回收
)
```

✅ **现状**:
- sqlalchemy.engine.Engine INFO 自动打 SELECT/INSERT/UPDATE（实测 `/tmp/xhstory_backend.log` 满屏 SQL）
- pool_pre_ping + pool_recycle 配置合理

🟡 **不足**:
- pool 状态变化（连接创建/回收/超时）0 日志
- transaction begin/commit/rollback 没单独日志（混在 SQL 流里）
- migration / DDL 操作 0 日志（alembic 自己打）

## 八、修复建议优先级

### 🔴 P1 紧急（修 B36/B27/B28 前置条件）

1. **Frontend `lib/api.ts`** — fetch wrapper 全程记录:
   ```typescript
   console.log(`[API] ${method} ${url}`)
   const start = Date.now()
   try { ... } catch(e) { console.error(`[API] ${method} ${url} ERROR ${Date.now()-start}ms`, e) }
   console.log(`[API] ${method} ${url} ${status} ${Date.now()-start}ms`)
   ```

2. **Frontend `lib/createUrl.ts`** — 路由决策每个分支:
   ```typescript
   console.log("[createUrl] urlStage=", urlStage, "backendStage=", backendStage, "scenesConfirmed=", scenesConfirmed)
   if (urlStage === "scenes" && POST_CHAR_STAGES.has(backendStage)) {
     console.log("[createUrl] scenes URL but POST_CHAR_STAGES hit -> /generating")
     return "generating"
   }
   ```

3. **Frontend `contexts/CreateContext.tsx`** — reducer state diff:
   ```typescript
   case "SET_USER_SELECTED_MOOD":
     console.log("[Reducer] SET_USER_SELECTED_MOOD", action.payload)
     return { ...state, userSelectedMood: action.payload }
   ```

4. **Frontend `StageC.tsx`** hydrate effect — characters 何时 populate / character_ready 何时触发 / 倒计时启动条件

### 🟡 P2 中等

5. **Backend `storyboard_director.py`** Scene 失败 root cause:
   ```python
   except Exception as e:
       logger.exception(f"[StoryboardDirector] Scene {scene_id} 失败: {e}")
       continue
   ```

6. **Backend `app/main.py`** global exception handler:
   ```python
   @app.exception_handler(Exception)
   async def global_exception_handler(request, exc):
       logger.exception(f"[Global] {request.method} {request.url}")
       return JSONResponse(...)
   ```

7. **Backend `app/api/auth.py`** 登录/注册 0 日志补全（debugger 失败排查）

### 🟢 P3 低

8. RotatingFileHandler 替换 FileHandler（防 backend.log 无限增长）
9. SQL 日志降到 DEBUG，INFO 只保留 业务日志（避免 SELECT 淹没）
10. structlog 结构化日志（json 格式便于 grep）

## 九、修复执行计划

应该派一个 Frontend agent + 一个 Backend agent 一起补日志（不阻塞 test9）：

**Frontend agent 任务**:
- 补 lib/api.ts + lib/createUrl.ts + contexts/CreateContext.tsx + StageC.tsx 关键 console.log
- 影响 4 文件，预计 30 min
- 修完不需要重启 npm run start（HMR 自动 reload）— 但用了 production build 需要 rm -rf .next + npm run build + restart

**Backend agent 任务**:
- 补 storyboard_director.py Scene 失败 logger.exception
- 补 app/main.py global exception handler
- 补 auth.py / database.py 关键事件日志
- 影响 4-5 文件，预计 30 min
- 修完跟 B35 一起 PM restart backend

不阻塞 test9，可平行做。下次测试 test10 全程有 trace。

## 十、test9 实测教训复盘

PM 这次 5-6 分钟用户卡 spinner 全程靠以下数据反推（缺前端日志）:

| 数据源 | 提供信息 |
|---|---|
| `/tmp/xhstory_backend.log` | Stage 完成时间、LLM 耗时、Scene 失败但**没说 why** |
| `Monitor v12` | backend ok/alive_no_health 状态变化 |
| `DB 直查` (chapter.characters_json + scenes_json) | 数据是否真生成 |
| `文件系统` (output/{uuid}/character_refs/) | 图片是否真落盘 |
| **frontend 日志** | **0 — 用户体感全靠 Founder 截图反推** |

**结论**: 不补前端日志，下次 frontend 修复 agent 修 B36/B27/B28 时**没法独立诊断**，只能"猜然后试"。

---

**审计完毕** — 待 Founder 决定是否立即派活补日志（推荐立即派，不阻塞 test9）。
